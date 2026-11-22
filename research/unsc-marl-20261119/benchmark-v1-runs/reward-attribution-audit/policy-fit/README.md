# Train a team on message effects that agree across writers

The agreement update transfers better than the nominal single-writer update on every archived free-form variant. It still trails the fixed standalone-credit policy on each of the three source-preserving variants. The two folds train separately on one exposed UN docket and replay on the other.

Three delegates simultaneously choose whether to send an available note. Each pays the modeled fee for a send. The trainer enumerates independent link delivery and the other delegates' stochastic actions. It computes the change in net team score from sending. In the agreement arm, each actor's update uses the endpoint nearest zero when the interval across writers and grades has a strict sign. An interval containing zero contributes no actor update. At deployment the delegate uses only its standalone credit, the link rate, the send fee and the frozen three shared coefficients. The source-scoped reference supplies standalone credit in all arms, including the fixed rule. [Protocol](protocol.md) · [Source audit](../README.md) · [Frozen inputs](plan.json)

| Trained → tested | Held writer | Fixed | Nominal fit | Agreement fit | Count-matched threshold |
| --- | --- | ---: | ---: | ---: | ---: |
| 2475 → 2686 | Original free-form | 5.963 | −3.797 | 16.665 | 11.006 |
| 2475 → 2686 | Revised free-form | −2.626 | −8.483 | 1.843 | −0.263 |
| 2475 → 2686 | Scoped rewrites | 31.201 | 30.460 | 26.150 | 29.852 |
| 2475 → 2686 | Verbatim | 35.204 | 35.010 | 30.700 | 33.702 |
| 2686 → 2475 | Restored notes, verbatim | 36.938 | 21.000 | 36.675 | 36.675 |
| 2686 → 2475 | Restored notes, plain comparison | 20.347 | 21.000 | 25.946 | 25.946 |
| 2686 → 2475 | Restored notes, scoped comparison | 17.961 | 21.000 | 24.613 | 24.613 |

Values are mean released points minus send fees over the same 16 held scenes for each writer. The agreement update retains 24 of 48 actor terms at the end of the 2475 fit and 11 of 48 on 2686. The nominal fit retains 48 in each. Independent calculation over the send and receipt masks verifies each greedy result and the writer-aware ceiling. A finite-difference check verifies the nominal gradient on one training scene per fold. [Training traces, actions and scores](results.json)

The dependent volume control raises the common standalone send threshold until the number of training sends matches the agreement fit. On the 2686-to-2475 fold, it reproduces all agreement actions on the held case and ties all held scores. In the reverse direction, it sends 29 notes on the held scenes to the agreement fit's 32. The agreement fit still leads it on both free-form writers and loses on both source-preserving writers. Training send counts match exactly. This makes the control a test of a transferable volume adjustment, with held volume itself still different in one fold. [Volume calibration and replay](volume-results.json)

The source-preserving writers deliver the highest absolute held scores. A policy fit that avoids bad drafts can therefore improve a weak writer's net reward while underusing evidence with a stronger writer. These are replays of same-assistant archive grades, two case families and modeled delivery costs. They involve no new drafting or language-model weight updates.

## Reproduce

```sh
set -o pipefail
python3 -B fit.py plan | cmp plan.json -
python3 -B fit.py run | cmp results.json -
python3 -B volume_audit.py | cmp volume-results.json -
```
