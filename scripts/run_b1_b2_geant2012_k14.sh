#!/usr/bin/env bash
set -u

cd ~/raceloom_image_rootfs/raceloom

run_one () {
  LABEL="$1"
  BENCH="$2"
  DEPTH="$3"

  echo
  echo "################################################################################"
  echo "$LABEL BAD"
  echo "################################################################################"

  ~/run_raceloom_progress.sh \
    "$BENCH/bad/model.json" \
    "$BENCH/bad/properties.json" \
    --depth "$DEPTH" \
    --strategy bfs \
    2>&1 | tee "$BENCH/bad_depth${DEPTH}_bfs.log"

  echo
  echo "################################################################################"
  echo "$LABEL GOOD/CONTROL"
  echo "################################################################################"

  ~/run_raceloom_progress.sh \
    "$BENCH/control/model.json" \
    "$BENCH/control/properties.json" \
    --depth "$DEPTH" \
    --strategy bfs \
    2>&1 | tee "$BENCH/control_depth${DEPTH}_bfs.log"

  echo
  echo "################################################################################"
  echo "SUMMARY $LABEL"
  echo "################################################################################"

  python3 - <<PY
from pathlib import Path
import re

bench = Path("$BENCH")
depth = "$DEPTH"

for side in ["bad", "control"]:
    log = bench / f"{side}_depth{depth}_bfs.log"
    print()
    print("==", side, "==")

    txt = log.read_text(errors="ignore")
    blocks = txt.split("========== Final Stats ==========")

    if len(blocks) < 2:
        print("NO FINAL STATS")
        continue

    block = blocks[-1]

    def get(label):
        m = re.search(rf"{re.escape(label)}:\\s*([^\\n]+)", block)
        return m.group(1).strip() if m else "?"

    print("branches:", get("Network model branches"))
    print("traces:", get("Generated traces"))
    print("harmful:", get("Harmful races found"))
    print("total:", get("Total execution time"))
PY
}

run_one \
  "B1 WAYPOINT-ORDER K14 T3_geant2012" \
  "benchmarks_comprehensive_topologies/b1_waypoint_order_churn/K14/T3_geant2012" \
  4

run_one \
  "B2 FORCED-DISTINCT K14 T3_geant2012" \
  "benchmarks_comprehensive_topologies/b2_route_mapping_forced_distinct/K14/T3_geant2012" \
  4
