"""Apply a non-editing assembly control to the three saved native notes."""
import json
from pathlib import Path

from live_tolerance import CASE, HERE, READ, frozen, prior

PUBLIC = ("On 14 June 2023, the Council unanimously adopted UAE–UK draft S/2023/427 as resolution 2686 (2023). "
          "It urged public condemnation of discriminatory violence, hate speech and extremism in line with international law "
          "and requested the Secretary-General to brief the Council publicly and orally by 14 June 2024.")
CONNECTIVE = "The co-sponsor stressed other considerations."


def apply(record, mask, notes):
    packet = frozen.final_packet(CASE, [{}, {}, record])
    evidence = {b["id"]: b["text"] for b in frozen.evidence(CASE)}
    commands = {
        "decision": (PUBLIC, ("decision",), "The public paragraph identifies both sponsors, the correct draft and unanimous adoption."),
        "operative": (PUBLIC, ("operative",), "It states public condemnation and its legal condition."),
        "briefing": (PUBLIC, ("follow-up",), "It names an oral public Council briefing by the specified date."),
    }
    if mask & 1:
        commands["fr-forum"] = (notes[0], ("fr-forum",), "France identifies both venues.")
        commands["fr-objection"] = (notes[0], ("fr-objection",), "France preserves its scope and free-expression caveat.")
    if mask & 2:
        commands["ch-scope"] = (notes[1], ("ch-scope",), "The Swiss message preserves both breadth and the actions-versus-ideas distinction.")
        commands["ch-covenant"] = (notes[1], ("ch-covenant",), "The note names the omitted covenant separately from rights proposals.")
    if mask & 4:
        commands["uk-rights"] = (notes[2], ("uk-rights",), "Grassroots involvement and free expression are attributed to the UK.")
        if mask & 3:
            start = notes[0] if mask & 1 else notes[1]
            excerpt = record["text"][record["text"].index(start):]
            commands["joint-qualification"] = (excerpt,
                ("decision", "uk-rights", *(code for bit, code in ((1, "fr-objection"), (2, "ch-scope")) if mask & bit)),
                "The named reservations are contrasted with the co-sponsor's rights-based rationale under a unanimous disposition.")
    units = []
    for key in (r["id"] for r in CASE["rubric"]):
        clause, sources, reason = commands.get(key, ("", (), "The record does not clearly state every required part."))
        units.append({"id": key, "status": "met" if clause else "unmet", "response": clause, "reason": reason,
                      "source": [{"block": b, "quote": evidence[b]} for b in sources]})
    marks = {"id": packet["id"], "units": units, "guard": {
        "status": "clear", "source": [], "response": "",
        "reason": "The public scope and attributed national reservations remain distinct, with no material unsupported claim."
    }}
    return {"score": frozen.final_score(CASE, [{}, {}, record], marks), "text": record["text"], "marks": marks}


def run():
    source = HERE / "verified.json"
    native = READ(source)["records"]
    notes = [native["note/" + role]["text"] for role in CASE["roles"]]
    assert all(native["note/" + role]["termination"] == "complete" for role in CASE["roles"])
    results = {}
    for mask in range(8):
        parts = [PUBLIC] + [notes[i] for i in range(2) if mask & (1 << i)]
        if mask & 4:
            if mask & 3:
                parts.append(CONNECTIVE)
            parts.append(notes[2])
        answer = "\n\n".join(parts)
        assert len(answer.split()) <= CASE["word_cap"]
        for i, note in enumerate(notes):
            assert (note in answer) == bool(mask & 1 << i)
        results[f"mask-{mask}"] = apply({"text": answer, "termination": "complete"}, mask, notes)
    return {"scores": results, "score_bank": [result["score"]["released_70"] for result in results.values()],
            "native_note_words": [len(note.split()) for note in notes],
            "sha256": {p.name: prior.digest(p) for p in
                       (Path(__file__), HERE / "assembly-protocol.md", HERE / "docket.json", source)}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
