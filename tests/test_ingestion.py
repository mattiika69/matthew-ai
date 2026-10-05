"""Capture/release invariants. Fixtures are synthetic and never enter the library."""
import hashlib
import importlib.util
import json
import tempfile
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


capture = module("import_source")
release = module("package_skill")


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "sources").mkdir()
        (self.root / "sources/catalog.json").write_text("[]\n")
        self.input = self.root / "input.md"
        self.input.write_bytes(b"Original line.\r\n\r\nExact spacing.  \r\n")
        self.kwargs = dict(source_id="S001", source_type="lesson", title="Synthetic lesson",
                           url="https://example.com/lesson", source_date=None,
                           author="Test Author", topics=["source-derived-topic"],
                           input_path=self.input, coverage="Written content only; recording not captured.")

    def ingest(self, **changes):
        return capture.ingest(self.root, **{**self.kwargs, **changes})

    def catalog(self):
        return json.loads((self.root / "sources/catalog.json").read_text())

    def full_manifest(self):
        return json.loads((self.root / "raw/manifest.json").read_text())

    def write_catalog(self, records):
        (self.root / "sources/catalog.json").write_text(json.dumps(records))

    def test_exact_bytes_and_provenance_preserved(self):
        result = self.ingest()
        record = self.catalog()[0]
        self.assertEqual(result["status"], "captured")
        self.assertEqual((self.root / "raw/S001.md").read_bytes(), self.input.read_bytes())
        self.assertEqual(record["sha256"], hashlib.sha256(self.input.read_bytes()).hexdigest())
        self.assertEqual(record["date"], None)
        self.assertEqual(record["author"], "Withheld pending review")
        self.assertEqual(record["topics"], [])
        self.assertEqual(record["url"], None)
        full = self.full_manifest()[0]
        self.assertEqual(full["author"], "Test Author")
        self.assertEqual(full["topics"], ["source-derived-topic"])
        self.assertEqual(full["url"], self.kwargs["url"])
        self.assertEqual(record["publication_status"], "unreviewed")
        self.assertEqual(record["visibility"], "private")
        self.assertIn("recording not captured", full["coverage"])
        self.assertFalse((self.root / "skills").exists())
        self.assertTrue((self.root / "proposals/S001.md").is_file())

    def test_reimport_is_noop_and_preserves_review_status(self):
        self.ingest()
        records = self.catalog()
        records[0]["publication_status"] = "cleared"
        self.write_catalog(records)
        before = (self.root / "sources/catalog.json").read_bytes()
        self.assertEqual(self.ingest()["status"], "unchanged")
        self.assertEqual((self.root / "sources/catalog.json").read_bytes(), before)

    def test_exact_duplicate_with_other_id_makes_no_changes(self):
        self.ingest()
        before = (self.root / "sources/catalog.json").read_bytes()
        result = self.ingest(source_id="S002")
        self.assertEqual(result["existing_ids"], ["S001"])
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual((self.root / "sources/catalog.json").read_bytes(), before)
        self.assertFalse((self.root / "raw/S002.md").exists())

    def test_changed_capture_requires_explicit_replacement(self):
        self.ingest()
        old = (self.root / "raw/S001.md").read_bytes()
        self.input.write_text("New source content.\n")
        with self.assertRaisesRegex(ValueError, "--replace"):
            self.ingest()
        self.assertEqual((self.root / "raw/S001.md").read_bytes(), old)

    def test_replacement_archives_bytes_metadata_and_never_changes_curated_file(self):
        self.ingest()
        records = self.catalog()
        records[0]["curated_files"] = ["references/curated.md"]
        records[0]["publication_status"] = "cleared"
        self.write_catalog(records)
        old_record = records[0]
        curated = self.root / "skills/matthew-ai/references/curated.md"
        curated.parent.mkdir(parents=True)
        curated.write_text("Deliberately curated knowledge; do not overwrite.\n")
        old_curated = curated.read_bytes()
        old_raw = self.input.read_bytes()
        self.input.write_text("New source version.\n")
        self.assertEqual(self.ingest(replace=True)["status"], "replaced")
        archived = self.root / "raw/revisions/S001" / f"{old_record['sha256']}.md"
        self.assertEqual(archived.read_bytes(), old_raw)
        metadata_files = list(archived.parent.glob("*.json"))
        self.assertEqual(json.loads(metadata_files[0].read_text())["public_record"], old_record)
        self.assertEqual(json.loads(metadata_files[0].read_text())["full_record"]["title"], "Synthetic lesson")
        self.assertEqual(curated.read_bytes(), old_curated)
        self.assertEqual(self.catalog()[0]["curated_files"], ["references/curated.md"])
        self.assertEqual(self.catalog()[0]["publication_status"], "unreviewed")

    def test_topic_overlap_and_manual_conflict_flag_are_review_candidates(self):
        self.ingest()
        self.input.write_text("Potentially different recommendation.\n")
        result = self.ingest(source_id="S002", conflicts_with=["S001"])
        self.assertEqual(result["comparison_candidates"], ["S001"])
        proposal = (self.root / "proposals/S002.md").read_text()
        self.assertIn("not evidence of a contradiction", proposal)
        self.assertIn("Explicitly flagged possible conflicts: S001", proposal)
        self.assertEqual(self.catalog()[1]["publication_status"], "unreviewed")

    def test_altered_raw_capture_cannot_be_silently_replaced(self):
        self.ingest()
        (self.root / "raw/S001.md").write_text("Untracked edit")
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            self.ingest(replace=True)

    def test_invalid_id_and_empty_input_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "source ID"):
            self.ingest(source_id="../escape")
        self.input.write_text("\n  ")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.ingest()

    def test_date_is_not_inferred_and_can_be_recorded_explicitly(self):
        self.ingest(source_date="2025-01-12")
        self.assertEqual(self.full_manifest()[0]["date"], "2025-01-12")
        self.assertEqual(self.catalog()[0]["date"], None)


    def test_private_metadata_and_share_tokens_stay_only_in_ignored_manifest(self):
        private_url = "https://example.com/document?access_token=PRIVATE_EXAMPLE#secret-fragment"
        self.ingest(title="Private Person refund dispute", author="Private Person",
                    topics=["Private account"], url=private_url,
                    coverage="Private account balance details")
        public_bytes = (self.root / "sources/catalog.json").read_text()
        self.assertNotIn("Private Person", public_bytes)
        self.assertNotIn("PRIVATE_EXAMPLE", public_bytes)
        self.assertNotIn("Private account", public_bytes)
        self.assertEqual(self.full_manifest()[0]["url"], private_url)
        self.assertEqual(self.catalog()[0]["title"], "Unreviewed source S001")

    def test_public_url_tokens_are_removed_but_original_remains_private(self):
        original = "https://www.youtube.com/watch?v=HS8EjMBhG8o&t=90s&token=PRIVATE_EXAMPLE#secret"
        self.ingest(visibility="public", url=original)
        self.assertEqual(self.catalog()[0]["url"], "https://www.youtube.com/watch?v=HS8EjMBhG8o&t=90s")
        self.assertEqual(self.full_manifest()[0]["url"], original)
        self.assertNotIn("PRIVATE_EXAMPLE", (self.root / "sources/catalog.json").read_text())


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.skill = self.root / "skills/matthew-ai"
        (self.skill / "references").mkdir(parents=True)
        (self.root / "sources").mkdir()
        (self.root / "raw").mkdir()
        (self.root / "raw/S001.md").write_text("Private full transcript with customer details.\n")
        (self.skill / "SKILL.md").write_text("# Test skill\n\nRead [knowledge](references/knowledge.md).\n")
        self.curated = self.skill / "references/knowledge.md"
        self.curated.write_text("# Reviewed principle\n\nA deliberately reviewed synthetic principle.\n\nSource: S001\nLocator: Lesson section 2\n")
        (self.skill / "references/sources.md").write_text("# Sources\n\nS001 — Synthetic lesson\nDate: unknown\n")
        self.records = [{"id": "S001", "title": "Synthetic lesson", "type": "lesson",
                         "date": None, "author": "Test Author", "topics": ["example"],
                         "url": None, "raw_path": "raw/S001.md",
                         "sha256": hashlib.sha256((self.root / "raw/S001.md").read_bytes()).hexdigest(),
                         "curated_files": ["references/knowledge.md"], "visibility": "private",
                         "publication_status": "cleared", "capture_method": "local-text-import",
                         "coverage": "Synthetic test fixture"}]
        self.save()
        release.record_review(self.root, "Synthetic test reviewer", "Reviewed synthetic fixtures for test publication.")

    def save(self):
        (self.root / "sources/catalog.json").write_text(json.dumps(self.records))

    def test_package_only_contains_skill_and_reviewed_private_extract_is_allowed(self):
        destination, sources, files = release.package(self.root, "0.1.0-beta.1")
        with zipfile.ZipFile(destination) as archive:
            names = archive.namelist()
            self.assertTrue(all(name.startswith("matthew-ai/") for name in names))
            self.assertFalse(any("raw/" in name or "catalog.json" in name for name in names))
            self.assertFalse(any(b"Private full transcript" in archive.read(name) for name in names))
        self.assertEqual(sources, 1)
        self.assertEqual(files, 3)

    def test_empty_catalog_and_unpopulated_curated_library_are_rejected(self):
        for records in ([], [{**self.records[0], "curated_files": []}]):
            self.records = records
            self.save()
            with self.assertRaisesRegex(ValueError, "empty knowledge"):
                release.validate(self.root)

    def test_unreviewed_source_is_rejected(self):
        self.records[0]["publication_status"] = "unreviewed"
        self.save()
        with self.assertRaisesRegex(ValueError, "deliberate public-distribution review"):
            release.validate(self.root)

    def test_missing_locator_is_rejected(self):
        self.curated.write_text("# Principle\n\nA deliberately reviewed synthetic principle.\nSource: S001\n")
        with self.assertRaisesRegex(ValueError, "Locator"):
            release.validate(self.root)

    def test_unknown_citation_is_rejected(self):
        self.curated.write_text(self.curated.read_text() + "\nSource: S999\nLocator: Other section\n")
        with self.assertRaisesRegex(ValueError, "Unknown source S999"):
            release.validate(self.root)

    def test_missing_offline_source_title_is_rejected(self):
        (self.skill / "references/sources.md").write_text("S001\n")
        with self.assertRaisesRegex(ValueError, "ID/title"):
            release.validate(self.root)

    def test_broken_pointer_is_rejected(self):
        (self.skill / "SKILL.md").write_text("Read [missing](references/missing.md).\n")
        with self.assertRaisesRegex(ValueError, "Broken"):
            release.validate(self.root)

    def test_raw_copy_in_skill_is_rejected_even_if_renamed(self):
        (self.skill / "references/accidental.md").write_bytes((self.root / "raw/S001.md").read_bytes())
        with self.assertRaisesRegex(ValueError, "Uncurated raw capture"):
            release.validate(self.root)

    def test_symlink_and_env_are_rejected(self):
        symlink = self.skill / "references/private.md"
        symlink.symlink_to(self.root / "raw/S001.md")
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            release.validate(self.root)
        symlink.unlink()
        (self.skill / ".env").write_text("SECRET=synthetic\n")
        with self.assertRaisesRegex(ValueError, "Private/build material"):
            release.validate(self.root)

    def test_existing_release_is_never_overwritten(self):
        destination, _, _ = release.package(self.root, "0.1.0")
        original = destination.read_bytes()
        with self.assertRaisesRegex(ValueError, "release exists"):
            release.package(self.root, "0.1.0")
        self.assertEqual(destination.read_bytes(), original)

    def test_citation_requires_reverse_provenance_mapping(self):
        (self.skill / "references/extra.md").write_text("Source: S001\nLocator: Lesson section 2\n")
        with self.assertRaisesRegex(ValueError, "does not record"):
            release.validate(self.root)


    def test_unregistered_transformed_raw_file_fails_review_manifest(self):
        (self.skill / "references/customer-notes.md").write_text(
            "# Notes\n\n" + (self.root / "raw/S001.md").read_text())
        with self.assertRaisesRegex(ValueError, "unreviewed files"):
            release.validate(self.root)

    def test_edited_cleared_file_requires_new_deliberate_review(self):
        self.curated.write_text(self.curated.read_text() + "\nPrivate customer email: synthetic@example.com\n")
        with self.assertRaisesRegex(ValueError, "changed files"):
            release.validate(self.root)

    def test_catalog_metadata_changes_invalidate_review(self):
        self.records[0]["coverage"] = "Changed metadata after publication review"
        self.save()
        with self.assertRaisesRegex(ValueError, "sources/catalog.json"):
            release.validate(self.root)

    def test_removed_package_file_invalidates_review(self):
        extra = self.skill / "references/optional.md"
        extra.write_text("Public helper instructions inspected by the reviewer.\n")
        release.record_review(self.root, "Test reviewer", "Inspected all synthetic content")
        extra.unlink()
        with self.assertRaisesRegex(ValueError, "missing files"):
            release.validate(self.root)

    def test_missing_review_manifest_is_rejected(self):
        (self.root / "sources/publication-review.json").unlink()
        with self.assertRaisesRegex(ValueError, "Publication review missing"):
            release.validate(self.root)

    def test_review_cannot_clear_unreviewed_private_metadata(self):
        self.records.append({"id": "S999", "title": "Private customer identity",
                             "url": "https://example.com/file?token=SECRET",
                             "visibility": "private", "publication_status": "unreviewed",
                             "curated_files": []})
        self.save()
        with self.assertRaisesRegex(ValueError, "deliberate public-distribution review"):
            release.record_review(self.root, "Test reviewer", "Attempted review")
        self.assertEqual(self.records[1]["publication_status"], "unreviewed")

    def test_review_rejects_credential_bearing_catalog_urls(self):
        for key in ("url", "transcript_url"):
            with self.subTest(key=key):
                self.records[0][key] = "https://example.com/file?token=SECRET"
                self.save()
                with self.assertRaisesRegex(ValueError, "sanitized and credential-free"):
                    release.record_review(self.root, "Test reviewer", "Attempted review")
                self.records[0][key] = None

    def test_placeholder_and_metadata_only_knowledge_cannot_be_reviewed(self):
        self.curated.write_text("# Placeholder\n\nSource: S001\nLocator: TODO\n")
        with self.assertRaisesRegex(ValueError, "no substantive teaching"):
            release.record_review(self.root, "Test reviewer", "Attempted review")
        self.curated.write_text("# Reviewed lesson\n\nFive meaningful words about synthetic teaching exist here.\n\nSource: S001\nLocator: TODO\n")
        with self.assertRaisesRegex(ValueError, "concrete.*Locator"):
            release.record_review(self.root, "Test reviewer", "Attempted review")

    def test_explicit_review_records_hashes_and_reviewer_without_clearing_sources(self):
        path = release.record_review(self.root, "Actual synthetic reviewer", "All catalog metadata and skill files inspected")
        review = json.loads(path.read_text())
        self.assertEqual(review["reviewer"], "Actual synthetic reviewer")
        self.assertEqual(set(review["sha256"]), {"sources/catalog.json", "skills/matthew-ai/SKILL.md",
                         "skills/matthew-ai/references/sources.md", "skills/matthew-ai/references/knowledge.md"})
        self.assertEqual(review["sha256"]["sources/catalog.json"], hashlib.sha256((self.root / "sources/catalog.json").read_bytes()).hexdigest())
        release.validate(self.root)


if __name__ == "__main__":
    unittest.main()
