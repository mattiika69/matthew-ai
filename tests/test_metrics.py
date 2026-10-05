"""Known-answer and failure-boundary tests; all examples are synthetic."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "skills/matthew-ai/scripts/metrics.py"
SPEC = importlib.util.spec_from_file_location("matthew_metrics", SCRIPT)
metrics = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(metrics)


class MetricsTests(unittest.TestCase):
    def calculate(self, values, requested, **context):
        return metrics.calculate({"values": values, "requested": requested, "context": context})

    def test_known_funnel_answers_and_definitions(self):
        values = {"ad_spend": 5000, "impressions": 250000, "clicks": 2500, "leads": 100,
                  "booked_calls": 25, "attended_calls": 20, "closed_calls": 5,
                  "new_customers": 5, "acquisition_cost": 6500, "visitors": 2000, "converted_visitors": 100}
        expected = {"ctr": 1, "cpm": 20, "cpc": 2, "cpl": 50, "cac": 1300,
                    "lead_to_call_rate": 25, "show_rate": 80, "close_rate": 25, "funnel_conversion_rate": 5}
        result = self.calculate(values, list(expected), counts_are_matched_unique_cohort=True,
                                conversion_name="opt-in", acquisition_cost_basis="sales and marketing")
        self.assertEqual({key: value["value"] for key, value in result["metrics"].items()}, expected)
        self.assertEqual(result["excluded"], {})
        self.assertEqual(result["metrics"]["close_rate"]["inputs"], {"closed_calls": 5, "attended_calls": 20})

    def test_roas_mer_aov_are_distinct_not_profit(self):
        result = self.calculate({"ad_spend": 1000, "attributed_revenue": 3000,
                                 "total_revenue": 10000, "total_marketing_spend": 2500,
                                 "order_revenue": 9000, "orders": 30}, ["roas", "mer", "aov"])
        self.assertEqual([result["metrics"][key]["value"] for key in ("roas", "mer", "aov")], [3, 4, 300])
        self.assertTrue(any("not profit" in warning for warning in result["warnings"]))

    def test_ad_spend_does_not_stand_in_for_total_acquisition_cost(self):
        result = self.calculate({"ad_spend": 1000, "new_customers": 5}, ["cac"])
        self.assertEqual(result["excluded"]["cac"]["missing"], ["values.acquisition_cost"])

    def test_cpa_requires_action_definition(self):
        self.assertEqual(self.calculate({"action_cost": 100, "actions": 4}, ["cpa"])["excluded"]["cpa"]["code"], "missing_context")
        result = self.calculate({"action_cost": 100, "actions": 4}, ["cpa"], action_name="booking")
        self.assertEqual(result["metrics"]["cpa"]["value"], 25)

    def test_missing_zero_and_zero_numerator_are_distinct(self):
        for values, code in (({}, "missing_values"), ({"ad_spend": 100, "leads": None}, "missing_values"),
                             ({"ad_spend": 100, "leads": 0}, "zero_denominator")):
            self.assertEqual(self.calculate(values, ["cpl"])["excluded"]["cpl"]["code"], code)
        self.assertEqual(self.calculate({"ad_spend": 0, "leads": 5}, ["cpl"])["metrics"]["cpl"]["value"], 0)

    def test_matched_unique_cohort_required(self):
        result = self.calculate({"booked_calls": 10, "attended_calls": 5}, ["show_rate"])
        self.assertEqual(result["excluded"]["show_rate"]["code"], "unconfirmed_cohort")

    def test_pure_stage_rate_has_no_currency_or_attribution_warning(self):
        result = self.calculate({"booked_calls": 100, "attended_calls": 25}, ["show_rate"],
                                counts_are_matched_unique_cohort=True, period="elapsed booking cohort")
        self.assertEqual(result["metrics"]["show_rate"]["value"], 25)
        self.assertEqual(result["warnings"], [])
        result = self.calculate({"ad_spend": 100, "leads": 5}, ["cpl"])
        self.assertTrue(any("context.currency" in item for item in result["warnings"]))
        self.assertTrue(any("context.attribution" in item for item in result["warnings"]))

    def test_blended_mer_does_not_require_platform_attribution(self):
        result = self.calculate({"total_revenue": 1000, "total_marketing_spend": 200}, ["mer"],
                                period="September", currency="USD", revenue_basis="net of refunds and tax")
        self.assertEqual(result["metrics"]["mer"]["value"], 5)
        self.assertEqual(result["warnings"], ["ROAS and MER are revenue/spend ratios, not profit or proof of incremental acquisition; their revenue and spend scopes differ."])

    def test_contradictory_counts_excluded_without_losing_independent_metrics(self):
        result = self.calculate({"booked_calls": 10, "attended_calls": 15, "clicks": 20,
                                 "impressions": 10, "ad_spend": 100, "leads": 5},
                                ["show_rate", "ctr", "cpl"], counts_are_matched_unique_cohort=True)
        self.assertEqual(result["excluded"]["show_rate"]["code"], "contradictory_counts")
        self.assertEqual(result["excluded"]["ctr"]["code"], "contradictory_counts")
        self.assertEqual(result["metrics"]["cpl"]["value"], 20)
        self.assertEqual(result["status"], "partial")

    def test_unrequested_stage_contradiction_still_reported(self):
        result = self.calculate({"leads": 4, "booked_calls": 10, "attended_calls": 5},
                                ["show_rate"], counts_are_matched_unique_cohort=True)
        self.assertEqual(result["metrics"]["show_rate"]["value"], 50)
        self.assertTrue(any("booked_calls exceeds leads" in warning for warning in result["warnings"]))

    def test_negative_contribution_is_real_loss(self):
        result = self.calculate({"net_revenue": 100, "variable_costs": 150},
                                ["contribution", "contribution_margin"], contribution_basis="fulfillment before acquisition")
        self.assertEqual(result["metrics"]["contribution"]["value"], -50)
        self.assertEqual(result["metrics"]["contribution_margin"]["value"], -50)

    def test_nonpositive_revenue_excludes_margin_not_amount(self):
        for revenue in (0, -20):
            result = self.calculate({"net_revenue": revenue, "variable_costs": 10},
                                    ["contribution", "contribution_margin"], contribution_basis="delivery costs")
            self.assertEqual(result["metrics"]["contribution"]["value"], revenue - 10)
            self.assertEqual(result["excluded"]["contribution_margin"]["code"], "nonpositive_revenue")

    def test_break_even_requires_explicit_contribution_and_horizon(self):
        self.assertEqual(self.calculate({"order_revenue": 1000, "orders": 5}, ["break_even_cac"])["excluded"]["break_even_cac"]["code"], "missing_values")
        self.assertEqual(self.calculate({"contribution_per_new_customer": 100}, ["break_even_cac"])["excluded"]["break_even_cac"]["code"], "missing_context")
        result = self.calculate({"contribution_per_new_customer": 100, "contribution_per_action": 12},
                                ["break_even_cac", "break_even_cpa"], action_name="lead",
                                contribution_basis="net of fulfillment and refunds, before acquisition and fixed overhead", contribution_horizon="first order")
        self.assertEqual(result["metrics"]["break_even_cac"]["value"], 100)
        self.assertEqual(result["metrics"]["break_even_cpa"]["value"], 12)

    def test_negative_contribution_has_no_nonnegative_break_even_spend(self):
        result = self.calculate({"contribution_per_new_customer": -5}, ["break_even_cac"],
                                contribution_basis="before acquisition", contribution_horizon="first order")
        self.assertEqual(result["excluded"]["break_even_cac"]["code"], "negative_contribution")

    def test_payback_requires_assumptions_and_monthly_contribution(self):
        values = {"acquisition_cost": 1000, "new_customers": 5, "monthly_contribution_per_customer": 50}
        context = {"acquisition_cost_basis": "sales plus marketing", "contribution_basis": "monthly net of serving costs, before acquisition"}
        self.assertEqual(self.calculate(values, ["payback_months"], **context)["excluded"]["payback_months"]["code"], "missing_context")
        context["payback_assumptions"] = ["Customers stay at least four months; contribution is constant and begins immediately."]
        self.assertEqual(self.calculate(values, ["payback_months"], **context)["metrics"]["payback_months"]["value"], 4)
        for contribution in (0, -5):
            values["monthly_contribution_per_customer"] = contribution
            self.assertEqual(self.calculate(values, ["payback_months"], **context)["excluded"]["payback_months"]["code"], "nonpositive_denominator")

    def test_ltv_is_not_guessed_from_order_values(self):
        result = self.calculate({"order_revenue": 5000, "orders": 5}, ["aov", "ltv"])
        self.assertEqual(result["metrics"]["aov"]["value"], 1000)
        self.assertEqual(result["excluded"]["ltv"]["code"], "unsupported_metric")

    def test_invalid_numbers_and_typo_rejected(self):
        for value in (True, "100", float("nan"), float("inf"), -1, 10**1000):
            with self.subTest(value=str(value)[:20]), self.assertRaises(metrics.InputError):
                self.calculate({"ad_spend": value}, ["cpl"])
        with self.assertRaises(metrics.InputError):
            self.calculate({"leads": 1.5}, ["cpl"])
        with self.assertRaises(metrics.InputError):
            self.calculate({"ad_spned": 100}, ["cpl"])
        with self.assertRaises(metrics.InputError):
            self.calculate({}, ["cpl"], counts_are_matched_unique_cohort="true")

    def test_overflow_is_excluded(self):
        result = self.calculate({"attributed_revenue": 1e308, "ad_spend": 1e-308}, ["roas"])
        self.assertEqual(result["excluded"]["roas"]["code"], "arithmetic_range")

    def test_scale_invariance_with_consistent_money_units(self):
        for scale in (0.1, 1, 100):
            result = self.calculate({"attributed_revenue": 3210 * scale, "ad_spend": 1070 * scale}, ["roas"])
            self.assertEqual(result["metrics"]["roas"]["value"], 3)

    def test_cli_stdin_json_and_exit_codes(self):
        completed = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps({"values": {"clicks": 1, "impressions": 3}, "requested": ["ctr"]}), text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["metrics"]["ctr"]["value"], 33.33333333)
        for raw in ('{"values":{"ad_spend":NaN}}', '{"values":{"leads":1,"leads":2}}', '{oops'):
            completed = subprocess.run([sys.executable, str(SCRIPT)], input=raw, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 2)
            self.assertEqual(json.loads(completed.stdout)["status"], "invalid_input")

    def test_cli_file_input_and_help(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.json"
            source.write_text(json.dumps({"values": {"clicks": 1, "ad_spend": 5}, "requested": ["cpc"]}))
            completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(source)], text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout)["metrics"]["cpc"]["value"], 5)
        completed = subprocess.run([sys.executable, str(SCRIPT), "--help"], text=True, capture_output=True)
        self.assertEqual(completed.returncode, 0)
        self.assertIn("payback_months", completed.stdout)


if __name__ == "__main__":
    unittest.main()
