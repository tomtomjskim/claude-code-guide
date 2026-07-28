import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_STATE = REPO_ROOT / "scripts" / "install_state.py"


class InstallStateCliTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.target = self.root / "project"
        self.target.mkdir()
        self.transaction = self.root / "transaction"
        self.state_home = self.root / "state"
        self.claude_home = self.root / "claude-home"
        self.env = {
            **os.environ,
            "CLAUDE_CODE_GUIDE_STATE_HOME": str(self.state_home),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_cli(self, *args, expected=0):
        result = subprocess.run(
            ["python3", str(INSTALL_STATE), *map(str, args)],
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return result

    def begin(self, include_home=False):
        args = [
            "begin",
            "--target",
            self.target,
            "--output",
            self.transaction,
            "--claude-home",
            self.claude_home,
        ]
        if include_home:
            args.append("--include-home")
        self.run_cli(*args)

    def finalize(self, include_home=False):
        args = [
            "finalize",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--profile",
            "team",
            "--claude-home",
            self.claude_home,
        ]
        if include_home:
            args.append("--include-home")
        self.run_cli(*args)

    def test_finalize_doctor_repair_and_uninstall_restore_original_state(self):
        original = self.target / ".claude" / "skills" / "existing" / "SKILL.md"
        original.parent.mkdir(parents=True)
        original.write_text("original\n", encoding="utf-8")

        self.begin()

        original.write_text("installed\n", encoding="utf-8")
        created = self.target / ".claude" / "skills" / "created" / "SKILL.md"
        created.parent.mkdir(parents=True)
        created.write_text("created\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(
            {(entry["scope"], entry["path"]) for entry in state["entries"]},
            {
                ("project", "skills/created/SKILL.md"),
                ("project", "skills/existing/SKILL.md"),
            },
        )

        doctor = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--json",
        )
        self.assertEqual(json.loads(doctor.stdout)["status"], "ok")

        original.write_text("drifted\n", encoding="utf-8")
        drift = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--json",
            expected=1,
        )
        self.assertEqual(json.loads(drift.stdout)["status"], "drifted")

        unmanaged = self.target / ".claude" / "skills" / "unmanaged" / "SKILL.md"
        unmanaged.parent.mkdir(parents=True)
        unmanaged.write_text("keep\n", encoding="utf-8")
        self.run_cli(
            "repair",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(original.read_text(encoding="utf-8"), "installed\n")
        self.assertEqual(unmanaged.read_text(encoding="utf-8"), "keep\n")

        self.run_cli(
            "uninstall",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(original.read_text(encoding="utf-8"), "original\n")
        self.assertFalse(created.exists())
        self.assertEqual(unmanaged.read_text(encoding="utf-8"), "keep\n")
        self.assertFalse(state_file.exists())

    def test_dry_run_does_not_change_drift_or_install_state(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state_before = state_file.read_bytes()
        managed.write_text("drifted\n", encoding="utf-8")

        repair = self.run_cli(
            "repair",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--dry-run",
            "--json",
        )
        self.assertEqual(json.loads(repair.stdout)["planned"], 1)
        self.assertEqual(managed.read_text(encoding="utf-8"), "drifted\n")

        uninstall = self.run_cli(
            "uninstall",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--dry-run",
            "--json",
        )
        self.assertEqual(json.loads(uninstall.stdout)["planned"], 1)
        self.assertEqual(managed.read_text(encoding="utf-8"), "drifted\n")
        self.assertEqual(state_file.read_bytes(), state_before)

    def test_repair_rejects_symlinked_destination_parent(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        outside = self.root / "outside"
        outside.mkdir()
        outside_file = outside / "managed" / "SKILL.md"
        outside_file.parent.mkdir()
        outside_file.write_text("outside\n", encoding="utf-8")

        shutil.rmtree(self.target / ".claude" / "skills")
        (self.target / ".claude" / "skills").symlink_to(outside, target_is_directory=True)

        result = self.run_cli(
            "repair",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("symlink", result.stderr.lower())
        self.assertEqual(outside_file.read_text(encoding="utf-8"), "outside\n")

    def test_unknown_schema_version_fails_closed(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["schema_version"] = 999
        state_file.write_text(json.dumps(state), encoding="utf-8")

        result = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("unsupported schema", result.stderr.lower())

    def test_state_id_path_traversal_fails_closed(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["state_id"] = "../outside"
        state_file.write_text(json.dumps(state), encoding="utf-8")
        (self.root / "outside").mkdir()

        result = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("state_id", result.stderr)

    def test_begin_rejects_existing_state_from_different_claude_home(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        second_transaction = self.root / "second-transaction"
        other_claude_home = self.root / "other-claude-home"
        result = self.run_cli(
            "begin",
            "--target",
            self.target,
            "--output",
            second_transaction,
            "--claude-home",
            other_claude_home,
            expected=2,
        )
        self.assertIn("Claude home", result.stderr)
        self.assertFalse(second_transaction.exists())

    def test_uninstall_rejects_tampered_previous_payload(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        previous_payload = (
            self.state_home
            / state["state_id"]
            / "previous"
            / "project"
            / "skills"
            / "managed"
            / "SKILL.md"
        )
        previous_payload.write_text("tampered\n", encoding="utf-8")

        result = self.run_cli(
            "uninstall",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("payload", result.stderr.lower())
        self.assertEqual(managed.read_text(encoding="utf-8"), "installed\n")
        self.assertTrue(state_file.exists())

    def test_repair_rejects_tampered_installed_payload(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        installed_payload = (
            self.state_home
            / state["state_id"]
            / "installed"
            / "project"
            / "skills"
            / "managed"
            / "SKILL.md"
        )
        installed_payload.write_text("tampered\n", encoding="utf-8")
        managed.write_text("drifted\n", encoding="utf-8")

        result = self.run_cli(
            "repair",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("payload", result.stderr.lower())
        self.assertEqual(managed.read_text(encoding="utf-8"), "drifted\n")


if __name__ == "__main__":
    unittest.main()
