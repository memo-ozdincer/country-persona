"""Score the frozen native decisions against the exact documentary environment."""
import json
import re

import decode_2721 as experiment

fixture = experiment.fixture
HERE = experiment.HERE
STOP = frozenset("a an and as at by for from in into is it of on or that the their to was with would".split())
LETTERS = ("A","B")


def words(text):
    return set(re.findall(r"[a-z]+",text.lower()))-STOP


def lexical(prompt):
    data = json.loads(prompt["messages"][1]["content"])
    received = words(data["observation"].get("explanation",""))
    candidates = [words(data["choices"][letter]) for letter in LETTERS]
    shares = [len(received & x)/max(1,len(received | x)) for x in candidates]
    return int(shares[1] > shares[0]), shares


def run():
    plan = json.loads((HERE/"plan.json").read_text())
    verified = json.loads((HERE/"verified.json").read_text())
    records,_ = fixture.cases()
    responses = verified["outputs"]
    assert set(responses) == {request["id"] for request in plan["requests"]}
    grouped = {}
    for req in plan["requests"]:
        mode, truth, mapping = req["id"].split("/")
        output = responses[req["id"]]
        phrase = experiment.MAPPINGS[mapping]
        margin = output["logits"][LETTERS[phrase.index(0)]] - output["logits"][LETTERS[phrase.index(1)]]
        raw = phrase[LETTERS.index(output["label"])]
        assert (margin >= 0 if raw == 0 else margin <= 0)
        overlap, overlaps = lexical(req)
        grouped.setdefault((mode,truth),{})[mapping] = {
            "raw_mapped":raw,"margin_0_minus_1":margin,
            "lexical_choice":phrase[overlap],"lexical_overlap_by_label":overlaps,
        }

    def collect(mode, truth):
        variants = grouped[mode,str(truth)]
        average = sum(row["margin_0_minus_1"] for row in variants.values())/2
        return int(average < 0), {
            **variants,"calibrated_margin":average,
            "agreement":variants["ab"]["raw_mapped"] == variants["ba"]["raw_mapped"],
        }

    no_receipt,no_stats = collect("no_receipt",None)
    arrival,arrival_stats = collect("arrival_only",None)
    modes = {}
    for mode in experiment.MODES:
        choices,decisions = {},{}
        for truth in (0,1):
            choices[truth],decisions[truth] = collect(mode,truth)
        conditions = []
        for row in json.loads((HERE.parent/"results.json").read_text())["conditions"]:
            q = fixture.Q(str(row["receipt_probability"]))
            p = fixture.Q(str(row["first_card_0_probability"]))
            arms = {"paired_decoder":choices,"arrival_only_model":{0:arrival,1:arrival},
                    "lexical":{x:decisions[x]["ab"]["lexical_choice"] for x in (0,1)},
                    **{label:{x:decisions[x][label]["raw_mapped"] for x in (0,1)}
                       for label in experiment.MAPPINGS}}
            score = {name:float(fixture.receipt_value(records,q,p,{**acts,None:no_receipt}))
                     for name,acts in arms.items()}
            assert max(score.values()) <= row["content_ceiling"]
            if all(choices[x] == x for x in (0,1)):
                assert score["paired_decoder"] == row["content_ceiling"]
            conditions.append({"delivery":float(q),"prior":float(p),"release":score,
                               "arrival_ceiling":row["arrival_only_ceiling"],"content_ceiling":row["content_ceiling"]})
        modes[mode] = {
            "decisions":decisions, "deployed":choices,
            "exact_paired":sum(p==t for t,p in choices.items()),
            "raw_exact":sum(d[label]["raw_mapped"]==t for t,d in decisions.items()
                            for label in experiment.MAPPINGS),
            "mapping_agreement":sum(d["agreement"] for d in decisions.values()),
            "lexical_exact":sum(d["ab"]["lexical_choice"] == t for t,d in decisions.items()),
            "retained_documentary_ceilings":sum(row["release"]["paired_decoder"]==row["content_ceiling"]
                                                 for row in conditions),
            "delivery_replay":conditions,
        }
    return {"absent":{"action":no_receipt,"orders":no_stats},
            "arrival_only":{"action":arrival,"orders":arrival_stats},"modes":modes,
            "verified_sha256":fixture.pin(HERE/"verified.json")}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
