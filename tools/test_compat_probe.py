"""Header-only compatibility probe. Run: python -m unittest discover -s tools -p test_compat_probe.py"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compat_probe
import gguf_writer
import linux_catalog

gguf_writer.TYPE_IDS.update({"BF16": 30, "Q8_0": 8, "Q5_0": 6, "Q4_K": 12, "IQ4_NL": 20, "IQ3_XXS": 18})


def write_header(path, arch, tensors, **meta):
    writer = gguf_writer.GGUFWriter()
    writer.add("general.architecture", arch)
    for key, value in meta.items():
        writer.add(key, value)
    for name, shape, type_name in tensors:
        writer.tensors.append(gguf_writer._Tensor(name, list(shape), type_name, b""))
    writer.write(path)


def flash_tensors(proj="BF16", down="IQ4_NL", ple=True, layers=48, experts=512):
    tensors = []
    for layer in range(layers):
        tensors.append((f"blk.{layer}.ffn_gate_inp.weight", [2560, experts], "BF16"))
        tensors.append((f"blk.{layer}.ffn_down_exps.weight", [640, 2560, experts], down))
        tensors.append((f"blk.{layer}.hc_attn_down.weight", [10240, 320], proj))
    if ple:
        tensors.append(("per_layer_token_embd.weight", [2560, 8], "Q8_0"))
    return tensors


class ProbeTests(unittest.TestCase):
    def test_bf16_projections_need_no_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"
            write_header(path, "qwen4exp", flash_tensors(), **{"qwen4exp.block_count": 48,
                                                               "qwen4exp.embedding_length": 2560})
            recipe, errors = compat_probe.inspect(path)
            self.assertEqual(errors, [])
            self.assertFalse(recipe["compat_bf16"])
            self.assertEqual(recipe["n_expert"], 512)
            self.assertEqual(recipe["ple_shard"], path.name)
            self.assertEqual(recipe["expert_down_types"], ["IQ4_NL"])

    def test_quantized_projection_requests_compat_bf16(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"
            write_header(path, "qwen4exp", flash_tensors(proj="Q8_0"))
            recipe, errors = compat_probe.inspect(path)
            self.assertEqual(errors, [])
            self.assertTrue(recipe["compat_bf16"])

    def test_missing_ple_is_one_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"
            write_header(path, "qwen4exp", flash_tensors(ple=False))
            recipe, errors = compat_probe.inspect(path)
            self.assertIsNone(recipe)
            self.assertTrue(any("per_layer_token_embd" in line for line in errors))

    def test_q5_0_down_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"
            write_header(path, "qwen4exp", flash_tensors(down="Q5_0"))
            recipe, errors = compat_probe.inspect(path)
            self.assertIsNone(recipe)
            self.assertTrue(any("Q5_0" in line for line in errors))

    def test_qwen3next_80b_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf"
            write_header(path, "qwen3next", [
                ("blk.0.ffn_gate_inp.weight", [2048, 512], "BF16"),
                ("blk.0.ffn_down_exps.weight", [512, 2048, 512], "Q4_K"),
            ], **{"qwen3next.embedding_length": 2048, "qwen3next.block_count": 48})
            recipe, errors = compat_probe.inspect(path)
            self.assertIsNone(recipe)
            text = "\n".join(errors)
            self.assertIn("Qwen3-Next-80B-A3B", text)
            self.assertIn("2048", text)
            self.assertIn("qwen4exp", text)
            self.assertNotIn("IQ3_XXS", text)

    def test_ple_in_the_second_shard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "model-00001-of-00002.gguf"
            second = root / "model-00002-of-00002.gguf"
            write_header(first, "qwen4exp", flash_tensors(ple=False))
            write_header(second, "qwen4exp", [("per_layer_token_embd.weight", [2560, 8], "Q8_0")])
            recipe, errors = compat_probe.inspect(first)
            self.assertEqual(errors, [])
            self.assertEqual(recipe["ple_shard"], second.name)

    def test_cli_exits_2_for_80b(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "thinking.gguf"
            write_header(path, "qwen3next", [], **{"qwen3next.embedding_length": 2048})
            self.assertEqual(compat_probe.main(["--gguf", str(path)]), 2)


class CatalogTests(unittest.TestCase):
    def test_linux_setup_merges_the_catalog(self):
        root = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(root))
        import setup
        self.assertIn("orca", setup.FAMILIES)
        self.assertIn("flashgguf", setup.FAMILIES)
        self.assertIs(setup.FAMILIES["orca"]["vision"], False)
        self.assertFalse(setup.reuse_gsq_shard2("orca"))
        self.assertFalse(setup.reuse_gsq_shard2("flashgguf"))
        self.assertTrue(setup.reuse_gsq_shard2("qwen"))
        self.assertTrue(setup.reuse_gsq_shard2("coder"))
        self.assertFalse(setup.use_q2_avx_pack("orca", "Q2_0", True))
        self.assertFalse(setup.use_q2_avx_pack("flashgguf", "Q2_K", True))
        self.assertTrue(setup.use_q2_avx_pack("qwen", "Q2_0", True))
        self.assertEqual(setup.model_row("IQ3_XXS", "orca")["arena_gb"], 49.8)
        self.assertEqual(setup.model_row("IQ3_XXS", "qwen")["arena_gb"], 42.9)
        self.assertIn("Q2_K", setup.model_choices())
        self.assertNotIn("qwen3next", setup.FAMILIES)
        cfg = root / "hypercore-flashgguf-q3_k_s.json"
        cfg.write_text('{"args": ["--max-context", "32768"]}', encoding="utf-8")
        try:
            got = setup.choices_from_config(cfg)
        finally:
            cfg.unlink()
        self.assertEqual(got["family"], "flashgguf")
        self.assertEqual(got["model"], "Q3_K_S")
    def test_shard_names_match_the_repos(self):
        orca = linux_catalog.CATALOG_FAMILIES["orca"]
        self.assertEqual(linux_catalog.shard_names(orca, "IQ3_XXS"), [
            "Qwen3.8-Flash-Next-Uncensored-IQ3_XXS-00001-of-00002.gguf",
            "Qwen3.8-Flash-Next-Uncensored-IQ3_XXS-00002-of-00002.gguf",
        ])
        flash = linux_catalog.CATALOG_FAMILIES["flashgguf"]
        self.assertEqual(linux_catalog.shard_names(flash, "Q2_K"), ["Qwen3.8-Flash-Next.Q2_K.gguf"])
        self.assertNotIn("qwen3next", linux_catalog.CATALOG_FAMILIES)

    def test_pack_argv_follows_the_probe(self):
        plain = linux_catalog.iq_pack_argv("python", "a.gguf", "out", False)
        self.assertNotIn("--compat-bf16", plain)
        converted = linux_catalog.iq_pack_argv("python", "a.gguf", "out", True, ("--experts-bin",))
        self.assertIn("--compat-bf16", converted)
        self.assertIn("--experts-bin", converted)

    def test_cli_prints_recipe_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.gguf"
            write_header(path, "qwen4exp", flash_tensors(proj="Q8_0"))
            import contextlib
            from io import StringIO
            buf = StringIO()
            with contextlib.redirect_stdout(buf):
                self.assertEqual(compat_probe.main(["--gguf", str(path)]), 0)
            self.assertTrue(json.loads(buf.getvalue())["compat_bf16"])


if __name__ == "__main__":
    unittest.main()
