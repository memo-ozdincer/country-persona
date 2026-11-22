"""Compare reused and fresh source-based approvals on altered source wording."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
PRIOR = RUNS/"writer-change-calibration"
LIVE = RUNS/"delisting-live-routing"
sys.path.insert(0, str(LIVE))
import live

read = live.read
WRITER = live.WITNESS
DELEGATES = {
    "malta": "Malta explained that the Focal Point would consult petitioners and collect information from several sources. Its report would help the sanctions committees deliberate and decide.",
    "a3plus": "For the African Council members and Guyana, Guyana said setting a time limit for the review would have been useful. The group hoped the provision for ongoing review would be implemented fully.",
    "switzerland": "Switzerland described the independent Ombudsperson for the 1267 regime as the ideal model. It nevertheless welcomed the stronger Focal Point as progress.",
}
DOCUMENTS = {
    "authority": "Annex I calls for the Focal Point to deliver a confidential report of facts without recommending an outcome. If a relevant State or a committee member recommends proceeding with delisting, the sanctions committee decides using its regular procedures.",
    "review": "The Council expressed its intention to keep reviewing the Focal Point's mandate and work on an ongoing basis. It set up a working group operating by consensus with responsibility for reviewing the Focal Point's semiannual reports.",
}
REVERSED_AUTHORITY = (
    "Annex I calls for a confidential factual report with a recommendation from the Focal Point. "
    "Upon a referral by a relevant State or committee member, the Focal Point makes the delisting "
    "decision and transmits it to the sanctions committee."
)
REVERSED_TIMING = (
    "For the African Council members and Guyana, Guyana said a time limit for the review would "
    "have been unhelpful. The group favored ongoing review alone and hoped it would be implemented fully."
)


def plan():
    case = read(live.BASE/"case.json")
    raw = {
        f"{e}/{d}": {"receipt":f"{e}/{d}","delegate_statement":DELEGATES[e],"adopted_document":DOCUMENTS[d]}
        for e,d in product(case["early"],case["late"])
    }
    raw["fictional/authority"] = raw["malta/authority"] | {"adopted_document": REVERSED_AUTHORITY}
    raw["fictional/review"] = raw["a3plus/review"] | {"delegate_statement": REVERSED_TIMING}
    paths = (Path(__file__), HERE/"protocol.md", LIVE/"live.py", WRITER/"witness.py",
             WRITER/"compact.py", PRIOR/"results.json", live.BASE/"case.json", live.BASE/"plan.json")
    return {"cards":raw,"baseline_licensed":read(PRIOR/"results.json")["prior"]["licensed"],
            "checkpoint":str(live.chair.MODEL),
            "checkpoint_index_sha256":live.chair.pin(live.chair.MODEL/"model.safetensors.index.json"),
            "pins":{str(path.relative_to(RUNS)):live.chair.pin(path) for path in paths}}


def collect(spec, call):
    case = read(live.BASE/"case.json")
    gate_system = read(live.BASE/"plan.json")["requests"][0]["messages"][0]["content"]
    rows = []
    for key, card in spec["cards"].items():
        sources = {field:card[field] for field in ("delegate_statement", "adopted_document")}
        request = {"messages": [{"role":"system","content":live.witness.SYSTEM},
                                {"role":"user","content":json.dumps(sources,ensure_ascii=False)}],
                   "max_output_tokens":live.witness.BUDGET}
        draft = call("write", request)
        candidate = live.compact.compact(draft, sources)
        relation, margins = None, None
        if candidate["fallback"] is None:
            relation, = (kind for kind,value in live.witness.CONNECTIVES.items() if value==candidate["text"])
            margins = []
            for side, text in zip(("early","late"),sources.values(),strict=True):
                replies = [call("label",row)["logits"] for row in
                           live.gate_queries(side,text,relation,case,gate_system)]
                a,b = replies
                margins.append((a["A"]-a["B"]+b["B"]-b["A"])/2)
        rows.append({"id":key,"receipt":card["receipt"],"draft":draft,"candidate":candidate,"relation":relation,
                     "margins":margins,"old_admits":margins is not None and card["receipt"] in spec["baseline_licensed"],
                     "fresh_admits":margins is not None and min(margins)>0})
    return {"branches":rows,"summaries":[]}


def replay(episodes):
    sys.path.insert(0, str(RUNS/"native-reward-routing-fit"))
    import learn

    spec = learn.plan()
    data, _ = learn.environment()
    old = read(RUNS/"native-reward-routing-fit/results.json")["training"]
    rows = {row["id"]:row for row in episodes["branches"]}
    marks = read(HERE/"marks.json")
    assert marks.keys()==rows.keys()
    released = {}
    for key,row in rows.items():
        mark = marks[key]
        assert mark["quote"]==row["candidate"]["text"]
        assert mark["status"] in {"fallback","supported","unsupported"}
        assert (mark["status"]=="fallback")== (row["relation"] is None)
        released[key] = {
            mode: 52 if not row[f"{mode}_admits"] else 70 if mark["status"]=="supported" else 0
            for mode in ("old","fresh")
        }
    policy = {}
    for mode in ("old","fresh"):
        table=learn.np.array([[released[f"{e}/{d}"][mode] for d in data["docs"]] for e in data["views"]])
        policy[mode]=learn.evaluate(data,table,old,spec)["summary"]
    return {"released":released,"policy":policy}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify","score"))
    mode=parser.parse_args().mode
    spec=plan()
    if mode!="plan":
        assert spec==read(HERE/"plan.json")
    with patch.object(live,"HERE",HERE),patch.object(live,"execute",side_effect=collect):
        functions={"plan":lambda _: spec,"run":live.run,"verify":live.verify,
                   "score":lambda _: replay(read(HERE/"evidence/episodes.json"))}
        data=functions[mode](spec)
    if mode!="run":
        print(json.dumps(data,ensure_ascii=False,indent=2))
