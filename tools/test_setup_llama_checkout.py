"""setup.py's llama.cpp checkout: a folder that only partly arrived is unpacked again from the archive
instead of being trusted.  The engine builds from ggml alone, so the gap only shows up when the image
encoder is configured - a CMake error about a file setup never mentioned - which is what answering "y"
to "Do you want images?" ran into.  Nothing is downloaded: the archive is a local file.

    python -m unittest tools.test_setup_llama_checkout
"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import setup  # noqa: E402

# one file per thing the two builds read: ggml for the engine, gguf-py for the pack tools, mtmd for the
# image encoder, and the build-info files llama.cpp's own CMakeLists.txt includes
FULL = {"ggml/CMakeLists.txt": "ggml", "gguf-py/gguf/__init__.py": "gguf", "tools/mtmd/mtmd.h": "mtmd",
        "cmake/build-info.cmake": "build info", "common/build-info.h": "header",
        "common/build-info.cpp.in": "template", "tools/ui/index.html": "the web ui, not used"}


def archive(z: Path, files: dict) -> None:
    """A llama.cpp-shaped zip: everything under one `llama.cpp-<sha>/` prefix, like GitHub's archive."""
    z.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(z, "w") as f:
        for name, body in files.items():
            f.writestr(f"llama.cpp-deadbeef/{name}", body)


def checkout(root: Path, files: dict) -> Path:
    llama = root / "third_party" / "llama.cpp"
    for name, body in files.items():
        p = llama / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return llama


class LlamaCheckout(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.zip = self.root / "third_party" / f"llama.cpp-{setup.LLAMA_CPP_COMMIT[:7]}.zip"
        archive(self.zip, FULL)
        self.zip.with_name(self.zip.name + ".done").write_text("", encoding="utf-8")

    def unpack(self, files):
        """get_llama_cpp() on a checkout holding `files`, with the archive already in third_party."""
        out = io.StringIO()
        llama = checkout(self.root, files)
        with mock.patch.object(setup, "ROOT", self.root), \
             mock.patch.object(setup, "download", lambda *a, **k: self.fail("downloaded from the network")), \
             mock.patch.object(sys, "stdout", out):
            try:
                return setup.get_llama_cpp(), out.getvalue()
            except SystemExit as e:
                return e.code, out.getvalue()

    def test_a_complete_checkout_is_left_alone(self):
        got, out = self.unpack({**FULL, "ggml/CMakeLists.txt": "the one this PC built with"})
        self.assertEqual(got, self.root / "third_party" / "llama.cpp")
        self.assertEqual((got / "ggml/CMakeLists.txt").read_text(), "the one this PC built with")
        self.assertEqual(out, "")

    def test_a_short_checkout_is_unpacked_again(self):
        """The engine's own files are there, so "is llama.cpp here" is true - and the image encoder's
        configure then stops on cmake/build-info.cmake.  setup unpacks the archive instead."""
        got, out = self.unpack({k: v for k, v in FULL.items() if k != "cmake/build-info.cmake"})
        self.assertEqual(got, self.root / "third_party" / "llama.cpp")
        self.assertIn("the llama.cpp checkout is short cmake/build-info.cmake: unpacking it again", out)
        self.assertEqual((got / "cmake/build-info.cmake").read_text(), "build info")
        self.assertFalse((got / "tools/ui").exists())          # #206: the web UI is still not unpacked
        self.assertFalse(self.zip.exists())                    # used up, as before

    def test_an_archive_short_of_a_build_file_names_it(self):
        """If the archive itself is short of one, setup stops with the file named and keeps the zip, so the
        next run unpacks it again instead of downloading 40 MB."""
        archive(self.zip, {k: v for k, v in FULL.items() if k not in ("common/build-info.h", "tools/mtmd/mtmd.h")})
        code, out = self.unpack({k: v for k, v in FULL.items() if k != "common/build-info.h"})
        self.assertEqual(code, 1)
        self.assertIn("has no tools/mtmd/mtmd.h, common/build-info.h", out)
        self.assertTrue(self.zip.exists())

    @unittest.skipUnless((ROOT / "third_party" / f"llama.cpp-{setup.LLAMA_CPP_COMMIT[:7]}.zip").exists(),
                        "the pinned archive is not on this PC")
    def test_the_check_only_asks_for_files_the_archive_ships(self):
        """The pinned llama.cpp really does have every file the check asks for: a check that asked for
        something the archive does not ship would make setup re-download 40 MB on every run."""
        with zipfile.ZipFile(ROOT / "third_party" / f"llama.cpp-{setup.LLAMA_CPP_COMMIT[:7]}.zip") as f:
            names = set(f.namelist())
        for want in setup.LLAMA_BUILD_FILES:
            self.assertTrue(any(n.endswith("/" + want) for n in names), want)


if __name__ == "__main__":
    unittest.main()
