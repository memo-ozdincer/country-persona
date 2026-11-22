"""Replay the fitted grade selector through the recorded prose channel."""
from collections import defaultdict
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json
import re

import torch

import three_seat_language as channel
import three_seat_positive_fit as trained

HERE = Path(__file__).resolve().parent
FIT = HERE / "evidence/three-seat-positive-fit.json"
shared = trained.shared
base = trained.base


def parsed(row):
    if row["output"] == "NONE" and row["ended"]:
        return None, True
    match = re.fullmatch(r"([ABC]) ([0-3])", row["output"]) if row["ended"] else None
    if match is None:
        return None, False
    return ("ABC".index(match[1]), int(match[2])), True


def exact_declaration(package, grade):
    return f"My delegation gives package {package} a confirmed grade of {grade}."


def read_declaration(sentence):
    match = re.fullmatch(r"My delegation gives package ([ABC]) a confirmed grade of ([0-3]).", sentence)
    if match is None:
        return None
    return "ABC".index(match[1]), int(match[2])


def readback(raw):
    grades = {}
    messages = []
    controls = []
    for p, grade in channel.VOCABULARY:
        key = f"{p}{grade}"
        intended = ("ABC".index(p), grade)
        value, valid = parsed(raw[f"read/{key}"])
        written = raw[f"write/{key}"]["output"]
        witness, force = {
            "C0": ("request a review", "requests_review"),
            "C1": ("request a review", "requests_review"),
            "C2": ("my grade of 2 be recorded", "reports_current_grade"),
            "C3": ("request a grade of 3", "requests_new_grade"),
        }.get(key, ("be adjusted", "requests_adjustment"))
        assert witness in written
        grades[intended] = value
        messages.append({"intended": intended, "written": written, "force_review": force, "force_witness": witness,
                         "parsed": value, "valid_format": valid, "exact": valid and value == intended,
                         "writer_finished": raw[f"write/{key}"]["ended"],
                         "writer_output_tokens": len(raw[f"write/{key}"]["output_ids"]),
                         "reader_output_tokens": len(raw[f"read/{key}"]["output_ids"])})
    for name, (text, wanted) in channel.CONTROLS.items():
        value, valid = parsed(raw[f"read/{name}"])
        expected = None if wanted is None else ("ABC".index(wanted[0]), wanted[1])
        controls.append({"id": name, "message": text, "expected": expected, "parsed": value,
                         "valid_format": valid, "correct": valid and value == expected})
    return grades, messages, controls


def compatible(grid, shown):
    return tuple(w for w in grid.worlds
                 if all(s is None or grid.claim(w, seat, s[0]) == s for seat, s in enumerate(shown)))


