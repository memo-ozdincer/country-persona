"""Score the DRC first pass with exact observed evidence and source-bound citations."""
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

import writer

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "evidence"
shared_spec = spec_from_file_location("haiti_record_scoring", HERE.parent / "haiti2023/results.py")
shared = module_from_spec(shared_spec)
shared_spec.loader.exec_module(shared)


def load(path):
    return json.loads(path.read_text())


def verified_bank(case):
    with patch.object(shared, "HERE", HERE):
        return shared.verified_bank(case)


def render_source(field, authorized):
    """Attach only the IDs established by the field's receipt contract."""
    expected = set(authorized)
    if field["cited"]:
        return field, False
    assert not shared.CITE.search(field["text"])
    marks = ", ".join(authorized)
    return {**field, "text": f"{field['text']} [{marks}]", "cited": expected}, True


def run():
    case = load(writer.CASE)
    archive = writer.replay(EVIDENCE)
    reviewed = load(HERE / "annotations.json")
    assert reviewed["transcript_sha256"] == writer.runner.digest(EVIDENCE / "transcript.jsonl")
    assert archive.keys() == reviewed["records"].keys()
    bank = verified_bank(case)
    actual = {}
    renderer_log = {}
    for name, row in archive.items():
        capacity = bank.get(frozenset(row["evidence_ids"]), {})
        allowed = {"overlap"} if name == "overlap" else capacity["proof"].keys() - {"procedure"}
        result = shared.checked(row, reviewed["records"][name], allowed)
        if row["variant"] == "field":
            rendered, attached = render_source(result, row["evidence_ids"])
            renderer_log[name] = {"was_attached": attached, "ids_match": set(row["evidence_ids"]) == rendered["cited"]}
            # An authored receipt can supply only the IDs assigned to the field.
            if not renderer_log[name]["ids_match"]:
                renderer_log[name]["guard_issue"] = "Model-generated source markers conflict with receipt."
        else:
            rendered = result
        actual[name] = rendered

    packets = {}
    for ids, reference in bank.items():
        if not 1 <= len(ids) <= 3:
            continue
        labels = [k for k in case["sources"] if k in ids]
        if "overlap" in reference["proof"]:
            labels.append("overlap")
        name = ",".join(sorted(ids))
        assembled = shared.compose([actual[key] for key in labels], case, ids, reference["proof"])
        if not all(renderer_log[key]["ids_match"] for key in labels):
            assembled["cited_ids_clear"] = False
            assembled["release"] = False
        packets[name] = assembled

    compare = {}
    for name, ids in writer.PACKETS.items():
        packet = frozenset(ids)
        fields = packets[",".join(sorted(ids))]
        integrated = shared.compose([actual[name]], case, ids, bank[packet]["proof"])
        assert fields["sum_of_caps"] == integrated["sum_of_caps"]
        compare[name] = {"separate_fields": fields, "whole_packet": integrated}
    return {"scope": "First-pass comparison. Citation attachment is an input-bound rendering operation fixed "
                     "before generation. Exact semantic spans were reviewed by the same assistant and no field "
                     "choice or retry enters the primary comparison.",
            "renderer": renderer_log, "field_packets": packets, "matched_receipts": compare,
            "verified_bank": {",".join(sorted(k)):v for k,v in bank.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
