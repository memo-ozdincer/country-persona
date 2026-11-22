# Documentary routing under reply rejection

The chair and responder learn seven shared action weights on three archived training dossiers and 27 authored receipt-value profiles. The clean and robust fits start with the same parameters, opening decisions and documentary rewards and each run 240 exact joint-return updates. The robust fit sees varying probabilities of reply rejection based on the physical request and the selected authorized card. A rejected attempt incurs its cost without changing the chair's receipt state. Both actors act on their own observations and public operating assumptions. [Locked setup](protocol.md) · [Learning and evaluation code](../facilitator_channel_fit.py)

The clean fit reproduces the archived weights within numerical tolerance. The robustness fit improves its training objective but sends zero requests in all 28 evaluated cells. Its evaluated scores equal the independent comparator. This is useful protection against the language failure and discards the clean channel's coordination gains. The exact public adaptive planner, which uses the same estimated reliability, sometimes retains small improvements under the authored noise profiles. On measured Resolution 2593 with the question visible, independence lies within 0.034 points on average of the exact planner with actual admission. That upper bound uses the same opening decisions and cannot be used at deployment. [Policies, score distributions and learning traces](results.json) · [Independent enumeration](audit.json)

| Channel | Original clean fit | Robust fit | Independent | Conservative selector | Selector with wrong declaration |
| --- | ---: | ---: | ---: | ---: | ---: |
| Four archival banks, clean | 49.593 | 49.231 | 49.231 | 49.593 | 49.231 |
| Same banks, simulated fallback rejection | 48.360 | 49.231 | 49.231 | 49.231 | 48.360 |
| Same banks, simulated topic asymmetry | 47.277 | 48.778 | 48.778 | 48.778 | 47.277 |
| Resolution 2593, source-only replies | 58.073 | 57.534 | 57.534 | 58.081 | 57.534 |
| Resolution 2593, question-visible replies | 52.148 | 57.534 | 57.534 | 57.534 | 53.591 |

These are mean **net objectives**, which combine final-record points, a 21-point completion bonus and message fees. Average each bank and prior equally within the three archival rows and average the two priors within each Resolution 2593 row. Raw material and completion probabilities are also archived. The observed matrix is the previously measured set of admitted replies, and all other noisy tables are authored stress conditions. The same cached replies serve both measured priors.

The selector was added after inspecting the robust policy. It chooses among independent delivery, the clean fit, the robust fit and the initial action rule with channel-aware features. It requires positive projected uplift above independence across the declared noisy profile and two plausible adverse channels before sending requests. It uses the public receipt rubric when comparing plans. On the measured question-visible channel, selection by mean projected score alone sends some uniform-prior requests and loses 1.292 points to independence in that cell. The conservative selector abstains on both priors. It keeps the better of the clean fit and the initial rule on the source-only branches. A wrong clean declaration removes much of the protection. The test establishes sensitivity to a public deployment assumption, with no learned channel identification. [Selector implementation](../facilitator_channel_select.py) · [Per-family choices and wrong-declaration controls](selection.json)

The original fit and robust fit concern documentary transport with archived scoring or a fixed renderer. Evaluation adds no newly generated discussions. Treat gains as routing results under the stated admission model. Synthesized records and final guard calibration still require separate evaluation.

## Replay

Use the project model Python environment from `benchmark-kit/reader-use`.

```sh
OPENBLAS_NUM_THREADS=1 python facilitator_channel_fit.py
OPENBLAS_NUM_THREADS=1 python facilitator_channel_fit_audit.py facilitator-channel-fit-evidence/results.json
OPENBLAS_NUM_THREADS=1 python facilitator_channel_select.py facilitator-channel-fit-evidence/results.json
```
