# Validation — 0.1.0-beta.1

Completed October 5, 2026. This is a usable public-source beta with tested mechanics and initial behavioral evidence. It is not Matthew's acceptance, a completed 50–100-source corpus, or evidence of repeat community usage.

## What passed

| Check | Observed result |
|---|---|
| Automated suite | **52 passing tests:** 21 metric and 31 ingestion/release checks, using Python 3.9 |
| Skill format | YAML name/description parsed successfully; local context pointers resolve |
| Source provenance | Four original video identities/dates checked; catalog, curated file mappings and source locators validated |
| Release review | Public metadata and all 11 distributed files reviewed; exact hashes recorded |
| ZIP | 11 files, 33,754 bytes; archive integrity and every file's equality to its reviewed source verified |
| Local install | `skills` CLI 1.5.18 discovered and copied Matthew AI into a temporary Codex project |
| Fresh runtime | Codex CLI 0.158.0-alpha.2.1 read the installed skill, selected relevant references, executed the calculator and separate cash arithmetic, and returned a correct prioritized response |
| Behavior scenarios | All 18 synthetic scenarios exercised across initial/revised runs; three scenarios explicitly rerun after repairs, with imperfections retained in the reports |

Reproduce the automated checks from the repository root:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
python3 -B tools/package_skill.py --check
```

The ZIP SHA-256 is `d8870adf8bbd6ca8cbf245e4ccbe4d3ef26329060ce2cb6b51119744f2799b39`.

## Changes made because of review and tests

Source review corrected the front-end cold-traffic scope of the offer/economics material, the first 10–20 **paid-ad** calls exception, and the locator for the hypothetical lead-delivery/replacement example. It added the six-factor industry assessment, direct-offer-first/conditional expansion choices and audience-dependent VSL length.

Behavior testing exposed the difference between elapsed appointments and completed sales cycles, inappropriate reuse of a revenue field for cash arithmetic, and irrelevant currency warnings on attendance calculations. The skill/definitions/calculator were revised; E03, E04 and E10 were rerun. The fresh installed-runtime scenario independently exercised the corrected calculation path and diagnosis.

Adversarial release review found that metadata could leak from private imports, arbitrary extra files could enter a package, later edits could retain stale clearance, and placeholder-only teaching could pass. The tools now redact private capture metadata, sanitize public URLs, require an explicit inventory of reviewed hashes, and reject those reproduced failure cases.

## Behavioral evidence and limits

Read the [initial run](tests/behavior-run-initial.md), [revised run](tests/behavior-run-revised.md), and [fresh installed-runtime test](tests/installed-runtime-smoke.md). The initial/revised scenarios share one evaluator's context, and the revised rubrics were visible; their self-scores are debugging observations, not a blinded quality benchmark. The root reviewer checked the recorded responses and retained partial results for broad intake, bundled process changes and decisions needing more business facts.

The fresh process correctly prioritized reviewing closing/qualification over buying cheaper leads or doubling spend. It calculated $1,875 total CAC and a $300 shortfall after stated acquisition/fulfillment costs, retained source scope, and distinguished a weak stage from proven causality. All nine command executions passed. Its minor unverified currency assumption is documented.

## Still unverified or unavailable

- No Claude account upload/session or representative member pilot has been exercised. Claude installation instructions were checked against current official documentation; that is not a live Claude integration test.
- Secondary transcript text has not been verified against original audio. Slides, diagrams and source screenshots were not visually reviewed.
- Authenticated Skool content was unavailable, and the authorized Drive folder link has not been supplied. Neither source is included.
- Four extensive recordings and 87 selected passages do not satisfy the broader 50–100 distinct-piece collection target; future additions should prioritize live diagnostic replies and coaching.
- No central analytics exist, so repeat usage, demand and business impact remain unmeasured. Voice/fidelity acceptance requires Matthew and member review.

Publication review records agent review of the material actually distributed. It does not claim that automated checks can discover every secret, validate every interpretation, or guarantee the quality of future model answers.
