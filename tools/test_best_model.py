"""Ranking only. Hardware is passed in, so this does not need a GPU."""
import sys
import unittest
from pathlib import Path

# best_model.py lives in tune/, beside the tuner it belongs to
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tune"))
import best_model


class RankTests(unittest.TestCase):
    def test_a_64gb_pc_prefers_measured_iq3_s_over_an_estimate(self):
        rows = best_model.offerings()
        ranked = best_model.rank(rows, ram=64, vram=24, disk_gb=200)
        best = best_model.recommend(ranked)
        self.assertEqual(best["family"], "qwen")
        self.assertEqual(best["model"], "IQ3_S")
        self.assertEqual(best["status"], "fits")

    def test_a_32gb_pc_keeps_only_the_coder(self):
        ranked = best_model.rank(best_model.offerings(), ram=32, vram=12, disk_gb=200)
        best = best_model.recommend(ranked)
        kept = [(r["family"], r["model"]) for r in ranked if r["status"] in ("fits", "low-ram")]
        self.assertEqual(kept, [("coder", "IQ1_M")])
        self.assertEqual((best["family"], best["model"]), ("coder", "IQ1_M"))

    def test_unknown_disk_does_not_reject(self):
        row = next(r for r in best_model.offerings() if r["family"] == "coder" and r["model"] == "IQ1_M")
        self.assertEqual(best_model.classify(row, ram=32, vram=12, disk_gb=None), "fits")

    def test_low_disk_drops_a_model_that_would_otherwise_fit(self):
        row = next(r for r in best_model.offerings() if r["family"] == "qwen" and r["model"] == "Q2_0")
        self.assertEqual(best_model.classify(row, ram=64, vram=12, disk_gb=10), "disk")
        self.assertEqual(best_model.classify(row, ram=64, vram=12, disk_gb=200), "fits")


if __name__ == "__main__":
    unittest.main()
