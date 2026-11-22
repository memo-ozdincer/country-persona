# Targeted clarification in the Iraq and Syria workshops

The earlier Iraq delegates supplied two truthful opening claims and repeated them. This fixed-budget comparison asks whether a public facilitator can elicit missing evidence with targeted questions. It uses the two source-audited workshops derived from UNBench and UNSC-Bench, with one overlap and one disjoint variant in each. Each role sees its own fictional mandate, the public historical reference and admitted workshop disclosures. The facilitator uses only the public ledger. The environment checks whether each answer is truthful and responds to the actual question. The historical vote can never certify a workshop result.

The arms reuse the same two opening messages per episode and have four sequential 64-token continuation calls each. The free arm alternates responders and asks for a new signed claim. The queried arm routes the next question to a specific responder and package, preferring the complement of a public acceptance. In ties it uses step parity and package order. This changes responder routing and question specificity together. The run compares the full protocols. It tracks the first certified continuation, successful admissions, repetitions, actual costs and cap hits in replayable records. The ledger determines when the session has evidence for an agreement or impasse. No generated final memo is scored by this probe.

## Public query budget

On the exact grid of 225 ordered private-menu pairs and all possible positive openings, there are 916 feasible and 108 disjoint menu/opening pairs. The dynamic program maximizes the mean of the two certification rates using only public observation of opening claims and previous answers, with a uniform menu/opening-pair measure inside each outcome class. It allows no voluntary information from the respondent beyond the queried sign. Under four queries the best balanced score is 0.703 (880/916 agreement and 48/108 impasse certificates for the chosen optimum). Variation across positive openings counts as multiple presentations of the same private pair. This grid-based upper bound describes the query-only protocol with reliable answers and this scoring distribution. [Planner](public_planner.py) · [Scores](planner.json)

| Query budget | Verified agreement /916 | Verified impasse /108 |
|---:|---:|---:|
| 0 | 256 | 0 |
| 1 | 640 | 0 |
| 2 | 832 | 0 |
| 3 | 832 | 0 |
| 4 | 880 | 48 |
| 5 | 904 | 96 |
| 6 | 916 | 108 |

Each row optimizes the balanced score separately. With positive openings an impasse needs four new exclusions, so three queries cannot suffice. Six queries cover every remaining unknown role–option sign. The jump between four and six helps distinguish more communication capacity from improvement at an equal budget.

## Frozen Qwen3.5-4B result

| Family and variant | Free disclosure | Routed query | Same router with truthful replies |
|---|---|---|---|
| Iraq overlap | Agreement at opening | Agreement at opening | Agreement at opening |
| Iraq impasse | Unresolved | Unresolved | Impasse on reply 4 |
| Syria overlap | Unresolved | Unresolved | Agreement on reply 2 |
| Syria impasse | Unresolved | Unresolved | Impasse on reply 4 |

All six actual shared openings supplied truthful signed claims. In the continuations, 5/16 queried replies and 12/16 free replies made a truthful claim. The remaining 11 and 4 replies respectively were untruthful. JSON format was valid throughout. Free disclosure repeated ten already visible claims. The admitted queried claims were all new. In Syria overlap, the UK delegate repeatedly rejected B even though B satisfies its extra-checkpoint condition. In Iraq impasse, France repeatedly accepted C even though it fails its private instruction. Rejected answers leave the public state unchanged, and the router can spend multiple steps on the same unresolved question. Re-asking did not recover either error. The free and query arms consumed 18,313 and 18,299 input tokens and generated 300 and 240 tokens respectively across their four episode paths, including the shared openings in both arms.

The same deterministic router issued enough questions from the actual openings when the responses were supplied truthfully from the private workshop definitions. That counterfactual establishes feasibility of the routing policy on these four development cases. The exact grid above shows failures remain possible under the same horizon even with perfectly grounded responders. Grounding the signed answer against the local mandate is the next controlled variable. The router was scripted and Qwen was frozen. No optimizer updates, general country fidelity, or improvement in final written records were measured. [Metrics](evidence/metrics.json) · [Raw transcript](evidence/transcript.jsonl) · [Truthful-response control](routing-control.json) · [Replay](evidence/replay.json)

## Allowing voluntary disclosures

The exact grid also supports a fixed alternating speaker schedule with one voluntary signed claim per slot. A role first looks for a local acceptance that matches a public peer acceptance, then excludes publicly accepted packages it cannot support. It next volunteers another useful exclusion, then another acceptance. The same four slots certify 856/916 agreements and 72/108 impasses, for a balanced score of 0.801. This gives a better balanced baseline than public queries on this grid. The local script uses its own menu and the actual public claims.

Even with both private menus available to a perfect scheduler that must respect the same speaker order, at most 84/108 impasses can be certified. The remaining 24 are disjoint three-versus-one menus, where one role must contribute three exclusions but receives only two slots. This is an information-capacity check. It gives a clear target and a ceiling for evaluating learned disclosure at the same budget. [Exact voluntary-disclosure results](voluntary-bound.json)
