"""Test letting one ordinary disclosure precede the query."""
import json
from types import SimpleNamespace
from unittest.mock import patch

import query_gate as gate

frontier, transfer, selection = gate.frontier, gate.transfer, gate.selection
router, episode = gate.router, gate.episode


def played(item, terms, receipt, defer):
    views = []

    def decide(obs, default=None):
        if obs[-1] is not None and not views:
            views.append(obs[-1])
            if defer:
                return selection.reuse.ROUTER.ROUTINE
        return default

    with patch.object(selection.reuse, "singleton_enabled",
                      new=lambda: selection.enabled(True, frontier.ordinary_when_possible)):
        with transfer.canonical.enabled(terms, "public", lambda: episode.delay.enabled(
                lambda _: "immediate")):
            available, default = router.available, router.default

            def observe(item, state):
                obs, moves, regular = available(item, state)
                local = None
                if default(obs, transfer.canonical.BASE) == selection.group.OFFER_SET:
                    local = gate.local_view(item, state, moves, regular)
                return (*obs, local), moves, regular

            with patch.object(router, "available", new=observe), patch.object(
                    router, "default", new=lambda obs, mode: default(obs[:-1], mode)):
                # The deferral is a single public ordinary turn. Subsequent
                # decisions use the standard decentralized router.
                actor = SimpleNamespace(get=decide)
                result = router.play(item, transfer.canonical.BASE, actor, recorded=receipt)
    return views[0] if views else None, result


def paired(inputs):
    for item, terms, receipt in inputs:
        view, now = played(item, terms, receipt, False)
        later = now
        if view is not None:
            also, later = played(item, terms, receipt, True)
            assert view == also
        left, right = item[0][1]
        yield "agreement" if left&right else "impasse", view, now, later


def evaluate():
    with patch.object(gate, "paired", new=paired):
        result = gate.evaluate()
    result["scope"] = "Team return fit between one ordinary turn and immediate query at the first opportunity."
    for panels in (result["train"], result["development"], result["heldout"], *result["transfers"].values()):
        for report in panels.values():
            report["defer_once"] = report.pop("publish_only")
            report["defer_if_covers_all_but_one"] = report.pop("publish_if_covers_all_but_one")
    return result


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
