# Transfer the shared-phrase writer to Resolution 2553

**The generated phrase exposed a six-point joint reward in both positive
orders.** The model supplied “about rushed negotiations” when it received
the UK and German negotiation cards. The template supplies the two
owners and the claim that they shared a concern. The exact pair gate
retained that comparison and rejected three unsupported candidates
generated from other authentic pairs. [Scored records and grades](scores.json)
· [Source locators and UNBench join](../provenance.json)

| Evidence and order | Fixed facts /70 | Two-delegation gate /70 | Exact pair gate /70 |
| --- | ---: | ---: | ---: |
| Negotiation statements, UK first | 31 | 37 | 37 |
| Negotiation statements, Germany first | 31 | 37 | 37 |
| UK negotiation and German Fund governance, UK first | 33 | 33 | 33 |
| UK negotiation and German Fund governance, Germany first | 33 | 0 | 33 |
| German and Belgian funding statements, Germany first | 31 | 0 | 31 |
| German and Belgian funding statements, Belgium first | 31 | 0 | 31 |
| UK alone | 26 | 26 | 26 |

A mere identity check permits the unsupported claims because both
cards belong to bona fide delegates. One crossed order asserts a
common concern about “the process” with only one negotiation card.
Both funding orders assert that Belgium and Germany “both raised
concerns about funding.” The visible statements support Belgium's
case for predictable funding and Germany's statement about management
authority, with no joint concern expressed. The assistant guard treats
that assertion as material. Reading it as a loose topic label would
retain the 31 standalone points. It would still earn no shared-process
credit.

## What the reward teaches the receiving desk

Germany can reply with its 5-point process card or its 7-point Fund
card. The first desk's UK concern either arrives or is lost. Fit the
reply choice on one fixed 64-exchange exploratory history for each
reward regime. The actions and delivery draws are the same. With the
standalone composer the reply fit always chooses the higher-value Fund
card. With the exact pair gate, it chooses the process card after the
UK negotiation card arrives and the Fund card otherwise.

| Scoring regime or control | Mean released /70 over 18 held transport settings |
| --- | ---: |
| Standalone, fitted | 28.817 |
| Exact pair gate, always process | 30.107 |
| Exact pair gate, always Fund | 28.817 |
| Exact pair gate, fitted or exhaustive | 30.632 |
| Two-delegation gate, fitted | 30.632 |
| Two-delegation gate, always Fund | 21.328 |

The weak gate happens to fit the same reply choices because the selected
path avoids the unsafe branch. Its worse always-Fund result shows what
happens when the party or the partner policy changes the branch mix.
The exact gate protects the fallback under those off-policy choices.
The available UK message contains a known topic, so this test measures
conditioning on arrival of that message. General text-based choice
under unfamiliar messages remains open. [Training and held outcomes](reply-fit.json)

The interface carries forward the short-phrase design from Resolution
2739 and changes the requested relation and phrase prefix. Card texts
are pre-existing, source-located paraphrases. The target was previously
exposed in other project experiments. The exact gate supplies a
case-specific relation pair, and the assistant supplies the grades.
There were seven frozen Qwen3.5-4B calls using 1,193 input and 22 output
tokens on Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition.
All calls completed and replayed exactly. No model weights changed.
The fitted reply policies use simulated delivery and archived rewards.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B concern_study.py plan | cmp plan.json -
"$python" -B concern_study.py verify | cmp verified.json -
"$python" -B annotate.py | cmp marks.json -
"$python" -B score_concern.py | cmp scores.json -
"$python" -B reply_fit.py | cmp reply-fit.json -
```

[Protocol](protocol.md) · [Exact saved replies](verified.json)
