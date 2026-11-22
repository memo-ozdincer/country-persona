# Execute a selected live UNIFIL routing contrast

The historical docket is France's draft S/2023/641, adopted as
resolution 2695 (2023). The supplied record distinguishes UNIFIL's
mandated independence from continued coordination with Lebanon.
The Brazil and China cards give a point of overlap and a difference
in how they assessed the text. Russia's card gives its own explanation
for abstaining. [UN meeting record](https://digitallibrary.un.org/record/4020309) ·
[Adopted resolution](https://digitallibrary.un.org/record/4020194?ln=en)

Use the frozen dense chair and recipient chosen by the four-score
quality selector for the asymmetric inventory law. Select the first
ideal-delivery inventory pair where the learned query improves the
record against both optimized no-request and query erasure. The
opening replies are shared across policy arms. Models receive only the
addressed source block, public mask and the question received. A
returned quote must exactly match the assigned source packet. The
compiler combines admitted quotes with a short public record. The
learned parameters route which source to request and reply with.
Qwen's role is to transmit the selected source text.

The selected inventory has 0.2952% mass under its stipulated prior.
In the all-delivered enumeration, it is the only inventory pair
with a quality gain over the calibrated fixed policy. Averaged over
the entire prior under that delivery assumption, expected released
points improve by 0.02067 and cost rises by 0.03443. This offsets the
quality gain on net. The selected native run demonstrates mechanism
and source retention. The broader comparisons retain the original
simulated loss model. [Prospective plan](plan.json) ·
[All-delivered prior replay](modeled-frequency.json)

## Original strict receipt gate

Four native calls copy the assigned passages, but only the Brazil
opener returns the exact requested card ID. Other calls return the
source text or a capitalized name in the card field. The strict
gate therefore leaves only Brazil's card public. The learned
policy does not make the intended Russia request from that state.
All four records release 42/70, with clear source guards. The
calibrated fixed rule spends an additional 0.05 on a China
question that also fails the strict receipt gate. The strict
result remains in the archive.

The first score replay encountered an import name collision with
an earlier live script. The reviewer now loads this run with an
explicit module name. This does not change the native requests
or replies. [Native trace](evidence/trace.jsonl) · [Scores](results.json) ·
[Token replay](verification.json)

The [source-bound follow-up control](scoped-card/README.md) restores
the intended Russia request from the same opening generations.
An exact 168-word composition fails the cap. A separate compact
123-word rendering scores 70/70, versus 63/70 for query erasure,
no request and the calibrated fixed arm. A fixed request explicitly
for Russia produces the identical record and cost using the exact
same native reply. The witness distinguishes receiving the relevant
request from erasure with the same charge, while leaving learned
routing and that directly matched fixed request tied.

Replay with the project Python, NumPy, Torch, Jinja and tokenizers.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
python3 live.py plan | cmp - plan.json
python3 review_witness_run.py verify | cmp - verification.json
python3 review_witness_run.py score | cmp - results.json
python3 frequency.py | cmp - modeled-frequency.json
cd scoped-card
python3 scoped.py plan | cmp - plan.json
python3 scoped_review.py verify | cmp - verification.json
python3 scoped_review.py score | cmp - results.json
python3 scoped_review.py score --compact | cmp - compact-scores/results.json
python3 scoped_review.py alternative --compact | cmp - compact-scores/alternative.json
```
