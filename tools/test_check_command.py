"""Guardrail cases for check_command: quotes, loops, heredocs, redirects, builtins, absolute paths.

Run:  python3 tools/test_check_command.py
"""
import sys

sys.path.insert(0, "/home/ai-agent/HyperCore")
from serve import terminal_mcp as t

# (command, should be allowed)
CASES = [
    ("grep -nE 'A|B' file", True),
    ("printf 'a\nb\nc'", True),
    ("for n in 1 2; do lmnope; done", False),
    ("for n in 1 2; do echo $n; done", True),
    ("total=3; for n in 1 2; do total=$((total + n)); done; echo $total", True),
    ("echo one | lmnope", False),
    ("cat <<'PY'\nimport os\nprint(1)\nPY", True),
    ("echo hi 2> /etc/x", False),
    ("echo hi > kept.txt", True),
    ("python3 -c 'import os; os.system(\"lmnope\")'", True),
    ("cd /home/ai-agent/HyperCore && python3 -m unittest", True),
    ("cd /etc", False),
    ("/usr/bin/echo hi", False),
    ("/home/ai-agent/.pyenv/versions/3.12.9/bin/python3 -c pass", True),
    ("ls *.py", True),
    ("if true; then lmnope; fi", False),
    ("while read line; do echo $line; done < f", True),
    ("echo $(lmnope)", False),
    ("echo $(date)", True),
    ("lmnope", False),
    ("", False),
    ("echo 'unclosed", False),
    ("git status", True),
    ("xargs -I{} lmnope", True),          # a program inside an argument is not seen: documented limit
    # the /dev device files are exempt from the root guard
    ("seq 1 3 > /dev/null", True),
    ("echo hi 2> /dev/null", True),
    ("cat big.txt | wc -l > /dev/null", True),
    ("true < /dev/null", True),
    ("wc -l < /dev/stdin", True),
    ("echo hi > /dev/stdout", True),
    ("echo hi 2> /dev/stderr", True),
    # ... and every other path outside the root is still refused
    ("echo hi > /dev/x", False),
    ("echo hi > /dev/null/x", False),
    ("wc -l < /dev/random", False),
    ("wc -l < /etc/hosts", False),
    ("cd /dev", False),
    ("echo hi > /tmp/x", False),
]

if __name__ == "__main__":
    bad = 0
    for command, allowed in CASES:
        try:
            t.check_command(command)
            result, reason = "allowed", ""
        except ValueError as exc:
            result, reason = "refused", str(exc)
        if (result == "allowed") != allowed:
            bad += 1
            print(f"MISMATCH  {command[:52]!r} -> {result}: {reason}")
    print(f"{len(CASES) - bad}/{len(CASES)} guardrail cases behaved as expected")

    # inside() directly: the exemption is for the four device files, nothing else.
    DEVICE = ["/dev/null", "/dev/stdout", "/dev/stderr", "/dev/stdin"]
    REFUSED = ["/etc/hosts", "/usr/bin/gcc", "/tmp/x", "/dev/random", "/dev", "/dev/../etc/hosts"]
    for path in DEVICE:
        try:
            got = str(t.inside(path))
            ok = got == path
        except ValueError:
            got, ok = "refused", False
        if not ok:
            bad += 1
            print(f"INSIDE MISMATCH  {path} -> {got}")
    for path in REFUSED:
        try:
            got = str(t.inside(path))
            ok = False
        except ValueError:
            ok = True
        if not ok:
            bad += 1
            print(f"INSIDE MISMATCH  {path} -> {got} (should be refused)")
    print(f"inside(): {len(DEVICE)} device paths allowed, {len(REFUSED)} outside paths refused")

    # relative paths still resolve under the root, as before
    for path, expected in [("kept.txt", "/home/kept.txt"), ("serve/terminal_mcp.py", "/home/serve/terminal_mcp.py")]:
        try:
            got = str(t.inside(path))
        except ValueError as exc:
            got = f"refused: {exc}"
        if got != expected:
            bad += 1
            print(f"INSIDE MISMATCH  {path} -> {got} (expected {expected})")
    print("inside(): relative paths still resolve under the root")

    sys.exit(1 if bad else 0)
