"""Locate writer-risk collisions under the public score previews."""
from collections import defaultdict
from itertools import product
from pathlib import Path

import retry as r


def groups_from_banks(include_level):
    banks, _ = r.point_banks()
    groups = defaultdict(list)
    for family,name,points in banks:
        for values in (points,[points[0],points[2],points[1],points[3]]):
            for receipt, retry in ((1,2),(2,1)):
                first, left, right, both = values
                after = both - values[receipt]
                key = ((first,left,right) if include_level else (left-first,right-first)) + (receipt,retry)
                rows = groups[key]
                row = (family,name,after)
                if row not in rows:
                    rows.append(row)
    cases = []
    for key, rows in sorted(groups.items()):
        opposite = [(a,b) for a,b in product(rows,repeat=2) if a[0]!=b[0] and a[2]>0>b[2]]
        if opposite:
            cases.append({"public_view":key,"positive_and_negative_families":opposite})
    assert all(pair[0][0]!=pair[1][0] for cell in cases for pair in cell["positive_and_negative_families"])
    return {"public_views":len(groups),"cross_family_opposite_sign_views":len(cases),"examples":cases}


def run():
    return {"exact_public":groups_from_banks(True),"policy_input_gains":groups_from_banks(False),
            "source_hashes":{p.name:r.digest(p) for p in (Path(__file__),r.WRITERS)}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
