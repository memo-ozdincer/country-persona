"""Bind the partial-disclosure readout to actual Syria workshop submissions."""
import hashlib
import json
from pathlib import Path

from decision_ledger import readout, truthful_disclosure

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "language" / "evidence"
FAMILY = "syria-cross-border-aid-july-2023"


def verify():
    transcript = EVIDENCE / "transcript.jsonl"
    source = transcript.read_bytes()
    sha = hashlib.sha256(source).hexdigest()
    assert sha == json.loads((EVIDENCE / "complete.json").read_text())["release_sha256"]
    records = {r["id"]: r for line in source.splitlines() for r in [json.loads(line)]}
    annotated = json.loads((EVIDENCE / "availability-annotations.json").read_text())["submissions"]
    refs = json.loads((HERE / "references.json").read_text())["families"][FAMILY]["workshop_refs_only"]
    decisions = {}
    for variant in ("overlap", "impasse"):
        decisions[variant] = {}
        reference = refs[variant]
        for arm in ("solo", "peer"):
            final = records[f"final-{arm}-{variant}"]
            messages = []
            for i, id_ in enumerate(final["dependencies"], start=1):
                disclosure = annotated[id_]
                assert disclosure["quote"] in records[id_]["output"]
                created = {"id": id_, "role": f"role-{i}", "accepts": disclosure["accept"],
                           "excludes": disclosure["exclude"]}
                messages.append(created)
            assert len(messages) == 2
            options, agents = "ABCD", ("role-1", "role-2")
            observed = readout(options, agents, messages)
            ablated = [readout(options, agents, [m])["state"] for m in messages]
            assert ablated == ["UNRESOLVED", "UNRESOLVED"]
            assert all(truthful_disclosure(m, known) for m, known in zip(messages, reference["allowed_by_role"], strict=True))
            assert sorted(observed["verified_options"]) == reference["joint_packages"]
            assert observed["state"] == ("AGREEMENT_POSSIBLE" if reference["joint_packages"] else "IMPASSE")
            decisions[variant][arm] = {
                "from_supplied_messages": observed,
                "each_message_alone": ablated,
                "message_ids_seen_by_writer": final["dependencies"],
            }
    return {"transcript_sha256": sha, "cases": decisions,
            "scope": "Same-assistant quote annotations over generated submissions. Reference labels are checked after compiling."}


if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
