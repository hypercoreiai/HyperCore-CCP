#!/usr/bin/env python3
"""Run the proposed serve/server.py patch verbatim against a real worker.

The two functions are copied from the proposal without change, so any failure here is
the patch failing, not a paraphrase of it.
"""
import sys

sys.path.insert(0, "/home/ai-user0/HyperCore")
import json
import queue
import struct
import sys

from serve.hypercore_supervisor import HyperCoreProcessSupervisor


def build_submit_payload(temperature, top_p, top_k, max_tokens, pcie_frac, spec_min_p, prompt_tokens):
    config_format = "<IffIIff"
    config_payload = struct.pack(config_format, 28, temperature, top_p, top_k, max_tokens, pcie_frac, spec_min_p)
    pad_block = struct.pack("<I", 0)
    prompt_len_payload = struct.pack("<Q", len(prompt_tokens))
    tokens_payload = struct.pack(f"<{len(prompt_tokens)}i", *prompt_tokens)
    return config_payload + pad_block + prompt_len_payload + tokens_payload


class FakeHandler:
    def __init__(self):
        self.out = []
    @property
    def wfile(self):
        return self
    def write(self, b):
        self.out.append(b.decode("utf-8"))
    def flush(self):
        pass


def process_active_stream_loop(sync_queue, handler_instance, request_uid):
    while True:
        try:
            msg_type, data_block, metrics = sync_queue.get(timeout=30.0)
            if msg_type == 3:
                # data_block is the int the listener put in slot 1; the real status is in
                # the payload bytes. Reading slot 1 means a rejected request looks accepted.
                status_code = int.from_bytes(metrics, "little") if metrics else data_block
                if status_code != 0:
                    handler_instance.wfile.write(
                        f"data: {json.dumps({'error': f'Submission rejected with status code: {status_code}'})}\n\n".encode())
                    break
                continue
            if msg_type == 4:
                # The listener routes (STREAM_TOKEN, token_id, prompt_reused): slot 1 is
                # the token id, slot 2 is the reuse count. Unpacking slot 1 as a pair
                # raises TypeError on the first token of every request.
                token_id, prompt_reused = data_block, metrics
                out = {"token_id": token_id, "prompt_reused": prompt_reused}
                handler_instance.wfile.write(f"data: {json.dumps(out)}\n\n".encode())
                handler_instance.wfile.flush()
            elif msg_type == 5:
                # The terminal frame carries the decoded summary in slot 2; slot 1 is the
                # -1 sentinel. prompt_reused has to come out of the summary.
                prompt_reused = metrics.get("prompt_reused", 0)
                out = {"done": True, "prompt_reused": prompt_reused, "metrics": metrics}
                handler_instance.wfile.write(f"data: {json.dumps(out)}\n\n".encode())
                handler_instance.wfile.flush()
                break
        except queue.Empty:
            print("FAIL: the loop timed out; the terminal frame never matched msg_type 5")
            break


def main() -> int:
    worker = "/home/ai-user0/HyperCore/build-shared/hypercore-worker"
    sock = "/tmp/patch_lab.sock"
    s = HyperCoreProcessSupervisor(worker_binary=worker, socket_path=sock, config='{"batch": 1}')
    s.start_worker()
    rid = s.next_request_id()
    q = s.open_stream(rid)
    payload = build_submit_payload(0.0, 1.0, 4, 8, -1.0, -1.0, [1, 2, 3, 4])
    print(f"payload length: {len(payload)} (SUBMIT_HEAD is 40 + 4 tokens = 56)")
    s.send_ipc_message(1, rid, payload)
    h = FakeHandler()
    process_active_stream_loop(q, h, rid)
    print("--- frames the handler emitted ---")
    for line in h.out[:4]:
        print(line.strip())
    if not h.out:
        print("(nothing: the loop never saw a token or a terminal frame)")
    s.shutdown()
    return 0 if h.out else 1


if __name__ == "__main__":
    sys.exit(main())
