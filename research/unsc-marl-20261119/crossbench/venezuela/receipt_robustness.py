"""Compare receipt selection and frozen retry policy on the same wider panels."""
from contextlib import nullcontext
import json
from pathlib import Path
from unittest.mock import patch

import receipt_selection as selection
import workshop_transfer as transfer

episode=transfer.episode
SEED=125407
WIDTHS=(7,8)


def comparison():
    rules=transfer.load(transfer.RETRIES)["rules"]
    output={}
    for mode in ("before_receipt","after_receipt_positive","after_receipt_or_scope"):
        context=nullcontext()
        if mode!="before_receipt":
            context=patch.object(selection.reuse,"singleton_enabled",
                                 new=lambda:selection.enabled(mode=="after_receipt_or_scope"))
        with context:
            tests=episode.panels(WIDTHS,425,3,SEED)
            output[mode]={condition:episode.measure(rows,rules) for condition,rows in tests.items()}
    result={"scope":"Synthetic held-out menus, unchanged fault tapes, same legal retry budget. All continuation and retry rules are fixed or replayed from the prior fit.",
            "seed":SEED,"widths":WIDTHS,"results":output}
    return result


if __name__=="__main__":
    print(json.dumps(comparison(),indent=2))
