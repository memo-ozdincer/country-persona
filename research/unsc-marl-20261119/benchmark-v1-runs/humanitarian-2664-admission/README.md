# Resolution 2664 final-record contrast

Can a brief improve on separately reporting the decision and the minority
position? The added information is a relationship between two sources. The
adopted resolution assigned monitoring to the 1267 Committee and requested
provider due diligence. India judged that the resulting text did not fully address
its call for a proactive Monitoring Team and stronger reporting. A brief that
connects these statements must keep the adopted safeguards and India's own
assessment distinct. [Adopted text, paragraphs 1–3 and 5–6](https://documents.un.org/api/symbol/access?l=en&s=s%2Fres%2F2664%282022%29&t=pdf) · [Meeting record, pp. 2–3 and 7–8](https://digitallibrary.un.org/record/3997357/files/S_PV.9214-EN.pdf)

The comparison is dated to adoption on 9 December 2022. The evidence cards are
curated paraphrases with primary-source locators. References to the two-year
period describe what was adopted that day. This event was already exposed in
the [UNBench workshop development](../../crossbench/disclosure/clarify/routing/README.md).
The final-record task and its anchors are new research fixtures outside the
frozen benchmark release.

| Evidence and candidate | Candidates | Raw /70 | Released /70 |
| --- | ---: | ---: | ---: |
| Both sources, standalone facts | 1 | 58 | 58 |
| Both sources, faithful synthesis | 3 | 70 | 70 |
| Both sources, material misreading added | 4 | 58 | 0 |
| India only, safe partial record | 1 | 40 | 40 |
| Adopted safeguards only, safe partial record | 1 | 48 | 48 |
| One source removed, synthesis still asserted | 2 | 40 or 48 | 0 |

The controls isolate false collective attribution, denial of adopted monitoring,
a global instead of regime-specific expiry, and invented prior approval.
The deletion tests reuse the same synthesis sentence from the full-evidence
case. The shortest synthesis is 104 words, four words longer than the
standalone record. It earns the additional points by integrating the
comparison into India's existing sentence rather than adding a second paragraph.

The [blinded packets](blind.json) use the frozen [final judge prompt](../../benchmark-v1.5/final-judge.md).
The [anchors](anchors.json) contain the assistant-authored grades, exact response
spans, source IDs, and release points. The frozen validator checks the citation
and response spans and computes scores from those grades. Judge behavior,
independent review, model-authored improvements, and policy learning remain
unmeasured. The six rubric items and 12-point comparison weight were chosen
for this pilot. The three positives are authored formulations of one fact
relationship and supply feasibility evidence for one docket.

For a matched authoring comparison, keep the first two cards public, assign
the safeguards card and national statement to separate desks, and reuse
the same 150-word final limit and frozen judge across conditions. Give the
pooled solo baseline both cards. Compare independent desk drafts plus synthesis
against peer-informed drafts in each speaker order. Preserve the delivered
card set for each output so the source-deletion guard is evaluated against
the evidence each system could actually use.

```bash
set -o pipefail
python3 -B replay.py | cmp anchors.json -
python3 -B replay.py --blind | cmp blind.json -
```
