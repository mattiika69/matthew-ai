#!/usr/bin/env python3
"""Capture local UTF-8 source text and propose review work; never edit curated knowledge.

For a URL, first obtain an authorized browser export or transcript, then pass that
file with --input and its original location with --url. This tool does not scrape,
transcribe, infer source dates, or establish publication permission.
"""
import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from publication import public_record, sanitized_url

ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9_-]*"


def digest(body):
    return hashlib.sha256(body).hexdigest()


def read_catalog(root):
    path = root / "sources" / "catalog.json"
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    if not isinstance(records, list):
        raise ValueError("sources/catalog.json must contain a list of records.")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("The source catalog contains duplicate IDs; resolve them before importing.")
    return records


def safe_target(root, relative):
    target = root / relative
    if not target.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"Path leaves repository: {relative}")
    for part in (target, *target.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"Symbolic links are not allowed for captures: {relative}")
    return target


def write_exact(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def ingest(root, *, source_id, source_type, title, url, source_date, author,
           topics, input_path, visibility="private", capture_method="local-text-import",
           coverage, replace=False, conflicts_with=()):
    root = Path(root).resolve()
    if not re.fullmatch(ID_PATTERN, source_id):
        raise ValueError("Use a source ID containing letters, numbers, hyphens, or underscores.")
    for name, value in (("type", source_type), ("title", title), ("author", author),
                        ("capture_method", capture_method), ("coverage", coverage)):
        if not isinstance(value, str) or not value.strip() or "\n" in value:
            raise ValueError(f"{name} must be a nonempty single line.")
    topics = list(dict.fromkeys(topic.strip() for topic in topics))
    if not topics or any(not topic or "\n" in topic for topic in topics):
        raise ValueError("Supply at least one nonempty topic derived from the source.")
    if source_date is not None:
        date.fromisoformat(source_date)
    if visibility not in ("public", "private"):
        raise ValueError("visibility must be public or private.")
    sanitized_url(url)  # Validate; the original URL is preserved only in ignored metadata.
    body = Path(input_path).read_bytes()
    if not body.decode("utf-8").strip():
        raise ValueError("The capture is empty.")
    checksum = digest(body)
    catalog = read_catalog(root)
    manifest_path = safe_target(root, "raw/manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    if not isinstance(manifest, list):
        raise ValueError("raw/manifest.json must contain a list of full source records.")
    full_records = {item["id"]: item for item in manifest}
    existing = next((record for record in catalog if record["id"] == source_id), None)
    known_ids = {record["id"] for record in catalog}
    if any(item not in known_ids or item == source_id for item in conflicts_with):
        raise ValueError("Each --conflicts-with ID must name another existing source.")
    duplicates = [record["id"] for record in catalog
                  if record.get("sha256") == checksum and record["id"] != source_id]
    if duplicates:
        return {"status": "duplicate", "sha256": checksum, "existing_ids": duplicates,
                "message": "Identical bytes already captured; no files or records changed. Review provenance before merging source identities."}
    target = safe_target(root, f"raw/{source_id}.md")
    proposal_path = safe_target(root, f"proposals/{source_id}.md")
    catalog_path = safe_target(root, "sources/catalog.json")
    record = {
        "id": source_id, "type": source_type, "title": title, "url": url,
        "date": source_date, "author": author, "topics": topics,
        "raw_path": f"raw/{source_id}.md", "sha256": checksum,
        "curated_files": list(existing.get("curated_files", [])) if existing else [],
        "visibility": visibility, "publication_status": "unreviewed",
        "capture_method": capture_method, "coverage": coverage,
    }
    if existing:
        if existing.get("raw_path") != record["raw_path"]:
            raise ValueError("Existing raw_path differs from the canonical capture path; review it manually.")
        if not target.is_file() or digest(target.read_bytes()) != existing.get("sha256"):
            raise ValueError("Existing raw capture is missing or its bytes changed; restore it before replacing.")
        prior_full = dict(full_records.get(source_id, existing))
        comparable = {key: prior_full.get(key) for key in record}
        comparable["publication_status"] = "unreviewed"
        comparable["curated_files"] = record["curated_files"]
        if comparable == record and not conflicts_with:
            return {"status": "unchanged", "id": source_id, "sha256": checksum}
        if not replace:
            raise ValueError("Source ID has different content or metadata; review it and use --replace deliberately.")
        # Old bytes AND old metadata remain recoverable, even for metadata-only updates.
        old_bytes = target.read_bytes()
        revision = safe_target(root, f"raw/revisions/{source_id}/{existing['sha256']}.md")
        old_metadata = json_bytes({"public_record": existing, "full_record": prior_full})
        metadata_path = safe_target(root, f"raw/revisions/{source_id}/{existing['sha256']}-{digest(old_metadata)[:16]}.json")
        for path, preserved in ((revision, old_bytes), (metadata_path, old_metadata)):
            if path.exists() and path.read_bytes() != preserved:
                raise ValueError("A preserved revision differs from its recorded bytes; investigate before proceeding.")
        for path, preserved in ((revision, old_bytes), (metadata_path, old_metadata)):
            if not path.exists():
                write_exact(path, preserved)
    elif target.exists() or proposal_path.exists():
        raise ValueError("An uncataloged capture or proposal already exists; inspect it before importing.")

    comparison_records = [full_records.get(item["id"], item) for item in catalog]
    candidates = [item for item in comparison_records if item["id"] != source_id
                  and set(item.get("topics", [])) & set(topics)]
    proposal = [f"# Review proposal: {source_id}", "", "Status: unreviewed", "",
                f"Source: {source_id}", f"Title: {title}",
                f"Raw capture: {record['raw_path']}", f"SHA-256: {checksum}",
                f"Coverage: {coverage}", "", "## What changed", ""]
    if existing:
        proposal += [f"Explicit replacement of {existing['sha256']}; earlier bytes and metadata are retained under raw/revisions/{source_id}/.",
                     "Publication clearance was reset; existing curated files were left unchanged."]
    else:
        proposal += ["New raw source captured; no curated knowledge was created or changed."]
    proposal += ["", "## Compare before curating", "",
                 "Topic overlap is a review candidate, not evidence of a contradiction; this tool does not perform semantic conflict detection."]
    proposal += [f"- {item['id']}: {item['title']}" for item in candidates] or ["- No topic-overlap candidates in the current catalog."]
    if conflicts_with:
        proposal += ["", "Explicitly flagged possible conflicts: " + ", ".join(conflicts_with) + "."]
    proposal += ["", "## Proposed curated update", "",
                 "Reviewer: identify the useful principle, framework, evidence, or judgment; distinguish direct teaching from inference; record the exact source locator.",
                 "Reviewer: compare context and dates, resolve or document disagreements, then edit curated knowledge deliberately.",
                 "Reviewer: prepare sanitized public metadata from raw/manifest.json and list approved skill-relative paths in curated_files; review both metadata and those files before setting publication_status to cleared.",
                 "After reviewing all package files, record their exact hashes with tools/review_release.py; new or edited files invalidate that review.",
                 "Raw captures remain private working files regardless of publication_status.", ""]
    write_exact(target, body)
    write_exact(proposal_path, "\n".join(proposal).encode("utf-8"))
    full_records[source_id] = record
    write_exact(manifest_path, json_bytes(sorted(full_records.values(), key=lambda item: item["id"])))
    updated = sorted([item for item in catalog if item["id"] != source_id] + [public_record(record)], key=lambda item: item["id"])
    write_exact(catalog_path, json_bytes(updated))
    return {"status": "replaced" if existing else "captured", "id": source_id,
            "sha256": checksum, "proposal": str(proposal_path.relative_to(root)),
            "comparison_candidates": [item["id"] for item in candidates]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--type", "--kind", dest="source_type", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--url", help="Original source URL; this is metadata, not a scraping command.")
    parser.add_argument("--date", help="Source date as YYYY-MM-DD; omit if unknown.")
    parser.add_argument("--author", required=True)
    parser.add_argument("--topic", action="append", required=True, help="Repeat for multiple source-derived topics.")
    parser.add_argument("--input", required=True, type=Path, help="Authorized UTF-8 text capture or transcript.")
    parser.add_argument("--visibility", choices=("public", "private"), default="private", help="Visibility of the original source, not publication approval.")
    parser.add_argument("--capture-method", default="local-text-import")
    parser.add_argument("--coverage", required=True, help="What was captured and what remains missing.")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--conflicts-with", action="append", default=[])
    args = parser.parse_args()
    try:
        result = ingest(ROOT, source_id=args.id, source_type=args.source_type, title=args.title,
                        url=args.url, source_date=args.date, author=args.author, topics=args.topic,
                        input_path=args.input, visibility=args.visibility, capture_method=args.capture_method,
                        coverage=args.coverage, replace=args.replace, conflicts_with=args.conflicts_with)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
