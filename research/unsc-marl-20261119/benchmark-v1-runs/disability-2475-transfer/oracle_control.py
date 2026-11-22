"""Verify an authored positive control and alternate reading of French shorthand."""
from live_2475 import CASE, HERE, READ, frozen, prior

PARAGRAPHS = (
    "On 20 June 2019 the Council unanimously adopted the Poland–UK draft S/2019/503 as Resolution 2475. "
    "It called for safe, timely and unimpeded humanitarian access and urged meaningful participation by persons "
    "with disabilities. It requested pertinent disability-disaggregated reporting within existing mandates and resources.",
    "France called on UN Member States to ratify and fully implement the disability convention, linking participation to safety.",
    "Russia read operative paragraph 11 of the resolution as reaching only Article 11 of the convention "
    "and opposed new international legal categories.",
    "The UK backed disability leadership and disability-disaggregated evidence for Council decisions. "
    "It agreed with Russia on avoiding new legal obligations.",
    "France advocated full convention implementation, while Russia applied its narrower reading to the resolution's paragraph 11.",
)
PARTS = {
    "decision": (0, ("decision",)),
    "action": (0, ("action",)),
    "report": (0, ("report",)),
    "fr-treaty": (1, ("fr-treaty",)),
    "ru-article": (2, ("ru-article",)),
    "ru-authority": (2, ("ru-authority",)),
    "uk-participation": (3, ("uk-participation",)),
    "uk-authority": (3, ("uk-authority",)),
    "uk-ru-ground": (3, ("uk-authority",)),
    "fr-ru-scope": (4, ("fr-treaty", "ru-article")),
}


def run():
    evidence = {b["id"]: b["text"] for b in frozen.evidence(CASE)}
    records = {}
    for mask in range(8):
        visible = {0, *(i + 1 for i in range(3) if mask & 1 << i)}
        if mask & 3 == 3:
            visible.add(4)
        answer = "\n\n".join(PARAGRAPHS[i] for i in sorted(visible))
        calls = [{}, {}, {"text": answer, "termination": "complete"}]
        packet = frozen.final_packet(CASE, calls)
        units = []
        for rule in CASE["rubric"]:
            key = rule["id"]
            index, sources = PARTS[key]
            met = index in visible
            units.append({"id": key, "status": "met" if met else "unmet",
                          "response": PARAGRAPHS[index] if met else "", "reason": "Authored coverage control.",
                          "source": [{"block": code, "quote": evidence[code]} for code in sources if met]})
        verdict = {"id": packet["id"], "units": units, "guard": {
            "status": "clear", "reason": "Authored, source-bounded record.", "source": [], "response": ""}}
        records[mask] = {"answer": answer, "marks": verdict, "score": frozen.final_score(CASE, calls, verdict)}
    bank = [r["score"]["released_70"] for r in records.values()]
    assert bank == [21, 28, 35, 49, 42, 49, 56, 70]
    native = READ(HERE / "scores.json")
    lenient = {}
    for arm in native["banks"]:
        series = [native["scores"][f"{arm}/mask-{i}"]["score"] for i in range(8)]
        lenient[arm] = [r["raw_70"][0] if r["release_blockers"] == ["guard_uncertain"] else r["released_70"]
                        for r in series]
    return {"authored_bank": bank, "france_russia_pair_excess": bank[3] - bank[1] - bank[2] + bank[0],
            "lenient_un_ratification_banks": lenient, "authored_records": records,
            "sha256": {p.name: prior.digest(p) for p in (HERE / "docket.json", HERE / "scores.json")}}


if __name__ == "__main__":
    frozen.emit(run())
