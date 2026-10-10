"""The text primitives behind read_file and edit_file: ranges, outlines, edits.

    python3 -m unittest serve.test_doc_text

These run against strings, not files, so they need no workspace and no server. The
per-tool behaviour is covered by serve/mcp/tests/test_docs.py and test_home.py; this
file covers the parts those cannot reach: the outline extractors for the languages the
servers route to, outline pagination, and the argument coercion.
"""
from __future__ import annotations

import unittest

from serve import doc_text as dt


class LineRanges(unittest.TestCase):
    def test_defaults_and_clamps(self):
        self.assertEqual(dt.resolve_line_range(None, None), (1, 2**31 - 1))
        self.assertEqual(dt.resolve_line_range(0, 3), (1, 3))          # models pass 0
        self.assertEqual(dt.resolve_line_range(5, 2), (5, 5))          # end below start
        self.assertEqual(dt.resolve_line_range("7", "9"), (7, 9))      # strings come through JSON

    def test_numbering_is_cat_n(self):
        self.assertEqual(dt.format_with_line_numbers("a\nb", 3), "     3\ta\n     4\tb")
        self.assertEqual(dt.format_with_line_numbers(""), "")

    def test_line_count_matches_the_numbering(self):
        self.assertEqual(dt.line_count("one\ntwo\n"), 2)
        self.assertEqual(dt.line_count("one\ntwo"), 2)
        self.assertEqual(dt.line_count(""), 0)

    def test_a_range_reports_where_to_continue(self):
        text = "\n".join(f"l{i}" for i in range(1, 121))
        body, note = dt.read_with_ranges(text, 3, 4)
        self.assertEqual(body, "     3\tl3\n     4\tl4")
        self.assertIn("continue with start_line=5", note)
        body, note = dt.read_with_ranges(text, 120, 120)
        self.assertEqual(note, "")
        body, note = dt.read_with_ranges(text, 121, 121)
        self.assertEqual(body, "")
        self.assertIn("past the end", note)

    def test_a_long_range_is_cut_at_a_line_boundary_and_names_the_next_line(self):
        text = "\n".join("x" * 200 for _ in range(200))
        body, note = dt.read_with_ranges(text, 1, 200)
        self.assertLessEqual(len(body), dt.MAX_RANGE_CHARS)
        self.assertIn("Continue with start_line=", note)
        last_line = int(note.split("lines 1-")[1].split(" of")[0])
        self.assertGreater(last_line, 1)


class Outlines(unittest.TestCase):
    def test_python_gives_classes_methods_and_constants(self):
        src = (
            "MAX = 3\n\n\n"
            "class Hub:\n"
            "    def start(self):\n"
            "        pass\n\n\n"
            "def run(a, b=1, *rest, **kw):\n"
            "    return a\n"
        )
        entries = dt.extract_outline("hub.py", src)
        kinds = [(e.kind, e.text) for e in entries]
        self.assertIn(("const", "MAX ="), kinds)
        self.assertIn(("class", "class Hub"), kinds)
        self.assertIn(("  method", "def start(self)"), kinds)
        self.assertIn(("def", "def run(a, b, *rest, **kw)"), kinds)

    def test_python_that_does_not_parse_falls_back(self):
        self.assertEqual(dt.extract_outline("broken.py", "def a(:\n"), [])

    def test_markdown_headings_and_code_blocks(self):
        entries = dt.extract_outline("doc.md", "# Top\n\n## Second\n\n```python\nx = 1\n```")
        self.assertEqual([(e.line, e.kind) for e in entries], [(1, "heading"), (3, "heading"), (5, "code")])

    def test_c_and_shell_functions(self):
        cpp = '#include <cuda_runtime.h>\nvoid gemv(const float* a) {\n  int x = 1;\n}\n'
        self.assertEqual([(e.kind, e.text) for e in dt.extract_outline("k.cu", cpp)],
                         [("include", "<cuda_runtime.h>"), ("func", "gemv")])
        sh = 'setup() {\n  echo hi\n}\nmain() {\n  setup\n}\n'
        self.assertEqual([e.text for e in dt.extract_outline("run.sh", sh)], ["setup", "main"])

    def test_config_keys(self):
        yaml = "servers:\n  docs:\n    command: python3\nsettings:\n  timeout_s: 90\n"
        self.assertEqual([e.text for e in dt.extract_outline("mcp.yaml", yaml)],
                         ["servers", "docs", "command", "settings", "timeout_s"])
        toml = "[model]\nn_ctx = 8\n[server]\nport = 8080\n"
        self.assertEqual([e.text for e in dt.extract_outline("cfg.toml", toml)], ["model", "server"])
        json_keys = dt.extract_outline("s.json", '{"alpha": 1, "beta": 2}')
        self.assertEqual([e.text for e in json_keys], ["alpha", "beta"])

    def test_a_plain_text_file_has_no_structure(self):
        self.assertEqual(dt.extract_outline("notes.txt", "just prose\nmore prose\n"), [])

    def test_pagination_reports_whether_more_follow(self):
        entries = [dt.OutlineEntry(i, "def", f"f{i}") for i in range(100)]
        page, more = dt.render_outline(entries, 0, 60)
        self.assertEqual(len(page.splitlines()), 60)
        self.assertTrue(more)
        page, more = dt.render_outline(entries, 60, 60)
        self.assertEqual(len(page.splitlines()), 40)
        self.assertFalse(more)


