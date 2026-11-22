# Resolution 2504 overlap across UNBench and UNSC-Bench

UNBench author-test event 2310 and UNSC-Bench adopted row 245 agree with all 15 official votes. The join uses meeting S/PV.8700, draft S/2020/24 and the dates and participant votes in the pinned files. The official meeting separately records an oral amendment rejected 3–7–5, adoption of the Belgium–Germany draft 11–0–4, and Russia's later withdrawal of S/2020/25. The three dispositions are distinct objects with distinct consequences. [Dataset and receipt audit](provenance.json) · [Official meeting record, pp. 2–3 and 12](https://digitallibrary.un.org/record/3847132/files/S_PV.8700-EN.pdf)

The public anchor carries the six-month authorization and its narrow crossing scope. The private cards carry the procedural result, the Belgian account on behalf of both co-penholders, and Russia's proposal and withdrawal. The 70-point rubric gives independent credit for each selected account and additional credit for correctly pairing the procedural result with Russia's two objects or contrasting Russia's proposed text with the penholders' rationale. The eight authored ceilings are **42, 46, 48, 52, 50, 59, 61, 70**. Five one-edit foils challenge a judge to preserve the identity of the adopted and withdrawn texts, the failed amendment outcome and the difference between requesting an assessment and obtaining its findings. These are authored evaluation fixtures. [Source packet and criteria](packet.json) · [Reference and five judge controls](foils.json) · [Official Resolution 2504](https://digitallibrary.un.org/record/3846843)

## Frozen judge calibration

Qwen3.5-4B passed the faithful record and rejected four of five foils. Its exact spans located the changed characters in each of the four rejections. It caught the reversed amendment outcome, both draft-identity swaps and the incorporation of rejected language. It passed the foil that replaces a request for the Secretary-General to examine alternatives with a finding that alternatives would suffice. That false pass exposes a consequential deadline and procedural-status error. Judge calibration on authored records is separate from performance of a deliberating team. [Judge instruction and protocol](judge-protocol.md) · [Six raw verdicts](final-records.json) · [Evidence localization](judge-localization.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_resolution_2504_provenance.py
python facilitator_resolution_2504_judge.py score facilitator-resolution-2504-evidence
python facilitator_resolution_2504_localization.py
```
