# Deploy trained desks with a live final writer

The same learned two-desk policy reverses its result when a frozen
Qwen3.5-4B chair writes the whole record. It beats the strongest
arrival-only policy on authored text by 2.57 utility points. On live
drafts it trails by 15.14 points. The learned policies, prices,
delivery probabilities, priors and receipt sets are identical
across both evaluations.

| Policy | Authored utility | Live utility | Live released /70 |
| --- | ---: | ---: | ---: |
| Both desks learned | 43.29 | −6.64 | 1.96 |
| Same sender with best arrival-only reply | 38.93 | −5.00 | 3.61 |
| Best arrival-only sender and reply | 40.72 | 8.50 | 8.50 |
| Best content-aware sender and reply | 43.32 | 8.50 | 8.50 |

Nine independent forward generations cover the nine possible delivered
receipt sets on Resolution 2721. All completed within both output caps.
The exact expectation integrates over the same 48 held combinations of
delivery probabilities and send prices as the original policy on this
docket, with equal mass on the Russia and African-members views. The
first desk chooses to send or withhold. The second selects a clause from
an observed receipt tag or silence. The optimally tuned arrival-only
control can change the sender and can reply differently on receipt and
silence while ignoring receipt identity. The content-aware oracle can
also condition on identity. Both oracles use the complete bank.

The chair states the consultation-versus-consent distinction in the
matched Russia branch. In the same record it changes encouragement to
consider an existing assessment into encouragement of an assessment,
which blocks release. The matched African-members draft says the
resolution “mandates” participation where the source recognizes its
necessity. Its closing sentence also misses the link between the
delegates' rationale and the adopted safeguard for UNAMA. Six of nine
drafts fail the factual guard. No branch releases relationship credit.
The best policies on live text withhold the first note at all 48 settings.

Counting raw coverage without the guard still leaves the trained pair
behind by 7.11 points on average and behind in every setting. Giving
full disposition credit for correctly reporting adoption and abstainers,
while retaining the factual guard, leaves the same 48 losses. These
are descriptive sensitivity checks with the frozen outputs.

The results favor testing constrained final-record realization before
training routing against these live rewards. A policy optimized on this
bank can improve its score by withholding information. The trial is one
exposed historical docket. The messages are registered public-source
excerpts, channel delivery is simulated, and grading is a single
same-assistant reading. Qwen weights are frozen. The results test policy
deployment with live generated finals under controlled delivery.

[Locked protocol](protocol.md) · [Exact outputs](verified.json) ·
[Evidence spans and grades](marks.json) · [Outcome replay](results.json) ·
[Scoring sensitivity](sensitivity.json) · [Worker receipt](evidence/launch.json)

From this directory in the existing Aurora Qwen runtime:

```bash
set -o pipefail
sha256sum -c scoring-lock.sha256
python -B collect_native.py plan | cmp plan.json -
python -B collect_native.py verify | cmp verified.json -
python -B score.py | cmp results.json -
python -B sensitivity.py | cmp sensitivity.json -
```

The nine model calls ran on an NVIDIA RTX PRO 6000 Blackwell Server
Edition. Token verification reuses the stored output and local tokenizer
and requires no GPU.
