"""Call the terminal MCP server over stdio and print the answer for one tool.

The stdin pipe is kept open until the reply arrives: the server answers a tools/call on a
daemon thread, so closing stdin first would end the process before the answer is written.

    python tools/mcp_probe.py '{"name":"status","arguments":{}}'
    python tools/mcp_probe.py '{"name":"query","arguments":{"path":"/home/ai-agent/HyperCore/mcp.yaml"}}'
"""
import json
import subprocess
import sys

SERVER = "/home/ai-agent/HyperCore/serve/mcp/terminal_mcp.py"
LINE = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "1"}}}


def call(name: str, arguments: dict) -> dict:
    proc = subprocess.Popen(["python3", SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, text=True)
    proc.stdin.write(json.dumps(LINE) + "\n")
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
    proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                "params": {"name": name, "arguments": arguments}}) + "\n")
    proc.stdin.flush()
    for line in proc.stdin and []:
        pass
    answer = None
    for line in proc.stdout:
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        if msg.get("id") == 2:
            result = msg.get("result") or {}
            text = "".join(c.get("text", "") for c in result.get("content", []))
            try:
                answer = json.loads(text)
            except ValueError:
                answer = {"text": text}
            break
    proc.stdin.close()
    proc.wait(timeout=10)
    if answer is None:
        return {"error": "no answer", "stderr": proc.stderr.read()[:1500]}
    return answer


if __name__ == "__main__":
    payload = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {"name": "status", "arguments": {}}
    print(json.dumps(call(payload["name"], payload.get("arguments") or {}), indent=1)[:4000])
