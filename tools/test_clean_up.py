"""Target selection only. Nothing under the real data folder is deleted."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import clean_up


class TargetTests(unittest.TestCase):
    def test_weights_are_removed_and_source_data_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "HyperCore"
            data = root / "HyperCore-data"
            for name in ("models", "packs", "mtp"):
                (data / name).mkdir(parents=True)
                (data / name / "weight.bin").write_bytes(b"x" * 10)
            (repo / "data").mkdir(parents=True)
            (repo / "data" / "expert-profile.bin").write_bytes(b"keep")
            (repo / "qwen-uncensored-gguf").mkdir()
            (repo / "qwen-uncensored-gguf" / "model.gguf").write_bytes(b"y" * 4)
            (repo / "pack").mkdir()
            (repo / "src").mkdir()
            (repo / "setup.py").write_text("source", encoding="utf-8")

            targets = clean_up.removal_targets([data, repo], repo)
            names = {p.name for p in targets}
            self.assertEqual(names, {"models", "packs", "mtp", "qwen-uncensored-gguf", "pack"})
            self.assertNotIn(repo / "data", targets)
            self.assertNotIn(repo, targets)
            self.assertEqual(clean_up.dir_bytes(data / "models"), 10)


if __name__ == "__main__":
    unittest.main()
