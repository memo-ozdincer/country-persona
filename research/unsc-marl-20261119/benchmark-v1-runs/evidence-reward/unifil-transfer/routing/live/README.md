# Run the selected UNIFIL questions with a live responder

The frozen learned router asks two extra questions at 0.80 delivery.
The exact record-aware router remains silent in both public states.
To check the reply mechanism, also query two matching productive
controls, one affirmative and one negative. The four calls use
three distinct model prompts because the two unnecessary questions
are identical from the responding delegate's view. The chair's public
histories differ, and the delegate sees only its local note and
the queried option. The locked payloads supply the option description as the menu evidence. Each local requirement is written in prose.
[Locked selection and prompt protocol](protocol.md) · [Actual calls](evidence/records.jsonl)

| Question | Observed sign | Released points before → after | Expected net at 0.80 |
| --- | --- | ---: | ---: |
| Extra impasse query 1 | Y | 56 → 56 | −0.075 |
| Extra impasse query 2 | Y | 56 → 56 | −0.075 |
| Productive agreement control | Y | 0 → 56 | +0.565 |
| Productive impasse control | N | 0 → 56 | +0.565 |

All four replies complete and agree with the corresponding private
role requirement. Each is incorporated into the public record only
after validation. A correct reply can be unnecessary. In the two
extra queries the added sign identifies one role's requirement,
while the other role's requirement remains ambiguous, so neither
reply earns the joint attribution item. The two productive signs
certify decisions. Their unchanged deterministic wording reuses
the matching same-assistant verdict with a quote checked against
each current public log. The first attempt to copy those marks
shared mutable quote fields across records, and the citation
validator caught it. Per-record copying corrects the marks and all
quotes replay.
[Before and after deck](deck.json) · [Scored live outcomes](results.json)

The model used NVIDIA RTX PRO 6000 Blackwell Server Edition, with
zero updates. All four raw replies and their native prompt and token
traces replay. The openings and policies are archived, and the
loss rate remains modeled. This is a diagnostic of actual delegate
signs in selected contexts and does not measure full live dialogue
or country alignment.
[Launch record](evidence/launch.json) · [Verification](verification.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python live.py deck | cmp - requests.json
python verify.py | cmp - verification.json
python score.py deck | cmp - deck.json
python score.py score | cmp - results.json
```
