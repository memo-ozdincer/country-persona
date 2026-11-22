"""Use the catalog's binding when a model returns the right IDs in the wrong order."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json

import facilitator_passage_routing_replay as replay
import facilitator_passage_routing_atoms as atoms

study, trained = replay.study, replay.trained


def by_identity(ordered):
    restored = deepcopy(ordered)
    controls = {}
    for key, packet, expected in study.cases():
        original = ordered["records"][key]
        record = restored["records"][key]
        tokens = {line.partition("|")[2].strip() for line in original["raw_answer"].splitlines()} if original["format"] else set()
        valid = {f: index for f, index in expected.items() if f != "public" and index in packet["passages"]}
        selected = {f: packet["passages"][index] for f, index in valid.items() if index in tokens}
        # Missing or decoy IDs never name one of the approved source fragments here.
        assert set(original["evidence_emitted"]).issubset(selected)
        record["evidence_emitted"] = selected
        record["field_pass"] = {f: f in selected for f in ("1", "2", "3")}
        docket, q, c = key.split("/")
        if original["withdrawn_control"]:
            assert "2" not in selected
            record["delivery"] = False
            controls[key] = {"field_two_withheld": True,
                             "model_explicitly_abstained_at_field_two": original["field_pass"]["2"],
                             "valid_fields_delivered": sorted(selected)}
        else:
            record["delivery"] = len(selected) == 3
            restored["matrices"][docket][int(q)][int(c)] = int(record["delivery"])
    restored["withheld_controls"] = controls
    return restored


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    p = study.EVIDENCE / "admission.json"
    fitted = study.HERE / "facilitator-measured-channel-evidence/fits.json"
    original, weights = trained.read(p), trained.read(fitted)
    collected = by_identity(original)
    print(json.dumps({"admission": collected, "routing": replay.run(collected, weights),
                      "atom_routing": atoms.run(collected, weights),
                      "sha256": {x.name: sha256(x.read_bytes()).hexdigest() for x in (p, fitted)}},
                     ensure_ascii=False, indent=2))
