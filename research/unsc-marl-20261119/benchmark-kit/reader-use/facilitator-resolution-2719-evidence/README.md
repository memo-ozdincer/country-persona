# Separate disagreement over an amendment from agreement on the resolution

This case concerns Security Council Resolution 2719. At meeting S/PV.9518, the US funding amendment passed 9–0–6, with France among the six abstentions. The amended resolution was then adopted 15–0–0. Paragraph 2 establishes case-by-case consideration. Paragraph 6 caps assessed UN funding at 75 percent of annual budgets for Council-authorized AU operations and calls for joint mobilization of the remainder. France raised the predictability of financing the remainder while supporting assessed funding for AU operations. [Official meeting, pp. 3–4](https://documents.un.org/api/symbol/access?l=en&s=s%2Fpv.9518&t=pdf) · [Resolution, paras. 2 and 6](https://digitallibrary.un.org/record/4031070/files/S_RES_2719_%282023%29-EN.pdf) · [Repertoire, p. 252](https://digitallibrary.un.org/record/4086808/files/ST_PSCA_1_Add.26-EN.pdf)

## Provenance and scoring

The 15 UNBench author-test vote rows for event 2517 match the official final vote. The frozen protocol incorrectly describes the docket as overlapping with UNSC-Bench. Both pinned UNSC-Bench splits lack a matching row by draft, meeting or the checked resolution and symbol aliases. This case is a UNBench extension. For the amendment tally, the direct locator supplied to the model is S/PV.9518, pp. 3–4. The packet's additional Repertoire locator says “Table 16”; use the printed page 252 instead. Both original inputs remain in the pinned artifact. [Dataset join](provenance.json) · [UNSC-Bench coverage audit](coverage.json) · [Locked packet](packet.json)

The three private cards cover the procedural vote, US argument and French objection. The public anchor is worth 42 points. The supplementary rubric awards five independent or conjunctive items worth 28 in total. The eight authored ceilings in bitmask order are **42, 48, 47, 53, 49, 59, 54, 70**, distinct from each declared and target bank previously used by the requester fit. The authored marginal benefit of adding the French card is 7 points alone and 17 points after both other cards. This is an eligibility ceiling. It requires that the generated record actually preserve the relevant details. [Scoring instructions](judge.md) · [All edges and frozen-policy replay](ceiling.json)

## Live comparison

Each arm uses three staged notes and one common final writer. Interactive note writers can see earlier notes. Independent note writers use only their assigned sources. The solo analyst has all cards on all three note-writing passes. All final calls use the public anchor plus the arm's three labeled notes. Calls and output-token caps match. Actual token counts and source visibility differ. The notes simulate how a record might be prepared after the meeting. They are generated text, and their relationships are distinct from the historical diplomats' interactions. [Prospective protocol](protocol.md) · [Complete calls](transcript.jsonl)

| Arm | Material / 70 | Release | First private ideas per note | Uptake links in final | Input / generated tokens |
| --- | ---: | --- | --- | ---: | ---: |
| Interactive | 58 | Fails | 2, 1, 2 | 2 | 1,894 / 469 |
| Independent | 57 | Passes | 2, 2, 2 | 0 | 1,599 / 436 |
| Solo analyst | 48 | Fails | 1, 2, 1 | 1 internal revision | 2,516 / 461 |

The interactive French note links France's funding concern to the procedural officer's account of its abstention and contrasts it with the US case for a cap. Both links reach the final text. The US interactive note mistakenly calls the amendment unanimous. The final restores the correct tally from the procedural note, then introduces an authority error by describing the framework resolution as authorizing operations. The supplement is 169 words against a cap of 154. The independent supplement preserves the US reasoning and passes the release guard at 151 words. It expresses uncertainty about the French contribution-level stance and falls short of the explicit comparison criterion. The solo supplement implies a financing guarantee in the case-by-case framework. The judgments are same-assistant exact-span annotations and use one run per arm. Only the independent arm passed release. [Exact review and composed records](results.json)

The separate receipt replay uses eligibility ceilings as rewards and simulated channels. It incorporates neither the three live final scores nor measured reply rates. On these authored ceilings, the archived fitted requester improves over silence in four of six channels and priors, with gains of 0.068–0.384 and losses of 0.055 and 0.122. The analytical degraded-delivery rule scores higher in all six. This is a new score structure and a failed training comparison under assumed transport, alongside a separate live-writing comparison. [Ceiling-based replay](ceiling.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
evidence=facilitator-resolution-2719-evidence
python facilitator_resolution_2719.py provenance
python facilitator_resolution_2719_coverage.py
python facilitator_resolution_2719.py blind "$evidence"
python facilitator_resolution_2719_score.py "$evidence"
python facilitator_resolution_2719_ceiling.py
```
