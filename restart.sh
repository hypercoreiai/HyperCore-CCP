#!/bin/sh
# restart.sh - stop the running HyperCore server, then start the run script setup.sh wrote.
#
#   ./restart.sh status                 what is running, on which port, with which config
#   ./restart.sh stop                   stop it
#   ./restart.sh start q2_0           start run-q2_0.sh, the script setup.sh wrote
#   ./restart.sh start q2_0 --dry-run  show what would happen, touch nothing
#
# Stopping is graceful: SIGTERM first; serve/server.py maps SIGTERM to the Ctrl+C path, which
# closes the MCP hub, the HTTP server, the engine and the vision encoder. SIGKILL follows after
# GRACE_S seconds if the process is still there.
set -eu

ROOT="${HYPERCORE_ROOT:-$(dirname "$0")}"
GRACE_S="${GRACE_S:-20}"
READY_S="${READY_S:-240}"
PID_FILE="${HOME}/.cache/hypercore/server.pid"
PORT_FILTER=""

usage() {
    cat <<'USAGE'
usage: restart.sh {status|stop|start <model>} [--port N] [--dry-run]
  status        show the running HyperCore server, its port and config
  stop          stop it
  start <model> run run-<model>.sh, the script setup.sh wrote
  --port N      restrict the action to the server on that port
  --dry-run     print what would happen, change nothing
USAGE
    exit 2
}

server_pids() {
    for proc in /proc/[0-9]*; do
        pid="${proc#/proc/}"
        [ "$pid" = "$$" ] && continue
        [ -r "$proc/cmdline" ] || continue
        cmdline="$(tr '\0' ' ' < "$proc/cmdline" 2>/dev/null || true)"
        case "$cmdline" in
            *serve/server.py*) ;;
            *) continue ;;
        esac
        if [ -n "$PORT_FILTER" ]; then
            case "$cmdline" in
                *"--port $PORT_FILTER"*|*"--port \"$PORT_FILTER\""*) ;;
                *) continue ;;
            esac
        fi
        echo "$pid"
    done
}

describe() {
    pid="$1"
    cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
    port="$(printf '%s' "$cmdline" | sed -n 's/.*--port[ "]*\([0-9]\{1,5\}\).*/\1/p' | head -1)"
    config="$(printf '%s' "$cmdline" | sed -n 's/.*--config[ "]*\([^ "]*\).*/\1/p' | head -1)"
    printf '  pid %s  port %s  config %s\n' "$pid" "${port:-?}" "${config:-none}"
}

stop_server() {
    pids="$(server_pids)"
    if [ -z "$pids" ]; then
        echo "no HyperCore server running"
        return 0
    fi
    for pid in $pids; do
        echo "stopping pid $pid"
        kill -TERM "$pid" 2>/dev/null || true
    done
    waited=0
    while [ "$waited" -lt "$GRACE_S" ]; do
        pids="$(server_pids)"
        [ -z "$pids" ] && { echo "stopped in ${waited}s"; return 0; }
        sleep 1
        waited=$((waited + 1))
    done
    for pid in $(server_pids); do kill -KILL "$pid" 2>/dev/null || true; done
    echo "forced after ${GRACE_S}s"
    return 0
}

run_script_for() { printf '%s/run-%s.sh\n' "$ROOT" "$1"; }

port_of() {
    [ -f "$1" ] || return 0
    sed -n 's/.*--port[ "]*\([0-9]\{1,5\}\).*/\1/p' "$1" | head -1
}

start_server() {
    script="$(run_script_for "$1")"
    if [ ! -f "$script" ]; then
        echo "no run script: run-$1.sh does not exist yet"
        echo "present: $(ls "$ROOT"/run-*.sh 2>/dev/null | sed 's#.*/##' | tr '\n' ' ')"
        return 1
    fi
    port="$(port_of "$script")"
    echo "starting $1 on port ${port:-?}"
    setsid nohup sh "$script" >/dev/null 2>&1 &
    pid=$!
    mkdir -p "$(dirname "$PID_FILE")"
    echo "$pid" > "$PID_FILE"
    waited=0
    while [ "$waited" -lt "$READY_S" ]; do
        code="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${port}/" 2>/dev/null || true)"
        [ -n "$code" ] || code=000
        if [ "$code" != "000" ]; then
            echo "listening after ${waited}s (HTTP $code), pid $pid"
            return 0
        fi
        if [ $((waited % 10)) = 0 ] && [ "$waited" != 0 ]; then
            echo "  still loading (${waited}s)"
        fi
        sleep 2
        waited=$((waited + 2))
    done
    echo "the server did not answer within ${READY_S}s; it is still starting, pid $pid"
    return 1
}

action="${1:-}"
shift || true
dry=""
model=""
while [ $# -gt 0 ]; do
    arg="$1"
    shift
    case "$arg" in
        --dry-run) dry=1 ;;
        --port) PORT_FILTER="${1:-}"; shift ;;
        *) if [ -z "$model" ]; then model="$arg"; else echo "unknown argument: $arg"; usage; fi ;;
    esac
done

case "$action" in
    status)
        pids="$(server_pids)"
        if [ -z "$pids" ]; then echo "no HyperCore server running"
        else for pid in $pids; do describe "$pid"; done; fi
        ;;
    stop)
        if [ -n "$dry" ]; then echo "dry run: would stop $(server_pids | tr '\n' ' ')"
        else stop_server; fi
        ;;
    start)
        if [ -z "$model" ]; then usage; fi
        if [ -n "$dry" ]; then
            echo "dry run: would stop $(server_pids | tr '\n' ' ')"
            script="$(run_script_for "$model")"
            if [ -f "$script" ]; then
                echo "dry run: would start $script on port $(port_of "$script")"
            else
                echo "dry run: $script does not exist yet, so nothing would start"
            fi
        else
            stop_server
            start_server "$model"
        fi
        ;;
    *) usage ;;
esac
