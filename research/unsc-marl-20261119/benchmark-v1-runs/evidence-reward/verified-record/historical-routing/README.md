# Reconstruct Resolution 2422 from verified desk receipts

**Comparator correction.** The earlier compact exact rerun inherited a
21-point bonus for a complete record. The learned and fixed rows used
released points alone. The [common-objective audit](reward-fit/objective-audit.json)
uses released points minus costs for every arm. On compact records, exact
continuation gains 0.2323, 0.1772 and 0.1828 over exact no-request.
Exact no-request still beats the old learned team in all three laws.
The original bonus-objective results remain archived below.

This historical reconstruction uses the archived three-desk routing
policy and its existing comparison arms. That policy previously earned
a small modeled advantage when sentences were assembled directly.
The advantage disappeared when frozen Qwen wrote the supplement.
The published case joins UNBench author-test event 2229 and
UNSC-Bench adopted row 197. [Prior experiment and verified dataset join](../../../../benchmark-kit/reader-use/tribunals2422-transfer/README.md) ·
[Official meeting](https://digitallibrary.un.org/nanna/record/1631976/files/S_PV.8295-EN.pdf?registerDownload=1&version=1&withMetadata=0&withWatermark=0) ·
[Adopted resolution](https://digitallibrary.un.org/record/1631600?ln=zh_CN&v=pdf)

Peru, Russia and Serbia each see only their two source-packet
sentences. Three frozen Qwen3.5-4B responses reproduce those six
sentences exactly. All three also echo the outer desk and evidence
wrapper, which the requested flat format excludes. The original
parser therefore admits zero. An adaptive parser accepts the
echoed form only under the addressed desk, then checks exact source
identity again. That recovers all six from the same three responses.
The recorded launch identifies NVIDIA RTX PRO 6000 Blackwell Server
Edition. No parameter updates occurred. The first CPU preflight
used the wrong relative path to the frozen packet and stopped
before model collection.

| With all desks received | Supplement words | Released / 70 |
| --- | ---: | ---: |
| Original parser | 0 | 33 |
| Normalized receipts, exact selected sentences | 64 | 58 |
| Normalized receipts, authored compact phrases | 70 | 70 |

The normalization and compact rendition are distinct changes. The
latter uses authored wording for the six supported claims, with
the same source evidence and length cap as literal assembly. It
does not credit Qwen with writing the short report. The Serbia
capacity criterion is credited only when the objection is reported
and distinguished from Council action. All grades use the same
assistant's source-backed marks.

[Run and frozen inputs](protocol.md) · [Native responses](evidence/calls.jsonl) ·
[Format repair](normalization-protocol.md) · [Compact clause control](compression-protocol.md) ·
[Scoring packets](packets.json) · [Marks](marks.json) · [Token replay](verification.json)

## Effect on the archived routing comparison

All receipt-mask probabilities and message costs are held fixed.
The table shows the frozen learned continuation's expected net gain
over silence with the same responder. Free-form and compact
supplement columns use the old 28-point supplement rubric. The
final column uses the published v1.2 full-record weights including
Serbia's participation and objection.

| Inventory law | Free-form forward | Free-form reverse | Exact sentences, supplement | Compact supplement | Compact full record |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uniform | −0.1102 | −0.1341 | +0.0710 | +0.1120 | +0.0516 |
| Asymmetric | −0.0286 | −0.0171 | +0.0151 | +0.0176 | +0.0017 |
| Correlated duplicates | −0.1542 | −0.1747 | +0.0800 | +0.1506 | +0.1322 |

The restored advantage applies to the same-responder silence control.
The fixed request for Serbia's evidence beats the frozen learned
continuation in all three full-record comparisons. Its margins over
learned routing on the compact records are 0.7774, 0.2355 and 1.0370.
The learned router and old exact comparator were selected against a
different score surface. The archived recalculation re-optimizes its legal question and reply
policies with a completion bonus on the compact v1.2 records,
with the original openers held fixed. It gains 0.4476, 0.3451 and
0.2797 over exact no-request. Exact no-request already beats the
frozen learned team in all three. These are modeled receipt
distributions and source-checked rendering from fresh native
receipt proposals. They do not establish a live dialogue advantage
or a general learned routing advantage.

[All receipt-weighted scores](results.json) · [Exact continuation protocol](replan-protocol.md) ·
[Recomputed exact comparators](replanned.json)

Replay with the project Python and the original research modules.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
python3 historical.py requests | cmp - requests.json
python3 review_history.py verify | cmp - verification.json
python3 review_history.py packets | cmp - packets.json
python3 review_history.py score | cmp - results.json
python3 replan.py | cmp - replanned.json
```

[Common-objective training and request pruning](reward-fit/README.md)
improves on both exact no-request and the best fixed ask on the six
historical rows. The separate synthetic holdout retains losses
against those controls.
