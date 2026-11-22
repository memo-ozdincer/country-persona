# Source-bound routing on Resolution 2417

**The first writer earned zero full comparison credits. A more explicit
instruction recovered one, which arrival-only routing could also exploit.**
The exact reviewed peer advantage was zero in both runs and both
presentation orders. Substituting the registered US reporting comparison
for that one omitted relationship restores **1.108 points** of peer
headroom. The threshold for fitting a routing policy did not pass.

The Council unanimously adopted draft S/2018/492 on 24 May 2018. The
Netherlands described possible Council tools for the four co-penholders.
Paragraph 9 concerns sanctions the Council can consider for obstructing
humanitarian assistance. The US expected more regular country reporting
and encouraged proactive warnings. Paragraphs 11 and 12 separately
continue regular reporting and ask for swift reporting when the specified
risk arises. Russia's broader account of food insecurity serves as a
third view; it raised factors outside conflict and limits on the Council's
remit. The case cards paraphrase the official records. The communication
channel, costs and clause inventory are simulated.
[Official meeting, pp. 2–4](https://digitallibrary.un.org/nanna/record/1627508/files/S_PV.8267-EN.pdf?registerDownload=1&version=1&withMetadata=0&withWatermark=0) ·
[Adopted text, paragraphs 9 and 11–12](https://documents.un.org/api/symbol/access?l=en&s=s%2Fres%2F2417%282018%29&t=pdf)

UNBench's author-test split gives 15 matching votes on event 2224.
The pinned UNSC-Bench files give zero matches across 258 adopted
and 211 vetoed rows. The dataset join uses the meeting's explicit draft
symbol and the draft filename. An early preflight incorrectly expected
the symbol in the draft body. The source file uses the print identifier
18-08385. This docket was new to the MARL series when the first plan
was frozen. Its public sources and unknown model pretraining exposure
make it a prospective project case, with the second prompt an adaptive
test on the same now-exposed material.
[Source join](provenance.json) · [Case and reference comparisons](case.json)

## Exact policy ceilings on 96 held settings

| Chair output | Best arrival-only | Best peer-informed | Peer gain |
| --- | ---: | ---: | ---: |
| Source-only | 37.242 | 37.242 | 0 |
| Initial writer with reviewed fallback, either order | 37.242 | 37.242 | 0 |
| Scope and timing prompt, canonical order with reviewed fallback | 39.457 | 39.457 | 0 |
| Scope and timing prompt, reverse order with reviewed fallback | 37.242 | 37.242 | 0 |
| Canonical scope and timing prompt with only the registered US comparison substituted | 39.457 | 40.565 | **1.108** |

With one rewarded comparison, the reply desk can favor the same
sanctions clause whenever a message arrives. Knowing the sender's
identity becomes valuable when US and Netherlands openings each have
a different useful reply. The one-cell substitution isolates that
difference. Its score equals the fully authored reference because every
other screened score already matches it. It is an authored intervention,
with no claim that a frozen or learned model produced the replacement.

The initial sanctions comparison described sanctions as a tool for
obstructing humanitarian assistance, reversing their purpose. In the
canonical revised draft the writer separated possible sanctions from
actual measures and identified obstruction of aid as the scope. Its
reverse-order version omitted the obstruction criterion. The revised
US draft either turned the US preference for more frequent reporting
into a request for faster reporting or omitted the frequency distinction.
The revised prompt recovered one scored relationship and increased
the number of drafts blocked by factual review from four to six across
the twelve packets. Each blocked comparison falls back to sourced
standalone text in the screened evaluation.
[Initial review](review.json) · [Revised review](scoped-drafting/review.json) ·
[Single-comparison substitution](component-swap.json)

This documentary comparison probe uses two roles and a fixed source-only
lead. Full deliberation and persona quality remain unmeasured.
The twelve packets cross all pairs with two presentation orders.
Qwen3.5-4B produced 24 total outputs on the NVIDIA RTX PRO 6000
Blackwell Server Edition. All calls completed. The two runs used
5,236 input and 693 output tokens. Scores are assistant annotations
on opaque packets. Independent agreement and training on a fresh,
source-grounded reward set remain unmeasured. Under the locked rubric,
better writing of the US reporting comparison is the change needed
before routing optimization can demonstrate a peer advantage here.

## Reproduce

In the Aurora Qwen environment, from this directory:

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B collect.py plan | cmp plan.json -
python -B collect.py verify | cmp verification.json -
python -B score.py | cmp results.json -
python -B scoped-drafting/run.py plan | cmp scoped-drafting/plan.json -
python -B scoped-drafting/run.py verify | cmp scoped-drafting/verification.json -
python -B scoped-drafting/compare.py | cmp scoped-drafting/results.json -
python -B component_swap.py | cmp component-swap.json -
python -B verify_results.py | cmp audit.json -
```

The audit checks prompt-only differences across 12 matched calls and
enumerates the exact policies for both information conditions at all 96
settings. Read the [initial protocol](protocol.md), the
[revised instruction](scoped-drafting/protocol.md) and the
[verification receipt](audit.json) for the tracked artifacts.
