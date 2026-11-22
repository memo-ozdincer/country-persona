"""Build final report comparisons from every exact receipt on reserve grid 198."""
import argparse
from collections import defaultdict
from itertools import product
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ranking as ranked
import recipient as receive
import joint_opener as opener
import selective as s

BASE = HERE.parents[1] / "private-retry/scoped-review/scoped_review.py"
ARCHIVE = s.SPACE / "historical-task.json"
RELEASE = s.SPACE.parents[1] / "benchmark-v1.5"
ROLES = ("First workshop desk", "Second workshop desk")
DRAW = 198
FEES = s.base.FEE
SCOPE = "This is a fictional workshop. Its disposition establishes no official Council action or commitment."


def load_collector():
    spec = importlib.util.spec_from_file_location("memo_collector", BASE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def model():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    assert DRAW in registry["partition"]["reserved"]
    entry, = (row for row in registry["accepted"] if row["draw"] == DRAW)
    with patch.dict(s.shared.FIXTURES, {"document": s.original.fixture(entry)}):
        grid = s.shared.Grid("document")
    fixed_weights = torch.tensor(s.read(s.FIT)["weights"], dtype=torch.float64)
    open_w = np.asarray(s.read(HERE.parent / "joint-opener.json")["weights"])
    rank_w = np.asarray(s.read(HERE.parent / "ranking.json")["coef"])
    value_w = np.asarray(s.read(HERE.parent / "recipient.json")["weights"])

    def stage(label, balanced):
        data = s.shared.Experiment(grid, balanced)
        for i, role in enumerate(data.roles):
            if role == 2:
                data.mask[i, 1:] = False
        raw = data.probabilities(fixed_weights).numpy()
        first = opener.choose(data, raw, opener.basis(data, data.prior, raw), open_w, FEES, "joint-fitted")
        results = ranked.measure(data, first, receive.aggregate(data, first), rank_w, value_w)
        return label, data, {key: results[key] for key in ("fixed", "rank-fit")}

    return grid, (stage("balanced", True), stage("uniform", False))


def receipt_rows(grid, data, choices):
    paired = defaultdict(float)
    for world, prior in data.prior.items():
        state = data.states["A", world[0]]
        assert np.array_equal(choices["fixed"][0][state], choices["rank-fit"][0][state])
        for a, (column, send) in enumerate(s.base.ACTIONS):
            p = choices["fixed"][0][state, a]
            if not p:
                continue
            one = grid.claim(world, 0, column)
            for seen, delivery in s.base.observations(one, send):
                peer = data.states["B", world[1], seen]
                two = [grid.claim(world, 1, int(choices[name][0][peer, :3].argmax())) for name in choices]
                for got_first, got_second in product((True, False), repeat=2):
                    link = (s.base.DELIVER if got_first else 1-s.base.DELIVER) * (
                            s.base.DELIVER if got_second else 1-s.base.DELIVER)
                    first = one if got_first else None
                    key = tuple((first, b if got_second else None) for b in two)
                    paired[key] += prior*p*delivery*link
    assert abs(sum(paired.values())-1.) < 1e-10
    for k, row in enumerate(choices.values()):
        predicted = sum(mass*bool(grid.information(pair[k])[1]) for pair, mass in paired.items())
        assert abs(predicted-row[1]["after_followup"]) < 1e-9
    return paired


def view_spec(grid, view, historical):
    admitted, warranted = grid.information(view)
    witness = []
    for world in admitted:
        cards = tuple(grid.cards[side][ix] for side, ix in enumerate(world))
        scores = {}
        for col, package in enumerate(grid.packages):
            values = [cards[0][col], cards[1][col], grid.public[col]]
            scores[package] = dict(feasible=min(values)>0, minimum=min(values), sum=sum(values))
        witness.append(dict(winners=sorted(grid.winners(world)), comparisons=scores))
    chosen = min(warranted) if warranted else "unresolved"
    claims = {role: None if grade is None else dict(package=grid.packages[grade[0]], grade=grade[1])
              for role, grade in zip(ROLES, view, strict=True)}
    prefix = f"Workshop disposition: {chosen}\n\n" + " ".join(row["text"] for row in historical) + "\n\n" + SCOPE
    allowance = 165-len(prefix.split())
    text = []
    for role, posted in claims.items():
        text.append(f"{role}: " + (f"{posted['package']} has grade {posted['grade']}." if posted else "no grade arrived."))
    rule = "A zero excludes a package. Rank feasible packages by highest minimum grade, then highest sum."
    if chosen == "unresolved":
        winners = sorted({"/".join(v["winners"]) for v in witness})
        reason = f"Possible winners by completion include {', '.join(winners)}; no disposition is shared."
    elif chosen == "impasse":
        reason = "Every package has a zero in each possible completion."
    else:
        reason = f"Package {chosen} wins in every possible completion."
    scope = f"The {len(witness)} possible completions describe uncertainty about the actual cards."
    fixed = " ".join((*text, rule, reason, scope))
    assert len(fixed.split()) <= allowance
    package = dict(checked_disposition=chosen, compatible_completions=witness, authenticated_reports=claims,
                   third_seat=dict(zip(grid.packages, grid.public, strict=True)), decision_rule=rule, max_words=allowance)
    system = (
        "Write only the fictional workshop rationale. The disposition and history are supplied separately. "
        "Name each desk's exact received package and grade, or explicitly say its report is missing. "
        "Use the stated zero rule, lowest grade and sum tie break to explain what all possible completions establish. "
        "Give the count of compatible completions and explain why they support or prevent a common disposition. "
        "Where results differ, name concrete competing results. Completions are possibilities rather than actual private cards. "
        "Use no other evidence. Do not make a decision heading, add history, or claim official action."
    )
    return dict(prefix=prefix, fixed=fixed, allowance=allowance, view=view, facts=package, history=historical,
                messages=[dict(role="system", content=system),
                          dict(role="user", content=json.dumps(package, ensure_ascii=False))])


def plan():
    grid, regimes = model()
    historical = [row for row in s.read(ARCHIVE)["evidence"] if row["id"] in ("apr-amendment", "apr-final")]
    assert len(historical) == 2
    tables = {label: receipt_rows(grid, data, choices) for label, data, choices in regimes}
    views = sorted({view for table in tables.values() for pair in table for view in pair}, key=str)
    indices = {view: f"v{i+1:02d}" for i, view in enumerate(views)}
    info = {indices[v]: view_spec(grid, v, historical) for v in views}
    requests = [dict(id=k, max_output_tokens=115, messages=r.pop("messages")) for k, r in info.items()]
    pairs = {label: [dict(fixed=indices[a], fitted=indices[b], mass=float(p)) for (a, b), p in table.items()]
             for label, table in tables.items()}
    from hashlib import sha256
    files = (Path(__file__), HERE/"protocol.md", HERE.parent/"ranking.json", HERE.parent/"joint-opener.json",
             BASE, RELEASE/"release.json", ARCHIVE, s.original.REGISTRY)
    payload = dict(requests=requests, views=info, pairs=pairs,
                   hashes={str(p.relative_to(RELEASE.parent)): sha256(p.read_bytes()).hexdigest() for p in files})
    return json.loads(json.dumps(payload, ensure_ascii=False))


def execute(mode):
    c = load_collector()
    directory = HERE / "evidence"
    with patch.multiple(c, HERE=HERE, EVIDENCE=directory, plan=plan):
        if mode == "run":
            b = c.base()
            prepared = plan()
            assert s.read(HERE/"plan.json") == prepared
            keys = {row["id"]: True for row in prepared["requests"]}
            with patch.object(b.suite, "collect", c.collect), patch.object(b, "roster", return_value=keys), patch.object(
                b, "HERE", HERE
            ), patch.object(b.suite.e, "HERE", RELEASE):
                b.run(directory)
        else:
            raw = {req["id"]: reply for req, reply in c.rows()}
            reference = plan()
            assert s.read(directory/"launch.json")["cases"] == list(reference["views"])
            packet = {}
            for key, row in reference["views"].items():
                generated = raw[key]
                for arm in ("literal", "scoped"):
                    paragraph = row["fixed"] if arm == "literal" else generated["text"]
                    packet[f"{key}/{arm}"] = dict(
                        answer=row["prefix"]+"\n\n"+paragraph, paragraph=paragraph, facts=row["facts"], history=row["history"],
                        complete=arm == "literal" or generated["termination"] == "complete",
                        input_tokens=generated["input_tokens"] if arm == "scoped" else 0,
                        output_tokens=generated["output_tokens"] if arm == "scoped" else 0)
            return packet


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "deck"))
    arg = parser.parse_args().mode
    if arg == "run":
        execute(arg)
    else:
        print(json.dumps(plan() if arg == "plan" else execute(arg), ensure_ascii=False, indent=2))
