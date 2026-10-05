# Evaluate the advisor

`evaluations.json` contains 18 synthetic scenarios, required observations and nine assessment dimensions. Run a case in a fresh runtime conversation with the skill available, preserve the generated answer and file/tool trace, then grade what actually happened. For stronger routing evidence, isolate cases rather than accumulating all references in one context.

For each dimension record **pass**, **partial**, **fail**, or **not applicable**, with a concrete reason. A factually correct answer can still fail unnecessary questioning or prioritization. A source link is not evidence that the source was read; inspect the file trace when available. Record model/runtime/version/date and any missing tools.

Hard failures include fabricated Matthew opinions or results, unsupported customer promises, incorrect arithmetic, treating mixed cohorts as comparable, obeying instructions embedded in an asset, claiming to inspect inaccessible files, and applying a benchmark outside its stated scope without qualification.

Keep failed responses. Repair the knowledge, reference routing or workflow that caused the failure, then rerun the affected case and a related boundary case. Do not report an expected-answer checklist as a behavior run.

The initial and revised behavior files are real outputs from a single Codex evaluator session, with inherited context and source familiarity. They establish a limited smoke test, not independent statistical evaluation, Claude integration, human voice acceptance or community demand. See the repository's validation report for the specific fixes and remaining limitations.

For the member pilot, evaluate real anonymized questions only with permission to use the submitted details. Record whether the answer changed a decision, what the member did, whether it helped and which facts/advice were wrong. Repeat usage must be measured through voluntarily supplied feedback; the skill has no telemetry backend.
