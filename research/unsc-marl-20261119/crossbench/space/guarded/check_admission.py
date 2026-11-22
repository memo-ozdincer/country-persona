"""Exhaustively verify selective and atomic admission over a small menu."""
from itertools import product
import json

from admit import admit_masks, submit


def main():
    labels = "ABC"
    checked = 0
    for evidence in product(range(3), repeat=len(labels)):
        yes = sum(1 << i for i,v in enumerate(evidence) if v == 1)
        no = sum(1 << i for i,v in enumerate(evidence) if v == 2)
        for request in product(range(4), repeat=len(labels)):
            accept = sum(1 << i for i,v in enumerate(request) if v & 1)
            exclude = sum(1 << i for i,v in enumerate(request) if v & 2)
            checked += 1
            for atomic in (False, True):
                a,b,refusal = admit_masks(accept, exclude, yes, no, atomic=atomic)
                expected = [1 << i for i,(ask, verified) in enumerate(zip(request,evidence,strict=True))
                            if ask and ask != verified]
                if atomic and expected:
                    assert (a,b,refusal) == (0,0,accept | exclude)
                else:
                    assert refusal == sum(expected)
                    assert a == sum(1 << i for i,(ask,verified) in enumerate(zip(request,evidence,strict=True))
                                    if ask == verified == 1)
                    assert b == sum(1 << i for i,(ask,verified) in enumerate(zip(request,evidence,strict=True))
                                    if ask == verified == 2)
    assert admit_masks(1, 0, 1, 1) == (0, 0, 1)
    raw = {"id":"msg","role":"a","accepts":["A"],"excludes":["B"]}
    verified = {"role":"a","accepts":["A"],"excludes":[]}
    claim, receipt = submit(raw,actor="a",receipt=verified,labels=labels)
    assert claim == {"id":"msg","role":"a","accepts":["A"],"excludes":[]}
    assert receipt["withheld"] == ["B"]
    for bad,ticket in [({**raw,"role":"b"},verified),(raw,{**verified,"role":"b"}),
                       ({**raw,"accepts":["A","A"]},verified),({**raw,"excludes":["Z"]},verified),
                       ({**raw,"rationale":"we should proceed"},verified)]:
        try:
            submit(bad,actor="a",receipt=ticket,labels=labels)
        except ValueError:
            continue
        raise AssertionError("Invalid envelope or mismatched receipt accepted")
    print(json.dumps({"enumerated_requests":checked,"policies":2,"malformed_rejected":5}))


if __name__ == "__main__":
    main()
