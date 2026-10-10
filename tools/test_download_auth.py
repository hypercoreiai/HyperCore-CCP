"""Hugging Face gated downloads: send a token, and do not call a 401 a network outage."""
import os
import unittest
from pathlib import Path
from unittest import mock

import setup


class DownloadAuthTest(unittest.TestCase):
    def test_headers_send_the_env_token_only_to_huggingface(self):
        with mock.patch.dict(os.environ, {"HF_TOKEN": "hf_test", "HUGGING_FACE_HUB_TOKEN": ""}):
            hf = setup.download_headers(
                "https://huggingface.co/orcarouter/Qwen3.8-Flash-Next-Uncensored-GGUF/resolve/main/x.gguf")
            other = setup.download_headers("https://example.com/x.gguf")
        self.assertEqual(hf["Authorization"], "Bearer hf_test")
        self.assertNotIn("Authorization", other)

    def test_a_saved_login_token_is_used_when_the_env_is_empty(self):
        with mock.patch.dict(os.environ, {"HF_TOKEN": "", "HUGGING_FACE_HUB_TOKEN": ""}, clear=False):
            with mock.patch.object(Path, "read_text", return_value="hf_saved\n"):
                self.assertEqual(setup.hf_access_token(), "hf_saved")

    def test_401_without_a_token_is_a_gate_not_a_disconnect(self):
        err = mock.Mock(code=401)
        msg, hint = setup.download_refusal("https://huggingface.co/x/resolve/main/a.gguf", err)
        self.assertIn("refused", msg)
        self.assertIn("HF_TOKEN", hint)
        self.assertNotIn("internet", hint)

    def test_404_does_not_retry_as_a_network_error(self):
        msg, hint = setup.download_refusal("https://huggingface.co/x/resolve/main/a.gguf", mock.Mock(code=404))
        self.assertIn("404", msg)
        self.assertIn("model name", hint)

    def test_a_dropped_connection_is_still_retried(self):
        self.assertIsNone(setup.download_refusal("https://huggingface.co/x", OSError("timed out")))


if __name__ == "__main__":
    unittest.main()
