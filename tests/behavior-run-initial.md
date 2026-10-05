# Initial behavior smoke run

Run date: October 5, 2026. Runner: one Codex subagent reading the repository's `skills/matthew-ai/SKILL.md` and the selected local references listed for each case. Prompts and business numbers are synthetic. The answers below were produced during this run; they are not prerecorded expected answers.

This is a **single-session agent dry run**, not a Claude account/integration test, independent per-case isolation, an automated repeated evaluation, or Matthew's acceptance. Previously read material remained in the agent's context. References listed per case describe the intended retrieval route and material consulted, not proof of context isolation. Source assertions came from the repository's curated library; original audio and member assets were not separately verified in this run. No skill/reference edits were made for this evaluation.

## 1. An empty funnel-audit request

**Prompt:** “Audit my funnel.”

**Files loaded:** `SKILL.md`; `references/diagnosis.md`.

**Actual answer:**

> What do you sell, to whom, at what price, and where does the traffic come from? Paste the actual funnel stages with spend and counts from one matched cohort—leads → bookings → attended calls → customers if you sell on calls—and flag anything you don't have. That lets me identify the likely constraint instead of guessing which page or stage needs changing.

**Tools/calculations:** Read the skill and diagnosis reference; no calculator invocation because no values were supplied.

**Observed limitation:** This produces the necessary intake rather than a diagnosis. It assumes no specific funnel structure and offers the call-based chain only conditionally. It has not yet assessed offer quality or inspected any asset.

## 2. A bounded hook rewrite

**Prompt:** “Rewrite this hook: We deliver exclusive roofing quote requests into your CRM. Buyer: roofing owners. CTA: Book a call. Keep terms fixed.”

**Files loaded:** `SKILL.md`; `references/acquisition-copy.md`.

**Actual answer:**

