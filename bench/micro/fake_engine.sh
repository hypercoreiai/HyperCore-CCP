#!/bin/bash
# Stand-in for engine/hypercore: prints the same boot line, reads GEN lines on stdin,
# answers with a DONE line, and exits on QUIT. Used to test tune_hypercore5.sh's plumbing.
echo "hypercore generate: session is up (engine fake)" >&2
while IFS= read -r line; do
    case "${line%% *}" in
        GEN)
            n=$(printf '%s' "$line" | awk '{print $2}')
            sleep 1
            echo "DONE ${n:-0} 1024 120.0 800.0 length 3 5 0 0 0 0 0 0.0 1024 0"
            ;;
        QUIT) break ;;
        *) echo "ERR unknown line: $line" ;;
    esac
done
