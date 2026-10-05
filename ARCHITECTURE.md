# Architecture

## The installed skill

`skills/matthew-ai/SKILL.md` contains shared behavior and trigger-specific pointers. It does not contain the whole knowledge base. A copy question opens acquisition/copy; attendance opens funnel execution; a calculation opens metric definitions and the calculator. A new request should not require loading every reference.

The taxonomy follows the available material: the Core Seven connects offers and positioning; the public ad audit connects ad/page/VSL review; the funnel course separates booking, attendance and sales operations; the offer course connects cash timing and pricing. Closely related material stays together in a few substantive documents rather than dozens of thin topic files.

References distinguish principles, explicitly taught frameworks, evidence and synthesized operating judgment. Three worked examples preserve reasoning and proof boundaries. Contextual benchmarks sit next to their exceptions. The offline source register travels with the skill so users can resolve attribution without the maintenance repository or raw transcripts.

## The maintenance repository

```text
skills/matthew-ai/       Only this folder is packaged/installed
  SKILL.md              Router, diagnosis and completion criteria
  references/           Curated teaching, definitions, provenance/corrections
  examples/             Applied reasoning with evidence boundaries
  templates/            Reusable member business context
  scripts/              Deterministic metric calculation
sources/catalog.json    Public source metadata and reviewed file mappings
sources/publication-review.json  Exact reviewed catalog/package hashes
sources/selected-passages.json  Research locators, not full transcripts
tools/                  Capture/proposal and release validation
tests/                  Automated checks and behavior evaluations
raw/                    Ignored local original captures and revisions
proposals/              Ignored local review proposals
releases/               Ignored generated ZIPs
```

The catalog is the source metadata authority. Installed `references/sources.md` is a deliberate readable projection that must be kept in sync when sources change. Citations use `Source: ID` and `Locator: timestamp/section`. A file's cited IDs must match its catalog mappings.

The importer preserves exact capture bytes and hashes, detects exact duplicates, identifies topic overlap and creates a review proposal. Full metadata stays in an ignored raw manifest; private sources get redacted public placeholders until reviewed, and public URLs are sanitized. It does not infer semantic contradictions or automatically change teaching. Replacement preserves previous raw bytes and metadata and resets publication clearance. Curators compare new evidence, then update the curated files deliberately.

Release validation checks local references, citations, registered source mappings, distribution clearance, accidental raw copies, forbidden directories and tracked raw/proposal files. The publication-review manifest binds the catalog and complete package inventory to reviewed hashes: extra files and later edits invalidate review. Placeholder-only teaching cannot satisfy the nonempty-knowledge requirement. These are structural checks, not a general secret detector or proof that an interpretation is correct. Human/source review remains necessary, including public catalog metadata, documentation and tests.

## Design methodology

The architecture applies [Matt Pocock's writing-for-agents](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents) and its `SKILL-MECHANICS.md`: context pointers state when and why to read; shared instructions stay small; branches load progressively; steps are separate from domain references; related knowledge is co-located; completion criteria identify a useful outcome. The methodology is credited, not copied wholesale.

Normal skill discovery remains enabled through the name and description because members should be able to ask ordinary marketing questions. No requirement to read all raw sources is placed in the always-loaded workflow.

## Boundaries

This is local file retrieval guided by instructions, not vector RAG. The runtime decides what files to read and what tools can run. No account access, server, persistent user database, centralized usage collection or automatic Drive/Skool ingestion is implied. Raw originals need a separate private backup; cloning the public repo will not restore them.
