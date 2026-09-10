"""Generate P3 signal-failure forensic artifacts from a completed P3 run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.experiments.p3_signal_failure_forensic import (  # noqa: E402
    DEFAULT_DEVELOPMENT_DATASET,
    DEFAULT_P3_DIR,
    run_failure_forensic,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p3-dir", default=str(DEFAULT_P3_DIR))
    parser.add_argument("--development-dataset", default=str(DEFAULT_DEVELOPMENT_DATASET))
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    report = run_failure_forensic(
        p3_dir=args.p3_dir,
        development_dataset_path=args.development_dataset,
        output_dir=args.output_dir,
    )
    print(report["artifact_dir"])
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
