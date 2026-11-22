"""Execute compiled records through all protected written-vote episode branches."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import corroboration_receiver as decoder

HERE = decoder.HERE
QUESTION = "Can you send the certified working file for this review?"


def execute(schedule, receiver, focus, inventory_index, request_kept, reply_kept, calibration):
    inventory = decoder.case.PAIRS[inventory_index]
    asked = bool(schedule[focus])
    observed = int(asked and request_kept)
    source = receiver[inventory_index][observed]
    assert source in inventory
    note = decoder.case.packet(source)
    result = decoder.case.compile_record(decoder.case.packet(focus), note if reply_kept else None,
                                         [decoder.case.KEYS[x] for x in inventory])
    cost = calibration.question_fee * asked + calibration.reply_fee
    return {**result, "request_sent": QUESTION if asked else None,
            "request_received": QUESTION if observed else None, "relay": note,
            "relay_received": bool(reply_kept), "net": result["score"] - cost}


def run():
    fit_path = HERE / "joint-fit-results.json"
    path = HERE / "joint-repair-results.json"
    fitted = decoder.case.read(fit_path)
    adjusted = decoder.case.read(path)
    calibration = decoder.transfer.Calibration()
    methods = {"learned": fitted["policies"]["learned"],
               "repaired": (adjusted["final_sender"], adjusted["final_responder"])}
    q_loss = calibration.question_loss
    r_loss = calibration.reply_loss
    prior = {"design_mixture": calibration.design_prior, **calibration.priors}
    manual = {name: dict.fromkeys(methods, 0.) for name in prior}
    central_examples = {}
    examined = 0
    for label, (sender, receiver) in methods.items():
        for focus, inventory, request, reply in product(range(4), range(6), (0, 1), (0, 1)):
            event = execute(sender, receiver, focus, inventory, request, reply, calibration)
            examined += 1
            branch = (1 - q_loss if request else q_loss) * (1 - r_loss if reply else r_loss)
            for name, table in prior.items():
                manual[name][label] += branch * table[focus, inventory] * event["net"]
            if focus == 3 and inventory == 5:
                central_examples[f"{label}/request_{request}/relay_{reply}"] = event
    for name, numbers in manual.items():
        assert np.isclose(numbers["learned"], fitted["outcomes"][name]["learned"])
        assert np.isclose(numbers["repaired"], adjusted["evaluations"][name]["post_repair"])
    return {"scope": "Execute authenticated source identities and actual record text in every declared loss branch. "
                     "The requester knows only its own card and the receiver uses the local inventory and received bit. "
                     "Historical excerpts and the assembly are supplied and bounded. No LLM generates the public record.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "repair_sha256": sha256(path.read_bytes()).hexdigest(),
            "branches_executed": examined, "recomputed_net": manual,
            "council_president_with_both_indonesia_sources_on_right": central_examples}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
