# Writing a final record from the sanctions workshop ledger

This compares two matched opening pairs where a learned routing rule supplied the exclusion needed to certify an impasse. Each script and guarded path uses the same seven continuation slots after two openings. A fifth record uses the shared agreement transcript where both policies made identical disclosures. The writer receives an identical format, public historical material, the admitted claims, and the computed ledger. It receives no private mandates or policy label. The first run used frozen Qwen3.5-4B, greedy decoding and a 200-token ceiling per record. The five-line task allows 140 words.

Both matched paths contain nine distinct scoped claims. In each pair, the script allocates four to India and five to Brazil, including Brazil's new acceptance of F. The guarded policy allocates six to India and three to Brazil, including India's exclusion of F. The ledger reaches a certificate on continuation seven in both guarded paths. The change in evidence explains the disposition change even though turn and unique-claim counts are identical. These are typed disclosures, so the counts do not measure argument quality or natural-language uptake. [Process replay](process.json)

The final rubric gives 14 points each to disposition, operative evidence, attributed positions, uncertainty and historical concerns, and authority. A separate check tracks invented official acts or commitments. Exact heading shape, exact disposition line and word budget are recorded outside the 70-point substantive score. The three authored calibration cases check whether the judge preserves intact clauses when a candidate invents a workshop exclusion or an official amendment. The verdicts verify quote containment and schema and were not obtained from a new model judge. [Rubric and packet builder](review.py) · [Anchor examples](calibration.json)

## Original model run and input correction

All five outputs began their Workshop line with the supported status. Both guarded writers also correctly explained the complete coverage of exclusions. The two script writers recognized F as open but did not clearly identify India as the role whose disclosure was missing. The agreement writer left out the operative package terms. All five preserved the official vote tally and authority boundary. Only one met the precise five-line and disposition line contract. All five stayed within the word cap.

The prompt required the draft symbol, but the original context supplied a resolution number and vote tally without the draft symbol. The resulting required historical item was unavailable under the evidence-only instruction. The original results are retained and the paired retest supplies the draft, meeting and date as one explicit metadata field. No other prompt field changes. The first retest attempt failed in batch preparation because of a source-lock wrapper error. It made zero generation calls, and the corrected invocation uses a separate directory. [Original transcripts](evidence/transcript.jsonl) · [Original exact-span review](evidence/scores.json) · [Failed retest receipt](evidence/instrument-attempt1-failure.json)

The deterministic renderer uses the same corrected writer packet. It preserves both historical concerns, names India's missing disclosure in the unresolved rows, and cites a scoped admission from each role. Its five records pass the case-specific review. This control demonstrates that the specified output fits the supplied source and word budget. It does not measure model writing quality. [Rendered records](formatted.json) · [Renderer review](formatter-scores.json)

## Paired metadata retest

| Public record | Original rubric /70 | Corrected packet rubric /70 |
|---|---:|---:|
| Shared agreement | 28 | 28 |
| AC script, unresolved | 28 | 28 |
| AC guarded, impasse | 42 | 42 |
| BC script, unresolved | 28 | 28 |
| BC guarded, impasse | 42 | 42 |

The retest gave all five prompts the exact historical draft symbol, meeting and date. All five writers still omitted the draft symbol and omitted the recorded concern about reporting standards. Both guarded memos again correctly explained the impasse against the signed exclusions. One unresolved memo contradicted itself by saying that A through G were excluded while F had no blocking disclosure. The shared agreement memo invented mutual compatibility for C, though the ledger certifies only A and leaves C open. These are workshop evidence errors. The official authority check remains clear.

The original statuses on all five Workshop lines were supported as prefixes, compared with four in the retest. Exact five-line and disposition formatting fell from 1/5 to 0/5. All ten answers stayed within 140 words and terminated at EOS. The complete contract stayed at 0/5 in both model runs. The five deterministic records score 70/70 on this same case-specific rubric. The same assistant authored and reviewed the criteria. Exact-span and token replay validate the artifacts but do not establish independent judge accuracy. [Corrected prompt transcripts](instrument-evidence/transcript.jsonl) · [Corrected prompt review](instrument-evidence/scores.json) · [Token replay](instrument-evidence/replay.json)

The experiment supports carrying the certified workshop disposition and exact historical fields directly into the user-facing record. A future explanatory writer can add supported context while leaving these fields fixed. This study exercises already structured role claims and one source-linked writing family. It does not validate free-form negotiation or independent judging.
