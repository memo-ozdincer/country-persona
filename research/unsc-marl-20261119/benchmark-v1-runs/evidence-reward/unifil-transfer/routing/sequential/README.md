# Ask a question whose answer enables the next question

Use all 768 public opening and world pairs from the UNIFIL routing
audit. The chair can stop or query any role about any package. A
delegate in the standard partnership sends a verified sign whenever
asked. All replies cost 0.035 and all questions cost 0.04. An erased
reply changes no public state. Measure independent delivery on each
turn. The final-record value is the same proxy as in the one-question
study. The earlier optional-send policies have a different cost model.
[Planning and counterpart protocol](protocol.md) · [Full replay](sequential.json)

| Policy at 80% delivery | Expected questions | Expected new proofs | Expected record gain | Total normalized net |
| --- | ---: | ---: | ---: | ---: |
| Exact, one question | 492.00 | 257.60 | 242.08 | 205.180 |
| Greedy, up to two questions | 749.60 | 337.28 | 334.656 | 278.436 |
| Exact lookahead, up to two | 953.00 | 394.56 | 385.600 | 314.125 |
| Learned value tree with the same lookahead | 961.00 | 394.56 | 385.472 | 313.397 |
| Exact lookahead with a myopic responder | 893.00 | 306.24 | 305.984 | 249.054 |

All policies act from public signs and the same single-condition
prior. For each question, the exact and learned lookahead integrate
all possible signs and erasure, then choose a second request
conditional on the result. The learned planner uses the frozen
synthetic-trained tree for each reply's predicted credit. The
counterpart swap keeps the exact planner's policy but permits
the responder to withhold a reply based on its immediate value.
The chair sees that as absence and still pays the question cost.

The exact two-question policy opens 113 states where the one-question
version stays silent. In 135 states, it begins with a question
whose sign cannot earn any immediate record credit either way.
For example, an affirmative signature from Brazil can enable
the next question to China about the same package. In one impasse
witness, successive exclusions of two different packages by the
same role complete the proof. A public claim can be worth delivering
because of what the other turn can do with it.

The same learned planner still falls below silence at 8% delivery,
with −0.296 total normalized net versus +0.509 for exact lookahead.
The repeated openings and sampled true worlds come from the same
exposed historical family. Delivery is simulated and aggregate
score increments are based on the documentary proxy.
[UNIFIL case and dataset provenance](../../README.md)

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 sequential.py | cmp - sequential.json
```

The three selected witnesses also ran with six live Qwen replies,
where each second question depended on its preceding verified sign.
The resulting briefs scored 70, 56 and 56. [Live sequences and grades](live/README.md)
