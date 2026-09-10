"""Run integrated capability qualification closure verification."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.experiments.integrated_capability_qualification_verification import (
    run_integrated_capability_qualification_verification,
)


def main() -> int:
    result = run_integrated_capability_qualification_verification()
    print(
        json.dumps(
            {
                "artifact_dir": result["artifact_dir"],
                "system_fingerprint": result["system_fingerprint"],
                "closure_decision": result["closure_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
