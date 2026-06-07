#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: ~/run_raceloom_progress.sh MODEL PROPERTIES [args...]"
  exit 2
fi

MODEL="$1"
PROPS="$2"
shift 2

ROOT="$HOME/raceloom_image_rootfs"
RACELOOM="$ROOT/raceloom"
LOG_DIR="$RACELOOM/progress_logs"
mkdir -p "$LOG_DIR"

STAMP="$(date +%Y_%m_%dT%H_%M_%S)"
LOG="$LOG_DIR/run_${STAMP}.log"

echo "Logging to: $LOG"
echo "Model: $MODEL"
echo "Properties: $PROPS"
echo "Args: $*"
echo

cd "$RACELOOM"

(
  PYTHONHOME="$ROOT/usr/local" \
  PYTHONPATH="$ROOT/usr/local/lib/python3.12/site-packages:$RACELOOM" \
  "$ROOT/usr/local/bin/python" main.py "$MODEL" "$PROPS" "$@"
) >"$LOG" 2>&1 &

PID="$!"
START="$(date +%s)"
LAST_N=0

fmt_kb() {
  local kb="${1:-0}"
  if [ "$kb" -ge 1048576 ]; then
    awk -v k="$kb" 'BEGIN { printf "%.2fG", k/1048576 }'
  elif [ "$kb" -ge 1024 ]; then
    awk -v k="$kb" 'BEGIN { printf "%.1fM", k/1024 }'
  else
    printf "%sK" "$kb"
  fi
}

tree_pids() {
  local root="$1"
  local all="$root"
  local changed=1
  while [ "$changed" = 1 ]; do
    changed=0
    for p in $all; do
      for c in $(pgrep -P "$p" 2>/dev/null || true); do
        case " $all " in
          *" $c "*) ;;
          *) all="$all $c"; changed=1 ;;
        esac
      done
    done
  done
  echo "$all"
}

echo "RaceLoom PID: $PID"
echo "Progress monitor started."
echo

while kill -0 "$PID" 2>/dev/null; do
  NOW="$(date +%s)"
  ELAPSED=$((NOW - START))
  M=$((ELAPSED / 60))
  S=$((ELAPSED % 60))

  # Print new RaceLoom output lines as they appear.
  N="$(wc -l < "$LOG" 2>/dev/null || echo 0)"
  if [ "$N" -gt "$LAST_N" ]; then
    sed -n "$((LAST_N + 1)),${N}p" "$LOG"
    LAST_N="$N"
  fi

  GENERATED="$(grep -E 'Generated traces:' "$LOG" | tail -1 | sed 's/^/ /' || true)"

  STAGE="running"
  if grep -q "Generating traces" "$LOG"; then STAGE="generating"; fi
  if grep -q "Analyzing traces" "$LOG"; then STAGE="analyzing"; fi
  if grep -q "Final Stats" "$LOG"; then STAGE="finalizing"; fi

  PIDS="$(tree_pids "$PID")"
  PID_CSV="$(echo "$PIDS" | tr ' ' ',')"

  CPU_SUM="$(ps -o %cpu= -p "$PID_CSV" 2>/dev/null | awk '{s+=$1} END{printf "%.1f", s+0}')"
  RSS_SUM_KB="$(ps -o rss= -p "$PID_CSV" 2>/dev/null | awk '{s+=$1} END{printf "%d", s+0}')"
  RSS_SUM="$(fmt_kb "$RSS_SUM_KB")"

  TOP_PROC="$(ps -o pid=,%cpu=,rss=,comm= -p "$PID_CSV" 2>/dev/null | sort -k2 -nr | head -1 | awk '{printf "top=%s cpu=%s%% rss=%.1fM cmd=%s", $1,$2,$3/1024,$4}')"
  MEM_LINE="$(free -m | awk '/^Mem:/ {printf "sysmem=%sM used/%sM avail", $3, $7}')"
  LOAD_LINE="$(awk '{printf "load=%s,%s,%s", $1, $2, $3}' /proc/loadavg 2>/dev/null || true)"

  echo "[${M}m${S}s] stage=${STAGE}${GENERATED} | tree_cpu=${CPU_SUM}% tree_rss=${RSS_SUM} | ${MEM_LINE} | ${LOAD_LINE} | ${TOP_PROC}"

  sleep 10
done

# Flush remaining log lines.
N="$(wc -l < "$LOG" 2>/dev/null || echo 0)"
if [ "$N" -gt "$LAST_N" ]; then
  sed -n "$((LAST_N + 1)),${N}p" "$LOG"
fi

wait "$PID"
STATUS="$?"

echo
echo "RaceLoom finished with exit code: $STATUS"
echo "Full log: $LOG"
exit "$STATUS"
