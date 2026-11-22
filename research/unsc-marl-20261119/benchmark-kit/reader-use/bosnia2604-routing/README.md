# Does a targeted source request improve the Resolution 2604 record?

Resolution 2604 provides a useful separation between the vote and the debate. France submitted S/2021/913 and all fifteen members voted for the EUFOR ALTHEA renewal. The United Kingdom backed Christian Schmidt and conditional use of executive powers. Russia challenged the appointment and treated the post as vacant. The adopted text authorized military activity and made no determination about the civilian appointment. The case matches UNBench author-test event 2408 and UNSC-Bench adopted row 251, including all fifteen votes. The join uses the draft symbol as well as date and votes. [Benchmark join](provenance.json) · [Meeting record](https://digitallibrary.un.org/record/3947096/files/S_PV.8896-EN.pdf) · [Adopted resolution](https://digitallibrary.un.org/record/3946754/files/S_RES_2604_%282021%29-EN.pdf)

The same frozen Qwen3.5-4B checkpoint produces every note and final. Each path uses two opening notes, a supplemental note and a final record, with per-call token caps of 64, 64, 80 and 190. The three team arms reuse the same two independent openings. A deterministic coverage rule checks those notes and requests the highest-weight apparent gap. Fixed supplements ask the named desk an open question without seeing the openings. Pooled solo can see both source cards in all three note calls. All final calls use the same instructions and public anchor. The four paths share calls and generation caps. They differ in input tokens, source visibility and follow-up wording. The fixed UK arm controls for desk choice. [Frozen prompts and weights](protocol.json) · [Run implementation](run.py)

| Arm | Material /70 | Release | Input tokens | Output tokens |
| --- | ---: | --- | ---: | ---: |
| Adaptive source request | 62 | Fail | 865 | 252 |
| Independent drafts + fixed UK | 36 | Pass | 807 | 261 |
| Independent drafts + fixed Russia | 63 | Pass | 814 | 266 |
| Pooled solo | 28 | Uncertain | 1,062 | 245 |

The two independent opening notes already identify the UK's 5+2 closure condition, Russia's objection to Schmidt's appointment and Russia's call for internal dialogue. They omit the UK's condition for using executive powers. The adaptive request asks for that qualification. Its answer supplies it and the final preserves it. The fixed UK supplement newly mentions executive powers but leaves them unqualified. The fixed Russian supplement adds Russia's affirmative vote and its criticism of the Office's effect on Dayton. Its final retains the 5+2 closure condition. Both the fixed Russian and adaptive finals preserve the call for Bosnian dialogue. This comparison includes one observed request target and source response. The routing rule uses authored lexical checks against the notes, with the grading criteria withheld from the final writer.

The adaptive final omits the 5+2 condition that was already in its input and changes the legal phrase “remaining seized” into a claim about seized assets. The phrase concerns the Council keeping the matter on its agenda. That invented legal detail fails release independently of coverage. The fixed UK statement about closure pending the 5+2 agenda could earn eight more points if interpreted as an explicit completion requirement. The pooled solo output links completion of 5+2 to stabilization rather than the condition for closing the Office. The review treats the added rationale as uncertain. These marks are from the same assistant under opaque candidate IDs. [Exact spans and adjudications](marks.json) · [Opening and follow-up annotations](process-marks.json) · [Replay and token counts](results.json) · [Model outputs](evidence/final-records.json)

## What the LLM judge caught

The full rationale prompt hits the 500-token cap on all four Qwen judgments. The compact prompt finishes all four and yields three valid JSON judgments. It recognizes the adaptive record's Russian dialogue criterion, which an initial manual mark missed. It also misses the adaptive record's asset-seizure error and overcredits the fixed UK and Russia records. In the fixed Russia case, it credits UK support for the military renewal as support for Schmidt's conditional executive powers, even though the cited span is verbatim. The exact-span filter rejects one altered span in the fixed UK judgment. Use structured output validation and semantic review separately. These judgments use the same checkpoint as the writer with independent ratings still pending. [Original judge instructions](judge-instructions.md) · [Compact instructions](judge-compact-instructions.md) · [Compact verdicts and differences](judge-compact-results.json)

## Replay

Run with Python, the local Qwen tokenizer and PyArrow available.

```bash
export PYTHONDONTWRITEBYTECODE=1
python audit.py provenance --root "$(git rev-parse --show-toplevel)" | cmp provenance.json
python audit.py score | cmp results.json
python judge_audit.py | cmp judge-results.json
python judge_audit.py --compact | cmp judge-compact-results.json
```

The replay verifies inputs and outputs at the token level, the prompt dependencies, frozen file hashes, and every credited span. The source cards are curator summaries. This is a single research-held event, with a bounded, deterministic routing rule and one drafting model. The generation run includes no policy or language model training.
