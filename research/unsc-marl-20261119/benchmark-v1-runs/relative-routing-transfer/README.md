# Compare the two reply choices directly

A frozen relative-choice policy reached **40.565 net points** on both
the original and reworded Resolution 2417 cards. This is the exact peer
optimum under the registered writer and **1.108** points above best
arrival-only. Donor-trained probability calibration reached **40.359**
on the original wording and **40.403** on the reworded cards. It selected
the default temperature and abstention bias, so it reproduced the
unfitted probability policy. No gain from the fitted calibration was
measured.

| Peer routing method | Original 2417 cards | Reworded 2417 cards |
| --- | ---: | ---: |
| Previous donor-trained independent pair reads | 39.859 | 37.504 |
| Fixed conjunction of previous independent reads | 40.565 | 39.728 |
| Fixed word overlap | 39.728 | 39.728 |
| Direct relative choice, hard assignment | **40.565** | **40.565** |
| Direct relative choice, fitted probabilities | 40.359 | 40.403 |
| Exact arrival-only bound | 39.457 | 39.457 |

The new prompt shows both reply clauses and a neither option at once.
It uses each candidate letter equally. The fit reconstructs donor class
targets from simulated realized scores after both actions have been
observed for a donor view. It uses 11 views from Resolutions 2721, 2744,
2664 and 2739 and 256 trajectories per donor docket. Leave-one-docket-out
donor log loss chooses the calibration regularization. The fitted mean
comparison value is 17.67. The probability and hard policies use the same
value scale. The target pairing key is used only for downstream scoring.
The unavailable answer-key replay recovers the same fitted policies.

## Where relative choice fails

The letter-averaged model identified all three output choices for each
2417 wording panel. It got only **6 of 11** donor choices right and
correctly abstained on **1 of 4** fictional controls. An individual
label order happened to match all target choices and three controls.
The other two orders matched two target choices each, per panel. The
original target and its paraphrases share the same historical positions.
This is robustness to these wording changes on one exposed docket.
A stable first choice across labels can still be wrong. On the control
that turned the Netherlands' position into a demand for immediate
sanctions, all three orders picked the associated sanctions passage.

The simulator assumes public possible views, private realized view and
known channel and fees. The two choices are part of the reply desk's
declared menu. The result measures routing to registered evidence. It
does not license a speculative comparison for release. The fixed rule's
score demonstrates a better observation than the previous binary reads
on these cards. New-family transfer and independent final-record
review remain open.

Frozen Qwen3.5-4B used 63 first-token forward reads on an NVIDIA RTX
PRO 6000 Blackwell Server Edition, with 16,686 input tokens across the
fitting and target cases. No new generator fit was made. The held net
scores charge for sending and exclude inference fees. The audit checks
192 held target settings. Its initial Python import resolved the wrong
`calibrate` module. A path-based import corrected the audit without
changing model calls or policy outputs.

[Protocol](protocol.md) · [Verified model reads](verification.json) · [Fits and actions](fit.json) ·
[Score replay](results.json) · [Target-key and label-order audit](audit.json)

Use the project Aurora environment from this directory.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_logits.py verify | cmp verification.json -
python -B calibrate.py plan | cmp fit-plan.json -
python -B calibrate.py fit | cmp fit.json -
python -B calibrate.py score | cmp results.json -
python -B audit.py | cmp audit.json -
```
