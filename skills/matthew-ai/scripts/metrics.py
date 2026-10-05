#!/usr/bin/env python3
"""Transparent marketing arithmetic. No dependencies or embedded benchmarks.

Run: python3 metrics.py --input business.json
Or pipe one JSON object to stdin: python3 metrics.py
See ../references/metric-definitions.md for input meanings and limitations.
"""

import argparse
import json
import math
import sys
from pathlib import Path


# name: (numerator field, denominator field, multiplier, unit)
RATIOS = {
    "ctr": ("clicks", "impressions", 100, "percent"),
    "cpm": ("ad_spend", "impressions", 1000, "currency per 1000 impressions"),
    "cpc": ("ad_spend", "clicks", 1, "currency per click"),
    "cpl": ("ad_spend", "leads", 1, "currency per lead"),
    "cac": ("acquisition_cost", "new_customers", 1, "currency per new customer"),
    "cpa": ("action_cost", "actions", 1, "currency per named action"),
    "roas": ("attributed_revenue", "ad_spend", 1, "multiple"),
    "mer": ("total_revenue", "total_marketing_spend", 1, "multiple"),
    "aov": ("order_revenue", "orders", 1, "currency per order"),
    "lead_to_call_rate": ("booked_calls", "leads", 100, "percent"),
    "show_rate": ("attended_calls", "booked_calls", 100, "percent"),
    "close_rate": ("closed_calls", "attended_calls", 100, "percent"),
    "funnel_conversion_rate": ("converted_visitors", "visitors", 100, "percent"),
}
SPECIAL = {
    "contribution": ("net_revenue", "variable_costs"),
    "contribution_margin": ("net_revenue", "variable_costs"),
    "break_even_cac": ("contribution_per_new_customer",),
    "break_even_cpa": ("contribution_per_action",),
    "payback_months": ("acquisition_cost", "new_customers", "monthly_contribution_per_customer"),
}
COUNT_FIELDS = {
    "impressions", "clicks", "leads", "new_customers", "actions", "orders",
    "booked_calls", "attended_calls", "closed_calls", "converted_visitors", "visitors",
}
SIGNED_FIELDS = {
    "attributed_revenue", "total_revenue", "order_revenue", "net_revenue",
    "contribution_per_new_customer", "contribution_per_action", "monthly_contribution_per_customer",
}
VALUE_FIELDS = set().union(*(set(item[:2]) for item in RATIOS.values()), *map(set, SPECIAL.values()))
COHORT_RATES = {"lead_to_call_rate", "show_rate", "close_rate", "funnel_conversion_rate"}
CONTEXT_TEXT = {
    "period", "currency", "attribution", "traffic_scope", "acquisition_cost_basis",
    "action_name", "conversion_name", "revenue_basis", "contribution_basis", "contribution_horizon",
}
CONTEXT_FIELDS = CONTEXT_TEXT | {"counts_are_matched_unique_cohort", "payback_assumptions"}
MONEY_METRICS = set(RATIOS) | set(SPECIAL)
MONEY_METRICS -= COHORT_RATES | {"ctr"}
ATTRIBUTION_METRICS = {"cpl", "cac", "cpa", "roas", "payback_months"}
TRAFFIC_METRICS = {"ctr", "cpm", "cpc", "cpl", "cac", "cpa", "roas", "lead_to_call_rate", "funnel_conversion_rate"}


class InputError(ValueError):
    """Malformed input; no calculations should be relied upon."""


