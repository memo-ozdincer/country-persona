"""Lock and verify a source-grounded authority comparison and its exact ceilings."""
import argparse
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASE = json.loads((HERE/"case.json").read_text())
RATES = tuple(map(Q, (".35",".55",".75",".95")))
PRIORS = tuple(map(Q,(".25",".5",".75")))
SLOTS = ("early_statements","late_clauses")
PUBLIC = CASE["public"]
RELATIONS = CASE["comparisons"]
OPTIONS = [[x["id"] for x in CASE[name]] for name in SLOTS]
BLOCKS = {x["id"]:x for name in ("public",*SLOTS,"comparisons") for x in CASE[name]}
BY_TEXT = {x["text"]:x["id"] for x in BLOCKS.values()}


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    return {"rates": list(map(str,RATES)), "priors":list(map(str,PRIORS)),
            "sha256":{p.name:pin(p) for p in (Path(__file__), HERE/"case.json",HERE/"protocol.md",
                                               HERE/"join_sources.py",HERE/"provenance.json")}}


def validate_slots(early, late):
    if any(v is not None and v not in allowed for v,allowed in zip((early,late),OPTIONS,strict=True)):
        raise ValueError("Invalid receipt owner or identifier")


def render(early, late):
    validate_slots(early,late)
    received = [r for r in (early,late) if r is not None]
    good = [r for r in RELATIONS if set(r["requires"]) <= set(received)]
    blocks = PUBLIC+[BLOCKS[c] for c in received]+good
    return "\n\n".join(r["text"] for r in blocks)


def verify(early, late, answer):
    validate_slots(early,late)
    try:
        lines = [BY_TEXT[line] for line in answer.split("\n\n")]
    except KeyError as error:
        raise ValueError("Unregistered or altered rendered text") from error
    public = [x["id"] for x in PUBLIC]
    actual = [x for x in (early,late) if x is not None]
    if lines[:len(public)+len(actual)] != public+actual:
        raise ValueError("Public record or receipt projection differs")
    relations = [x["id"] for x in RELATIONS if all(s in actual for s in x["requires"])]
    if lines[len(public)+len(actual):] != relations:
        raise ValueError("Comparison absent, extra, or lacking support")
    if len(answer.split()) > CASE["word_cap"]:
        raise ValueError("Word cap exceeded")
    section = {"public":sum(BLOCKS[id_]["weight"] for id_ in public),
               "standalone":sum(BLOCKS[id_]["weight"] for id_ in actual),
               "relation":sum(BLOCKS[id_]["weight"] for id_ in relations)}
    return {"released_70":sum(section.values()),"sections":section,"criterion_ids":lines}


def rejection(early,late,answer):
    try:
        verify(early,late,answer)
    except ValueError:
        return 1
    raise AssertionError("Invalid record passed verification")


def cases():
    records, rejected = {}, 0
    for early,late in product(*(list(range(2))+[None] for _ in SLOTS)):
        own,source = (OPTIONS[i][x] if x is not None else None for i,x in enumerate((early,late)))
        record = render(own,source)
        grade = verify(own,source,record)
        independent = 34 + 8*(early is not None) + 6*(late is not None) + 22*(early is not None and early==late)
        assert independent == grade["released_70"]
        paragraphs = record.split("\n\n")
        bad = {"\n\n".join(paragraphs[::-1]),"\n\n".join(paragraphs+paragraphs[-1:])}
        bad.update("\n\n".join(paragraphs[:i]+paragraphs[i+1:]) for i in range(len(paragraphs)))
        bad.update(record+"\n\n"+row["text"] for row in RELATIONS)
        for wrong in BY_TEXT:
            bad.add("\n\n".join(paragraphs[:-1]+[wrong]))
        rejected += sum(rejection(own,source,variant) for variant in sorted(bad-{record}))
        if own is not None:
            rejected += rejection(source,own,record)
        records[f"{early}/{late}"] = {"receipts":[own,source],"text":record,"grade":grade}
    return records,rejected


def receipt_value(bank, q, prior, policy):
    total = Q(0)
    for slot, first, second in product((0,1),repeat=3):
        world = prior if slot == 0 else 1-prior
        earlier = slot if first else None
        mass = world*(q if first else 1-q)*(q if second else 1-q)
        if policy == "random":
            reward = sum((bank[f"{earlier}/{move if second else None}"]["grade"]["released_70"] for move in (0,1)),Q(0))/2
        else:
            action = policy[earlier]
            reward = bank[f"{earlier}/{action if second else None}"]["grade"]["released_70"]
        total += mass*reward
    return total


def evaluate(records, q, prior):
    available = (None,0,1)
    fixed = int(prior < Q(1,2))
    arrival = max(receipt_value(records,q,prior,{None:first,0:same,1:same}) for first,same in product((0,1),repeat=2))
    content = max(receipt_value(records,q,prior,dict(zip(available,acts,strict=True)))
                  for acts in product((0,1),repeat=len(available)))
    reached = receipt_value(records,q,prior,{None:fixed,0:0,1:1})
    blind = receipt_value(records,q,prior,{m:fixed for m in available})
    random = receipt_value(records,q,prior,"random")
    base = 34+14*q
    assert reached == content == base+22*q*q
    assert blind == arrival == base+22*q*q*max(prior,1-prior)
    assert random == base+11*q*q
    return {"first_card_0_probability":float(prior),"receipt_probability":float(q),
            "random":float(random),"fixed":float(blind),"arrival_only_ceiling":float(arrival),
            "content_rule":float(reached),"content_ceiling":float(content),
            "content_gain":float(content-arrival),"break_even_per_arrived_read":float((content-arrival)/q)}


def run():
    lock = HERE/"plan.json"
    assert json.loads(lock.read_text()) == plan()
    records,rejected = cases()
    rows = [evaluate(records,q,prior) for q,prior in product(RATES,PRIORS)]
    return {"plan_sha256":pin(lock),"valid_receipt_records":records,"invalid_mutations_rejected":rejected,
            "conditions":rows}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),ensure_ascii=False,indent=2))
