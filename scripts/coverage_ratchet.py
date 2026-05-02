"""Coverage ratchet - prevents coverage from decreasing between PRs."""

import json
import subprocess
import sys
from pathlib import Path

BASELINE = Path(".coverage-baseline.json")
TOLERANCE = 0.5


def parse_coverage() -> dict[str, float]:
    """Run pytest and extract per-metric coverage percentages."""
    result = subprocess.run(
        [sys.executable, "-m", "coverage", "json", "-o", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    totals = data["totals"]
    return {
        "statements": totals["percent_covered"],
        "branches": totals.get("percent_covered_branches", totals["percent_covered"]),
    }


def main() -> int:
    """Compare current coverage against baseline; fail if regressed."""
    current = parse_coverage()

    if "--update" in sys.argv or not BASELINE.exists():
        BASELINE.write_text(json.dumps(current, indent=2) + "\n")
        print(f"Baseline updated: {current}")
        return 0

    baseline = json.loads(BASELINE.read_text())
    failed = False
    for metric, value in current.items():
        prev = baseline.get(metric, value)
        diff = value - prev
        ok = diff >= -TOLERANCE
        status = "PASS" if ok else "FAIL"
        sign = "+" if diff >= 0 else ""
        print(f"{metric}: {prev}% -> {value}% ({sign}{diff:.1f}%) {status}")
        if not ok:
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
