import unittest
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ReasoningStateCostHardeningTest(unittest.TestCase):
    def read(self, relative_path: str) -> str:
        return (REPO_ROOT / relative_path).read_text(encoding="utf-8")

    def test_cache_write_example_uses_non_overlapping_usage_fields(self):
        input_cost = Decimal("10000") * Decimal("3") / Decimal("1000000")
        cache_write_cost = Decimal("40000") * Decimal("3.75") / Decimal("1000000")
        output_cost = Decimal("3000") * Decimal("15") / Decimal("1000000")

        self.assertEqual(input_cost + cache_write_cost + output_cost, Decimal("0.225"))

        doc = self.read("docs/15-token-pricing-optimization.md")
        self.assertIn("합계:                                      $0.225", doc)
        self.assertNotIn("$0.000345", doc)
        self.assertIn("cache token 이중 계산 금지", doc)

    def test_cache_read_example_is_correct(self):
        input_cost = Decimal("10000") * Decimal("3") / Decimal("1000000")
        cache_read_cost = Decimal("40000") * Decimal("0.30") / Decimal("1000000")
        output_cost = Decimal("3000") * Decimal("15") / Decimal("1000000")

        self.assertEqual(input_cost + cache_read_cost + output_cost, Decimal("0.087"))

    def test_fast_mode_uses_current_supported_models_and_prices(self):
        doc = self.read("docs/18-fast-mode.md")

        for required in (
            "Claude Opus 5, Claude Opus 4.8",
            "Input $10 / MTok, Output $50 / MTok",
            "fastModePerSessionOptIn",
            "CLAUDE_CODE_DISABLE_FAST_MODE",
            "$0.750",
        ):
            with self.subTest(required=required):
                self.assertIn(required, doc)

        self.assertNotIn("Opus 4.6 전용 고속 출력 모드", doc)
        self.assertNotIn("반드시 비활성화해야 합니다", doc)

    def test_context_doc_separates_thinking_and_checkpoint(self):
        doc = self.read("docs/19-context-window-internals.md")

        for required in (
            "redacted_thinking",
            "model switch",
            "Semantic checkpoint",
            "logging allowlist",
            "autoCompactWindow",
        ):
            with self.subTest(required=required):
                self.assertIn(required, doc)

    def test_harness_uses_current_precedence_and_safe_examples(self):
        doc = self.read("docs/29-harness-engineering.md")

        self.assertIn(
            "Managed settings\n→ command line arguments\n→ local settings\n→ project settings\n→ user settings",
            doc,
        )
        self.assertIn("prepared statement", doc)
        self.assertIn("감사 로그 Allowlist", doc)
        self.assertIn("Provider State", doc)
        self.assertNotIn("SQL 파라미터 바인딩 사용하지 않음", doc)
        self.assertNotIn("유일한 방법입니다", doc)

    def test_plan_records_second_order_cost_error(self):
        plan = self.read("docs/plans/2026-08-13-reasoning-state-cost-hardening.md")

        self.assertIn("두 번째 오류", plan)
        self.assertIn("$0.225", plan)
        self.assertIn("managed settings를 최고 우선순위", plan)


if __name__ == "__main__":
    unittest.main()