def _validate(payload):
    if not isinstance(payload, dict):
        raise InputError("Input must be a JSON object.")
    unknown = set(payload) - {"values", "context", "requested"}
    if unknown:
        raise InputError("Unknown top-level fields: " + ", ".join(sorted(unknown)))
    values = payload.get("values", {})
    context = payload.get("context", {})
    requested = payload.get("requested", list(RATIOS) + list(SPECIAL))
    if not isinstance(values, dict) or not isinstance(context, dict):
        raise InputError("values and context must be JSON objects.")
    if not isinstance(requested, list) or any(not isinstance(name, str) for name in requested):
        raise InputError("requested must be an array of metric names.")
    if len(set(requested)) != len(requested):
        raise InputError("requested contains duplicate metric names.")
    unknown_values = set(values) - VALUE_FIELDS
    unknown_context = set(context) - CONTEXT_FIELDS
    if unknown_values or unknown_context:
        names = ["values." + key for key in sorted(unknown_values)]
        names += ["context." + key for key in sorted(unknown_context)]
        raise InputError("Unknown fields (check for typos): " + ", ".join(names))
    for name, value in values.items():
        if value is None:
            continue  # Unavailable is not zero.
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InputError(f"values.{name} must be a finite JSON number or null.")
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise InputError(f"values.{name} must be finite and representable.")
        if name not in SIGNED_FIELDS and value < 0:
            raise InputError(f"values.{name} cannot be negative.")
        if name in COUNT_FIELDS and value != int(value):
            raise InputError(f"values.{name} must be a whole count, not a modeled conversion or rate.")
    for name, value in context.items():
        if name in CONTEXT_TEXT and (not isinstance(value, str) or not value.strip()):
            raise InputError(f"context.{name} must be a nonempty string; omit it if unknown.")
        if name == "counts_are_matched_unique_cohort" and not isinstance(value, bool):
            raise InputError(f"context.{name} must be true or false.")
        if name == "payback_assumptions" and (
            not isinstance(value, list) or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)
        ):
            raise InputError("context.payback_assumptions must be a nonempty array of explicit assumptions.")
    return values, context, requested


