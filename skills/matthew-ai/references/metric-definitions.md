# Metric calculations

Load this reference when the member supplies funnel counts, asks for unit economics, or makes a claim based on CAC, CPA, ROAS, contribution, or payback. Use [the calculator](../scripts/metrics.py) for arithmetic when Python execution is available. This is standard arithmetic, **not Matthew's benchmarks or teaching**; source-backed diagnosis belongs in the relevant curated knowledge.

## Calculate and interpret

1. Reuse the member's stated period, currency, attribution, and traffic scope; clarify missing context only where it changes the decision. Keep separate campaigns, periods, currencies, and cohorts in separate inputs.
2. Map actual counts and monetary amounts to the definitions below. Keep unavailable inputs absent or `null`. Use matched unique stage counts for funnel rates; one lead/call/visitor counts at most once at each relevant stage.
3. Run `python3 scripts/metrics.py --input business.json` from the installed skill directory, or send the same JSON to standard input. `--help` lists the supported metrics. Python 3.9+ is sufficient; there are no dependencies or network calls.
4. Check `excluded` and `warnings` before using results. A calculation is done when its numerator, denominator, scope, and limitations are clear; a calculated rate alone does not identify a bottleneck or establish a benchmark.

If code execution is unavailable, explain that limitation and provide the formula and required inputs; do not claim the calculator ran.

## Input and output

```json
{
  "context": {
    "period": "September 2026 lead cohort, observed through October 5",
    "currency": "USD",
    "attribution": "CRM first-touch paid acquisition",
    "traffic_scope": "Meta campaign A only",
    "counts_are_matched_unique_cohort": true,
    "acquisition_cost_basis": "Ad spend plus allocated acquisition sales and marketing costs",
    "revenue_basis": "Collected revenue after refunds, excluding sales tax"
  },
  "values": {
    "ad_spend": 5000,
    "leads": 100,
    "booked_calls": 25,
    "attended_calls": 20,
    "closed_calls": 5,
    "new_customers": 5,
    "acquisition_cost": 6500
  },
  "requested": ["cpl", "lead_to_call_rate", "show_rate", "close_rate", "cac"]
}
```

This synthetic arithmetic example is not a Matthew case study or benchmark. Its outputs are CPL 50, lead-to-call 25%, show 80%, close 25%, and CAC 1300.

`requested` is optional; absent it, every supported metric is attempted, and missing metrics are reported as excluded. Results include the formula, actual inputs, value (rounded to eight decimal places), and unit. Rates use percent units (25 means 25%); ROAS/MER use multiples (2 means 2×). Counts must be whole numbers: fractional modeled platform conversions need a separately defined analysis. Money uses one currency, with its unit reported in `context.currency`.

Exit code 0 means valid input was processed, even if some/all metrics were excluded; inspect `status`, `metrics`, and `excluded`. Exit code 2 means malformed input. Misspelled fields, duplicate JSON keys, numeric strings, booleans used as numbers, negative expenses/counts, and nonfinite numbers are rejected. Missing denominators and zero denominators are separate exclusions. Rate numerators above their denominators are excluded so contradictory counts cannot masquerade as valid conversion rates. Negative revenue/contribution is retained with a warning because refunds and losses can be real.

## Metric meanings