class Edits(unittest.TestCase):
    def test_sequential_edits_apply_in_order(self):
        text, report = dt.apply_edits("a\nb\nc\n", [dt.Edit("a", "A"), dt.Edit("b", "B")])
        self.assertEqual(text, "A\nB\nc\n")
        self.assertEqual(len(report), 2)

    def test_an_ambiguous_match_names_the_lines(self):
        with self.assertRaises(ValueError) as caught:
            dt.apply_edits("x\nx\n", [dt.Edit("x", "y")])
        self.assertIn("lines 1, 2", str(caught.exception))

    def test_a_line_hint_selects_one_match(self):
        text, _ = dt.apply_edits("x\nx\n", [dt.Edit("x", "y", 2)])
        self.assertEqual(text, "x\ny\n")
        with self.assertRaises(ValueError):
            dt.apply_edits("x\nx\n", [dt.Edit("x", "y", 9)])

    def test_a_copied_line_number_prefix_is_stripped(self):
        text, report = dt.apply_edits("alpha\nbeta\n", [dt.Edit("     2\tbeta", "BETA")])
        self.assertEqual(text, "alpha\nBETA\n")
        self.assertIn("prefix was removed", report[0])

    def test_empty_old_text_is_refused(self):
        with self.assertRaises(ValueError):
            dt.apply_edits("a\n", [dt.Edit("", "b")])

    def test_edits_are_parsed_from_a_list_a_dict_or_a_json_string(self):
        edits, error = dt.parse_edits('[{"old_text": "a", "new_text": "b"}]')
        self.assertEqual(error, "")
        self.assertEqual(len(edits), 1)
        edits, error = dt.parse_edits({"old_text": "a", "new_text": "b"})
        self.assertEqual(error, "")
        self.assertEqual(len(edits), 1)
        _, error = dt.parse_edits("not json")
        self.assertIn("must be a list", error)
        _, error = dt.parse_edits([{"old_text": "a", "new_text": 3}])
        self.assertIn("must be strings", error)
        _, error = dt.parse_edits([])
        self.assertIn("non-empty", error)

    def test_alternate_key_names_are_accepted(self):
        edits, error = dt.parse_edits([{"old": "a", "new": "b", "line": "3"}])
        self.assertEqual(error, "")
        self.assertEqual((edits[0].old_text, edits[0].new_text, edits[0].line), ("a", "b", 3))


class StructureContext(unittest.TestCase):
    def test_a_range_inside_a_function_reports_that_function(self):
        src = "class Hub:\n    def start(self):\n        pass\n\n\ndef top():\n    return 1\n"
        self.assertEqual(dt.enclosing_symbol("hub.py", src, 3, 3), "def start")
        self.assertEqual(dt.enclosing_symbol("hub.py", src, 1, 3), "class Hub")
        self.assertEqual(dt.enclosing_symbol("hub.py", src, 7, 7), "def top")
        self.assertIsNone(dt.enclosing_symbol("hub.py", src, 1, 7))   # spans both, no single owner

    def test_ranges_come_from_braces_when_ast_is_not_available(self):
        src = '#include <stdio.h>\nvoid gemv(int n) {\n  int i = 1;\n}\n'
        self.assertEqual(dt.enclosing_symbol("k.c", src, 3, 3), "func gemv")
        self.assertIsNone(dt.enclosing_symbol("notes.txt", "plain prose\n", 1, 1))

    def test_shell_function_ranges_end_at_the_closing_brace(self):
        src = 'setup() {\n  echo a\n}\nmain() {\n  setup\n}\n'
        self.assertEqual(dt.enclosing_symbol("run.sh", src, 2, 2), "func setup")
        self.assertEqual(dt.enclosing_symbol("run.sh", src, 5, 5), "func main")
        self.assertIsNone(dt.enclosing_symbol("run.sh", src, 1, 6))   # spans both, no single owner

    def test_a_read_range_carries_the_symbol_note(self):
        src = "def f():\n    a = 1\n    b = 2\n"
        _body, note = dt.read_with_ranges(src, 2, 3, "f.py")
        self.assertIn("are inside def f", note)
        _body, note = dt.read_with_ranges(src, 2, 3)
        self.assertNotIn("inside", note)


class Coercion(unittest.TestCase):
    def test_a_sequence_arrives_in_several_shapes(self):
        self.assertEqual(dt.coerce_sequence(["a", "b"]), ["a", "b"])
        self.assertEqual(dt.coerce_sequence('["seq 1 3", "wc -l"]'), ["seq 1 3", "wc -l"])
        self.assertEqual(dt.coerce_sequence("seq 1 3\nwc -l"), ["seq 1 3", "wc -l"])
        self.assertEqual(dt.coerce_sequence("a; b"), ["a", "b"])
        self.assertEqual(dt.coerce_sequence([]), [])
        self.assertEqual(dt.coerce_sequence(None), [])
        self.assertEqual(dt.coerce_sequence("  "), [])
        with self.assertRaises(ValueError):
            dt.coerce_sequence(7)

    def test_a_json_array_in_a_string_that_is_not_json_falls_back_to_lines(self):
        self.assertEqual(dt.coerce_sequence("[not, json]"), ["[not, json]"])

    def test_int_arguments_are_bounded(self):
        self.assertEqual(dt.clamp_int(None, 1, 10, 5), 5)
        self.assertEqual(dt.clamp_int(0, 1, 10, 5), 1)
        self.assertEqual(dt.clamp_int(99, 1, 10, 5), 10)
        self.assertEqual(dt.clamp_int("7", 1, 10, 5), 7)
        self.assertEqual(dt.clamp_int("abc", 1, 10, 5), 5)


if __name__ == "__main__":
    unittest.main()
