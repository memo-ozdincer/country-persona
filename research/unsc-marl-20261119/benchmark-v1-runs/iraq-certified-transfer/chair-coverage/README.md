# Ask the certified chair to cover the vote and documentation

Four new frozen Qwen3.5-4B finals reused the archived Iraq workshop
notes, correct decision certificate, output limits and explicit
decision-line format. One added system paragraph asked the chair to
state the vote, distinguish the consultation options, and identify
who could change the mandate. It supplied no answers. The comparison
covers overlap and impasse, both in both speaker orders.
[Protocol](protocol.md) · [Actual prompts and finals](evidence/records.jsonl)

| Chair prompt | Exact decisions /4 | Cleared guards /4 | Strict records /4 | Raw coverage /280 | Released coverage /280 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Archived literal format | 4 | 4 | 1 | 210 | 210 |
| Same prompt with checklist | 4 | 1 | 1 | 168 | 70 |

The UK-first impasse improves from 42 to 70. It states the unanimous
vote, correctly explains that an annex choice cannot resolve the term
conflict, and keeps authority with the Council. The France-first
impasse also recovers unanimity but claims all four options add a
confidential annex. Only B and C do. One overlap answer claims the
menu varies solely in annex inclusion, overlooking duration. The
other attributes the fictional consultation summary to the historical
Council decision and misstates both delegates' acceptable options.
All four decision lines remain exact. The extra prompt costs 64 input
tokens per writer call and the new finals use 155 more output tokens
across the four states, with the same ceilings.

The intervention recovers documentary material on one order and
lowers aggregate quality. This distinguishes grounded final coverage
from simply prompting the chair to discuss more details. A follow-up
can require the chair to bind each requested statement to the
relevant public source block and verified workshop declaration before
rendering. Comparing that interface with the stronger archived
baseline would test the remaining source-use error.

The run used one NVIDIA RTX PRO 6000 Blackwell Server Edition, four
writer calls and zero updates. The archived and new marks are
same-assistant readings on an exposed family. The release scorer
checks exact spans and the mechanical decision. The records remain
available for independent review. The [CPU verification receipt](verification.json) checks the exact prompt delta and all token traces. [Verification recovery](verification-attempt.md)
[Launch](evidence/launch.json) · [Masked deck](deck.json) · [Marks](marks.json) · [Scores](results.json)

From this directory in the project Aurora Qwen environment:

```bash
set -o pipefail
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 OPENBLAS_NUM_THREADS=1
python verify.py | cmp - verification.json
python score.py deck | cmp - deck.json
python score.py score | cmp - results.json
```
