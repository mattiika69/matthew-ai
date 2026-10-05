#!/usr/bin/env python3
"""Validate reviewed knowledge and create a ZIP containing only skills/matthew-ai."""
import argparse
import hashlib
import json
import re
import subprocess
import zipfile
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import unquote, urlparse

from publication import validate_public_metadata

ROOT = Path(__file__).resolve().parents[1]
SOURCE = re.compile(r"\bSource:\s*[`\[]?([A-Za-z0-9][A-Za-z0-9_-]*)")
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)")
IGNORED_NAMES = {".DS_Store", "__pycache__", ".pytest_cache"}
FORBIDDEN_NAMES = {"raw", "proposals", ".git", ".env", "node_modules"}


def validate_content(root):
    root = Path(root).resolve()
    skill = root / "skills" / "matthew-ai"
    catalog = json.loads((root / "sources" / "catalog.json").read_text(encoding="utf-8"))
    if not isinstance(catalog, list):
        raise ValueError("Source catalog must be a list.")
    records = {}
    for item in catalog:
        source_id = item["id"]
        if source_id in records:
            raise ValueError(f"Duplicate source ID: {source_id}")
        records[source_id] = item
    relevant = [item for item in catalog if item.get("curated_files")]
    if not relevant:
        raise ValueError("No curated teaching sources; an empty knowledge library cannot be released.")
    validate_public_metadata(catalog)
    if not (skill / "SKILL.md").is_file():
        raise ValueError("SKILL.md is missing.")
    inventory_path = skill / "references" / "sources.md"
    if not inventory_path.is_file():
        raise ValueError("references/sources.md is required so source citations resolve offline.")
    inventory = inventory_path.read_text(encoding="utf-8")
    files = []
    for path in sorted(skill.rglob("*")):
        relative = path.relative_to(skill)
        if path.is_symlink():
            raise ValueError(f"Resolve symbolic links before packaging: {relative}")
        if any(part in IGNORED_NAMES or part.endswith(".pyc") for part in relative.parts):
            continue
        if any(part in FORBIDDEN_NAMES or part.startswith(".env.") for part in relative.parts):
            raise ValueError(f"Private/build material cannot live in the distributed skill: {relative}")
        if path.is_file():
            files.append(path)
    if sum(path.stat().st_size for path in files) > 25_000_000:
        raise ValueError("This project's 25 MB package budget is exceeded; review oversized assets.")
    raw_hashes = {item.get("sha256") for item in catalog}
    for path in files:
        if hashlib.sha256(path.read_bytes()).hexdigest() in raw_hashes:
            raise ValueError(f"Uncurated raw capture found in the skill: {path.relative_to(skill)}")
    for item in relevant:
        source_id = item["id"]
        if item.get("publication_status") != "cleared":
            raise ValueError(f"Curated material requires deliberate public-distribution review: {source_id}")
        if item.get("visibility") not in ("public", "private"):
            raise ValueError(f"Original source visibility is missing: {source_id}")
        if not re.search(r"(?<![A-Za-z0-9_-])" + re.escape(source_id) + r"(?![A-Za-z0-9_-])", inventory) or item["title"] not in inventory:
            raise ValueError(f"Offline source inventory lacks the ID/title: {source_id}")
        for relative in item["curated_files"]:
            path = (skill / relative).resolve()
            if not path.is_relative_to(skill.resolve()) or path not in files:
                raise ValueError(f"Curated source file missing or outside package: {source_id}: {relative}")
            if path.suffix != ".md" or source_id not in SOURCE.findall(path.read_text(encoding="utf-8")):
                raise ValueError(f"Curated file lacks Source: {source_id}: {relative}")
            if not has_teaching_body(path.read_text(encoding="utf-8")):
                raise ValueError(f"Curated file has no substantive teaching beyond metadata: {relative}")
    # Validate every explicit citation and every ordinary relative Markdown pointer.
    for path in files:
        if path.suffix != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(skill).as_posix()
        matches = list(SOURCE.finditer(text))
        for index, match in enumerate(matches):
            source_id = match.group(1)
            record = records.get(source_id)
            if record is None:
                raise ValueError(f"Unknown source {source_id} in {relative}")
            if record.get("publication_status") != "cleared":
                raise ValueError(f"Unreviewed source cited in distributed file: {source_id}")
            if relative != "references/sources.md" and relative not in record.get("curated_files", []):
                raise ValueError(f"Catalog does not record {relative} as influenced by {source_id}")
            citation = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
            locator = re.search(r"\bLocator:\s*([^\n]+)", citation)
            if not locator or not valid_locator(locator.group(1)):
                raise ValueError(f"Source {source_id} lacks a concrete section/page/timestamp Locator in {relative}")
        for link_match in LINK.finditer(text):
            link = (link_match.group(1) or link_match.group(2)).strip().strip("<>")
            # Optional Markdown link titles are not part of the path.
            link = re.split(r'\s+["\']', link, maxsplit=1)[0]
            parsed = urlparse(link)
            if parsed.scheme or link.startswith("#"):
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_relative_to(skill.resolve()) or not target.exists():
                raise ValueError(f"Broken or external local pointer in {relative}: {link}")
    if (root / ".git").exists():
        tracked = subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True).stdout.decode().split("\0")
        if any(name.startswith(("raw/", "proposals/")) for name in tracked):
            raise ValueError("Raw captures or proposals are tracked by Git; remove them from the index before public release.")
    return files, relevant


