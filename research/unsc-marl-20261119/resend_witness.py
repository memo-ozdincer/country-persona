"""Retain the deciding transcript for a recovered agreement and lost impasse."""
import json
from pathlib import Path
import sys

import ordinary_resend as simulation


def examples(rules):
    wanted = {"myanmar": ("agreement", False, True), "mali": ("impasse", True, False)}
    result = {}
    for family, panels in simulation.audit.samples():
        if family not in wanted:
            continue
        find = wanted[family]
        for index, (item, terms, receipt) in enumerate(panels["independent"]):
            if simulation.fit.world_label(item) != find[0]:
                continue
            ordinary, replay = [], []
            view, before, _ = simulation.run_episode(item, terms, receipt, lambda _:False, ordinary)
            if view is None or before[0]!=find[1] or simulation.gate.choose(view,rules):
                continue
            _, after, exposure = simulation.run_episode(item,terms,receipt,
                lambda view:not simulation.gate.choose(view,rules), replay)
            if after[0]!=find[2]:
                continue
            result[family] = {"source_row":index,"outcome":find[0],"local_view":
                              dict(zip(simulation.FEATURES,view,strict=True)),
                              "terms":terms,"opening":simulation.router.sp.opened(item[0][3],item[0][2]),
                              "fixed":{"counts":before,"events":ordinary},
                              "learned":{"counts":after,"events":replay,"resend_exposure":exposure}}
            break
    assert result.keys()==wanted.keys()
    return result


if __name__ == "__main__":
    rules = json.loads(Path(sys.argv[1]).read_text())["rules"]
    print(json.dumps(examples(rules),indent=2))