| Output | Inputs and calculation | Required interpretation |
|---|---|---|
| `ctr` | `clicks / impressions × 100` | Define the same click type throughout; this calculator's rate assumes at most one counted click per impression. |
| `cpm` | `ad_spend / impressions × 1000` | Spend and impressions cover the same advertising scope. |
| `cpc` | `ad_spend / clicks` | Same spend and click type as above. |
| `cpl` | `ad_spend / leads` | Leads attributable to that spend; this is advertising CPL, excluding other acquisition costs. |
| `cac` | `acquisition_cost / new_customers` | Acquisition cost includes the sales/marketing cost categories explicitly stated in `acquisition_cost_basis`; orders are not necessarily new customers. |
| `cpa` | `action_cost / actions` | Supply `action_name` and the cost attributable to it; the action could be a lead, booking, sale, or another event. CPA is not automatically CAC. |
| `roas` | `attributed_revenue / ad_spend` | Revenue attributed to that advertising scope; record attribution and revenue treatment. |
| `mer` | `total_revenue / total_marketing_spend` | Blended revenue divided by all marketing spend in the chosen business/period scope; this implementation includes more than ad spend, so label differently scoped source metrics explicitly. |
| `aov` | `order_revenue / orders` | Orders and their corresponding revenue; define refunds, tax, and discounts in `revenue_basis`. |
| `lead_to_call_rate` | `booked_calls / leads × 100` | One first booking per unique lead in the same cohort; repeated bookings require deduplication. |
| `show_rate` | `attended_calls / booked_calls × 100` | Attendance against those same bookings; future appointments cannot yet be classified as no-shows. |
| `close_rate` | `closed_calls / attended_calls × 100` | Unique attended calls that closed, observed long enough for the sales cycle; this is an attended-call close rate. |
| `funnel_conversion_rate` | `converted_visitors / visitors × 100` | Unique visitors reaching the event named in `conversion_name`, with the same cohort and observation window. |
| `contribution` | `net_revenue − variable_costs` | State included cost categories in `contribution_basis`; fixed overhead and omitted costs are not deducted. |
| `contribution_margin` | `(net_revenue − variable_costs) / net_revenue × 100` | Same scope/cost treatment; positive revenue is required. |
| `break_even_cac` | `contribution_per_new_customer` | Explicit contribution **before acquisition cost**, plus `contribution_basis` and `contribution_horizon`; this is a contribution ceiling, not full-company breakeven or a target CAC. |
| `break_even_cpa` | `contribution_per_action` | Explicit expected contribution **before action cost**, plus `action_name`, `contribution_basis`, and `contribution_horizon`; if the action is a lead, the member must supply the justified downstream expected contribution. |
| `payback_months` | `(acquisition_cost / new_customers) / monthly_contribution_per_customer` | Explicit recurring monthly contribution **before acquisition cost**, `acquisition_cost_basis`, `contribution_basis`, and a nonempty `payback_assumptions` array. |

Funnel-stage rates require `counts_are_matched_unique_cohort: true`; a calendar month's leads and calendar month's sales can represent different people. Treat that declaration as a fact to establish, not a switch to set for convenience. The calculator checks local arithmetic contradictions; it cannot verify attribution, source accuracy, elapsed sales cycles, overlapping revenue attribution across platforms, or whether different fields really belong to the same cohort.

Payback is a simplified estimate assuming constant monthly contribution starting immediately, no churn, and no discounting. The explicit assumptions must address retention, timing, and contribution stability; if those are unsupported, report the result as conditional. Zero or negative monthly contribution has no finite payback in this model. Use actual cumulative cohort cash flows for realized payback.

No LTV is inferred from AOV, no benchmark is supplied, and no automatic scaling recommendation is generated. LTV requires an explicit revenue-versus-contribution definition, customer cohort, observation horizon, retention assumptions, and relevant costs; use the supplied source-backed model if available. A high ROAS can coexist with unprofitable fulfillment, and period CAC can be distorted by acquisition timing.

## Cash ratios that are not named calculator metrics

Upfront cash collection and net/recognized revenue are different quantities. Keep `net_revenue` for actual net revenue on the declared accounting basis; **never put upfront cash in that field just to reuse the contribution output**. Cash left after stated costs is not automatically recognized revenue, gross margin, accounting contribution, or profit.

For the cash objective in [economics and benchmarks](economics-benchmarks.md), use a separate transparent Python calculation when needed:

```python
upfront_cash = 12000
acquisition_cost = 2500
fulfillment_cost = 2500
combined_cost = acquisition_cost + fulfillment_cost
cash_multiple = upfront_cash / combined_cost if combined_cost > 0 else None
cash_after_stated_costs = upfront_cash - combined_cost
print({"upfront_cash_multiple": cash_multiple,
       "cash_after_stated_costs": cash_after_stated_costs})
```

Those synthetic inputs produce 2.4× and 7000 remaining before any unstated costs. Confirm that cash and costs concern the same customer/unit and the front-end offer/delivery period being evaluated; label that period explicitly. Preserve the distinction between upfront cash and later recurring revenue or LTV. Read the economics reference for the source's scope before applying its target. Missing inputs remain missing; a zero denominator makes the ratio undefined. Report the exact formula and supplied cost inclusions, and do not infer gross margin unless revenue and complete COGS for that same unit/period are established.

## Definition sources

The [Google Ads metric reference](https://support.google.com/google-ads/answer/9451527?hl=en) and [average CPC definition](https://support.google.com/google-ads/answer/14074?hl=en) support the advertising terminology. [Stripe's CAC payback explanation](https://stripe.com/resources/more/what-is-the-cac-payback-period) supports acquisition-cost/new-customer and monthly-contribution payback arithmetic. These are external definitions, not Matthew's positions; this file specifies the exact operational conventions used by the calculator where labels vary between businesses.
