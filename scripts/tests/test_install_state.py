import argparse
import importlib.util
import json
import os
import signal
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
            "CLAUDE_CONFIG_DIR": str(self.claude_home),
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

    def persistent_transaction(self, name="test-transaction"):
        module = load_install_state_module()
        return (
            self.state_home
            / "transactions"
            / module.path_identity(self.target)
            / name
        )

    def mark_changes_published(self, snapshot=None):
        snapshot = Path(snapshot or self.transaction)
        module = load_install_state_module()
        with mock.patch.dict(os.environ, self.env):
            _, manifest, before = module.deserialize_snapshot(snapshot)
            after = module.scan_manifest(
                self.target,
                self.claude_home,
                manifest,
            )
            transaction = module.read_transaction(snapshot)
            transaction["published"] = sorted(
                set(transaction["published"])
                | module.changed_record_keys(before, after)
            )
            module.write_transaction(snapshot, transaction)

    def finalize(self, include_home=False, snapshot=None):
        self.mark_changes_published(snapshot)
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

    def test_uninstall_sigkill_after_state_unlink_rolls_forward(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": "uninstall_after_state_unlink",
        }

        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "uninstall",
                "--target",
                str(self.target),
                "--claude-home",
                str(self.claude_home),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(managed.read_text(encoding="utf-8"), "original\n")
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )
        second = self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--json",
        )
        self.assertEqual(json.loads(second.stdout)["recovered"], 0)

    def test_uninstall_sigkill_after_payload_cleanup_recovers_without_payload(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": (
                "uninstall_after_state_generation_cleanup"
            ),
        }

        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "uninstall",
                "--target",
                str(self.target),
                "--claude-home",
                str(self.claude_home),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(managed.read_text(encoding="utf-8"), "original\n")
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )

    def test_uninstall_catchable_post_commit_error_rolls_forward(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        module = load_install_state_module()
        state_file = (
            self.target
            / ".claude"
            / "claude-code-guide-install-state.json"
        )
        original_remove = module.remove_path_durably
        injected = False

        def fail_once_after_state_unlink(path):
            nonlocal injected
            original_remove(path)
            if Path(path) == state_file and not injected:
                injected = True
                raise OSError("injected post-commit fsync failure")

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            dry_run=False,
            json=False,
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "remove_path_durably",
                side_effect=fail_once_after_state_unlink,
            ):
                module.command_uninstall(args)

        self.assertTrue(injected)
        self.assertEqual(managed.read_text(encoding="utf-8"), "original\n")
        self.assertFalse(state_file.exists())
        transaction_parent = (
            self.state_home
            / "transactions"
            / module.path_identity(self.target)
        )
        self.assertEqual(list(transaction_parent.iterdir()), [])

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

    def test_repair_sigkill_after_capture_restores_pre_repair_drift(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()
        managed.write_text("user drift before repair\n", encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": "repair_after_capture",
        }

        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "repair",
                "--target",
                str(self.target),
                "--claude-home",
                str(self.claude_home),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(
            managed.read_text(encoding="utf-8"),
            "user drift before repair\n",
        )
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.run_cli(
            "repair",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(managed.read_text(encoding="utf-8"), "installed\n")

    def test_repair_preserves_edit_after_initial_drift_inspection(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()
        managed.write_text("initial drift\n", encoding="utf-8")

        module = load_install_state_module()
        original_inspect = module.inspect_runtime_state

        def inject_edit_after_inspection(target, claude_home, state):
            report, observed = original_inspect(target, claude_home, state)
            managed.write_text("CONCURRENT USER EDIT\n", encoding="utf-8")
            return report, observed

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            dry_run=False,
            json=False,
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "inspect_runtime_state",
                side_effect=inject_edit_after_inspection,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.command_repair(args)

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
            "publish",
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
        self.assertTrue(destination.is_file())

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

    def test_sigkill_after_generated_capture_recovers_idempotently(self):
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"keep": true}\n', encoding="utf-8")
        transaction = self.persistent_transaction()
        self.begin(output=transaction)
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": "publish_after_capture",
        }

        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "publish",
                "--target",
                str(self.target),
                "--snapshot",
                str(transaction),
                "--scope",
                "project",
                "--path",
                "settings.local.json",
                "--source",
                str(generated),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"keep": true}\n',
        )
        second = self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--json",
        )
        self.assertEqual(json.loads(second.stdout)["recovered"], 0)
        self.assertFalse(transaction.exists())
        self.assertEqual(
            list(destination.parent.glob(".settings.local.json.ccg-base-*")),
            [],
        )
        self.assertEqual(
            list(destination.parent.glob(".settings.local.json.ccg-stage-*")),
            [],
        )

    def test_recovery_preserves_edit_created_after_publish_crash(self):
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"keep": true}\n', encoding="utf-8")
        transaction = self.persistent_transaction("concurrent-recovery")
        self.begin(output=transaction)
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": "publish_after_capture",
        }
        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "publish",
                "--target",
                str(self.target),
                "--snapshot",
                str(transaction),
                "--scope",
                "project",
                "--path",
                "settings.local.json",
                "--source",
                str(generated),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(killed.returncode, -signal.SIGKILL)
        destination.write_text('{"concurrent": true}\n', encoding="utf-8")

        result = self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            expected=2,
        )

        self.assertIn("unexpected", result.stderr.lower())
        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )
        self.assertTrue(transaction.exists())

    def test_finalize_sigkill_after_commit_ready_rolls_forward(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        transaction = self.persistent_transaction("commit-ready")
        self.begin(output=transaction)
        managed.parent.mkdir(parents=True)
        managed.write_text("installed\n", encoding="utf-8")
        self.mark_changes_published(transaction)
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_FAULT_POINT": "finalize_after_commit_ready",
        }

        killed = subprocess.run(
            [
                "python3",
                str(INSTALL_STATE),
                "finalize",
                "--target",
                str(self.target),
                "--snapshot",
                str(transaction),
                "--profile",
                "team",
                "--source-revision",
                "test-revision",
                "--claude-home",
                str(self.claude_home),
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertEqual(killed.returncode, -signal.SIGKILL)
        self.run_cli(
            "recover",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
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
        self.assertFalse(transaction.exists())

    def test_finalize_rejects_change_without_completed_publish_journal(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin()
        managed.parent.mkdir(parents=True)
        managed.write_text("unjournaled\n", encoding="utf-8")

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

        self.assertIn("without a completed publish journal", result.stderr)
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )

    def test_publish_rejects_concurrent_generated_file_base_drift(self):
        self.begin()
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"concurrent": true}\n', encoding="utf-8")
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")

        result = self.run_cli(
            "publish",
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

    def test_publish_does_not_overwrite_edit_after_journal_authorization(self):
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"before": true}\n', encoding="utf-8")
        self.begin()
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        module = load_install_state_module()
        original_write_json = module.write_json_atomic

        def inject_after_authorization(path, payload, mode=0o600):
            original_write_json(path, payload, mode)
            if Path(path).name == "authorized.json":
                replacement = destination.with_name(".concurrent-settings")
                replacement.write_text(
                    '{"concurrent": true}\n',
                    encoding="utf-8",
                )
                os.replace(replacement, destination)

        args = argparse.Namespace(
            target=str(self.target),
            snapshot=str(self.transaction),
            scope="project",
            path="settings.local.json",
            source=str(generated),
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "write_json_atomic",
                side_effect=inject_after_authorization,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.command_publish(args)

        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )
        self.assertTrue(generated.is_file())

    def test_publish_error_recovery_preserves_edit_before_quarantine(self):
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"before": true}\n', encoding="utf-8")
        self.begin()
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        module = load_install_state_module()
        original_replace = module.os.replace
        injected = False

        def fail_after_link(name):
            if name == "publish_after_link":
                raise OSError("injected publish failure")

        def inject_before_recovery_quarantine(source, target):
            nonlocal injected
            if (
                Path(source) == destination
                and ".ccg-recovery-" in Path(target).name
                and not injected
            ):
                injected = True
                destination.write_text(
                    '{"concurrent": true}\n',
                    encoding="utf-8",
                )
            return original_replace(source, target)

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            snapshot=str(self.transaction),
            scope="project",
            path="settings.local.json",
            source=str(generated),
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "fault_point",
                side_effect=fail_after_link,
            ):
                with mock.patch.object(
                    module.os,
                    "replace",
                    side_effect=inject_before_recovery_quarantine,
                ):
                    with self.assertRaises(module.InstallStateError):
                        module.command_publish(args)

        self.assertTrue(injected)
        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )
        self.assertTrue(self.transaction.exists())

    def test_finalize_rejects_edit_after_generated_settings_publish(self):
        destination = self.target / ".claude" / "settings.local.json"
        destination.parent.mkdir(parents=True)
        destination.write_text('{"before": true}\n', encoding="utf-8")
        self.begin()
        generated = self.root / "generated-settings.json"
        generated.write_text('{"hooks": {}}\n', encoding="utf-8")
        self.run_cli(
            "publish",
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
        destination.write_text(
            '{"concurrent": true}\n',
            encoding="utf-8",
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
        self.assertIn("authorized generated file changed", result.stderr.lower())

        rollback = self.run_cli(
            "abort",
            "--target",
            self.target,
            "--snapshot",
            self.transaction,
            "--claude-home",
            self.claude_home,
            expected=2,
        )
        self.assertIn("unexpected drift", rollback.stderr.lower())
        self.assertEqual(
            destination.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
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

    def test_new_manifest_rejects_active_claude_agent_ownership(self):
        for index, managed_path in enumerate(
            (
                "claude-home:agents/code-reviewer.md",
                "claude-home:team",
            )
        ):
            with self.subTest(managed_path=managed_path):
                transaction = self.root / f"rejected-transaction-{index}"
                result = self.run_cli(
                    "begin",
                    "--target",
                    self.target,
                    "--output",
                    transaction,
                    "--claude-home",
                    self.claude_home,
                    "--source",
                    REPO_ROOT,
                    "--profile",
                    "enterprise",
                    "--source-revision",
                    "test-revision",
                    "--managed-file",
                    managed_path,
                    "--include-home",
                    expected=2,
                )

                self.assertIn("team/", result.stderr)
                self.assertFalse(transaction.exists())

    def test_v48_reinstall_relinquishes_legacy_active_agent_ownership(self):
        source_agent = REPO_ROOT / "agents" / "code-reviewer.md"
        managed_path = "team/agents/code-reviewer.md"
        self.begin(include_home=True, managed_paths=[])
        self.run_cli(
            "publish",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--snapshot",
            self.transaction,
            "--scope",
            "claude-home",
            "--path",
            managed_path,
            "--source",
            source_agent,
        )
        self.finalize(include_home=True)

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        first_state_root = self.state_home / state["state_id"]
        entry = next(
            item
            for item in state["entries"]
            if item["scope"] == "claude-home"
            and item["path"] == managed_path
        )

        installed_payload = (
            first_state_root
            / "installed"
            / "claude-home"
            / "team"
            / "agents"
            / "code-reviewer.md"
        )
        legacy_payload = (
            first_state_root
            / "installed"
            / "claude-home"
            / "agents"
            / "code-reviewer.md"
        )
        legacy_payload.parent.mkdir(parents=True)
        installed_payload.replace(legacy_payload)

        installed_agent = self.claude_home / managed_path
        legacy_agent = self.claude_home / "agents" / "code-reviewer.md"
        legacy_agent.parent.mkdir(parents=True)
        installed_agent.replace(legacy_agent)
        shared_adapter = self.root / "shared-adapter.md"
        shutil.copyfile(legacy_agent, shared_adapter)
        legacy_agent.unlink()
        legacy_agent.symlink_to(shared_adapter)

        entry["path"] = "agents/code-reviewer.md"
        state["guide_version"] = "4.7"
        state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        second_transaction = self.root / "transaction-v48"
        self.begin(
            include_home=True,
            managed_paths=[],
            output=second_transaction,
        )
        self.run_cli(
            "publish",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
            "--snapshot",
            second_transaction,
            "--scope",
            "claude-home",
            "--path",
            managed_path,
            "--source",
            source_agent,
        )
        self.finalize(include_home=True, snapshot=second_transaction)

        migrated_state = json.loads(state_file.read_text(encoding="utf-8"))
        managed = {
            (item["scope"], item["path"])
            for item in migrated_state["entries"]
        }
        self.assertIn(("claude-home", managed_path), managed)
        self.assertNotIn(
            ("claude-home", "agents/code-reviewer.md"),
            managed,
        )
        self.assertTrue(legacy_agent.is_symlink())
        self.assertEqual(legacy_agent.resolve(), shared_adapter.resolve())
        self.assertFalse(first_state_root.exists())

        self.run_cli(
            "uninstall",
            "--target",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertTrue(legacy_agent.is_symlink())
        self.assertEqual(legacy_agent.resolve(), shared_adapter.resolve())
        self.assertFalse((self.claude_home / managed_path).exists())

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
        self.state_home.mkdir(exist_ok=True)
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
        self.mark_changes_published()

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
        self.env["GIT_CONFIG_GLOBAL"] = os.devnull
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
        exclude_path = Path(
            subprocess.run(
                [
                    "git",
                    "-C",
                    nested_target,
                    "rev-parse",
                    "--git-path",
                    "info/exclude",
                ],
                text=True,
                capture_output=True,
                check=True,
            ).stdout.strip()
        )
        if not exclude_path.is_absolute():
            exclude_path = nested_target / exclude_path
        self.assertIn(
            "/apps/service/.claude/claude-code-guide-install-state.json",
            exclude_path.read_text(encoding="utf-8").splitlines(),
        )

    def test_source_revision_change_requires_explicit_force_boundary(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        self.begin(source_revision="revision-v1")
        managed.parent.mkdir(parents=True)
        managed.write_text("installed-v1\n", encoding="utf-8")
        self.mark_changes_published()
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

    def test_uninstall_restores_quarantine_when_capture_fails(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        module = load_install_state_module()
        original_path_record = module.path_record

        def fail_quarantine_capture(entry, path):
            if ".ccg-quarantine-" in Path(path).name:
                raise OSError("injected quarantine capture failure")
            return original_path_record(entry, path)

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            dry_run=False,
            json=False,
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module,
                "path_record",
                side_effect=fail_quarantine_capture,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.command_uninstall(args)

        self.assertEqual(managed.read_text(encoding="utf-8"), "installed\n")
        self.assertEqual(
            list(managed.parent.glob(".*.ccg-quarantine-*")),
            [],
        )
        self.assertTrue(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).is_file()
        )

    def test_uninstall_preserves_edit_made_immediately_before_capture(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        module = load_install_state_module()
        original_replace = module.os.replace
        injected = False

        def inject_before_capture(source, destination):
            nonlocal injected
            if (
                Path(source) == managed
                and ".ccg-quarantine-" in Path(destination).name
                and not injected
            ):
                injected = True
                managed.write_text(
                    "CONCURRENT USER EDIT\n",
                    encoding="utf-8",
                )
            return original_replace(source, destination)

        args = argparse.Namespace(
            target=str(self.target),
            claude_home=str(self.claude_home),
            dry_run=False,
            json=False,
        )
        with mock.patch.dict(os.environ, self.env):
            with mock.patch.object(
                module.os,
                "replace",
                side_effect=inject_before_capture,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.command_uninstall(args)

        self.assertTrue(injected)
        self.assertEqual(
            managed.read_text(encoding="utf-8"),
            "CONCURRENT USER EDIT\n",
        )
        transaction_parent = (
            self.state_home
            / "transactions"
            / module.path_identity(self.target)
        )
        self.assertTrue(any(transaction_parent.iterdir()))

    def test_runtime_recovery_preserves_edit_between_check_and_quarantine(self):
        managed = self.target / ".claude" / "skills" / "managed" / "SKILL.md"
        managed.parent.mkdir(parents=True)
        managed.write_text("original\n", encoding="utf-8")
        self.begin()
        managed.write_text("installed\n", encoding="utf-8")
        self.finalize()

        module = load_install_state_module()
        with mock.patch.dict(os.environ, self.env):
            target, claude_home, state, state_root = module.load_runtime_state(
                str(self.target),
                str(self.claude_home),
            )
            entries = list(reversed(state["entries"]))
            before_records = {
                f"{entry['scope']}:{entry['path']}": (
                    module.expected_entry_record(entry, "installed")
                )
                for entry in entries
            }
            snapshot = module.begin_runtime_transaction(
                "uninstall",
                target,
                claude_home,
                state,
                entries,
                before_records,
            )
            managed.write_text("original\n", encoding="utf-8")
            original_replace = module.os.replace
            injected = False

            def inject_before_recovery_quarantine(source, destination):
                nonlocal injected
                if (
                    Path(source) == managed
                    and ".ccg-recovery-" in Path(destination).name
                    and not injected
                ):
                    injected = True
                    managed.write_text(
                        "CONCURRENT USER EDIT\n",
                        encoding="utf-8",
                    )
                return original_replace(source, destination)

            with mock.patch.object(
                module.os,
                "replace",
                side_effect=inject_before_recovery_quarantine,
            ):
                with self.assertRaises(module.InstallStateError):
                    module.recover_runtime_transaction(
                        snapshot,
                        target,
                        claude_home,
                    )

        self.assertTrue(injected)
        self.assertEqual(
            managed.read_text(encoding="utf-8"),
            "CONCURRENT USER EDIT\n",
        )
        self.assertTrue(snapshot.exists())
        self.assertTrue(state_root.exists())

    def test_durable_mkdir_fsyncs_each_new_component_and_parent(self):
        module = load_install_state_module()
        nested = self.root / "durable" / "one" / "two"
        calls = []
        original_fsync = module.fsync_directory

        def record_fsync(path):
            calls.append(Path(path))
            original_fsync(path)

        with mock.patch.object(
            module,
            "fsync_directory",
            side_effect=record_fsync,
        ):
            module.ensure_directory_durable(nested)

        self.assertTrue(nested.is_dir())
        for path in (
            self.root,
            self.root / "durable",
            self.root / "durable" / "one",
            nested,
        ):
            self.assertIn(path, calls)

    def test_stale_state_cleanup_is_scoped_to_current_target(self):
        module = load_install_state_module()
        other_target = self.root / "other-project"
        other_target.mkdir()
        self.state_home.mkdir()
        foreign = self.state_home / (
            f".cleanup-state-{module.path_identity(other_target)}-"
            "deadbeef"
        )
        foreign.mkdir()

        with mock.patch.dict(os.environ, self.env):
            module.cleanup_stale_tombstones(self.target)

        self.assertTrue(foreign.is_dir())


if __name__ == "__main__":
    unittest.main()