def calculate(payload):
    """Return calculated metrics and explicit exclusions, never diagnoses."""
    values, context, requested = _validate(payload)
    output = {
        "basis": "standard arithmetic; not Matthew teachings or benchmarks",
        "context": context,
        "rounding_decimal_places": 8,
        "metrics": {},
        "excluded": {},
        "warnings": [],
    }
    warnings = output["warnings"]
    requested_set = set(requested)
    relevant_context = []
    if requested_set & (set(RATIOS) | set(SPECIAL)):
        relevant_context.append("period")
    if requested_set & MONEY_METRICS:
        relevant_context.append("currency")
    if requested_set & ATTRIBUTION_METRICS:
        relevant_context.append("attribution")
    if requested_set & TRAFFIC_METRICS:
        relevant_context.append("traffic_scope")
    for field in relevant_context:
        if field not in context:
            warnings.append(f"Missing context.{field}; arithmetic alone does not establish comparability.")
    if any(values.get(name, 0) is not None and values.get(name, 0) < 0 for name in SIGNED_FIELDS):
        warnings.append("Negative revenue/contribution supplied; confirm refund and cost treatment.")
    if context.get("counts_are_matched_unique_cohort") is True:
        for later, earlier in (("booked_calls", "leads"), ("attended_calls", "booked_calls"),
                               ("closed_calls", "attended_calls"), ("converted_visitors", "visitors")):
            if values.get(later) is not None and values.get(earlier) is not None and values[later] > values[earlier]:
                warnings.append(f"Cohort contradiction: {later} exceeds {earlier}; reconcile before diagnosing the funnel, including when that stage's rate was not requested.")

    def exclude(name, code, detail, missing=None):
        issue = {"code": code, "detail": detail}
        if missing:
            issue["missing"] = missing
        output["excluded"][name] = issue

    def require_context(name, fields):
        missing = ["context." + key for key in fields if not context.get(key)]
        if missing:
            exclude(name, "missing_context", "Define the basis before calculating this metric.", missing)
        return not missing

    for name in requested:
        if name not in RATIOS and name not in SPECIAL:
            exclude(name, "unsupported_metric", "Supported metrics are listed by --help; LTV requires a separate, explicit cohort model.")
            continue
        fields = RATIOS[name][:2] if name in RATIOS else SPECIAL[name]
        missing = ["values." + key for key in fields if values.get(key) is None]
        if missing:
            exclude(name, "missing_values", "Missing inputs are not treated as zero.", missing)
            continue
        inputs = {key: values[key] for key in fields}
        if name in COHORT_RATES and context.get("counts_are_matched_unique_cohort") is not True:
            exclude(name, "unconfirmed_cohort", "Confirm these are matched, unique funnel-stage counts; calendar totals or repeated events cannot establish this conversion rate.")
            continue
        if name in {"cpa", "break_even_cpa"} and not require_context(name, ["action_name"]):
            continue
        if name == "funnel_conversion_rate" and not require_context(name, ["conversion_name"]):
            continue
        if name in {"cac", "payback_months"} and not require_context(name, ["acquisition_cost_basis"]):
            continue
        if name in {"contribution", "contribution_margin", "break_even_cac", "break_even_cpa", "payback_months"}:
            if not require_context(name, ["contribution_basis"]):
                continue
        if name.startswith("break_even_") and not require_context(name, ["contribution_horizon"]):
            continue
        if name == "payback_months" and not require_context(name, ["payback_assumptions"]):
            continue

        try:
            if name in RATIOS:
                top, bottom, multiplier, unit = RATIOS[name]
                if values[bottom] <= 0:
                    exclude(name, "zero_denominator", f"{bottom} is zero; the ratio is undefined, not zero or infinity.")
                    continue
                if (name in COHORT_RATES or name == "ctr") and values[top] > values[bottom]:
                    exclude(name, "contradictory_counts", f"{top} exceeds {bottom}; reconcile counting/cohorts before treating this as a conversion rate.")
                    continue
                result = values[top] / values[bottom] * multiplier
                formula = f"{top} / {bottom}" + (f" * {multiplier}" if multiplier != 1 else "")
            elif name in {"contribution", "contribution_margin"}:
                result = values["net_revenue"] - values["variable_costs"]
                formula, unit = "net_revenue - variable_costs", "currency"
                if name == "contribution_margin":
                    if values["net_revenue"] <= 0:
                        exclude(name, "nonpositive_revenue", "Contribution margin requires positive net revenue; contribution amount remains calculable.")
                        continue
                    result = result / values["net_revenue"] * 100
                    formula, unit = "(net_revenue - variable_costs) / net_revenue * 100", "percent"
            elif name.startswith("break_even_"):
                field = fields[0]
                if values[field] < 0:
                    exclude(name, "negative_contribution", "Negative contribution leaves no nonnegative acquisition/action spend that breaks even.")
                    continue
                result, formula = values[field], field
                unit = "currency per new customer" if name.endswith("cac") else "currency per named action"
                warnings.append(f"{name} is only the supplied contribution ceiling over {context['contribution_horizon']}; it excludes costs not included in contribution_basis and is not a recommended bid.")
            else:  # payback_months
                if values["new_customers"] <= 0 or values["monthly_contribution_per_customer"] <= 0:
                    exclude(name, "nonpositive_denominator", "Positive new customers and monthly contribution per customer are required for a finite payback estimate.")
                    continue
                result = (values["acquisition_cost"] / values["new_customers"]) / values["monthly_contribution_per_customer"]
                formula = "(acquisition_cost / new_customers) / monthly_contribution_per_customer"
                unit = "months"
                warnings.append("payback_months assumes constant monthly contribution beginning immediately, no churn, and no discounting; verify the stated assumptions and use cash-flow cohorts for actual payback.")
            if not math.isfinite(result):
                raise OverflowError
        except (OverflowError, ZeroDivisionError):
            exclude(name, "arithmetic_range", "Inputs exceed the supported numeric range; rescale money consistently or verify the data.")
            continue
        output["metrics"][name] = {"value": round(result, 8), "unit": unit, "formula": formula, "inputs": inputs}

    if "roas" in output["metrics"] or "mer" in output["metrics"]:
        warnings.append("ROAS and MER are revenue/spend ratios, not profit or proof of incremental acquisition; their revenue and spend scopes differ.")
    if not context.get("revenue_basis") and any(name in output["metrics"] for name in ("aov", "roas", "mer", "contribution", "contribution_margin")):
        warnings.append("Specify context.revenue_basis before comparing results: refunds, discounts, tax, and recognition timing can change the numerator.")
    output["status"] = "partial" if output["excluded"] else "calculated"
    if not output["metrics"]:
        output["status"] = "no_metrics_calculated"
    return output


def _reject_constant(value):
    raise InputError(f"{value} is not a finite JSON number.")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog="Metrics: " + ", ".join(list(RATIOS) + list(SPECIAL)))
    parser.add_argument("--input", type=Path, help="JSON file; otherwise read stdin")
    args = parser.parse_args(argv)
    try:
        raw = args.input.read_text(encoding="utf-8") if args.input else sys.stdin.read()
        payload = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        result = calculate(payload)
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "invalid_input", "error": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
