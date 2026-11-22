"""Reuse the previous docket's frozen evaluation and quote check."""
import importlib.util
import json
from unittest.mock import patch

from writer_revision import HERE, PARENT

spec = importlib.util.spec_from_file_location("tolerance_quote_score_before_revision", PARENT / "score_tolerance.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)

if __name__ == "__main__":
    with patch.object(scorer, "HERE", HERE):
        print(json.dumps(scorer.score(), ensure_ascii=False, indent=2))
