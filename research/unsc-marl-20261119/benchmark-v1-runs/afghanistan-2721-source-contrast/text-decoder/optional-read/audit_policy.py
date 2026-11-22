"""Check whether selected rereads help beyond a matched reread count."""
import json
from statistics import mean

import optional as study


def run():
    path = study.HERE/"results.json"
    saved = study.read(path)
    groups = {}
    for row in saved["held_rows"]:
        arms = row["arms"]
        read_mass = arms["fit"]["extra_calls"]
        assert 0 <= read_mass <= row["rate"]+study.TOL
        # The diagnostic matches the observed call budget in each scene.
        random_released = arms["never"]["released"]+(read_mass/row["rate"])*(
            arms["always"]["released"]-arms["never"]["released"])
        net = random_released-read_mass*row["fee"]
        cell = {"mode":row["mode"],"rate":row["rate"],"prior":row["prior"],"fee":row["fee"],
                "fit_minus_random": arms["fit"]["net"]-net,
                "random_same_budget":{"released":random_released,"extra_calls":read_mass,"net":net},
                "fit_minus_table":arms["fit"]["net"]-arms["order_table"]["net"],
                "fit_minus_never":arms["fit"]["net"]-arms["never"]["net"],
                "fit_minus_canonical":arms["fit"]["net"]-arms["canonical"]["net"]}
        groups.setdefault("/".join(row["first_orders"]),[]).append(cell)
    summaries = {}
    for order,rows in groups.items():
        summaries[order] = {}
        for control in ("random","table","never","canonical"):
            deltas = [row["fit_minus_"+control] for row in rows]
            summaries[order][control] = {"mean_delta":mean(deltas),
                "wins":sum(v>study.TOL for v in deltas),"losses":sum(v < -study.TOL for v in deltas)}
    return {"source_sha256":study.sha(path),"summary":summaries,"scenes":groups}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
