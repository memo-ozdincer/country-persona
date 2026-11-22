# Follow the adaptive recipient through to a final record

Use outer-space reserve grid 198, where the learned recipient
improved the balanced workshop and regressed under uniform worlds.
The policies share an opener, chair, delivery branches and exact
verifier. Their messages produce 17 distinct chair inputs.
The inputs differ on 45.64% of balanced trajectories and 46.00%
of uniform trajectories. Every distinct input is scored, including
ones that lead to the same certified disposition.

The decision heading, two official April vote passages and the
fictional scope sentence are held fixed. The source context is
linked to the archived UNBench drafts and the UNSC-Bench vetoed
April draft. Neither model prompts nor the literal rendering
include an actual hidden grade. The writer sees received grades
and the structured summary of all compatible completions.
[Protocol](protocol.md) · [Trajectory and prompt lock](plan.json) · [Final rubric](rubric.json)

## Paired documentary results

| Writer and policy | Released /70 | Settled release /70 |
| --- | ---: | ---: |
| Literal, fixed recipient | 70.000 | 54.653 |
| Literal, always use learned ranking | 70.000 | 54.630 |
| Literal, adapt from 32 observations | 70.000 | 55.184 |
| Scoped Qwen, any of the three policies | 0.000 | 0.000 |

These are exact means using equal weight for the two regimes.
Released points reward a faithful unresolved record when evidence is
insufficient. Settled release counts those points only when the
verifier establishes a package or impasse. All literal records
earn full documentary credit regardless of the status. At the same
message cost, adaptation improves settled release by 0.531 points.
Relative to fixed, the unconditional rank adds 1.215 settled points
in balanced worlds and loses 1.260 under uniform worlds. The history
switch uses the rank with probability 94.19% under balanced worlds
and 6.49% under uniform worlds, as in the previous exact replay.

The fixed historical passages keep the vote tally and permanent-member
veto intact. Generated workshop rationales still change the meaning
of the proof. One claims that zero compatible completions exist
despite a uniquely supported impasse. Another reverses the ordering
of grades one and two. In a third, the model conflates package C losing
with being infeasible. Across the 17 generated rationales, 15 fail
the source guard, one is uncertain and one passes the guard with a
capped response. Every record receives explicit, same-assistant
judgments with quote checks. These grades are diagnostic evidence
from one exposed simulated world family.
[All records](deck.json) · [Judgments](marks.json) · [Exact paired replay](replay.json)

## Reduce the proof to verified outcome counts

The paired policy comparison has exactly two trajectories that
switch between settled and unresolved status. One moves from an
unresolved result to an impasse with the rank policy. The other
moves from a warranted A to unresolved. Both trajectories occur
under both priors, with different probabilities.

The follow-up selects all four endpoint views of those
trajectories. It fixes the grade ownership and ranking rule in the
final text and asks Qwen to explain the counts of compatible
outcomes in at most 30 words. Three of four earn 70. The pivotal
impasse says both completions yield impasse, then concludes that
“no feasible disposition exists.” The grade is uncertain because
that can mean either no feasible package or no warranted
disposition. A source-safe rendering distinguishes those claims
explicitly.

On these pivotal trajectories, the stricter grade turns the
adaptive policy's literal +0.531 settled-point gain into −0.845
with the tally writer. The missing impasse release removes the
positive branch. The negative branch still releases the fixed
recipient's warranted A. If the ambiguous impasse wording were
read as meaning no feasible package and given full credit, the
tally result for these trajectories would equal the literal
result. These four calls test the pivotal contribution alone.
The run leaves the tally writer's outcomes on the other 13
receipt views unmeasured.
[Follow-up protocol](tally/protocol.md) · [Tally inputs and paragraphs](tally/deck.json) ·
[Judgments](tally/marks.json) · [Paired contribution](tally/scores.json)

## Verify

The two runs generate 21 native paragraphs using frozen Qwen3.5-4B
and NVIDIA RTX PRO 6000 Blackwell Server Edition. The launch receipts include
each owned PID, start time and the correct run roster.
[Main launch](evidence/launch.json) · [Tally launch](tally/evidence/launch.json) ·
[Replay correction](tally/preparation.md)

Use the project Python environment in this directory:

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python memo.py plan | cmp plan.json -
python memo.py deck | cmp deck.json -
python score.py score | cmp scores.json -
python score.py replay | cmp replay.json -
python tally.py plan | cmp tally/plan.json -
python tally.py deck | cmp tally/deck.json -
python tally_score.py | cmp tally/scores.json -
```
