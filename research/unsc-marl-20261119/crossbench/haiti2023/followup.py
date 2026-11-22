"""Separate a deterministic citation attachment from a model comparison retry."""
import json
from unittest.mock import patch

import writer
import results
import policy_replay
import comparison_retry as retry

HERE = results.HERE
DIRECTORY = HERE / "followup-evidence"


def cite_known_single_source(field, name):
    if field["cited"]:
        return field
    assert not results.CITE.search(field["text"])
    return {**field, "text": field["text"] + f" [{name}]", "cited": {name}}


def assemble(fields, rules):
    case = results.load(writer.CASE)
    outputs = {}
    for packet, ref in rules.items():
        if not 1 <= len(packet) <= 3:
            continue
        group = [fields[field] for field in case["sources"] if field in packet]
        if "overlap" in ref["proof"]:
            group.append(fields["overlap"])
        name = ",".join(sorted(packet))
        outputs[name] = results.compose(group, case, packet, ref["proof"])
    return outputs


def run():
    baseline = results.load(results.EVIDENCE / "results.json")
    rules = results.verified_bank(results.load(writer.CASE))
    initial = {k: {**v, "cited": set(v["cited"])} for k, v in baseline["raw_fields"].items()}
    rendered = {k: cite_known_single_source(initial[k], k) for k in writer.TASKS if k != "overlap"}
    # Verify that the sole operation on the four body texts is a source suffix.
    changed = [k for k, v in rendered.items() if v["text"] != initial[k]["text"]]
    assert set(changed) == {"MANDATE", "SAFEGUARDS"}
    before = {**rendered, "overlap": initial["overlap"]}
    with patch.multiple(writer, build=retry.build, locks=retry.locks):
        repaired = writer.replay(DIRECTORY)["overlap"]
    reviewed = results.load(HERE / "followup-annotations.json")
    assert reviewed["transcript_sha256"] == writer.runner.digest(DIRECTORY / "transcript.jsonl")
    after = {**rendered, "overlap": results.checked(repaired, reviewed["overlap"], {"overlap"})}
    measurements = {}
    for name, fields in (("citations_only", before), ("citations_and_comparison", after)):
        packets = assemble(fields, rules)
        measures = policy_replay.run({**baseline, "field_packets": packets})
        measurements[name] = {"packets": packets, "route_replay": measures["conditions"]}
    return {"scope": "Posthoc diagnostics only. Citation attachment names the known single source and changes "
                     "no words. The one-call comparison retry receives an authored common proposition and separate vote "
                     "fields. The policies and physical receipts remain fixed.",
            "format_only_fields": changed, "measurements": measurements}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