def projection(data, weights, mapping, mode, cost=None):
    grid = data.grid
    out = defaultdict(float)
    for world, p in data.prior.items():
        a_state = data.states["A", world[0]]
        deadlock = "impasse" in grid.winners(world)
        out["impasse_mass"] += p * deadlock
        out["agree_mass"] += p * (not deadlock)
        for (i, pay), a in zip(base.ACTIONS, weights[a_state, :len(base.ACTIONS)], strict=True):
            first = grid.claim(world, 0, i)
            first_prose = mapping[first]
            if mode == "bound" and first_prose != first:
                first_prose = None
            for peer_arrived, side_p in base.observations(True, pay):
                receipt = first_prose if peer_arrived else None
                b_state = data.states.get(("B", world[1], receipt), data.states["B", world[1], None])
                for j, b in enumerate(weights[b_state, :3]):
                    second = grid.claim(world, 1, j)
                    second_prose = mapping[second]
                    if mode == "bound" and second_prose != second:
                        second_prose = None
                    for got_a, got_b in product((False, True), repeat=2):
                        shown = (first_prose if got_a else None, second_prose if got_b else None)
                        delivery = (base.DELIVER if got_a else 1 - base.DELIVER) * (
                            base.DELIVER if got_b else 1 - base.DELIVER)
                        mass = p * a * side_p * b * delivery
                        worlds = compatible(grid, shown)
                        certified = frozenset.intersection(*(grid.winners(w) for w in worlds)) if worlds else frozenset()
                        out["mass"] += mass
                        out["peer_send"] += mass * pay
                        if cost is not None:
                            out["uncached_model_calls"] += mass * (2 + int(got_a) + int(got_b) + int(bool(peer_arrived)))
                            out["uncached_generated_tokens"] += mass * (
                                cost[first][0] + cost[second][0]
                                + cost[first][1] * (int(got_a) + int(bool(peer_arrived)))
                                + cost[second][1] * int(got_b))
                        out["unsupported_certificate"] += mass * bool(certified) * (world not in worlds)
                        out["false_certificate"] += mass * bool(certified - grid.winners(world))
                        warranted = bool(certified) and world in worlds
                        out["certified_agreement"] += mass * warranted * (not deadlock)
                        out["certified_impasse"] += mass * warranted * deadlock
    assert abs(out.pop("mass") - 1.) < 1e-9
    result = {key: float(value) for key, value in out.items()}
    result["net"] = result["certified_agreement"] + result["certified_impasse"] - base.FEE * result["peer_send"]
    result["agreement_recall"] = result["certified_agreement"] / result["agree_mass"]
    result["impasse_recall"] = result["certified_impasse"] / result["impasse_mass"]
    return result


def run():
    torch.set_num_threads(1)
    raw = channel.replay(channel.ROOT)
    soft, notes, controls = readback(raw)
    original = json.loads(FIT.read_text())
    registered = json.loads(trained.REGISTRY.read_text())
    entries = {r["draw"]: r for r in registered["accepted"]}
    frozen = torch.as_tensor(original["weights"], dtype=torch.float64)
    declarations = [exact_declaration(p, g) for p, g in channel.VOCABULARY]
    exact = {key: read_declaration(declaration) for key, declaration in zip(soft, declarations, strict=True)}
    assert all(key == value for key, value in exact.items())
    assert all(read_declaration(text) is None for text, _ in channel.CONTROLS.values())
    cost = {note["intended"]: (note["writer_output_tokens"], note["reader_output_tokens"]) for note in notes}
    reviewed = {note["intended"]: note["parsed"] if note["force_review"] == "reports_current_grade" else None
                for note in notes}
    scores = []
    for saved in original["reserved"]:
        key = saved["grid_id"]
        with patch.dict(shared.FIXTURES, {"target": trained.fixture(entries[key])}):
            data = trained.data_for(shared.Grid("target"))
            weights = data.probabilities(frozen).numpy()
            measures = {
                "typed": projection(data, weights, exact, "bound"),
                "prose_with_grade_binding": projection(data, weights, soft, "bound", cost),
                "prose_without_grade_binding": projection(data, weights, soft, "unbound", cost),
                "strict_same_assistant_force_review": projection(data, weights, reviewed, "bound", cost),
            }
            assert abs(measures["typed"]["net"] - saved["results"]["fitted"]["net"]) < 1e-9
            assert measures["prose_with_grade_binding"]["unsupported_certificate"] == 0.
            scores.append({"grid": key, "known_independent_net": saved["results"]["exact_independent"]["net"],
                           "modes": measures})
    return {"scope": "Frozen Qwen realized and read one-grade messages. Each resulting mapping is reused across "
                     "the finite exact trajectories. A grade-binding mode admits only the already selected tuple. "
                     "A strict same-assistant annotation with exact spans separately requires a current grade "
                     "rather than a proposal to adjust or revisit it. This tests transport through natural wording.",
            "recorded_messages": notes, "reader_controls": controls, "exact_declaration_control": declarations,
            "exact_roundtrips": sum(note["exact"] for note in notes), "scores": scores}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
