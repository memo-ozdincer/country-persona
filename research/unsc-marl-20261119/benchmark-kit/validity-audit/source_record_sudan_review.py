"""Evaluate the Sudan reserve using the same five-component record rubric."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_review as review
from source_record_sudan import pack


def read(directory, annotation_path):
    frozen = json.dumps(pack())
    class Packet:
        def read_text(self):
            return frozen
    with patch.object(review, "PACK", new=Packet()):
        if annotation_path is None:
            return review.bundle(directory)[0]
        marks = json.loads(annotation_path.read_text())
        return {"scope": marks["scope"], "final": review.score(directory, marks), "budgets": review.budgets(directory)}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory",type=Path)
    cli.add_argument("--annotations",type=Path)
    args=cli.parse_args()
    print(json.dumps(read(args.directory,args.annotations),indent=2,ensure_ascii=False))
