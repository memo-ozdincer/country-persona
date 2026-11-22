"""Compare the fitted scope selector with a fixed compound-reply preference."""
import json
from pathlib import Path
import sys

import learn_scope as fit


def compare(results):
    ordinary_available = fit.FEATURES.index("ordinary_target_available")
    panels = fit.synthetic("holdout", (7, 8), 500, 3)
    panels.update({f"venezuela/{name}": rows
                   for name, rows in fit.archive(list(fit.transfer.cases())).items()})
    output = {}
    for label, rows in panels.items():
        control = fit.score(rows, lambda obs: not obs[ordinary_available])
        fitted = fit.score(rows, lambda obs: fit.disclose(obs, results["policy"]))
        if label.startswith("venezuela/"):
            expected = results["un_fit_families"]["venezuela"][label.split("/")[1]]["fit"]
        else:
            expected = results["heldout"][label]["fit"]
        assert fitted == expected
        output[label] = {"prefer_ordinary_when_available": control, "fit": fitted}
    return {"scope": "Fixed comparator devised after inspecting the independent holdout trace.",
            "comparison": output}


if __name__ == "__main__":
    results = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(compare(results), indent=2))
