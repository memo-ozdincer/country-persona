# Match the private inventory across public receipt states

Keep both private inventories and attempted opening sends fixed. Change
which opening messages reach the chair. A fixed chair target can still
signal something about the receipt state. If its card is already present,
the target becomes illegal and the request is suppressed. The responder
can distinguish silence and an addressed request, and can use either to
choose any card it holds.

The initial cross-inventory search finds candidate pairs under several
dockets and priors using globally optimized responders. The stronger
matched search lets each fixed responder optimize directly on the selected
states. It finds zero two-state witnesses. Across three public states,
the frozen learned policy beats every such fixed request in one UNIFIL
witness and one Myanmar witness, both under the asymmetric prior. The
other ten docket-by-prior rows have no qualifying three-state witness.
[Initial search](results.json) · [Matched pairs](matched.json) ·
[Matched triplets](triplets.json)

In both triplets the chair observes Brazil's card alone, China's alone,
or both in the UNIFIL case, with the corresponding source slots in
Myanmar. The learned team uses silence, a request for slot 1, and a
request for slot 3 respectively. These three signals allow different
responses with one held inventory. The best pair- or triplet-specific
fixed responder optimizes over its held inventory, its earlier send and
the heard target. It cannot observe the chair's receipt mask directly.
The chair's best fixed target may still convey two distinguishable
signals. Both fixed and learned policies can reply on silence.

The learned continuation earns 196 released points summed across the
three evenly weighted UNIFIL states. The strongest fixed continuation
earns 189. After query and reply costs the summed difference is 6.95,
or 2.32 points per state. The archived Myanmar score bank yields the
same result. These are selected, exposed receipt-state contrasts from
archived score banks. Follow-up delivery is forced successful and
opening costs cancel across arms.

## Reproduce

Use the project Python with NumPy and CPU Torch.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
python3 context_audit.py | cmp - results.json
python3 matched.py 2 | cmp - matched.json
python3 matched.py 3 | cmp - triplets.json
```