def has_teaching_body(text):
    """Reject empty stubs, not judge the truth or usefulness of teaching."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "---", "Source:", "Locator:")):
            continue
        if re.match(r"^(?:Title|Date|Author|Status|URL|Topics?|Coverage|SHA-256):", stripped, re.I):
            continue
        if re.fullmatch(r"(?i)(?:todo|tbd|pending|placeholder|coming soon)[.!: ]*", stripped):
            continue
        lines.append(stripped)
    # Structural minimum only; reviewed hashes and behavior evaluation serve
    # different purposes and neither can be replaced by a word-count threshold.
    return len(re.findall(r"\b\w+\b", " ".join(lines))) >= 5


def valid_locator(value):
    stripped = value.strip().strip("`[] ")
    return bool(stripped) and not re.match(r"(?i)(?:todo|tbd|unknown|pending|placeholder|n/a|none|missing|coming soon)\b", stripped)


def reviewed_hashes(root, files):
    paths = [root / "sources/catalog.json", *files]
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}


def record_review(root, reviewer, note):
    """Record a deliberate review; never clear sources or infer permission."""
    root = Path(root).resolve()
    if not reviewer.strip() or not note.strip():
        raise ValueError("Provide the actual reviewer and a note describing the completed publication review.")
    files, _ = validate_content(root)
    manifest = {"schema_version": 1, "reviewer": reviewer.strip(), "note": note.strip(),
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "sha256": reviewed_hashes(root, files)}
    destination = root / "sources/publication-review.json"
    if destination.is_symlink():
        raise ValueError("Publication review manifest must not be a symbolic link.")
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return destination


def validate(root):
    root = Path(root).resolve()
    files, records = validate_content(root)
    path = root / "sources/publication-review.json"
    if not path.is_file() or path.is_symlink():
        raise ValueError("Publication review missing; inspect catalog metadata and every package file, then run tools/review_release.py.")
    review = json.loads(path.read_text(encoding="utf-8"))
    if review.get("schema_version") != 1 or not review.get("reviewer") or not review.get("note") or not review.get("reviewed_at"):
        raise ValueError("Publication review metadata is incomplete.")
    expected = review.get("sha256", {})
    actual = reviewed_hashes(root, files)
    if expected != actual:
        added = sorted(set(actual) - set(expected))
        removed = sorted(set(expected) - set(actual))
        changed = sorted(name for name in set(actual) & set(expected) if actual[name] != expected[name])
        details = []
        for label, names in (("unreviewed files", added), ("missing files", removed), ("changed files", changed)):
            if names:
                details.append(label + ": " + ", ".join(names))
        raise ValueError("Publication review is stale (" + "; ".join(details) + "). Review the changes and record a new review deliberately.")
    return files, records


def package(root, version):
    root = Path(root).resolve()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", version):
        raise ValueError("Use a version such as 0.1.0 or 0.1.0-beta.1.")
    files, records = validate(root)
    destination = root / "releases" / f"matthew-ai-{version}.zip"
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        raise ValueError("That release exists; choose a new version.")
    skill = root / "skills" / "matthew-ai"
    with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, Path("matthew-ai") / path.relative_to(skill))
    return destination, len(records), len(files)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Required unless --check is used.")
    parser.add_argument("--check", action="store_true", help="Validate without creating a ZIP.")
    args = parser.parse_args()
    try:
        if args.check:
            files, records = validate(ROOT)
            print(f"Release validation passed: {len(records)} curated sources, {len(files)} files.")
        else:
            if not args.version:
                parser.error("--version is required unless --check is used.")
            destination, sources, files = package(ROOT, args.version)
            print(f"Created {destination.name}: {sources} curated sources, {files} files.")
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
