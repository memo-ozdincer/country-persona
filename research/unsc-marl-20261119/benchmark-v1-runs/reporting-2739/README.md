# Resolution 2739 · shared reporting, divided vote

In both speaker orders, the peer-informed notes carried forward an
unsupported interpretation from the first desk. None of the six final
records cleared the source guard under the first reading. The strongest
pooled solo record preserved the reporting distinction and also
overstated Algeria's opposition and exceeded the word cap.

## Source and setup

The Council adopted Japanese–US draft S/2024/500 by 12–0–3 on
27 June 2024. Resolution 2739 extended the reporting request in paragraph
10 of Resolution 2722 through 15 January 2025. The co-sponsors sought
timely information for Council deliberations. Algeria said that it valued
the monthly reporting, while it abstained over implementation of
Resolution 2722 and what it regarded as misuse or misinterpretation of
self-defence. Its explanation supplies no endorsement of the date or the
whole extension. [Official meeting](https://digitallibrary.un.org/record/4053580/files/S_PV.9672-EN.pdf) ·
[Adopted resolution](https://digitallibrary.un.org/record/4053356)

UNBench event 2540 has 15 author-test vote rows, consistent with the
official tally and named abstentions. The parsed Statements array omits
Algeria even though its explanation is present in the full Content field
and the official PDF. Searching all 258 rows of the pinned UNSC-Bench
adopted table by draft, resolution and meeting yields no match. The
first provenance attempt required the UNBench draft ID field to contain
the UN document symbol. This file uses the print identifier 24-11687.
The verified join instead checks the draft filename, named sponsors and
the explicitly named draft symbol in the meeting content. The early
plan attempt failed while the provenance receipt was absent. Both
preparation errors preceded the locked run.
[Source join](provenance.json) · [Docket and rubric](docket.json)

The experiment uses the closed v1.5 prompts, roles and token budgets on
a separately locked docket. The final is limited to 130 words. The
88-word authored calibration record receives full credit. Each matched
peer and independent arm shares its opening note within an order.
[Locked protocol](protocol.md) · [Plan and pins](plan.json) ·
[Authored anchor](anchor.json)

## Measured results

| First desk | Independent raw /70 | Peer raw /70 | Pooled solo raw /70 |
| --- | ---: | ---: | ---: |
| Co-sponsors | 28 | 14 | 28 |
| Algeria | 28 | 14 | 56 |

All six released scores are zero, so the primary peer effect is zero in
both speaker orders. The two peer arms both lose 14 raw points against
independent drafting. No final retains the reference to operative
paragraph 10 of Resolution 2722. Both pooled solo finals preserve the
bounded reporting comparison. Four team finals instead claim agreement
on the reporting extension or its limits. In the stronger solo final,
the quote “Algeria opposed the resolution's underlying framework
regarding sovereignty and self-defence” expands an implementation
objection into opposition to an underlying framework. That final also
runs to 134 words. [Opaque final packets and traces](verified.json) ·
[Exact-span grades](final-marks.json) · [Scores](results.json)

- **Co-sponsors open.** The opening note says “Positions overlapped on
  reporting extension but differed on Houthi cessation demands”. The
  peer-informed Algeria note repeats that comparison. The final
  retains agreement on the extension and uses Algeria's sovereignty
  concerns as the opposing position.
- **Algeria opens.** The opening note says “Positions overlapped on
  reporting limits but differed on military authorization”. The
  peer-informed sponsors' note repeats that interpretation and attributes
  opposition to misuse of self-defence to Algeria. The final repeats
  the split as a disagreement over military authorization.

Independent notes also invent contrasts, so repeated wording identifies
a route by which an error survives. The experiment does not establish
that access caused the entire final error. With the co-sponsors opening,
peer exposure adds 117 logical input tokens relative to independent
drafting. With Algeria opening it adds 104. Nine of twelve logical
working notes hit the generation cap. Seven of ten distinct physical
working-note calls reach the cap. Every final ends normally.

The 16 physical Qwen3.5-4B calls consume 9,378 input and 2,251 output
tokens on NVIDIA RTX PRO 6000 Blackwell Server Edition, with zero
optimizer updates. The verified run reconstructs all prompt and output
tokens and the matched opening reuse. Assistant judgments were made
against the opaque packets before opening the arm mapping. The same
assistant designed the case. Independent agreement and family-level
generalization remain unmeasured.
[Worker receipt](evidence/launch.json) · [Evidence hashes](evidence/complete.json)

## Reproduce

Run from this directory in the project workspace using the existing
Aurora environments. These commands verify the archive without GPU use.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
env_root=/mfs1/u/memo/country-persona-research/envs
py="$env_root/aurora-qwen35-smoke-v1/bin/python"
"$env_root/open-character-20261004-v1/bin/python" sources.py | cmp provenance.json -
"$py" collect.py plan | cmp plan.json -
"$py" collect.py verify | cmp verified.json -
"$py" score.py final-marks.json | cmp results.json -
```
