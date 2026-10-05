# Fresh installed-skill runtime test

Date: 2026-10-05. A separate ephemeral Codex CLI process ran in a temporary project with Matthew AI installed by the skills CLI. The agent used the normal `.agents/skills/matthew-ai` path, read-only execution, the configured default model, and synthetic business data. This test had a fresh conversation rather than the evaluator's earlier conversation. It still used this machine's normal Codex configuration; it is not a pristine-account or Claude integration test.

## Prompt

Use Matthew AI. I sell a front-end cold-traffic B2B service. One matched, fully matured 60-day cohort had $6,000 ad spend, $7,500 total acquisition costs, 1,000 leads, 100 booked calls, 80 attended calls and four new customers. There are no open opportunities left. Each customer paid $3,000 upfront and costs $1,200 to fulfill. I think we should cut the form questions to get even cheaper leads and double ad spend. What should I do first?

The harness additionally requested relevant-file retrieval, calculator use, no file edits/private browsing/history use, and a concise answer with citations.

## Observed execution

The process read `SKILL.md`, diagnosis, metric definitions, economics/benchmarks and funnel execution, then looked up the source titles. It ran the installed calculator for CPL, CAC, advertising-only customer CPA, booking, attendance and closing. It separately calculated upfront cash versus acquisition/fulfillment cost in Python, rather than reusing accounting-revenue inputs. Commands completed successfully. No raw transcript or unrelated domain reference was read in the recorded command trace.

Calculator results: CPL 6; total CAC 1875; advertising-only customer CPA 1500; booking 10%; show 80%; attended-call closing 5%. Separate cash arithmetic: 12000 upfront, 12300 combined stated costs, ratio 0.9756097561, cash remaining −300.

## Actual final answer

> **Keep spend and the form unchanged. First investigate why only four of 80 attended calls became customers.**
>
> The calculator gives:
>
> - **CPL:** $6.
> - **Lead→booking:** 10%; **show rate:** 80%; **attended-call close rate:** 5%.
> - **Total acquisition CAC:** $1,875—not the $1,500 advertising-only cost.
> - **Cash economics:** $12,000 upfront ÷ ($7,500 acquisition + $4,800 fulfillment) = **0.976×**. You’re **$300 short after those stated costs**, before overhead or other costs.
>
> Matthew’s front-end cold-traffic teaching progresses from covering combined acquisition and fulfillment costs toward **2× upfront cash**. That is an offer-design target, not a universal profitability rule. [How To Create An Amazing Offer (FULL COURSE), 2:01:00–2:03:55](https://www.youtube.com/watch?v=HS8EjMBhG8o&t=7260s).
>
> Your 5% attended-call close rate is below his contextual **15–30%** range. That identifies an inspection point; it does not establish the cause. [How To Build A Funnel That Converts Like Crazy (FULL COURSE), 2:00:31–2:01:43](https://www.youtube.com/watch?v=Ra3_QNPzBeA&t=7231s).
>
> **My recommended first action:** review form answers and call recordings across the four wins and lost attended opportunities. Classify buyer fit, ability/intent to buy, offer understanding, unresolved objections and follow-up.
>
> If unsuitable buyers dominate, preserve or strengthen useful qualification. If suitable buyers consistently reject or misunderstand the offer, address the evidenced offer or sales-process problem.
>
> Only test removing questions when that audit supports it. Judge the next matured cohort by **total CAC and cash after acquisition plus fulfillment**, not CPL. Four customers give limited evidence for predicting performance at doubled spend.

## Reviewer assessment

Pass for this scenario: relevant retrieval, executed and correct arithmetic, correct cash schema, no repeated questions about supplied facts, source-specific reasoning with scope, one diagnostic priority and conditional next steps. The answer distinguishes observation from causal proof and does not invent results or a scaling percentage.

Minor limitation: the calculator input labelled the supplied dollar symbol as USD, although the prompt did not explicitly identify the dollar currency. All computations used the same unconverted amounts and the final answer retained `$`. This should remain a data-quality assumption, not a verified currency fact.

This is one successful installed-runtime test, not an estimate of reliability or a substitute for Matthew/member review. Original recordings and source diagrams were not verified by this run. Raw runtime event logs are retained privately in the build workspace; this record includes only task-relevant observed actions and the final response.
