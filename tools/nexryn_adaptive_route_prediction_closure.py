"""Write adaptive route prediction closure and core checkpoint artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.experiments.adaptive_route_prediction_closure import (  # noqa: E402
    run_closure_and_checkpoint,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--program-artifact-dir", default=None)
    parser.add_argument("--checkpoint-root", default=None)
    args = parser.parse_args()
    kwargs = {}
    if args.program_artifact_dir:
        kwargs["program_artifact_dir"] = args.program_artifact_dir
    if args.checkpoint_root:
        kwargs["checkpoint_root"] = args.checkpoint_root
    result = run_closure_and_checkpoint(**kwargs)
    print(result["program_artifact_dir"])
    print(result["checkpoint_dir"])
    print(json.dumps(result["next_gap_decision"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
