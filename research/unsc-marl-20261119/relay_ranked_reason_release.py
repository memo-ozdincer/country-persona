"""Release a checked numeric explanation or the verified reference memo."""
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import relay_ranked_reason as reason


def approved(paragraph, certificate):
    if "selected" not in certificate:
        return False
    selected, alternative = certificate["selected"], certificate["alternative"]
    winner, peer = (re.escape(r["package"]) for r in (selected, alternative))
    provisional = ", though one card remains unverified" if certificate["provisional"] else ""
    clause = certificate["decisive_comparison"]
    if clause == "higher lower grade":
        assert selected["lower_grade"] > alternative["lower_grade"]
        body = (rf"Package {winner} (?:wins with a decisive|is selected with a decisive|is decisive with a) "
                rf"lower grade of {selected['lower_grade']} versus (?:Package )?{peer}'s "
                rf"{alternative['lower_grade']}")
    elif clause == "higher sum breaks an equal lower grade":
        assert selected["lower_grade"] == alternative["lower_grade"] and selected["sum"] > alternative["sum"]
        body = (rf"Package {winner} wins because its sum of {selected['sum']} exceeds (?:Package )?{peer}'s sum of "
                rf"{alternative['sum']}, breaking the tie in lower grade")
    else:
        return False
    return re.fullmatch(body + re.escape(provisional) + r"\.", paragraph) is not None


def release(directory):
    raw = directory / "short/memos.jsonl"
    references = directory.parent / "relay-ranked-final/reference.json"
    reference_by_id = {row["id"]: row["record"] for row in json.loads(references.read_text())}
    expected = {row["id"]: row["expected"] for row in reason.suite()}
    result, negatives = [], []
    for row in map(json.loads, raw.read_text().splitlines()):
        id_ = row["id"]
        pack = expected[id_]
        assert json.dumps(pack, sort_keys=True) == json.dumps(row["expected"], sort_keys=True)
        body = row["output"]
        frame = pack["frame"]
        cert = pack["certificate"]
        within_limit = len(body.split()) <= min(32, pack["word_limit"])
        kept = row["stop"] == "eos" and within_limit and approved(body, cert)
        if kept:
            memo = "\n\n".join((*frame[:2], body, frame[-1]))
            edits = {
                "appended_authority": body + " The Security Council adopted it.",
                "new_winner": body.replace("Package " + cert["selected"]["package"], "Package Z", 1),
                "flipped_winner_grade": re.sub(r"(?<= of )[1-9]", "9", body, count=1),
                "different_alternative": body.replace(cert["alternative"]["package"] + "'s", "Z's"),
                "unclosed": body.removesuffix("."),
            }
            for name, changed in edits.items():
                assert changed != body
                verdict = approved(changed, cert)
                assert not verdict
                negatives.append({"id": id_, "mutation": name, "paragraph": changed, "admitted": verdict})
        else:
            memo = reference_by_id[id_]
        assert len(memo.split()) <= 120
        assert memo.splitlines()[0] == frame[0]
        assert memo.endswith(frame[-1])
        result.append({"id": id_, "model_sentence_kept": kept, "memo": memo, "words": len(memo.split())})
    return {"raw_sha256": sha256(raw.read_bytes()).hexdigest(),
            "reference_sha256": sha256(references.read_bytes()).hexdigest(),
            "records": result, "mutation_checks": negatives}


if __name__ == "__main__":
    print(json.dumps(release(Path(sys.argv[1])), indent=2, ensure_ascii=False))
