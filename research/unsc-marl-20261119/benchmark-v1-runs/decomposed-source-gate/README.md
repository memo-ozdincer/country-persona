# Check the two necessary claims independently

Splitting the evidence check fixes the objection-only failure on
Resolution 2739. It also drops the valid A3+ timing claim on Resolution
2744. The two cases need different improvements to the verifier.

| Fixed-policy replay | Prior verifier | Split claims | Best arrival-only with split claims |
| --- | ---: | ---: | ---: |
| 2739 paraphrased, lower prices | 35.404 | **40.036** | 39.724 |
| 2739 paraphrased, original prices | 31.804 | 35.958 | **37.772** |
| 2744 canonical | 40.565 | 39.039 | **39.457** |

On 2739, the prior verifier gave the objection-only paraphrase a
+0.500 margin on the combined claim. The split verifier gives
−3.375 for endorsement of continued reporting and +3.875 for the
reason for abstaining. The reporting-only foil supplies the opposite
pattern, +2.500 and −3.688, and also falls back. Both complete
phrasings clear both requirements. The corrected vote-only
attribution clears neither. All six 2739 cases match the locked key.
The restored low-price policy wins 80 of 96 conditions and still
overspends on the original price grid.

On 2744, the group says a time-bound review would have been useful
in both source phrasings. The new timing claim scores −0.563 on the
original and −0.875 on the source-faithful version. The endorsement
of implementing continuous review scores +3.313 and +2.875.
Both complete notes lose the relationship credit. The three
other notes, including the fictional rejection of the quoted
preference, correctly fail the combined gate. The canonical
timing-label margins are −1.875 and +0.750. Label orientation
still matters even when the proposition is checked individually.

Each claim uses the same two label orders. Its margin is their
mean, and the smaller of the two claim margins decides whether
the opening supports the comparison. Splitting adds two logical
label queries per checked source. The worker completed 44 label
queries with 9,442 input tokens on an eight-thread AMD EPYC
9575F 64-Core Processor. The table includes the original
simulation's channel cost. It excludes source-verifier compute.

The 2739 replay changes only the early claim labels. The vote-only
fragment remains archived in the original-input arm and uses the
full attribution in the updated arm. The 2744 source-faithful
replay substitutes the corresponding verification signal and keeps
the reward rubric fixed. Late-source checks, other relation checks
and policies come from their previous runs. This is one frozen
checkpoint on two exposed dockets. Native free-form synthesis and
transfer to unseen families remain outside the experiment.

[Locked protocol](protocol.md) · [Exact prompts](plan.json) ·
[Worker receipt](evidence/launch.json) · [Verified labels](verified.json) ·
[Claim margins and policy replay](results.json)

Run from this directory using the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B probe.py plan | cmp plan.json -
python -B probe.py verify | cmp verified.json -
python -B probe.py score | cmp results.json -
```
