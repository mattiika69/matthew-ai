# Feed Matthew AI new knowledge

## Keep authoring in Drive

Google Docs is suitable for your notes, frameworks and lesson writing. Keep the original docs, transcripts, images and asset explanations in one authorized Drive folder. Export a useful document as Markdown or text when curating it; retain its original link, title and date. Preserve image files and their surrounding explanation, and record whether somebody actually inspected the visual or only extracted text.

The public GitHub repo is the canonical **released skill**. Drive is an authoring/source location. Editing a Drive file does not update the skill automatically in this version.

## Capture → compare → curate → release

1. Obtain the source through an authorized export, transcript or accessible browser session. Prefer original captions/transcripts; record partial coverage and transcription uncertainty. Do not infer a video's contents from its title.
2. Import the text below. Raw content and full capture metadata go to ignored `raw/`; private sources enter `sources/catalog.json` with redacted placeholders. A separate proposal goes to ignored `proposals/`. Public-source URLs are sanitized, but still review titles, paths and every public metadata field.
3. Read the proposal and relevant existing teaching. Exact duplicates are detected by hash; topic overlaps are comparison candidates, not proven semantic conflicts.
4. Extract the useful principle, framework, evidence or judgment. Give it an exact locator and distinguish explicit teaching from synthesis/inference. Preserve the original context, exceptions and what would change the recommendation.
5. Edit the appropriate existing reference or example. Add a new file only when its retrieval purpose justifies it. Never let ingestion overwrite curated knowledge automatically.
6. Compare conflicts by date and context. Record genuine corrections in `references/sources.md`; preserve unresolved disagreements and obtain Matthew's judgment when material.
7. Review the actual public diff—including titles, URLs and metadata—for private/member information, unsupported claims and redistribution rights. Sanitize or omit details; public originals do not automatically make every copied third-party asset yours to redistribute.
8. Add the skill-relative files to `curated_files`, prepare safe public metadata, and deliberately set `publication_status` to `cleared` only after review. This clears public metadata and listed curated files, not raw originals. Every public catalog record needs review, including sources not yet incorporated. Update the installed source inventory and relevant evaluations.
9. Run the tests, inspect behavior on the changed topics, and record the completed publication review using the command below. It binds the catalog and each packaged file to its reviewed bytes. Update the changelog, commit and push. Package and publish a new version only after review.

Example capture (replace the illustrative fields and path with a real authorized source):

```bash
python3 tools/import_source.py \
  --id S005 \
  --type lesson \
  --title 'Actual lesson title' \
  --author 'Matthew Larsen' \
  --topic offers \
  --input /path/to/authorized-lesson.md \
  --visibility private \
  --coverage 'Written lesson only; embedded video not captured'
```

Use `--url` for the original location and `--date YYYY-MM-DD` when known. `--url` records provenance; this CLI does not scrape or transcribe a URL. For a changed source with the same ID, use `--replace` after review: previous bytes/metadata remain under `raw/revisions/`, curated files remain intact, and clearance is reset. Use `--conflicts-with S001` to flag a suspected conflict for review.

Private source metadata can itself be sensitive. Replace redacted placeholders only with deliberately sanitized public metadata and omit a private URL if necessary; keep the exact original location in the ignored raw manifest/private archive. Never commit credentials, member business details or unreviewed raw captures. `.gitignore` is not a substitute for reviewing a staged diff.

## Release

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 tools/review_release.py --reviewer 'Actual reviewer name' --note 'Describe the publication review completed'
python3 tools/package_skill.py --check
python3 tools/package_skill.py --version 0.1.0-beta.2
```

The reviewer command records your completed review; it does not perform that review or approve unreviewed sources. It writes `sources/publication-review.json`. Any added, removed or changed packaged file, or changed catalog, requires another review. The version above is an example of the next release. The packager will not overwrite an existing ZIP. Review the actual archive, then use GitHub Releases to create the corresponding tag and attach that ZIP. Users of uploaded Claude skills must upload the new package; CLI users explicitly update their installation. Do not describe a repository commit as an automatic update to every user's copy.

## What to collect next

Prioritize authenticated Skool replies/coaching where Matthew diagnoses a specific business and changes his advice after new information. Then add the authorized Drive folder's strongest frameworks, actual ads/pages with explanations, and call transcripts. This beta starts with four extensive public recordings; expand toward the requested 50–100 distinct pieces without inflating the count by treating excerpts as independent sources.

For pilot feedback, ask members to voluntarily submit the question, answer, whether they acted, and where it was wrong or unhelpful. Remove private business details before adding regression cases. The skill does not collect this automatically; there are no usage analytics to report unless you separately gather them.
