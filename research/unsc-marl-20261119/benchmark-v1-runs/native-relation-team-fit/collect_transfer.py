"""Freeze and collect the four source propositions on the 2553 cards."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
SOURCE = RUNS / "role-scoped-comparison"
TEAM = RUNS / "documentary-team-policy"
ARCHIVE = RUNS / "reform-2553-transfer/documentary-routing/results.json"
sys.path.insert(0, str(SOURCE))
import collect_cpu as cpu
import collect_roles as old

prior, collector, read = old.prior, old.collector, old.read
SLOTS = ("early_delegate_statement", "reply_delegate_statement")
VIEWS = ("uk-explanation", "uk-inclusion", "belgium-explanation")
REPLIES = ("fund", "process")
CLAIMS = {
    "joint-process": (
        "The early speaker itself says the negotiations over the reform draft were rushed or allowed too little time.",
        "The replying speaker itself says the negotiations over the reform draft were rushed or allowed too little time.",
    ),
    "joint-fund": (
        "The early speaker itself says effective reform depends on adequate, predictable or sustainable funding.",
        "The replying speaker itself says management authority over the Peacebuilding Fund remains with the Secretary-General.",
    ),
}
WEIGHTS = {"joint-process": 6, "joint-fund": 4}
CONTROLS = (
    ("quoted-rush", "uk-explanation/process", 0,
     "The UK quoted a claim that negotiations were rushed and insufficiently rigorous, then rejected it and said the time allowed was adequate.", None),
    ("rejected-rush", "uk-explanation/process", 1,
     "Germany rejected a criticism of penholding and said there had been more than enough time to negotiate the draft.", None),
    ("rejected-fund", "belgium-explanation/fund", 0,
     "Belgium said predictable funding was desirable but explicitly rejected the view that reliable funding is essential to effective reform.", None),
    ("authority-transfer", "belgium-explanation/fund", 1,
     "Germany said the Secretary-General formerly managed the Peacebuilding Fund but declared that this authority now belongs exclusively to the Board.", None),
    ("paraphrase-timing", "uk-explanation/process", 1,
     "Germany said the drafters left the other representatives too short a window to work through the proposal.", "joint-process"),
    ("paraphrase-authority", "belgium-explanation/fund", 1,
     "Germany backs voluntary assistance. In its view the power to administer the Peacebuilding Fund still rests with the head of the UN Secretariat, the Secretary-General.", "joint-fund"),
)


def build():
    archive = read(ARCHIVE)["cases"]
    pairs = {}
    for view in VIEWS:
        for reply in REPLIES:
            datum = archive[view]["records"][reply]
            sources = datum["packet"]["evidence"]
            actor = "be-" if view.startswith("belgium") else "gb-"
            cards = ["\n".join(x["text"] for x in sources if x["id"].startswith(prefix))
                     for prefix in (actor, "de-")]
            assert all(cards)
            links = [x["id"] for x in datum["verdict"]["units"]
                     if x["id"].startswith("joint-") and x["status"] == "met"]
            assert len(links) <= 1 and set(links) <= set(CLAIMS)
            pairs[f"{view}/{reply}"] = {"cards": cards, "expected": next(iter(links), None), "real": True}
    for name, base, idx, text, expected in CONTROLS:
        pair = list(pairs[base]["cards"])
        pair[idx] = text
        pairs[name] = {"cards": pair, "expected": expected, "real": False}
    return pairs


def plan():
    pairs = build()
    requests, seen, refs = [], set(), {}
    for key, record in pairs.items():
        refs[key] = []
        for i, card in enumerate(record["cards"]):
            slot = SLOTS[i]
            ident = slot + "-" + collector.suite.e.checksum(card)[:10]
            refs[key].append(ident)
            if ident in seen:
                continue
            seen.add(ident)
            for relation, claim in CLAIMS.items():
                for order, mapping in prior.MAPPINGS.items():
                    inputs = {"source_role": slot, "source_text": card, "proposition": claim[i],
                              "responses": {label: "established" if meaning == "process" else "not established"
                                            for label, meaning in mapping.items()}}
                    requests.append(prior.base.earlier.request(f"{ident}/{relation}/{order}", 2, old.SYSTEM, inputs))
    assert len(requests) == 44
    anchors = old.plan()
    paths = (Path(__file__), HERE / "protocol.md", HERE / "fit.py", ARCHIVE, TEAM / "train_team.py",
             TEAM / "plan.json", TEAM / "results.json", SOURCE / "collect_cpu.py",
             SOURCE / "plan.json", SOURCE / "results.json")
    return {"pairs": pairs, "references": refs, "requests": requests,
            "checkpoint_index_sha256": anchors["checkpoint_index_sha256"],
            "pins": anchors["pins"] | {str(p.relative_to(RUNS.parent)): collector.sha(p) for p in paths}}


def act(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == read(HERE / "plan.json")
    with patch.object(cpu, "HERE", HERE), patch.object(cpu, "OUT", HERE / "evidence-cpu"), patch.object(
            cpu, "locked", return_value=spec):
        return {"run": cpu.run, "verify": cpu.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    args = parser.parse_args()
    result = act(args.mode)
    if args.mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
