"""Replay the prompt transfer on the Gulf of Guinea workshop."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "council-workshop-exclusion-policy-20261123"))

from readout import compare, pretty


if __name__ == "__main__":
    reference = HERE.parent / "council-workshop-held-pilot-20261123"
    print(pretty({"impasse": compare("guinea", "impasse", reference / "all-sol", HERE / "guinea-impasse-priority"),
                  "feasible": compare("guinea", "feasible", reference / "feasible-all-sol",
                                      HERE / "guinea-feasible-priority")}))
