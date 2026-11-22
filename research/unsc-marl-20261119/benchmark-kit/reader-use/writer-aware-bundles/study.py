"""Learn how to select a safe writing bundle before valuing a request."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import facilitator_guard_calibrated_fit as archive
import facilitator_silence_joint_fit as previous

E = HERE.parent
fit, joint, R = previous.fit, previous.joint, previous.R
KNOWN = (0, 1, 2, 4)
MASKS = tuple(range(8))
UNKNOWN = tuple(m for m in MASKS if m not in KNOWN)
L2 = .25


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def banks():
    output = []
    for family, item in archive.training_banks().items():
        output.append({"family": family, "mode": "archived_writer", "source": item["path"],
                       "sha256": item["sha256"], "release": item["guarded"], "raw": item["material"]})
    for key, file in (
        ("fixed_public", "facilitator-fixed-public-bank-evidence/results.json"),
        ("free_writer", "facilitator-free-record-bank-evidence/results.json"),
        ("verified_accounts", "facilitator-validated-accounts-evidence/apostrophe.json")
    ):
        path = E / file
        record = json.loads(path.read_text())
        output.append({"family": "haiti_2699", "mode": key, "source": file, "sha256": sha(path),
                       "release": record["released_bank"], "raw": record["material_bank"]})
    theater = E / "tribunals2422-transfer/writer-results.json"
    cases = json.loads(theater.read_text())["records"]
    for order, states in cases.items():
        records = [states[str(m)] for m in MASKS]
        output.append({"family": "tribunals_2422", "mode": order,
                       "source": str(theater.relative_to(E)), "sha256": sha(theater),
                       "release": [42+r["released"] if r["release"] else 0 for r in records],
                       "raw": [42+r["raw"] for r in records]})
    assert len(output) == 10 and len({r["family"] for r in output}) == 7
    assert all(len(r["release"]) == len(r["raw"]) == 8 for r in output)
    assert all(all(0 <= g <= m <= 70 for g,m in zip(r["release"],r["raw"],strict=True)) for r in output)
    return output


def subsets(mask, allowed=MASKS):
    return [m for m in allowed if m & mask == m]


def reviewed(bank):
    return {mask: (bank["release"][mask], bank["raw"][mask]) for mask in KNOWN}


def baseline(anchors, mask):
    return max(anchors[option][0] for option in subsets(mask,KNOWN))


def additive(anchors, mask):
    return float(np.clip(anchors[0][0]+sum(
        anchors[k][0]-anchors[0][0] for k in subsets(mask,KNOWN) if k),0,70))


def features(anchors, mask):
    values = [anchors[k] for k in subsets(mask,KNOWN) if k]
    empty, raw = anchors[0]
    singleton = baseline(anchors,mask)
    return np.array([1., float(len(values) == 3), sum(g == 0 for g,_ in values) / len(values),
                     singleton/70, empty/70, sum(m-raw for _,m in values)/70,
                     (additive(anchors,mask)-singleton)/70])


def fit_labels(rows):
    seen = {k: sum(r["family"] == k for r in rows) for k in {r["family"] for r in rows}}
    x, y, weight = [], [], []
    for row in rows:
        public = reviewed(row)
        for mask in UNKNOWN:
            x.append(features(public,mask))
            y.append((row["release"][mask]-baseline(public,mask))/70)
            weight.append(1/seen[row["family"]])
    x, y = np.asarray(x), np.asarray(y)
    scale = np.sqrt(weight)
    ridge = np.sqrt(L2) * np.eye(x.shape[1])
    coef = np.linalg.lstsq(np.vstack((x*scale[:,None],ridge)), np.r_[y*scale,np.zeros(x.shape[1])], rcond=None)[0]
    return coef, {"samples":len(y), "families":len(seen), "train_rmse":float(np.sqrt(np.average((x@coef-y)**2,weights=weight))*70)}


def predicted(anchors, params):
    known = {k: v[0] for k,v in anchors.items()}
    additive_prediction = known | {s:additive(anchors,s) for s in UNKNOWN}
    learned = known | {s:float(np.clip(baseline(anchors,s)+70*features(anchors,s)@params,0,70)) for s in UNKNOWN}
    return additive_prediction, learned


def choose(predictions, mask, allowed=MASKS):
    # Keep the smallest bundle in score ties.
    return max(subsets(mask,allowed), key=lambda k:(predictions[k],-k.bit_count(),-k))


def choice_tables(case, params):
    truth = case["release"]
    public = reviewed(case)
    known = {k:v[0] for k,v in public.items()}
    plain, learned = predicted(public, params)
    tables = {"all_received": (list(MASKS), plain),
              "reviewed_only": ([choose(known,m,KNOWN) for m in MASKS],known),
              "singleton_additive": ([choose(plain,m) for m in MASKS],plain),
              "learned_ridge": ([choose(learned,m) for m in MASKS],learned),
              "all_labels_oracle": ([choose(truth,m) for m in MASKS],truth)}
    return tables


def replay(case, tables):
    reward, raw = (np.asarray(case[key]) for key in ("release","raw"))
    public, _ = predicted(reviewed(case),np.zeros(7))
    declared = np.asarray([public[m] for m in MASKS])
    old = previous.budget.read(previous.OLD)["training"]["budget_fit"]
    result = {}
    for label in fit.live.PRIORS:
        prior = R.TEST_PRIORS[label]
        l,r = previous.opening(declared,prior,old)
        mass = joint.opening(l,r,prior)
        slate = {}
        for name,(selected,predictions) in tables.items():
            estimate = np.array([predictions[s] for s in selected])
            actual = reward[selected]
            q, a = fit.exact(estimate,mass,fit.PERFECT)
            measure = joint.metric((l,r,q,a),prior,actual,fit.PERFECT)
            receipt = np.asarray(measure["receipt_mass"])
            assert abs(receipt.sum()-1) < 1e-10
            slate[name] = {"net":measure["net"], "requests":measure["expected_requests"],
                           "guarded_points":float(receipt@actual), "raw_points":float(receipt@raw[selected]),
                           "release_probability":float(receipt@(actual>0)),
                           "withheld_more_than_zero":float(receipt@np.asarray([s!=m for m,s in enumerate(selected)])),
                           "requests_map":q.tolist()}
        assert all(row["net"] <= slate["all_labels_oracle"]["net"] + 1e-10 for row in slate.values())
        result[label] = slate
    return result


def run():
    rows = banks()
    scores = {}
    for item in rows:
        k = item["family"]+"/"+item["mode"]
        family = item["family"]
        train = [v for v in rows if v["family"] != family]
        assert family not in {v["family"] for v in train}
        parameters, fit_receipt = fit_labels(train)
        tables = choice_tables(item,parameters)
        details = {}
        for name,(table,_) in tables.items():
            scores_at_receipt = [item["release"][x] for x in table]
            details[name] = {"selected":table,"release_at_receipt":scores_at_receipt,
                             "mean_uniform_receipt":float(np.mean(scores_at_receipt))}
        scores[k] = {"fit":fit_receipt,"weights":parameters.tolist(),
                     "selection":details,"routing":replay(item,tables)}
    return {"banks":rows,"checks":scores,"sha256": {str(f.relative_to(E)):sha(f) for f in (
        Path(__file__),HERE/"protocol.md",previous.OLD)}}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