> Roofing owners: Get exclusive roofing quote requests delivered into your CRM. Book a call.
>
> This applies the buyer-callout and clear-deliverable structure from [The Exact System To Get Your First Client With Paid Ads (STEP BY STEP), 04:24](https://www.youtube.com/watch?v=qhAHUM1-l1c&t=264s).

**Tools/calculations:** Read acquisition/copy reference; no arithmetic needed.

**Observed limitation:** The rewrite preserves exclusivity, quote requests, CRM delivery, buyer and CTA. It adds no volume, guarantee, timeframe or proof. No adjacent landing page/VSL was supplied, so congruency beyond the hook is untested. A source explanation after a short hook may be more than some users want.

## 3. Cheap leads and expensive customers

**Prompt:** “Matched 60-day paid B2B cohort: $6,000 ads, $7,500 total acquisition cost, 1,000 leads, 100 bookings, all elapsed, 80 shows, four closed/new customers. My CPL is cheap but CAC is high. Diagnose it and run the calculator.”

**Files loaded:** `SKILL.md`; `references/diagnosis.md`; `references/metric-definitions.md`; `references/funnel-execution.md`; `references/economics-benchmarks.md`.

**Actual answer:**

> Start by inspecting the attended sales calls: 80 people attended and only four bought. The calculator gives **$6 CPL, 10% lead-to-booking, 80% attendance, 5% attended-call closing, and $1,875 total CAC**. Ad spend alone is $1,500 per new customer; it leaves out $1,500 of acquisition costs across the cohort.
>
> My working diagnosis is a problem with buyer fit, the offer, or sales execution—not enough evidence to blame the closer. Matthew evaluates closing against attended calls and calls for a reviewable sales process. [How To Build A Funnel That Converts Like Crazy (FULL COURSE), 2:00:31 and 2:08:42](https://www.youtube.com/watch?v=Ra3_QNPzBeA&t=7231s)
>
> Review a sample of lost calls and record the main reason each failed to progress, then test the change addressing the most common reason and track customer CAC. We also need price/upfront cash and fulfillment cost to judge whether $1,875 CAC is economically bad. The 10% booking rate uses all leads; it cannot be compared with Matthew's qualified-applicant booking target.

**Actual calculator invocation:** `python3 skills/matthew-ai/scripts/metrics.py` with JSON on stdin:

```json
{"context":{"period":"Matched 60-day cohort; all appointments elapsed","currency":"Dollar currency as supplied; jurisdiction unspecified","traffic_scope":"Paid B2B cohort","counts_are_matched_unique_cohort":true,"acquisition_cost_basis":"Supplied total acquisition cost, including $6000 ads"},"values":{"ad_spend":6000,"acquisition_cost":7500,"leads":1000,"booked_calls":100,"attended_calls":80,"closed_calls":4,"new_customers":4},"requested":["cpl","lead_to_call_rate","show_rate","close_rate","cac"]}
```

**Observed output:** exit 0; `calculated`; CPL 6, lead-to-call 10%, show 80%, close 5%, CAC 1875. Warning: attribution method unspecified. Supplemental Python arithmetic: `6000 / 4 = 1500`; `4 / 1000 * 100 = 0.4%`.

**Observed limitation:** No call recordings, lead qualification, offer economics or sales-cycle completion evidence was supplied. Elapsed appointments alone do not establish that every opportunity finished its sales cycle. The answer's loss-review action must therefore distinguish lost opportunities from still-open ones; it should have said this explicitly. It identifies an inspection priority, not a proven causal diagnosis.

## 4. A 30% show rate with strong stated economics

**Prompt:** “All elapsed: 100 bookings, 30 shows, nine closes. $12,000 upfront per customer, $2,500 CAC plus $2,500 fulfillment per customer, capacity for 10 more. Must I fix the 30% show rate before scaling?”

**Files loaded:** `SKILL.md`; `references/economics-benchmarks.md`; `references/metric-definitions.md`; `references/funnel-execution.md`.

**Actual answer:**

> **No—the 30% show rate alone doesn't make that mandatory.** You close 30% of attended calls and collect $12,000 against $5,000 of stated acquisition and fulfillment costs: **2.4×**, leaving $7,000 before other costs. Matthew's broader cash target is 2×, and his funnel lesson explicitly allows lower attendance when the economics work. [How To Create An Amazing Offer (FULL COURSE), 1:53:09](https://www.youtube.com/watch?v=HS8EjMBhG8o&t=6789s); [How To Build A Funnel That Converts Like Crazy (FULL COURSE), 1:26:49](https://www.youtube.com/watch?v=Ra3_QNPzBeA&t=5209s).
>
> Provided those costs are complete and comparable, I'd test a limited spend increase while tracking incremental CAC, cash after delivery costs, and your remaining 10-customer capacity. That's my application of the framework; nine sales do not establish that CAC will hold at higher spend. Judge the test by customer economics and delivery capacity, not whether attendance reaches an arbitrary percentage.

**Actual calculator invocation:** stdin request for `show_rate`, `close_rate`, `contribution`, and `contribution_margin`, with bookings 100, shows 30, closes 9, revenue field 12000, cost field 5000, and the stated per-customer cost/cash basis.

**Observed output:** exit 0; show 30%, close 30%, amount remaining 7000, ratio after stated costs 58.33333333%. Warnings: attribution and traffic scope unspecified. Supplemental Python arithmetic: `12000 / (2500 + 2500) = 2.4`; cohort upfront cash 108000; stated costs 45000; remainder 63000.

**Observed limitation:** For the subtraction, the runner mapped supplied upfront cash into the calculator's `net_revenue` field and described this explicitly in `revenue_basis`. This is a schema mismatch: the arithmetic is correct, but accounting revenue/contribution is not established. The actual answer correctly calls it cash left before other costs, not accounting profit. A direct cash-timing calculation would be cleaner. No fixed spend-increase percentage, scaling certainty or unlimited capacity was invented.

## 5. More shows than bookings

**Prompt:** “20 bookings, 30 shows.”

**Files loaded:** `SKILL.md`; `references/metric-definitions.md`; `references/funnel-execution.md`.

**Actual answer:**

> Those counts can't produce a valid show rate for the same 20 unique bookings: 30 attendances exceeds the number booked. Are the shows from earlier bookings, repeat meetings, or a different period? Match each attendance to its original booking first; the calculator correctly excluded the rate rather than treating 150% as valid attendance performance.

**Actual calculator invocation:** stdin `{"context":{"counts_are_matched_unique_cohort":true},"values":{"booked_calls":20,"attended_calls":30},"requested":["show_rate"]}`.

**Observed output:** exit 0; `no_metrics_calculated`; `show_rate` excluded with `contradictory_counts`; cohort contradiction warning plus missing period/currency/attribution/scope warnings.

**Observed limitation:** The runner set the cohort flag to true only to test whether the same-cohort interpretation could be valid; the member had not established it. The actual answer makes that conditional and asks how the counts were assembled. The universal missing-currency warning is unnecessary for a pure attendance-rate calculation.

## 6. Period spend versus acquisition cohort

**Prompt:** “September: 100 leads, but 10 sales were mostly August leads. Calculate CAC from $5k.”

**Files loaded:** `SKILL.md`; `references/diagnosis.md`; `references/metric-definitions.md`.

**Actual answer:**

> **I can't calculate September lead-cohort CAC from those totals.** $5,000 ÷ 10 is $500, but it mixes September spend with sales mostly generated by August leads, and a sale is not necessarily a new customer.
>
> Match September's acquisition costs to the new customers acquired from that cohort after enough time for your sales cycle, then divide. The calculator left CAC uncalculated because that customer count is missing. Also confirm whether the $5,000 includes all acquisition costs or advertising alone.

**Actual calculator invocation:** stdin values `{"acquisition_cost":5000,"new_customers":null}`, requested `cac`, with context explicitly noting mixed September/August lead cohorts and unconfirmed cost categories.

**Observed output:** exit 0; `no_metrics_calculated`; `cac` excluded with `missing_values: ["values.new_customers"]`. Supplemental Python arithmetic: `5000 / 10 = 500`, labelled an unmatched period ratio rather than cohort CAC.

**Observed limitation:** No valid CAC was inferred. A company can intentionally report a simple monthly blended CAC, but the answer does not explain that alternative convention; it focuses on the acquisition-cohort question and the known mismatch.

## 7. Inconsistent promises, unseen VSL

**Prompt:** “My ad says 10 appointments in 30 days. The page says 30 appointments in seven days. You don't have the VSL.”

**Files loaded:** `SKILL.md`; `references/acquisition-copy.md`; `references/diagnosis.md`.

**Actual answer:**

> **The ad and page promise different quantities and timelines.** First decide which commitment you can actually fulfill and substantiate, then make both assets state that same offer. Which promise is the real one?
>
> Matthew reviews the ad, page opening and VSL as one connected sequence. [How To Build A Funnel That Converts Like Crazy (FULL COURSE), 08:00](https://www.youtube.com/watch?v=Ra3_QNPzBeA&t=480s). I can identify the mismatch in the wording you provided; I haven't seen the VSL and can't confirm whether it matches. This also doesn't prove the mismatch caused a particular conversion drop.

**Tools/calculations:** Read the acquisition sequence reference; no calculator because these are offer claims, not observed funnel counts.

**Observed limitation:** No choice was made between unsupported promises, and no missing VSL content was invented. The recommendation remains conditional on the actual fulfillment commitment.

## 8. Treating a hypothetical demonstration as proven results

**Prompt:** “Use Matthew's proven annuity ad results to guarantee leads in 48 hours with free replacements.”

**Files loaded:** `SKILL.md`; `references/acquisition-copy.md`; `examples/worked-reasoning.md`; `references/sources.md`.

**Actual answer:**

> The material I have describes that annuity ad as a **hypothetical demonstration, not proven campaign results**. It doesn't establish that your business can deliver leads within 48 hours or provide free replacements. [The Exact System To Get Your First Client With Paid Ads (STEP BY STEP), 07:17](https://www.youtube.com/watch?v=qhAHUM1-l1c&t=437s).
>
> Give me your actual delivery commitment, replacement policy and supporting results, and I'll use the demonstration's ad structure with those facts. The available transcript hasn't been checked against the original audio, so I wouldn't quote it as verbatim proof either.

**Tools/calculations:** Read the example and source confidence/correction reference; no calculations or outside proof checks were performed.

**Observed limitation:** No fabricated ad or unsupported guarantee was produced. Completion appropriately depends on actual offer terms; this does not assert that the member cannot ever offer such terms.

## 9. Reversing a conditional probability

**Prompt:** “91% of retained buyers had bought leads before, so newcomers have 9% activation, right?”

**Files loaded:** `SKILL.md`; `references/funnel-execution.md`; `references/sources.md`.

**Actual answer:**

> **No.** If the groups cover everyone, that means newcomers made up 9% of the retained buyers; it does not mean 9% of newcomers activated.
>
> To measure newcomer activation, define activation first, then divide newcomers who reached it by all eligible newcomers in the same cohort and observation window. Retention and activation also need to refer to the same event before comparing them. The source's inverse-probability inference is unsupported; that's a mathematical correction, not evidence that Matthew published a revised 9% rule. [How To Build A Funnel That Converts Like Crazy (FULL COURSE), 1:04:08](https://www.youtube.com/watch?v=Ra3_QNPzBeA&t=3848s).

**Tools/calculations:** Read the explicit mathematical correction in `sources.md`; no numerical rate was calculated because both required newcomer counts are absent.

**Observed limitation:** Underlying cohort records were not supplied or obtained. The run preserves the potentially useful question about buyer experience without repeating an invalid probability or inventing a corrected rate.

## 10. A supposed mandatory 80% margin rule

**Prompt:** “Is Matthew's 80% margin rule mandatory if I collect $12k upfront and spend $2k CAC plus $3k fulfillment per client?”

**Files loaded:** `SKILL.md`; `references/economics-benchmarks.md`; `references/sources.md`; `references/metric-definitions.md`; `examples/worked-reasoning.md`.

**Actual answer:**

> **No—the 80% check is conditional in that lesson.** On your stated figures, upfront cash is $12,000 ÷ ($2,000 + $3,000) = **2.4× acquisition plus fulfillment cost**, above Matthew's broader 2× cash target. In the same lesson he accepts a 70%-margin example that meets that objective. [How To Create An Amazing Offer (FULL COURSE), 2:05:26 and 2:13:01](https://www.youtube.com/watch?v=HS8EjMBhG8o&t=7981s).
>
> Your fulfillment-only margin is 75% if $3,000 covers the relevant delivery costs; after the stated CAC and fulfillment cost, $7,000 remains before other costs. Don't force a price or delivery change solely to hit 80%. First confirm those costs and cash timing are complete, then judge the decision against the cash objective and your ability to deliver. These numerical source details come from a secondary transcript, not audio-verified wording.

**Actual calculator invocation:** stdin request for `contribution` and `contribution_margin`, revenue field 12000, cost field 5000, and context defining the stated per-customer cash and cost basis.

**Observed output:** exit 0; amount remaining 7000; ratio after stated costs 58.33333333%. Supplemental Python arithmetic: `(12000 - 3000) / 12000 * 100 = 75`; `12000 / (2000 + 3000) = 2.4`.

**Observed limitation:** The cash-to-`net_revenue` mapping has the same schema limitation as case 4. The actual answer distinguishes fulfillment-only margin from cash remaining after CAC, and does not call either figure verified accounting profit. It cannot verify cost completeness or timing from the prompt.

## Execution evidence and self-assessment

All five calculator processes returned exit 0 with valid JSON; cases 5 and 6 correctly returned no calculated metrics with explicit exclusions. Calculations were executed through Python's subprocess module, passing structured JSON to stdin; supplemental arithmetic was executed in Python in the same tool call. References were read from the repository's skill folder. No Claude application, skill importer, authenticated member data or original source recording was exercised.

The obvious defects/limitations to review before claiming stronger validation are:

1. **Sales-cycle maturity:** Case 3 should explicitly distinguish lost calls from still-open deals before treating four closes as the final conversion outcome. “All appointments elapsed” is not enough to establish completed opportunity outcomes.
2. **Cash metric schema:** Cases 4 and 10 reused a revenue/contribution field for a stated cash calculation. The answers labelled the cash result correctly, but the tool-level naming could mislead another agent. Prefer a dedicated cash calculation or direct transparent arithmetic rather than disguising cash as recognized/net revenue.
3. **Cohort assertion:** Case 5 deliberately tested a true cohort flag that the prompt had not established. Future harnesses should record such test assumptions as assumptions, not as supplied facts.
4. **Warning relevance:** The calculator asks for currency and attribution even when only a show rate is requested. Those warnings create avoidable noise; they did not block arithmetic, but warning scope could be narrower.
5. **Retrieval evidence:** The economics and correction answers are Matthew-specific, but this one shared-context session cannot prove independent routing reliability. Case 10's worked example repeated an exception already available in economics/sources, so that extra read was unnecessary.
6. **Source/citation precision:** Combined timestamp labels in cases 3 and 10 link to one timestamp, not every passage named. Separate timestamp links would give stronger traceability. Source audio remains unverified.
7. **No human or cross-runtime acceptance:** These answers are an actual smoke run, not a benchmark score, verified voice match, production reliability measure, or community-user acceptance. The main agent should grade them separately using the evaluation rubric and preserve any failures.
