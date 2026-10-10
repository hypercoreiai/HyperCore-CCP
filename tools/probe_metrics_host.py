"""One-shot probe: does /metrics survive a supervisor-backed engine, on either host?

Run with the supervisor at HEAD and again with the fix, to see whether the host
actually matters.

    python3 tools/probe_metrics_host.py 127.0.0.1 8101
"""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from serve.frame_fixture import ScriptedWorker  # noqa
from serve.frontend import ChatTemplate  # noqa
from serve.hypercore_supervisor import HyperCoreProcessSupervisor  # noqa
from serve.server import ByteTokenizer, HyperCoreRequestHandler, Service, serve  # noqa


def main() -> int:
    host = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8101

    sup = HyperCoreProcessSupervisor(transport=ScriptedWorker(max_slots=2, tokens=4).connect,
                                     max_restarts=0)
    sup.start()
    svc = Service(HyperCoreRequestHandler(sup), ByteTokenizer(),
                  ChatTemplate(ROOT / "serve/chat_template.jinja"), model_name="probe")
    httpd = serve(svc, host=host, port=port)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/metrics", timeout=10) as r:
            body = json.load(r)
        print(f"host={host} port={port}: HTTP {r.status} "
            f"slots={body['live']['slots']} outside_slots={body['live']['outside_slots']}")
        return 0
    except Exception as exc:
        print(f"host={host} port={port}: {type(exc).__name__}: {exc}")
        return 1
    finally:
        httpd.shutdown()
        sup.stop()


if __name__ == "__main__":
    raise SystemExit(main())
