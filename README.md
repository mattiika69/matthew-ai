# Matthew AI

An AI advisor that applies Matthew Larsen's documented reasoning to your offers, funnels, ads, copy and acquisition economics. Give it your business context and the decision you need help with; it should identify the constraint, consult the relevant teaching and prioritize the next action.

**Initial public-source beta.** The library contains curated teaching from four public recordings, with 87 timestamped passages selected during research. It is strongest on offers and call-based acquisition. Transcripts came from a secondary source and have not been checked against the original audio; Skool, Drive and private calls are not included yet. This is not the planned broader 50–100-piece corpus or a claim that Matthew has approved every answer.

## Install in Claude — easiest option

1. Download `matthew-ai-0.1.0-beta.1.zip` from the [beta release](https://github.com/mattiika69/matthew-ai/releases/tag/v0.1.0-beta.1).
2. In Claude, open **Customize → Skills → + → Create skill → Upload a skill** and select the ZIP.
3. Enable the skill and Claude's code execution capability, then start a chat: **“Use Matthew AI to review my funnel.”**

Your account's plan, organization controls and usage limits still apply. For updates, download and upload the new release ZIP; an uploaded copy does not automatically follow GitHub. [Claude's current skill instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

## Install in Claude Code or Codex

With Node.js available, run the matching command in the project where you want to use the skill:

```bash
# Claude Code
npx skills add mattiika69/matthew-ai --skill matthew-ai --agent claude-code

# Codex
npx skills add mattiika69/matthew-ai --skill matthew-ai --agent codex

# Update the project installation later
npx skills update matthew-ai -p
```

Add `-g` to install globally; use `npx skills update matthew-ai -g` for that installation. Start a fresh conversation after installing/updating. Commands follow the [skills CLI documentation](https://github.com/vercel-labs/skills#readme), checked October 5, 2026. GitHub is the canonical source; installed copies need an explicit update.

## Use it

Paste your details into the [business brief](skills/matthew-ai/templates/business-context.md), or simply provide enough context for the question. Attach actual ads, page copy, screenshots, call excerpts or metrics when relevant.

Examples:

- “My CPL is low but CAC is high. Here are the same cohort's leads, bookings, shows, closes and costs. What should I inspect first?”
- “Review this ad and landing page together. Keep my offer and proof fixed.”
- “People book but do not show. Here are the booking delays and pre-call messages.”
- “Should I scale this offer? Here is upfront cash, acquisition cost, fulfillment cost and remaining capacity.”

The skill distinguishes explicit teaching, synthesized frameworks and its own inference. It should ask only for information that changes the recommendation, cite relevant sources and avoid invented guarantees or results. It can analyze images only when the chosen runtime can actually inspect the attachment.

## What is included

- A compact [router and advisory workflow](skills/matthew-ai/SKILL.md).
- Curated offers/positioning, acquisition/copy, funnel execution, economics/benchmarks and diagnostic knowledge.
- A real public audit and clearly labelled hypothetical examples.
- An offline [source and correction register](skills/matthew-ai/references/sources.md).
- A dependency-free calculator for 18 standard metrics; it does not invent LTV or turn benchmarks into automatic decisions.
- Capture, review and release tools, with automated checks and recorded behavior evaluations.

The runtime supplies the model and any execution tools. This repository runs no inference service, vector database or member backend. Users consume their own account/API allowance. The skill itself provides no centralized memory, membership gating, analytics or automatic source synchronization.

## Improve and maintain it

Read [MAINTAINING.md](MAINTAINING.md) to add lessons, transcripts or Drive exports without overwriting curated teaching. [ARCHITECTURE.md](ARCHITECTURE.md) explains the routing and source separation. [VALIDATION.md](VALIDATION.md) records what was tested and what remains unverified.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/package_skill.py --check
python3 tools/package_skill.py --version 0.1.0-beta.1
```

Python 3.9+ is sufficient. Packaging creates a ZIP under `releases/`; that directory, raw captures and review proposals are ignored by Git. Publishing a release is a separate action after reviewing the actual files.
