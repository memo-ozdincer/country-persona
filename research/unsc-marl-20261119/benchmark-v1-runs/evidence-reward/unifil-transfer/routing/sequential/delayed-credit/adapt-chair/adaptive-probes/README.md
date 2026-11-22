# Learn a stable partner's availability from prior replies

The adaptive policy chooses which role to probe next or when to
stop. It uses the current receipt posterior, the number of
expected future dialogues and a two-probe cap per role. To avoid
using the held outcomes for policy selection, it values future
dialogues on 4,096 synthetic opening-world presentations.
The final test uses the 768 UNIFIL presentations and four known
profile possibilities, plus one profile outside the prior.
[Protocol](protocol.md) · [All probe and deployment returns](probe.json)

| Stable deployment horizon | No probes | One probe per role | Two probes per role | Adaptive probing |
| ---: | ---: | ---: | ---: | ---: |
| 1 dialogue | 0.335 | 0.233 | 0.120 | 0.335 |
| 5 dialogues | 1.675 | 1.642 | 1.557 | 1.688 |
| 20 dialogues | 6.699 | 6.925 | 6.946 | 7.016 |
| 100 dialogues | 33.493 | 35.101 | 35.686 | 35.802 |

The table is the prior-weighted total normalized net after
acknowledgment fees. For one dialogue the policy stops without
probing. At five it probes Desk Two once. At twenty it still probes
Desk Two first, with expected total requests of 2.20 to 3.00 across
the four profiles. It improves by 1.083 over no probes when Desk Two
is absent. The same learned policy trails no probes when both roles
are available or both are rarely available. Outside the prior, the
adaptive policy loses 0.065 at twenty and gains 0.235 at one hundred.
These are stable-partner rollouts, with a public channel rate of 0.80
and exact inference about the declared profile set.

## Use a receipt from an ordinary question

The prior-only chair issues 494 last-slot questions across the
768 held states. On 224, every possible role requirement makes
sending worthwhile. On the other questions, a silent role may be
unwilling to send even when present. Hold the initial question and
its cost fixed across policies. Update future routing from the
receipt alone by conditioning on predicted public willingness, by
updating only on the 224 unambiguous questions, or by assuming
every asked role would have sent.

| Actual availability | Update only on certain sends | Condition on public willingness | Assume mandatory replies |
| --- | ---: | ---: | ---: |
| Both available | −0.000663 | −0.000885 | −0.002387 |
| Desk One absent | +0.005324 | +0.007189 | +0.009237 |
| Desk Two absent | +0.013601 | +0.025516 | +0.024125 |
| Both rarely available | −0.001646 | −0.002054 | −0.003733 |
| Outside prior support | −0.000358 | −0.001693 | −0.001957 |

These are changes in expected normalized net **per future dialogue**
relative to retaining the prior. The updater that uses public
willingness gains 0.00744 per dialogue on the four-profile prior
average, compared with 0.00681 under a mandatory-reply assumption.
For an actual absent Desk Two it gains 0.02552. When both are
available or both are rarely available, even cost-free observations
can move the posterior to a worse policy. The outside-prior result
also reverses the expected gain. The passive evaluation replays
one initial final-slot decision per partner, with no policy change
to that question, and models delivery. It does not record a new
live acknowledgment. The first script attempt could not write the
result because its receipt path variable was missing. The corrected
run also makes the naive arm update after every asked question,
including those where no candidate would send.
[Ordinary receipt protocol](passive-protocol.md) · [Receipt-conditioned replay](passive.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 probe.py | cmp - probe.json
python3 passive.py | cmp - passive.json
```
