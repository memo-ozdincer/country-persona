# Frozen v1 baseline on the Syria workshop pair

The benchmark's exact prompts ran with frozen Qwen3.5-4B. The comparison
covers both fictional mandate variants, both speaker orders and all
three v1 arms. All 12 episodes have the two note calls and one final
call prescribed by v1, with 32 physical calls after sharing four
openings. The collection was on one NVIDIA RTX PRO 6000 Blackwell
Server Edition with no optimizer updates.
[Protocol](protocol.md) · [Launch receipt](evidence/launch.json) · [Token and request verification](verification.json)

| Arm | Exact final decisions /4 | Notes certify the key /4 | Both requirements recover key if treated as complete /4 | Released points /280 |
| --- | ---: | ---: | ---: | ---: |
| Independent drafts | 0 | 2 | 4 | 0 |
| Peer-informed | 0 | 2 | 3 | 0 |
| Pooled solo | 0 | 2 | 4 | 56 |

**The peer arm introduced two different failures in the overlap case.**
With Brazil first, the UK echoed Package A and also said it required an
additional checkpoint. A uses ordinary reporting. The public ledger
flags the UK endorsement and its exclusion of A as contradictory. With
the UK first, Brazil echoed the checkpoint note and omitted its own
nine-month requirement. The independent notes preserved both requirements
in both orders. Package B follows if those requirements are treated as
the complete fictional constraints. The strict ledger needs explicit
positive compatibility on both sides and leaves those independent
overlap episodes unresolved. [Notes and exact-span marks](notes-marks.json)

**The final writer missed all six impasse decisions.** Each pair of
working notes identifies incompatible required durations, which is
enough to exclude every option even though no joint agreement is
asserted. Every final still starts with `Decision: UNRESOLVED`.
One peer final also invents a UK proposal of the nine-month Package B.
The other identifies the conflict in prose and reaches 168 words against
a 150-word cap. Both pooled finals explain the conflict and preserve the
fictional scope. Both use the wrong first-line decision. A mechanical
outcome score and a prose coverage score expose different failures.
[Masked finals](final-packets.json) · [Anchored final review](final-marks.json) · [Episode scores](results.json)

The masked packets separate annotation from arm IDs. The same assistant
authored the marks, and no independent semantic judge ran. The notes
diagnostic checks quote-backed requirements and explicit endorsements.
The strict readout uses only those observations. Private cards enter
only during the environment audit of truth and the answer key. The
requirements-only column is a deliberately stronger assumption about the
completeness of disclosed requirements. It can recover the answer even
when an explicit endorsement conflicts with it.

The overlap runs give a concrete training target for a responder that
sees an earlier proposal. Preserve a truthful own requirement and
withhold endorsement when the visible proposal violates it. The impasse
runs also give a separate chair target when the constraints already
exclude all options. Use these separate endpoints before attributing a
terminal failure to the communication policy. This one exposed
family measures the frozen baseline.

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
python collect.py verify evidence | cmp verification.json
python review.py notes | cmp notes-packets.json
python review.py finals | cmp final-packets.json
python review.py score | cmp results.json
```
