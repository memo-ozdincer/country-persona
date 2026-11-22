"""Bind a measured archive lookup to a protected requester and receiver episode."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import written_vote_protocol as runtime
from written_vote_protocol import decoder

HERE = decoder.HERE
CLARIFY = "Which record should I retrieve: a national explanation or the Council President's transmission of the result?"


def dispatch(chosen, available, roster, request_kept, relay_kept, sender, responder, calibration):
    if not chosen or chosen not in available:
        return {"clarification": CLARIFY, "request_sent": None, "relay": None, "score": None}
    focus = decoder.case.KEYS.index(chosen)
    return runtime.execute(sender, responder, focus, roster, request_kept, relay_kept, calibration)


def run():
    confirmed_path = HERE / "scoped-lookup-evidence/results.json"
    confirmed = decoder.case.read(confirmed_path)["records"]
    fit_path = HERE / "joint-repair-results.json"
    fit = decoder.case.read(fit_path)
    calibration = decoder.transfer.Calibration()
    sender, responder = fit["final_sender"], fit["final_responder"]
    controls = {}
    checked = 0
    examples = {}
    for key, decision in confirmed.items():
        actual = decision["reference"]
        available = (actual,) if actual != "ambiguous" else ("indonesia_national", "council_president")
        selected = decision["chosen"]
        if actual == "ambiguous":
            # Underspecified requests have no designated focal ownership.
            # Successful abstention has no simulated outreach or record.
            clarifying = dispatch(selected, available, 5, True, True, sender, responder, calibration)
            assert not selected and clarifying["score"] is None
            examples[key] = clarifying
            continue
        correct_focus = decoder.case.KEYS.index(actual)
        rows = []
        for roster, q, response in product(range(6), (0, 1), (0, 1)):
            record = dispatch(selected, available, roster, q, response, sender, responder, calibration)
            oracle = runtime.execute(sender, responder, correct_focus, roster, q, response, calibration)
            agree = record == oracle
            checked += 1
            rows.append({"roster": roster, "request_delivered_if_sent": bool(q), "reply_delivered": bool(response),
                         "score": record["score"], "typed_score": oracle["score"], "equal_to_typed": agree})
            if roster == 5 and q and response and actual in available and key.startswith("mission/"):
                examples[key] = record
        controls[key] = {"resolved_card": selected, "expected_card": actual,
                         "matching_branches": sum(row["equal_to_typed"] for row in rows), "branches": rows}
    points = {}
    for name, prior in {"design_mixture": calibration.design_prior, **calibration.priors}.items():
        net = 0.
        for focus, card in enumerate(decoder.case.KEYS):
            selected = confirmed[f"mission/{card}"]["chosen"]
            for roster, q, response in product(range(6), (0, 1), (0, 1)):
                result = dispatch(selected, (card,), roster, q, response, sender, responder, calibration)
                # Refused operation is credited zero under the strict contract.
                score = 0. if result["score"] is None else result["net"]
                weight = (1 - calibration.question_loss if q else calibration.question_loss) * (
                    1 - calibration.reply_loss if response else calibration.reply_loss)
                net += prior[focus, roster] * weight * score
        points[name] = {"language_routed_net": float(net), "typed_net": fit["evaluations"][name]["post_repair"]}
        if all(confirmed[f"mission/{key}"]["chosen"] == key for key in decoder.case.KEYS):
            assert np.isclose(net, points[name]["typed_net"])
    paths = (confirmed_path, fit_path, Path(runtime.__file__), HERE / "task.json")
    return {"scope": "Fresh measured lookup decisions feed the fixed typed repaired protocol. The validation cohort "
                     "consists of authored prompts on one docket and exact simulator branches. The local archival "
                     "identity is authenticated. Nothing in this run learns from these branches.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "inputs_sha256": {str(path.relative_to(HERE)): sha256(path.read_bytes()).hexdigest() for path in paths},
            "branches_checked": checked, "all_case_branches": controls,
            "mission_scores": points, "examples": examples}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
