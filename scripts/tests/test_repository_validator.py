import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "validate-repository.py"


class RepositoryValidatorTest(unittest.TestCase):
    def run_validator(self, root, expected=0):
        result = subprocess.run(
            ["python3", str(VALIDATOR), "--root", str(root), "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        return json.loads(result.stdout)

    def test_current_repository_portable_surfaces_are_valid(self):
        report = self.run_validator(REPO_ROOT)
        self.assertEqual(report["status"], "ok")
        self.assertGreater(report["catalog"]["skills"], 0)

    def test_validator_reports_hidden_unicode_personal_paths_and_missing_skill_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "skills" / "broken").mkdir(parents=True)
            (root / "templates").mkdir()
            (root / "templates" / "settings.json.example").write_text(
                '"/Users/alice/.claude"\ntext\u200bhidden\n', encoding="utf-8"
            )

            report = self.run_validator(root, expected=1)
            codes = {item["code"] for item in report["issues"]}
            self.assertIn("missing-skill-contract", codes)
            self.assertIn("personal-absolute-path", codes)
            self.assertIn("hidden-unicode", codes)


if __name__ == "__main__":
    unittest.main()
