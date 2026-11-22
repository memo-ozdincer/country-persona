"""Replay first-stage temporal credit with changes to the last delegate's policy."""
from collections import Counter
from hashlib import sha256
from pathlib import Path

import delayed as fit

HERE = Path(__file__).resolve().parent
E, s = fit.E, fit.s
SWAPS = {"both_available": (1.,1.), "desk_one_absent": (0.,1.),
         "desk_two_absent": (1.,0.), "both_rare": (.25,.25)}


def run():
    config = E.read(s.r.BENCH / "case.json")
    tree = E.read(s.r.BENCH / "transfer-fit.json")["tree"]
    weights = E.read(HERE/"delayed.json")["weights"]
    menu = config["menu"]
    stats = {}
    for name, actual in SWAPS.items():
        unaware, check = fit.stage(menu,tree,.8,availability=actual)
        informed, _ = fit.stage(menu,tree,.8,availability=actual,believed_availability=actual)
        counts = {mode: Counter() for mode in ("mandatory","informed_public","informed_fit","unaware_fit")}
        changed = 0
        for world in config["worlds"]:
            for state, truth in fit.all_states(world,menu):
                known, blind = informed(state,truth), unaware(state,truth)
                if known is not None:
                    assert known["query"]==blind["query"] and known["sent"]==blind["sent"]                            and known["withheld"]==blind["withheld"]
                pairs = {
                    "mandatory": (known,"mandatory"),
                    "informed_public": (known,"exact_public_credit"),
                    "informed_fit": (known,"fitted"),
                    "unaware_fit": (blind,"fitted"),
                }
                results = {label:check(state,item,mode,weights) for label,(item,mode) in pairs.items()}
                changed += results["informed_fit"]["first_send"] != results["unaware_fit"]["first_send"]
                for label, row in results.items():
                    counts[label].update({k:v for k,v in row.items() if k not in ("first_query","first_send")})
                    counts[label]["first_sends"] += row["first_send"]
        stats[name] = {"partner_availability":actual,"arms":counts,"changed_first_actions":changed}
    paths=(Path(__file__),HERE/"crossplay-protocol.md",HERE/"delayed.py",HERE/"delayed.json")
    return {"first_stage_delivery":.8,"results":stats,
            "sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__=="__main__":
    E.emit(run())
