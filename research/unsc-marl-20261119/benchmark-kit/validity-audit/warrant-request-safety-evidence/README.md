# Check gains against every disclosure policy still compatible with the receipts

Start from grade-only planning. Use earlier public receipts to eliminate deterministic local disclosure tables that could not have produced them. The current receipts imply different sets of possible card types under each remaining partner model. For every possible request, compute the lowest conditional expected gain over the grade-only request across those possible type sets. The chair changes the request only when the lower bound is positive. [Locked protocol](protocol.md) · [Implementation](../warrant_request_safety.py)

The guarantee assumes that the partner uses one stable deterministic table, always sends a valid grade before independent erasures, and that the inventory prior is known. Under those conditions the actual table remains feasible, so its conditional expected net return on every changed request is at least that of the grade-only baseline. Individual realized outcomes can still be worse. The publication certificate remains independent of the inferred table and checks every grade-compatible world. [Direct enumeration and stable-condition audit](audit.json)

## Results

| Opening behavior | Grade-only | Four histories | Sixteen histories | True partner known |
| --- | ---: | ---: | ---: | ---: |
| Archived model-selected reports | 0.814646 | 0.816444 | 0.817642 | 0.817674 |
| Mixed synthetic team | 0.719475 | 0.722312 | 0.723668 | 0.728404 |
| Coordinate-search synthetic team | 0.879104 | 0.880810 | 0.882678 | 0.885444 |

The receiver improves all four model-disclosure conditions after 16 histories and reaches the known-partner mean in three. The mean gains are about 0.003 net over grade-only and 0.005 over the earlier blend on the same archived cases. In domain 0 it certifies more decisions. In domain 1 certification is unchanged and the receiver saves unnecessary requests. The numerical bound check independently enumerates a case where every surviving table supports stopping and saving the 0.14 expected request and reply cost. [All branch scores](results.json) · [Earlier blend and route comparison](../warrant-language-team-evidence/README.md)

A shift from mixed to coordinate partners can exclude the current true table. After four mixed histories, 30 of 768 histories produce a worse expected net than grade-only planning under the shifted team. After 16 mixed histories, three histories still regress. The stable-team guarantee does not extend to these conditions. The language replay reuses previously inspected model outputs. It changes the chair's inference and request decision, with exact follow-up and certification as before. [Shift tests](results.json)

## Replay

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python warrant_request_safety.py
OPENBLAS_NUM_THREADS=1 python warrant_request_safety_audit.py warrant-request-safety-evidence/results.json
```
