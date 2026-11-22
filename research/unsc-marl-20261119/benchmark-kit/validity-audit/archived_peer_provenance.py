"""Verify three annotated source-to-record chains against actual chair inputs."""
import json

from peer_evidence_judge import EVIDENCE, SPACE, SOURCE_FILES, read, runner

SUDAN = EVIDENCE / "source-record-sudan-chair-control/transcript.jsonl"
MINURSO = EVIDENCE / "minurso-deliberation-named/transcript.jsonl"


def transcript(path):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    result = {row["id"]: row for row in rows}
    assert len(rows) == len(result)
    return result


def body(row):
    return json.loads(row["messages"][-1]["content"])


def span(text, quote):
    start = text.index(quote)
    return {"quote": quote, "start": start, "end": start + len(quote)}


def report():
    sudan = transcript(SUDAN)
    peer = sudan["sudan-chair-control/original/interactive"]
    solo = sudan["sudan-chair-control/original/draft_free"]
    access = "humanitarian access"
    source_access = body(peer)["evidence"]["TEXT"]
    assert source_access == body(solo)["evidence"]["TEXT"]
    assert not body(solo)["working_text"]
    assert all(access not in row["text"].lower() for row in body(peer)["working_text"])

    space = transcript(SPACE)
    peer_space = space["best-contrast.interactive.final"]
    independent_space = space["best-contrast.independent.final"]
    same_receipt_space = space["lowest-contrast.independent.final"]
    assert body(peer_space)["docket"] == body(independent_space)["docket"]
    assert "china-reason" not in body(independent_space)["delivered_source_notes"]
    received = body(peer_space)["delivered_source_notes"]["china-reason"]
    assert received == space["best-contrast.interactive.right"]["output"]
    assert received == body(same_receipt_space)["delivered_source_notes"]["china-reason"]
    assert peer_space["output"] == same_receipt_space["output"]
    space_reference = {x["id"]: x["text"] for x in read(SOURCE_FILES[1])["evidence"]}
    assert received == space_reference["china-reason"]

    minurso = transcript(MINURSO)
    peer_sahara = minurso["chair-peer"]
    assert "peer-0" in peer_sahara["seen"]
    peer_claim = body(peer_sahara)["national_drafts"]["DZ-DRAFT"]
    assert peer_claim == minurso["peer-0"]["output"]
    source_sahara = body(peer_sahara)["public_evidence"]["MAIN"]

    return {
        "scope": "Same-assistant adjudicated exact-span witnesses from unedited archived outputs. "
                 "This validates trace linkage and receipt controls for three specific propositions.",
        "trace_sha256": {p.parent.name: runner.digest(p) for p in (SUDAN, SPACE, MINURSO)},
        "witnesses": [
            {"kind": "already_visible", "record": peer["id"], "final": span(peer["output"], access),
             "dossier_id": "TEXT", "dossier": span(source_access, "facilitating humanitarian access"),
             "same_claim_without_drafts": span(solo["output"], access)},
            {"kind": "new_peer_evidence", "record": peer_space["id"],
             "final": span(peer_space["output"], "seeking broader measures and early binding multilateral agreements"),
             "delivered_note_id": "china-reason", "delivered_note": span(
                 received, "seeking broader measures and early work toward binding multilateral agreements"),
             "independent_record_lacking_note": independent_space["id"],
             "same_receipt_identical_output": same_receipt_space["id"]},
            {"kind": "unsupported", "record": peer_sahara["id"],
             "final": span(peer_sahara["output"], "Abstained on MAIN (DZ-DRAFT)"),
             "delivered_note_id": "DZ-DRAFT", "delivered_note": span(peer_claim, "Algeria abstained on Resolution 2756"),
             "contradiction_dossier_id": "MAIN",
             "contradiction": span(source_sahara, "one member not participating (Algeria)")},
        ],
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, ensure_ascii=False))
