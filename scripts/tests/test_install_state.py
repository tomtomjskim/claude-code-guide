import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_STATE = REPO_ROOT / "scripts" / "install_state.py"


def load_install_state_module():
    spec = importlib.util.spec_from_file_location(
        "install_state_under_test",
        INSTALL_STATE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def begin(
        self,
        include_home=False,
        managed_paths=None,
        output=None,
        source_revision="test-revision",
        allow_source_change=False,
    ):
        profile = "enterprise" if include_home else "team"
        args = [
            "begin",
            "--target",
            self.target,
            "--output",
            output or self.transaction,
            "--claude-home",
            self.claude_home,
            "--source",
            REPO_ROOT,
            "--profile",
            profile,
            "--source-revision",
            source_revision,
        ]
        if allow_source_change:
            args.append("--allow-source-change")
        for managed_path in managed_paths or ["project:skills/managed/SKILL.md"]:
            args.extend(["--managed-file", managed_path])
        if include_home:
            args.append("--include-home")
        self.run_cli(*args)

    def finalize(self, include_home=False, snapshot=None):
        profile = "enterprise" if include_home else "team"
        args = [
            "finalize",
            "--target",
            self.target,
            "--snapshot",
            snapshot or self.transaction,
            "--profile",
            profile,
            "--source-revision",
            "test-revision",
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

        self.begin(
            managed_paths=[
                "project:skills/existing/SKILL.md",
                "project:skills/created/SKILL.md",
            ]
        )

        original.write_text("installed\n", encoding="utf-8")
        created = self.target / ".claude" / "skills" / "created" / "SKILL.md"
        created.parent.mkdir(parents=True)
        created.write_text("created\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["source_revision"], "test-revision")
        self.assertRegex(state["target_id"], r"^[0-9a-f]{24}$")
        self.assertRegex(state["state_id"], r"^[0-9a-f]{32}$")
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

    def test_duplicate_state_entry_fails_closed(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["entries"].append(dict(state["entries"][0]))
        state_file.write_text(json.dumps(state), encoding="utf-8")

        result = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("duplicate", result.stderr.lower())

    def test_claude_home_state_entry_outside_allowlist_fails_closed(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        state["entries"][0]["scope"] = "claude-home"
        state["entries"][0]["path"] = ".ssh/config"
        state_file.write_text(json.dumps(state), encoding="utf-8")

        result = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("outside", result.stderr.lower())

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
            "--source-revision",
            "test-revision",
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

    def test_abort_only_rolls_back_declared_write_set(self):
        self.begin(managed_paths=[])
        installed = self.target / ".claude" / "skills" / "dispatch" / "SKILL.md"
        installed.parent.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / "skills" / "dispatch" / "SKILL.md", installed)

        concurrent = (
            self.target
            / ".claude"
            / "skills"
            / "concurrent"
            / "user-created.md"
        )
        concurrent.parent.mkdir(parents=True)
        concurrent.write_text("preserve me\n", encoding="utf-8")

        self.run_cli(
            "abort",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--claude-home",
            self.claude_home,
        )
        self.assertFalse(installed.exists())
        self.assertEqual(concurrent.read_text(encoding="utf-8"), "preserve me\n")

    def test_abort_preserves_unexpected_drift_on_declared_path(self):
        managed = self.target / ".claude" / "skills" / "dispatch" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("before\n", encoding="utf-8")
        self.begin(managed_paths=[])
        managed.write_text("concurrent edit\n", encoding="utf-8")
        safe_installed = self.target / ".claude" / "skills" / "stage" / "SKILL.md"
        safe_installed.parent.mkdir(parents=True)
        shutil.copyfile(
            REPO_ROOT / "skills" / "stage" / "SKILL.md",
            safe_installed,
        )

        result = self.run_cli(
            "abort",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("unexpected drift", result.stderr.lower())
        self.assertEqual(managed.read_text(encoding="utf-8"), "concurrent edit\n")
        self.assertFalse(safe_installed.exists())

    def test_authorized_generated_settings_roll_back_when_previously_absent(self):
        self.begin()
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        self.run_cli(
            "authorize",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--scope",
            "project",
            "--path",
            "settings.local.json",
            "--source",
            generated,
        )
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        os.replace(generated, destination)

        self.run_cli(
            "abort",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--claude-home",
            self.claude_home,
        )
        self.assertFalse(destination.exists())

    def test_authorize_rejects_concurrent_generated_file_base_drift(self):
        self.begin()
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"concurrent": true}\n', encoding="utf-8")
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")

        result = self.run_cli(
            "authorize",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--scope",
            "project",
            "--path",
            "settings.local.json",
            "--source",
            generated,
            expected=2,
        )
        self.assertIn("changed since begin", result.stderr.lower())
        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )

    def test_enterprise_abort_preserves_unmanaged_claude_home_file(self):
        self.begin(include_home=True, managed_paths=[])
        installed = self.claude_home / "team" / "agents.yaml"
        installed.parent.mkdir(parents=True)
        shutil.copyfile(REPO_ROOT / "agents.yaml", installed)
        concurrent = self.claude_home / "team" / "user-created.md"
        concurrent.write_text("preserve me\n", encoding="utf-8")

        self.run_cli(
            "abort",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--claude-home",
            self.claude_home,
            "--include-home",
        )
        self.assertFalse(installed.exists())
        self.assertEqual(concurrent.read_text(encoding="utf-8"), "preserve me\n")

    def test_copied_state_is_rejected_for_a_different_target(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        other_target = self.root / "other-project"
        other_state = other_target / ".claude" / "claude-code-guide-install-state.json"
        other_state.parent.mkdir(parents=True)
        shutil.copyfile(
            self.target / ".claude" / "claude-code-guide-install-state.json",
            other_state,
        )

        result = self.run_cli(
            "doctor",
            "--target",
            other_target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("target", result.stderr.lower())

    def test_finalize_ignores_predictable_state_root_symlink(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")

        predictable_id = __import__("hashlib").sha256(
            str(self.target.resolve()).encode("utf-8")
        ).hexdigest()[:24]
        outside = self.root / "outside"
        outside.mkdir()
        self.state_home.mkdir()
        (self.state_home / predictable_id).symlink_to(
            outside, target_is_directory=True
        )

        self.finalize()
        state = json.loads(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).read_text(encoding="utf-8")
        )
        self.assertNotEqual(state["state_id"], predictable_id)
        self.assertEqual(list(outside.iterdir()), [])

    def test_reinstall_publishes_new_generation_then_removes_old_generation(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed-v1\n", encoding="utf-8")
        self.finalize()
        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        first_state = json.loads(state_file.read_text(encoding="utf-8"))

        second_snapshot = self.root / "transaction-2"
        self.begin(output=second_snapshot)
        managed.write_text("installed-v2\n", encoding="utf-8")
        self.finalize(snapshot=second_snapshot)
        second_state = json.loads(state_file.read_text(encoding="utf-8"))

        self.assertNotEqual(first_state["state_id"], second_state["state_id"])
        self.assertFalse((self.state_home / first_state["state_id"]).exists())
        self.assertTrue((self.state_home / second_state["state_id"]).is_dir())

    def test_reinstall_does_not_silently_adopt_preexisting_drift(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed-v1\n", encoding="utf-8")
        self.finalize()
        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        first_state = json.loads(state_file.read_text(encoding="utf-8"))
        first_entry = first_state["entries"][0]

        managed.write_text("user drift\n", encoding="utf-8")
        second_snapshot = self.root / "transaction-2"
        self.begin(output=second_snapshot)
        self.finalize(snapshot=second_snapshot)
        second_state = json.loads(state_file.read_text(encoding="utf-8"))
        second_entry = second_state["entries"][0]

        self.assertEqual(
            second_entry["installed_sha256"],
            first_entry["installed_sha256"],
        )
        doctor = self.run_cli(
            "doctor",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--json",
            expected=1,
        )
        self.assertEqual(json.loads(doctor.stdout)["status"], "drifted")

    def test_finalize_adds_state_file_to_local_git_exclude(self):
        subprocess.run(
            ["git", "init", "-q", self.target],
            check=True,
            capture_output=True,
        )
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        git_path = subprocess.run(
            [
                "git",
                "-C",
                self.target,
                "rev-parse",
                "--git-path",
                "info/exclude",
            ],
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        exclude_path = Path(git_path)
        if not exclude_path.is_absolute():
            exclude_path = self.target / exclude_path
        self.assertTrue(
            any(
                line.endswith(
                    ".claude/claude-code-guide-install-state.json"
                )
                for line in exclude_path.read_text(encoding="utf-8").splitlines()
            )
        )

    def test_finalize_rejects_a_git_tracked_state_file(self):
        subprocess.run(
            ["git", "init", "-q", self.target],
            check=True,
            capture_output=True,
        )
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state_file.write_text("{}\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", self.target, "add", "-f", state_file],
            check=True,
            capture_output=True,
        )

        result = self.run_cli(
            "finalize",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--profile",
            "team",
            "--source-revision",
            "test-revision",
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("must not be tracked", result.stderr.lower())

    def test_nested_git_target_ignores_repository_relative_state_path(self):
        repository = self.root / "monorepo"
        nested_target = repository / "apps" / "service"
        nested_target.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", repository],
            check=True,
            capture_output=True,
        )
        self.target = nested_target
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        status = subprocess.run(
            [
                "git",
                "-C",
                repository,
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        self.assertNotIn(
            "claude-code-guide-install-state.json",
            status,
        )

    def test_source_revision_change_requires_explicit_force_boundary(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin(source_revision="revision-v1")
        managed.parent.mkdir(parents=True)
        managed.write_text("installed-v1\n", encoding="utf-8")
        self.run_cli(
            "finalize",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--profile",
            "team",
            "--source-revision",
            "revision-v1",
            "--claude-home",
            self.claude_home,
        )

        result = self.run_cli(
            "begin",
            "--target",
            self.target,
            "--output",
            self.root / "transaction-v2",
            "--source",
            REPO_ROOT,
            "--profile",
            "team",
            "--source-revision",
            "revision-v2",
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("--force", result.stderr)

    def test_uninstall_rechecks_managed_file_after_initial_doctor(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        module = load_install_state_module()
        original_doctor = module.doctor_report

        def inject_edit_after_doctor(target, claude_home, state):
            report = original_doctor(target, claude_home, state)
            managed.write_text("CONCURRENT USER EDIT\n", encoding="utf-8")
            return report

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            dry_run=False,
            json=False,
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "doctor_report",
                side_effect=inject_edit_after_doctor,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.command_uninstall(args)

        self.assertEqual(
            managed.read_text(encoding="utf-8"),
            "CONCURRENT USER EDIT\n",
        )
        self.assertTrue(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).is_file()
        )


if __name__ == "__main__":
    unittest.main()
