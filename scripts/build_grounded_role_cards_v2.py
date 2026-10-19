"""Repair a missing antecedent found in hand-reading the preflight-only cards."""
import hashlib
import json
from pathlib import Path

from build_grounded_role_cards import build, ROOT, PARENT

OUT = ROOT / "research/grounded-role-cards-20261019-v2"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=False)
    rows, grounding = build()
    prior = json.loads((PARENT / "grounding.json").read_text())
    uk = next(s for s in prior["spans"] if s["id"] == "GBR-earlier")
    span = next(s for s in grounding["spans"] if s.get("parent_span") == "GBR-earlier")
    start = uk["quote"].index("Seventy-seven years ago")
    stop = uk["quote"].index("any State.", start) + len("any State.")
    complete = uk["quote"][start:stop]
    for row in rows:
        assert row["messages"][1]["content"].count(span["quote"]) == 1
        row["messages"][1]["content"] = row["messages"][1]["content"].replace(span["quote"], complete)
    span.update(start=uk["start"]+start, end=uk["start"]+stop, quote=complete,
                quote_sha256=hashlib.sha256(complete.encode()).hexdigest())
    grounding["removed_narrative"] = "Greetings, nuclear anxiety, terrorism aside, UK casualty/atrocity statistics and individual victim story. The Modi sentence remains inside the India cessation quote. Original full dossier retained."
    grounding["preflight_correction"] = "v1 UK quote began They without its antecedent. v2 restores the two preceding Charter sentences before any card model answers; v1 remains unchanged and unrun on GPU."
    for name, data in [("examples.json", rows), ("grounding.json", grounding)]:
        (OUT/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n")
    (OUT/"rubric.json").write_bytes((PARENT/"rubric.json").read_bytes())
    for row in rows:
        (OUT/(row["id"]+".txt")).write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")
    print(json.dumps(dict(examples=2, source_spans=12, antecedent_repaired=True)))
