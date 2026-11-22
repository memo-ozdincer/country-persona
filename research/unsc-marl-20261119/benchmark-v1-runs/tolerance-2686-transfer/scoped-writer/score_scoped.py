"""Compose exact quote checks from one reading of each reusable fragment."""
import json
from pathlib import Path

from scoped_writer import CASE, CONNECTIVE, HERE, PARENT, READ, frozen, notes, prior


def score():
    document = READ(HERE / "verified.json")
    visible = {key: row["text"] for key, row in document["fragments"].items()}
    visible.update({f"archived-{i}": text for i, text in enumerate(notes())})
    readings = READ(HERE / "annotations.json")
    assert set(readings) == set(visible)
    block_text = {row["id"]: row["text"] for row in frozen.evidence(CASE)}
    permitted = {"public": {b["id"] for b in CASE["public"]}}
    for keys in ("role", "archived"):
        for i, blocks in enumerate(CASE["owned"]):
            permitted[f"{keys}-{i}"] = {row["id"] for row in blocks}

    def cite(clause, key):
        status, response, sources, reason = clause
        assert not response or response in visible[key]
        assert set(sources) <= permitted[key]
        return {"status": status, "response": response, "reason": reason,
                "source": [{"block": b, "quote": block_text[b]} for b in sources]}

    fragment_units = {key: {unit: cite(mark, key) for unit, mark in reading["units"].items()}
                      for key, reading in readings.items()}
    fragment_guards = {key: cite(reading["guard"], key) for key, reading in readings.items()}
    result = {}
    for name, record in document["records"].items():
        arm, tag = name.split("/")
        prefix = "role" if arm == "scoped" else "archived"
        mask = int(tag.split("-")[1])
        keys = ["public"] + [f"{prefix}-{i}" for i in range(3) if mask & 1 << i]
        units = {}
        for key in keys:
            assert not units.keys() & fragment_units[key].keys()
            units.update(fragment_units[key])
        met = {key for key, mark in units.items() if mark["status"] == "met"}
        guard = next((fragment_guards[key] for label in ("failed", "uncertain") for key in keys
                      if fragment_guards[key]["status"] == label),
                     {"status": "clear", "response": "", "source": [],
                      "reason": "Each included fragment preserves material scope and attribution."})
        reservations = met & {"fr-objection", "ch-scope"}
        if "decision" in met and reservations and "uk-rights" in met and CONNECTIVE in record["text"]:
            start = record["text"].index(visible[keys[1]])
            logic = ("decision", "uk-rights", *sorted(reservations))
            cites = {c["block"]: c for criterion in logic for c in units[criterion]["source"]}
            units["joint-qualification"] = {"status": "met", "response": record["text"][start:],
                                            "source": list(cites.values()),
                                            "reason": "Distinct named national positions follow the unanimous disposition and explicit connective."}
        packet = frozen.final_packet(CASE, [{}, {}, record])
        assert frozen.judge.request(packet) == document["blind_packets"][packet["id"]]
        verdict = {"id": packet["id"], "guard": guard,
                   "units": [{"id": r["id"], **units.get(r["id"], {
                       "status": "unmet", "response": "", "source": [],
                       "reason": "The included fragments do not establish this criterion."})} for r in CASE["rubric"]]}
        result[name] = {"packet": packet["id"], "score": frozen.final_score(CASE, [{}, {}, record], verdict),
                        "marks": verdict, "included_fragments": keys}
    return {"scores": result,
            "banks": {variant: [result[f"{variant}/mask-{mask}"]["score"]["released_70"] for mask in range(8)]
                      for variant in ("scoped", "verbatim")},
            "sha256": {f.name: prior.digest(f) for f in (Path(__file__), HERE / "verified.json",
                       HERE / "annotations.json", PARENT / "docket.json")}}


if __name__ == "__main__":
    print(json.dumps(score(), ensure_ascii=False, indent=2))
