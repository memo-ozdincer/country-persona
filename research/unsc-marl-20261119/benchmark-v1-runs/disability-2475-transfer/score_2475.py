"""Apply the frozen documentary scorer and contrast pair coverage with additivity."""
import json
from pathlib import Path

from live_2475 import CASE, HERE, READ, frozen, prior

GROUPS = ((3, 1, 2), (5, 1, 4), (6, 2, 4))
JOINT = ("fr-ru-scope", "uk-ru-ground")


def run():
    document = READ(HERE / "verified.json")
    judgments = READ(HERE / "annotations.json")
    assert set(judgments) == set(document["blind_packets"])
    blocks = {row["id"]: row["text"] for row in frozen.evidence(CASE)}

    def citation(mark):
        status, text, names, reason = mark
        return {"status": status, "response": text, "reason": reason,
                "source": [{"block": name, "quote": blocks[name]} for name in names]}

    rows = {}
    for name, record in document["records"].items():
        packet = frozen.final_packet(CASE, [{}, {}, record])
        verdict = judgments[packet["id"]]
        units = [{"id": rule["id"], **citation(verdict["units"].get(rule["id"], (
                    "unmet", "", [], "The record does not establish the complete criterion.")))}
                 for rule in CASE["rubric"]]
        marks = {"id": packet["id"], "units": units, "guard": citation(verdict["guard"])}
        assert frozen.judge.request(packet) == document["blind_packets"][packet["id"]]
        rows[name] = {"packet": packet["id"], "marks": marks,
                      "score": frozen.final_score(CASE, [{}, {}, record], marks)}
    banks, effects, joint = {}, {}, {}
    for arm in ("verbatim", "compared"):
        series = [rows[f"{arm}/mask-{mask}"]["score"] for mask in range(8)]
        bank = [score["released_70"] for score in series]
        banks[arm] = bank
        low = [score["raw_70"][0] for score in series]
        effects[arm] = {}
        for pair, i, j in GROUPS:
            additive = bank[i] + bank[j] - bank[0]
            raw_additive = low[i] + low[j] - low[0]
            effects[arm][str(pair)] = {"observed": bank[pair], "additive": additive,
                                       "excess": bank[pair] - additive, "raw_observed": low[pair],
                                       "raw_additive": raw_additive, "raw_excess": low[pair] - raw_additive}
        joint[arm] = [{key: score["units"][key] for key in JOINT} for score in series]
    return {"banks": banks, "pair_effects": effects, "joint": joint, "scores": rows,
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "docket.json",
                       HERE / "verified.json", HERE / "annotations.json", HERE / "source-audit.md")}}


if __name__ == "__main__":
    frozen.emit(run())
