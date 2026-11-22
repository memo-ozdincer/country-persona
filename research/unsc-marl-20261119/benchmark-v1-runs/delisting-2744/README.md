# Test the delivery-value learner on a new 2744 docket

The delivery-value team matched the content-aware oracle in **96 of
96 held settings** on Resolution 2744. It beat the strongest
arrival-only control in **80 settings** and tied it in the other 16.
The frozen source verifier recovered both authored comparisons,
declined the other four genuine receipt pairs, and rejected four
marked fictional reversals.

| Policy on 2744 | Mean utility |
| --- | ---: |
| Delivery-value sender and learned reply | **40.565** |
| Sampled joint policy gradient, matched query budget | 40.391 |
| Best arrival-only sender and reply | 39.457 |
| Learned sender with fixed first document reply | 37.513 |
| Content-aware oracle with the same observation | **40.565** |

The locked task separates Malta's account of how reports inform
committee decisions from the A3+ preference for a time-bound review.
On Malta's note, the relevant Annex I passage preserves the Focal
Point's factual reporting role and the committee's authority to
decide. With the A3+ note, the relevant adopted distinction is the
Council's intention to review the mechanism continuously. Switzerland's
comparison to the Ombudsperson remains a standalone attributed
position. A matched note and document produce 70 under the authored
pilot rubric. Other complete pairs produce 52. The renderer includes
only the delivered statements and any admitted relation. [Meeting record,
pp. 2–5](https://digitallibrary.un.org/record/4054820) ·
[Resolution 2744, paras. 1–5 and Annex I](https://digitallibrary.un.org/record/4054837)

This docket was selected after the AUSSOM candidate was found in
earlier project material. The pre-run search found no prior authored
case for the 2744 decision in the benchmark research files. The
pinned UNBench copy puts event 2545's 15 roll-call rows in the author
test split. The draft, date and vote match the official record. The
pinned UNSC-Bench adopted table has no matching entry among 258
rows. The case is new to this experimental series. The sources
are public and model pretraining exposure is unknown.
[Dataset join and pinned files](provenance.json)

The sender and responder train from scratch for 512 updates per arm
using Qwen-derived relation rewards. The sampled control uses double
the episode batch to match the value learner's two scores per sampled
context. Both use the same seed, channel schedule, held price grid and
local observations. The companion training slot repeats 2664 solely
because the existing training code expects two dockets. Policy
parameters are separate by docket. The report's internal field
`archival_fit` contains the newly trained sampled control. The
oracle enumerates reply mappings and optimizes the sender with the
same binary receive signal. The arrival-only control also optimizes
the sender and can distinguish receipt from silence. On 2744,
arrival alone no longer identifies the best document.

The rubric uses project-authored 30/12/10/18 weights for public,
delegate, document and relationship coverage. Those are experimental
payoffs. The A3+ source card says it “urged” effective implementation
where the transcript expresses hope that continuous review will be
fully implemented. The scored distinction is its explicit desire
for a time-bound review, which is unchanged by that paraphrase.
The four fictional foils were labeled as such in their text, which
could cue abstention. They were excluded from training and are
reported separately from the real crossed pairs. The benchmark still
needs independent scoring and native drafting. These outcome-table
rollouts do not measure free-text deliberation.

The 28 first-token label reads ran on an eight-thread AMD EPYC 9575F
64-Core Processor worker on Aurora. The frozen Qwen weights and
v1.6 benchmark remain unchanged. Earlier native drafting trials used
NVIDIA RTX PRO 6000 Blackwell Server Edition.

[Case and source locators](case.json) · [Locked prompts](plan.json) ·
[Stored token replay](verified.json) · [Final records and joint training](results.json) ·
[Protocol](protocol.md) · [Worker receipt](evidence-cpu/launch.json)

Use the existing source-audit environment for `provenance.py` and the
Aurora Qwen environment for the other commands. Verification uses the
tokenizer and stored evidence.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect_delisting.py plan | cmp plan.json -
python -B collect_delisting.py verify | cmp verified.json -
python -B fit_delisting.py | cmp results.json -
```
