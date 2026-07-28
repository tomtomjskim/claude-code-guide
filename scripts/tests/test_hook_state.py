import json
import os
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS = REPO_ROOT / "hooks" / "boilerplates"


class HookStateIsolationTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.state_dir = self.root / "state"
        self.legacy_dir = self.root / "legacy"
        self.legacy_dir.mkdir()

    def tearDown(self):
        self.temp_dir.cleanup()

    def copied_hook(self, name: str) -> Path:
        source = HOOKS / name
        destination = self.root / name
        text = source.read_text(encoding="utf-8")
        text = text.replace("/tmp/claude-hooks", str(self.legacy_dir))
        destination.write_text(text, encoding="utf-8")
        destination.chmod(0o755)
        return destination

    def guard_input(self, session_id=None) -> str:
        payload = {
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "general-purpose",
                "description": "bounded implementation",
                "prompt": "제약: 변경 범위는 지정된 테스트 파일만. 다른 파일 수정 금지.",
            },
        }
        if session_id is not None:
            payload["session_id"] = session_id
        return json.dumps(payload, ensure_ascii=False)

    def run_hook(self, hook: Path, input_text: str, **environment):
        env = {
            **os.environ,
            "CLAUDE_HOOK_STATE_DIR": str(self.state_dir),
            "MIN_PROMPT_LENGTH": "0",
            **environment,
        }
        return subprocess.run(
            ["bash", str(hook)],
            input=input_text,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def counter_files(self):
        if not self.state_dir.exists():
            return []
        return sorted(self.state_dir.glob("agent-count-*"))

    def test_guard_uses_private_override_and_hides_raw_session_id(self):
        hook = self.copied_hook("guard-agent.sh")
        session_id = f"session-{uuid.uuid4()}"

        result = self.run_hook(
            hook,
            self.guard_input(session_id),
            MAX_AGENT_CALLS="3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        counters = self.counter_files()
        self.assertEqual(len(counters), 1)
        self.assertNotIn(session_id, counters[0].name)
        self.assertEqual(counters[0].stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.state_dir.stat().st_mode & 0o777, 0o700)
        self.assertEqual(list(self.legacy_dir.iterdir()), [])

    def test_guard_missing_session_id_is_fail_open_without_counter(self):
        hook = self.copied_hook("guard-agent.sh")

        first = self.run_hook(
            hook,
            self.guard_input(),
            MAX_AGENT_CALLS="1",
        )
        second = self.run_hook(
            hook,
            self.guard_input(),
            MAX_AGENT_CALLS="1",
        )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("session_id", second.stderr)
        self.assertEqual(self.counter_files(), [])
        self.assertEqual(list(self.legacy_dir.iterdir()), [])

    def test_guard_counts_sessions_independently(self):
        hook = self.copied_hook("guard-agent.sh")
        first_session = f"first-{uuid.uuid4()}"
        second_session = f"second-{uuid.uuid4()}"

        first = self.run_hook(
            hook,
            self.guard_input(first_session),
            MAX_AGENT_CALLS="1",
        )
        blocked = self.run_hook(
            hook,
            self.guard_input(first_session),
            MAX_AGENT_CALLS="1",
        )
        independent = self.run_hook(
            hook,
            self.guard_input(second_session),
            MAX_AGENT_CALLS="1",
        )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(blocked.returncode, 2, blocked.stderr)
        self.assertEqual(independent.returncode, 0, independent.stderr)
        self.assertEqual(len(self.counter_files()), 2)

    def test_guard_parallel_increments_are_not_lost(self):
        hook = self.copied_hook("guard-agent.sh")
        session_id = f"parallel-{uuid.uuid4()}"
        env = {
            **os.environ,
            "CLAUDE_HOOK_STATE_DIR": str(self.state_dir),
            "MIN_PROMPT_LENGTH": "0",
            "MAX_AGENT_CALLS": "50",
        }
        processes = [
            subprocess.Popen(
                ["bash", str(hook)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
            for _ in range(12)
        ]

        results = [
            process.communicate(self.guard_input(session_id))
            for process in processes
        ]

        self.assertTrue(
            all(process.returncode == 0 for process in processes),
            results,
        )
        counters = self.counter_files()
        self.assertEqual(len(counters), 1)
        self.assertEqual(counters[0].read_text(encoding="utf-8").strip(), "12")

    def test_guard_rejects_symlinked_state_root_without_writing_target(self):
        hook = self.copied_hook("guard-agent.sh")
        outside = self.root / "outside"
        outside.mkdir()
        self.state_dir.symlink_to(outside, target_is_directory=True)

        result = self.run_hook(
            hook,
            self.guard_input(f"session-{uuid.uuid4()}"),
            MAX_AGENT_CALLS="3",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unsafe", result.stderr.lower())
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual(list(self.legacy_dir.iterdir()), [])

    def test_audit_and_level3_logs_use_private_override(self):
        audit = self.copied_hook("audit-agent.sh")
        careful = self.copied_hook("safety-careful.sh")
        audit_result = self.run_hook(
            audit,
            self.guard_input(f"audit-{uuid.uuid4()}"),
        )
        careful_result = self.run_hook(
            careful,
            json.dumps(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "ALTER TABLE users ADD COLUMN note TEXT"},
                }
            ),
            TMPDIR=str(self.legacy_dir),
        )

        self.assertEqual(audit_result.returncode, 0, audit_result.stderr)
        self.assertEqual(careful_result.returncode, 0, careful_result.stderr)
        self.assertTrue((self.state_dir / "agent-audit.log").is_file())
        self.assertTrue((self.state_dir / "level3.log").is_file())
        self.assertEqual(list(self.legacy_dir.iterdir()), [])

    def test_audit_sanitizes_newlines_in_every_logged_field(self):
        audit = self.copied_hook("audit-agent.sh")
        payload = {
            "tool_name": "Agent",
            "session_id": "session\nforged-session",
            "tool_input": {
                "subagent_type": "reviewer\r\nforged-type",
                "description": "description\nforged-description",
                "prompt": "prompt\r\nforged-prompt",
            },
        }

        result = self.run_hook(
            audit,
            json.dumps(payload),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        log = (self.state_dir / "agent-audit.log").read_text(encoding="utf-8")
        self.assertEqual(len(log.splitlines()), 1)
        self.assertNotIn("\r", log)
        self.assertIn("session=session forged-session", log)
        self.assertIn("type=reviewer  forged-type", log)

    def test_level3_log_sanitizes_command_newlines(self):
        careful = self.copied_hook("safety-careful.sh")
        log_path = self.root / "level3-injection.log"
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "docker rm -f current\n[forged] WARNING",
            },
        }

        result = self.run_hook(
            careful,
            json.dumps(payload),
            LEVEL3_LOG=str(log_path),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        log = log_path.read_text(encoding="utf-8")
        self.assertEqual(len(log.splitlines()), 1)
        self.assertNotIn("\r", log)
        self.assertIn("docker rm -f current [forged] WARNING", log)


if __name__ == "__main__":
    unittest.main()
