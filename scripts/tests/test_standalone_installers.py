import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL_HOOKS = REPO_ROOT / "scripts" / "install-hooks.sh"
INSTALL_SKILLS = REPO_ROOT / "scripts" / "install-skills.sh"


class StandaloneInstallerSafetyTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.target = self.root / "project"
        self.target.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        self.env = {
            **os.environ,
            "HOME": str(self.home),
            "CLAUDE_CONFIG_DIR": str(self.home / ".claude"),
            "SHARED_AGENTS_HOME": str(self.home / ".agents"),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_installer(self, script: Path, *arguments):
        return subprocess.run(
            ["bash", str(script), *map(str, arguments)],
            text=True,
            capture_output=True,
            env=self.env,
            check=False,
        )

    def test_installers_reject_symlinked_project_root(self):
        linked_target = self.root / "linked-project"
        linked_target.symlink_to(self.target, target_is_directory=True)

        for script, arguments in (
            (INSTALL_SKILLS, ("--skills", "dispatch", linked_target)),
            (
                INSTALL_HOOKS,
                ("--hooks", "guard-agent", "--no-settings", linked_target),
            ),
        ):
            with self.subTest(script=script.name):
                result = self.run_installer(script, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlink", result.stderr.lower())

        self.assertFalse((self.target / ".claude").exists())

    def test_installers_reject_symlinked_project_claude_directory(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.target / ".claude").symlink_to(
            outside,
            target_is_directory=True,
        )

        for script, arguments in (
            (INSTALL_SKILLS, ("--skills", "dispatch", self.target)),
            (
                INSTALL_HOOKS,
                ("--hooks", "guard-agent", "--no-settings", self.target),
            ),
        ):
            with self.subTest(script=script.name):
                result = self.run_installer(script, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlink", result.stderr.lower())

        self.assertEqual(list(outside.iterdir()), [])

    def test_installers_reject_symlinked_destination_directories(self):
        outside = self.root / "outside"
        outside.mkdir()
        claude_dir = self.target / ".claude"
        claude_dir.mkdir()

        for destination, script, arguments in (
            (
                claude_dir / "skills",
                INSTALL_SKILLS,
                ("--skills", "dispatch", self.target),
            ),
            (
                claude_dir / "hooks",
                INSTALL_HOOKS,
                ("--hooks", "guard-agent", "--no-settings", self.target),
            ),
        ):
            with self.subTest(script=script.name):
                destination.symlink_to(outside, target_is_directory=True)
                result = self.run_installer(script, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlink", result.stderr.lower())
                destination.unlink()

        self.assertEqual(list(outside.iterdir()), [])

    def test_hook_installer_rejects_non_catalog_traversal_name(self):
        outside_destination = self.target / "scripts"
        outside_destination.mkdir()

        result = self.run_installer(
            INSTALL_HOOKS,
            "--hooks",
            "../../scripts/install-hooks",
            "--no-settings",
            self.target,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hook", result.stderr.lower())
        self.assertFalse((outside_destination / "install-hooks.sh").exists())

    def test_team_install_without_force_preserves_existing_agent_pair(self):
        shared_home = Path(self.env["SHARED_AGENTS_HOME"])
        adapter = shared_home / "adapters" / "claude" / "code-reviewer.md"
        adapter.parent.mkdir(parents=True)
        adapter.write_text("existing adapter\n", encoding="utf-8")
        active = Path(self.env["CLAUDE_CONFIG_DIR"]) / "agents" / "code-reviewer.md"
        active.parent.mkdir(parents=True)
        custom_target = self.root / "custom-agent.md"
        custom_target.write_text("custom routing\n", encoding="utf-8")
        active.symlink_to(custom_target)

        result = self.run_installer(
            INSTALL_SKILLS,
            "--team",
            "--skills",
            "dispatch",
            self.target,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertEqual(adapter.read_text(encoding="utf-8"), "existing adapter\n")
        self.assertTrue(active.is_symlink())
        self.assertEqual(active.resolve(), custom_target.resolve())

    def test_team_install_without_force_preserves_active_symlink_without_adapter(self):
        active = Path(self.env["CLAUDE_CONFIG_DIR"]) / "agents" / "code-reviewer.md"
        active.parent.mkdir(parents=True)
        custom_target = self.root / "custom-agent.md"
        custom_target.write_text("custom routing\n", encoding="utf-8")
        active.symlink_to(custom_target)
        adapter = (
            Path(self.env["SHARED_AGENTS_HOME"])
            / "adapters"
            / "claude"
            / "code-reviewer.md"
        )

        result = self.run_installer(
            INSTALL_SKILLS,
            "--team",
            "--skills",
            "dispatch",
            self.target,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertTrue(active.is_symlink())
        self.assertEqual(active.resolve(), custom_target.resolve())
        self.assertFalse(adapter.exists())
        self.assertFalse(adapter.is_symlink())

    def test_team_install_without_force_preserves_dangling_active_symlink(self):
        active = Path(self.env["CLAUDE_CONFIG_DIR"]) / "agents" / "code-reviewer.md"
        active.parent.mkdir(parents=True)
        missing_target = self.root / "missing-custom-agent.md"
        active.symlink_to(missing_target)
        adapter = (
            Path(self.env["SHARED_AGENTS_HOME"])
            / "adapters"
            / "claude"
            / "code-reviewer.md"
        )

        result = self.run_installer(
            INSTALL_SKILLS,
            "--team",
            "--skills",
            "dispatch",
            self.target,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertTrue(active.is_symlink())
        self.assertEqual(os.readlink(active), str(missing_target))
        self.assertFalse(adapter.exists())
        self.assertFalse(adapter.is_symlink())


if __name__ == "__main__":
    unittest.main()
