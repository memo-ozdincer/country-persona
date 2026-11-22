# Keep the verified decision and official record fixed

The previous writer could discard a correct workshop certificate or
change the reason a draft failed while paraphrasing it. This crossover
keeps the decision line, official history, option wording and authority
limit fixed. The first arm allows frozen Qwen3.5-4B to write only a
paragraph about the mandates the chair received. The second copies the
authenticated mandate text into the same layout.

The four pairs reuse the previous Iraq and Syria worlds and their
selected options. The one-report prompts are identical within each
family and are run once. Six physical calls therefore produce eight
logical paragraphs. All six complete. Generated paragraphs take 22–39
words against 45–50 available, with every assembled record under the
frozen 150-word cap.
[Protocol](protocol.md) · [Immutable text, allowed words and requests](plan.json)

| Writer | One mandate, released /280 | Two mandates, released /280 | Full-credit records with both mandates |
| --- | ---: | ---: | ---: |
| Original free writer | 56 | 28 | 0/4 |
| Protected record, generated mandate paragraph | 224 | 266 | 3/4 |
| Protected record, literal mandates | 224 | 280 | 4/4 |

The reviewer credits all sixteen protected records with source-safe
release. The fixed history preserves the actual Council outcomes,
including the distinct reasons for failure of the two Syria drafts.
The additional mandated position adds 14 points in three of four
generated records and in all four literal records. The generated
Syria impasse-alternate paragraph says both roles have a “duration
constraint” without saying that each requires six months. The literal
paragraph preserves both values. In the one-report arms, positions
remain incomplete because the second mandate is absent.
[All final texts](deck.json) · [Exact-span judgments](marks.json) · [Frozen rubric scores](scores.json)

The prior writer produced the complete record natively. The protected
method supplies the audited official and package text directly and
sets a narrow task for any language generation. The literal control
requires authenticated, typed-compatible cards. The experiment uses
exposed workshop variants, with assistant-authored judgments and no
new judge or training calls.

## Use released-record points when a decision is already warranted

Freeze the nominal-fee opening choices from the earlier fitted value
function. Change the second desk's action only after proof arrives and
when it holds the matching card. Fit the marginal documentary reward
on Iraq and apply it on Syria, and repeat in the other direction.
Rewards use released points divided by 70, publicly weighted by docket
priority. Transport and report fees are simulated, and unchanged
branches cancel. All comparisons below are gains over always waiting
after proof, averaged over the same 48 held availability settings at
0.06 per attempted report.

| Writer | Fitted follower | Fixed 14-point value for a missing position | Exact archived-grade optimum |
| --- | ---: | ---: | ---: |
| Original free writer | 0.000000 | −0.018713 | 0.000000 |
| Protected record, generated mandate paragraph | +0.008533 | +0.009467 | +0.011362 |
| Protected record, literal mandates | +0.014517 | +0.014517 | +0.014517 |

With the protected literal record, the second report always recovers 14 points out of 70. The fit
learns that increment from the other workshop and ties the fixed rule
at all four prices. With the scoped writer, the increment varies. The
fit leaves useful reports unsent at the training fee and loses net
against waiting at 0.15 and 0.25. The variation comes from whether the generated paragraph states the actual mandate. These are conditional
marginal replays on two known event families, without fresh
deliberation runs or decoder training.
[Reward protocol](reward-replay-protocol.md) · [Release banks and branch replays](reward-replay.json)

## Verify

The six physical calls used NVIDIA RTX PRO 6000 Blackwell Server
Edition and the unchanged Qwen3.5-4B checkpoint. The launch records
the actual four workshop IDs. The replay validates the locked prompts,
token traces, source quotes and arithmetic without regenerating text.
[Launch receipt](evidence/launch.json) · [Raw model paragraphs](evidence/calls.jsonl)

Run in the project Python environment:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
python protected.py plan | cmp plan.json -
python protected.py deck | cmp deck.json -
python score.py judge-deck | cmp judge-deck.json -
python score.py score | cmp scores.json -
python reward_replay.py | cmp reward-replay.json -
```
