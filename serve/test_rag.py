"""The /home index: path jail, document types, and folder rows. Never crawls the real /home."""
import tempfile
import unittest
import zipfile
from pathlib import Path

from serve import rag


class Index(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "index.sqlite"
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "notes.md").write_text("# Gas\n\nCasper Wyoming fuel notes live in this folder.\n", encoding="utf-8")
        unit = self.root / "units"
        unit.mkdir()
        (unit / "local.service").write_text("[Service]\nExecStart=/usr/bin/example-daemon\n", encoding="utf-8")
        docx = docs / "sheet.docx"
        with zipfile.ZipFile(docx, "w") as zf:
            zf.writestr("word/document.xml",
                        "<w:document><w:p><w:t>quarterly spreadsheet totals</w:t></w:p></w:document>")
        outside = Path("/etc/passwd")
        if outside.is_file():
            link = self.root / "escape.txt"
            link.symlink_to(outside)
        (self.root / "secret.pem").write_text("not a document", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_search_finds_documents_and_directories(self):
        state = rag.crawl(self.root, self.db)
        self.assertEqual(state["phase"], "ready")
        self.assertGreaterEqual(state["files"], 3)
        hits = rag.search("Casper fuel", db_path=self.db, root=self.root)
        self.assertTrue(any(h["path"].endswith("notes.md") for h in hits))
        dirs = rag.search("units", db_path=self.db, root=self.root)
        self.assertTrue(any(h["kind"] == "directory" and h["path"].endswith("units") for h in dirs))
        sheets = rag.search("spreadsheet totals", db_path=self.db, root=self.root)
        self.assertTrue(any(h["path"].endswith("sheet.docx") for h in sheets))
        pem = rag.search("not a document", db_path=self.db, root=self.root)
        self.assertFalse(any(h["path"].endswith(".pem") for h in pem))
        (self.root / "docs" / "notes.md").write_text("replaced marker zephyrtext\n", encoding="utf-8")
        rag.crawl(self.root, self.db)
        self.assertFalse(rag.search("Casper fuel", db_path=self.db, root=self.root))
        again = rag.search("zephyrtext", db_path=self.db, root=self.root)
        self.assertTrue(any(h["path"].endswith("notes.md") for h in again))

    def test_symlink_and_outside_paths_are_refused(self):
        rag.crawl(self.root, self.db)
        hits = rag.search("root", db_path=self.db, root=self.root)
        self.assertFalse(any(h["path"].startswith("/etc") for h in hits))
        with self.assertRaises(ValueError):
            rag.structure("/etc", root=self.root)
        with self.assertRaises(ValueError):
            rag.read_document("/etc/passwd", root=self.root)
        escape = self.root / "escape.txt"
        if escape.is_symlink():
            with self.assertRaises(ValueError):
                rag.read_document(str(escape), root=self.root)

    def test_attach_inserts_a_note_without_rewriting_the_user(self):
        rag.crawl(self.root, self.db)
        messages = [
            {"role": "system", "content": "Be brief."},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "Where are the Casper fuel notes?"},
        ]
        out, hits = rag.attach(messages, db_path=self.db, root=self.root)
        self.assertEqual(messages[-1]["content"], "Where are the Casper fuel notes?")
        roles = [m["role"] for m in out]
        self.assertEqual(roles[:2], ["system", "system"])
        self.assertNotIn("system", roles[2:])
        self.assertIn("notes.md", out[1]["content"])
        self.assertTrue(hits)
        from serve.frontend import ChatTemplate
        template = ChatTemplate(Path(__file__).resolve().parents[1] / "serve" / "chat_template.jinja")
        rendered = template.render(out, reasoning_effort="medium")
        self.assertIn("notes.md", rendered)
        self.assertIn("Where are the Casper fuel notes?", rendered)

    def test_status_reports_an_index_built_by_another_process(self):
        rag.crawl(self.root, self.db)
        rag._state.update(phase="idle", files=0, dirs=0, started=0.0)   # as a fresh server would have it
        st = rag.status(self.db, self.root)
        self.assertGreaterEqual(st["rows"], 1)
        self.assertEqual(st["phase"], "ready")
        self.assertGreaterEqual(st["files"], 3)
        self.assertGreaterEqual(st["dirs"], 1)

    def test_structure_stays_inside_the_root(self):
        tree = rag.structure(str(self.root), depth=2, root=self.root)
        self.assertIn("notes.md", tree)
        self.assertIn("local.service", tree)
        self.assertNotIn("/etc", tree)


if __name__ == "__main__":
    unittest.main()
