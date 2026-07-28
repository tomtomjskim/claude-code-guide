import json
import os
import signal
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
QUICK_SETUP = REPO_ROOT / "scripts" / "quick-setup.sh"
MANAGE_INSTALL = REPO_ROOT / "scripts" / "manage-install.sh"
VALIDATE_SYSTEM = REPO_ROOT / "scripts" / "validate-system.sh"


class QuickSetupLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.target = self.root / "project"
        self.target.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.claude_home = self.home / ".claude"
        self.state_home = self.root / "state"
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "CLAUDE_CONFIG_DIR": str(self.claude_home),
            "CLAUDE_CODE_GUIDE_SOURCE": str(REPO_ROOT),
            "CLAUDE_CODE_GUIDE_STATE_HOME": str(self.state_home),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_command(self, *command, expected=0):
        result = subprocess.run(
            list(map(str, command)),
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

    def test_solo_install_records_state_and_is_manageable(self):
        self.run_command(
            "bash",
            QUICK_SETUP,
            "--profile",
            "solo",
            "--target",
            self.target,
            "--skip-stack",
        )

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["profile"], "solo")
        self.assertGreater(len(state["entries"]), 0)

        doctor = self.run_command(
            "bash",
            MANAGE_INSTALL,
            "doctor",
            "--target",
            self.target,
            "--json",
        )
        self.assertEqual(json.loads(doctor.stdout)["status"], "ok")

    def test_local_script_uses_its_checkout_without_source_override(self):
        env = dict(self.env)
        env.pop("CLAUDE_CODE_GUIDE_SOURCE")
        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        self.assertTrue(state_file.is_file())

    def test_dry_run_does_not_write_target_or_state(self):
        self.run_command(
            "bash",
            QUICK_SETUP,
            "--profile",
            "solo",
            "--target",
            self.target,
            "--skip-stack",
            "--dry-run",
        )
        self.assertFalse((self.target / ".claude").exists())
        self.assertFalse(self.state_home.exists())

    def test_quick_setup_rejects_symlink_target(self):
        linked_target = self.root / "linked-project"
        linked_target.symlink_to(self.target, target_is_directory=True)
        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(linked_target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())
        self.assertFalse((self.target / ".claude").exists())

    def test_remote_dry_run_keeps_requested_source_ref(self):
        env = dict(self.env)
        env.pop("CLAUDE_CODE_GUIDE_SOURCE")
        result = subprocess.run(
            [
                "bash",
                "-s",
                "--",
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
                "--dry-run",
                "--ref",
                "v4.5.0",
            ],
            input=QUICK_SETUP.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            env=env,
            cwd=self.target,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("preview only", result.stderr.lower())
        self.assertIn("v4.5.0", result.stdout)
        self.assertFalse((self.target / ".claude").exists())

    def test_stdin_execution_does_not_misdetect_parent_as_local_checkout(self):
        fake_guide = self.root / "fake-guide"
        fake_scripts = fake_guide / "scripts"
        fake_scripts.mkdir(parents=True)
        (fake_scripts / "install_state.py").write_text(
            "# marker only\n", encoding="utf-8"
        )
        env = dict(self.env)
        env.pop("CLAUDE_CODE_GUIDE_SOURCE")
        result = subprocess.run(
            [
                "bash",
                "-s",
                "--",
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
                "--dry-run",
                "--ref",
                "v4.5.0",
            ],
            input=QUICK_SETUP.read_text(encoding="utf-8"),
            text=True,
            capture_output=True,
            env=env,
            cwd=fake_scripts,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn("preview only", result.stderr.lower())
        self.assertIn("v4.5.0", result.stdout)

    def test_remote_apply_rejects_moving_or_short_refs_before_network_access(self):
        env = dict(self.env)
        env.pop("CLAUDE_CODE_GUIDE_SOURCE")
        for source_ref in ("main", "v4.5.0", "abcdef1"):
            with self.subTest(source_ref=source_ref):
                result = subprocess.run(
                    [
                        "bash",
                        "-s",
                        "--",
                        "--profile",
                        "solo",
                        "--target",
                        str(self.target),
                        "--skip-stack",
                        "--ref",
                        source_ref,
                    ],
                    input=QUICK_SETUP.read_text(encoding="utf-8"),
                    text=True,
                    capture_output=True,
                    env=env,
                    cwd=self.target,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("40-character commit", result.stderr)
                self.assertFalse((self.target / ".claude").exists())

    def test_enterprise_install_validates_with_explicit_project_and_claude_home(self):
        self.run_command(
            "bash",
            QUICK_SETUP,
            "--profile",
            "enterprise",
            "--target",
            self.target,
            "--skip-stack",
        )

        validation = self.run_command(
            "bash",
            VALIDATE_SYSTEM,
            "--project",
            self.target,
            "--claude-home",
            self.claude_home,
        )
        self.assertIn("System validation PASSED", validation.stdout)

    def test_enterprise_install_honors_custom_claude_config_dir(self):
        custom_claude_home = self.home / "custom-claude"
        env = {
            **self.env,
            "CLAUDE_CONFIG_DIR": str(custom_claude_home),
        }
        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "enterprise",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertTrue((custom_claude_home / "team" / "agents.yaml").is_file())
        self.assertFalse((self.home / ".claude" / "team").exists())

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertIn("claude-home", {entry["scope"] for entry in state["entries"]})

        unmanaged = custom_claude_home / "team" / "keep-unmanaged.txt"
        unmanaged.write_text("keep\n", encoding="utf-8")
        uninstall = subprocess.run(
            [
                "bash",
                str(MANAGE_INSTALL),
                "uninstall",
                "--target",
                str(self.target),
                "--json",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            uninstall.returncode,
            0,
            msg=f"stdout:\n{uninstall.stdout}\nstderr:\n{uninstall.stderr}",
        )
        self.assertEqual(unmanaged.read_text(encoding="utf-8"), "keep\n")
        self.assertFalse((custom_claude_home / "team" / "agents.yaml").exists())
        self.assertFalse(state_file.exists())

    def test_failed_enterprise_validation_leaves_uninstallable_state(self):
        broken_source = self.root / "broken-guide"
        shutil.copytree(
            REPO_ROOT,
            broken_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        (broken_source / "prompts" / "pm.md").unlink()
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_SOURCE": str(broken_source),
        }
        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "enterprise",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)

        state_file = self.target / ".claude" / "claude-code-guide-install-state.json"
        self.assertTrue(state_file.is_file())
        uninstall = subprocess.run(
            [
                "bash",
                str(MANAGE_INSTALL),
                "uninstall",
                "--target",
                str(self.target),
                "--json",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(
            uninstall.returncode,
            0,
            msg=f"stdout:\n{uninstall.stdout}\nstderr:\n{uninstall.stderr}",
        )
        self.assertFalse(state_file.exists())

    def test_failed_install_step_rolls_back_partial_changes(self):
        broken_source = self.root / "broken-install-guide"
        shutil.copytree(
            REPO_ROOT,
            broken_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        (broken_source / "scripts" / "install-hooks.sh").write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    'target="${@: -1}"',
                    'mkdir -p "$target/.claude/hooks"',
                    'printf "partial\\n" > "$target/.claude/hooks/partial.sh"',
                    "exit 42",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        existing = self.target / ".claude" / "skills" / "existing" / "SKILL.md"
        existing.parent.mkdir(parents=True)
        existing.write_text("keep-original\n", encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_SOURCE": str(broken_source),
        }

        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        self.assertEqual(result.returncode, 42)
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep-original\n")
        self.assertFalse((self.target / ".claude" / "skills" / "dispatch").exists())
        self.assertEqual(
            (
                self.target / ".claude" / "hooks" / "partial.sh"
            ).read_text(encoding="utf-8"),
            "partial\n",
        )
        self.assertFalse(
            (self.target / ".claude" / "claude-code-guide-install-state.json").exists()
        )

    def test_preexisting_install_lock_blocks_a_second_install(self):
        lock = self.target / ".claude" / ".claude-code-guide-install.lock"
        lock.mkdir(parents=True)
        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("install lock", result.stderr.lower())

    def test_force_overlays_managed_files_without_deleting_user_additions(self):
        extra = (
            self.target
            / ".claude"
            / "skills"
            / "dispatch"
            / "USER-NOTES.md"
        )
        extra.parent.mkdir(parents=True)
        extra.write_text("keep this file\n", encoding="utf-8")

        self.run_command(
            "bash",
            QUICK_SETUP,
            "--profile",
            "solo",
            "--target",
            self.target,
            "--skip-stack",
            "--force",
        )

        self.assertEqual(extra.read_text(encoding="utf-8"), "keep this file\n")
        self.assertTrue(
            (
                self.target
                / ".claude"
                / "skills"
                / "dispatch"
                / "SKILL.md"
            ).is_file()
        )

    def test_term_signal_rolls_back_and_releases_install_lock(self):
        slow_source = self.root / "slow-install-guide"
        shutil.copytree(
            REPO_ROOT,
            slow_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        marker = self.root / "hooks-started"
        (slow_source / "scripts" / "install-hooks.sh").write_text(
            "\n".join(
                [
                    "#!/bin/bash",
                    f"touch {marker}",
                    "sleep 30",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_SOURCE": str(slow_source),
        }
        process = subprocess.Popen(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )
        deadline = time.monotonic() + 10
        while not marker.exists() and process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                self.fail("hook installer did not reach the signal checkpoint")
            time.sleep(0.05)

        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        self.assertNotEqual(
            process.returncode,
            0,
            msg=f"stdout:\n{stdout}\nstderr:\n{stderr}",
        )
        self.assertFalse((self.target / ".claude" / "skills" / "dispatch").exists())
        self.assertFalse(
            (
                self.target
                / ".claude"
                / ".claude-code-guide-install.lock"
            ).exists()
        )

    def test_term_after_settings_write_restores_existing_settings(self):
        slow_source = self.root / "slow-settings-guide"
        shutil.copytree(
            REPO_ROOT,
            slow_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        marker = self.root / "settings-written"
        hook_installer = slow_source / "scripts" / "install-hooks.sh"
        original_script = hook_installer.read_text(encoding="utf-8")
        published_marker = "    # CCG_SETTINGS_PUBLISHED\n"
        self.assertIn(published_marker, original_script)
        hook_installer.write_text(
            original_script.replace(
                published_marker,
                published_marker
                + f'    touch "{marker}"\n'
                + "    sleep 30\n",
                1,
            ),
            encoding="utf-8",
        )
        settings = self.target / ".claude" / "settings.local.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"keep": true}\n', encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_SOURCE": str(slow_source),
        }
        process = subprocess.Popen(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )
        deadline = time.monotonic() + 10
        while not marker.exists() and process.poll() is None:
            if time.monotonic() >= deadline:
                process.kill()
                self.fail("settings installer did not reach the signal checkpoint")
            time.sleep(0.05)

        os.killpg(process.pid, signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
        self.assertNotEqual(
            process.returncode,
            0,
            msg=f"stdout:\n{stdout}\nstderr:\n{stderr}",
        )
        self.assertNotIn("unexpected drift", stderr.lower())
        self.assertEqual(settings.read_text(encoding="utf-8"), '{"keep": true}\n')
        self.assertFalse((self.target / ".claude" / "skills" / "dispatch").exists())
        self.assertFalse((self.target / ".claude" / "hooks" / "guard-agent.sh").exists())
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )

    def test_edit_after_settings_publish_is_preserved_and_install_fails(self):
        edited_source = self.root / "edited-settings-guide"
        shutil.copytree(
            REPO_ROOT,
            edited_source,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        hook_installer = edited_source / "scripts" / "install-hooks.sh"
        original_script = hook_installer.read_text(encoding="utf-8")
        published_marker = "    # CCG_SETTINGS_PUBLISHED\n"
        self.assertIn(published_marker, original_script)
        hook_installer.write_text(
            original_script.replace(
                published_marker,
                published_marker
                + "    printf '%s\\n' '{\"concurrent\": true}' "
                + '> "$TARGET_SETTINGS"\n',
                1,
            ),
            encoding="utf-8",
        )
        settings = self.target / ".claude" / "settings.local.json"
        settings.parent.mkdir(parents=True)
        settings.write_text('{"keep": true}\n', encoding="utf-8")
        env = {
            **self.env,
            "CLAUDE_CODE_GUIDE_SOURCE": str(edited_source),
        }

        result = subprocess.run(
            [
                "bash",
                str(QUICK_SETUP),
                "--profile",
                "solo",
                "--target",
                str(self.target),
                "--skip-stack",
            ],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "authorized generated file changed",
            result.stderr.lower(),
        )
        self.assertEqual(
            settings.read_text(encoding="utf-8"),
            '{"concurrent": true}\n',
        )
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "claude-code-guide-install-state.json"
            ).exists()
        )
        self.assertFalse(
            (
                self.target
                / ".claude"
                / "skills"
                / "dispatch"
                / "SKILL.md"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
