"""Isolate the effect of an overlong fixed public paragraph on the frozen replay."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_emergency_session_score as locked

PUBLIC = {
    "S0": "On 27 February 2022 the Council adopted resolution 2623 (2022), 11 in favour and one against (Russia), with three abstentions (China, India and the United Arab Emirates).",
    "S1": "It decided to call a General Assembly emergency special session on Ukraine, recording that permanent-member disagreement at its 8979th meeting had prevented the Council from exercising its primary responsibility.",
}


def run(path):
    views = locked.fit.load(path / "review-items.json")
    annotations = locked.fit.load(path / "marks.json")
    scores = {}
    revised = {}
    header = "\n".join(f"[{sid}] {text}" for sid, text in PUBLIC.items())
    with patch.object(locked.fit.unama.study, "packet", locked.study.packet):
        for mask in range(8):
            key = f"normalized/{mask}"
            original = views[key]
            supplement = "\n".join(original["record"].splitlines()[2:])
            updated = f"{header}\n{supplement}".rstrip()
            new = {**original, "record": updated}
            marks = annotations[key].copy()
            for item, span in (("decision", PUBLIC["S0"]),
                               ("mandate", "decided to call a General Assembly emergency special session on Ukraine"),
                               ("reporting", "permanent-member disagreement at its 8979th meeting had prevented the Council from exercising its primary responsibility"),
                               ("authority", PUBLIC["S0"]), ("support", PUBLIC["S1"])):
                assert marks[item][0] == "met"
                marks[item] = ["met", span]
            if mask == 0:
                marks["citation"] = ["met", header]
            scores[key] = locked.fit.unama.score_record(new, marks)
            assert scores[key]["points"] == locked.fit.unama.score_record(original, annotations[key])["points"]
            revised[key] = updated
    return {"scope": "Post hoc public prefix compression. Retain all frozen generated supplements and their "
                     "material grades. Re-evaluate the word limit and run the unchanged one-pair rule.",
            "sources": PUBLIC, "compacted_records": revised, "scores": scores, "transfer": locked.evaluate(scores),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (
                Path(__file__), Path(locked.__file__), path / "review-items.json", path / "marks.json", path / "results.json")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2, ensure_ascii=False))
