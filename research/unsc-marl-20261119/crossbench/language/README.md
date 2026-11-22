# Syria language-model workshop pilot

The frozen Syria pair changes the United Kingdom workshop delegate's private instruction while holding the dossier, packages and Brazil instruction fixed. The agreement variant permits package B for both delegates. In the impasse variant Brazil can accept A or B and the UK can accept C or D. The prior meeting paper contains the failed nine- and six-month drafts. Those facts are supplied retrospectively. The exercise asks the model to distinguish that historical record from the fictional negotiation.

Qwen3.5-4B generates separate private openings. The first role's identical input is evaluated once and reused across variants. The independent revisions each see only their own opening. Peer revisions each see the same own opening and the actual other-role opening, with no sequential dependence between revisions. The fixed same-model writer receives the two submissions for its arm. The direct analyst receives both private cards and uses the same final instruction. No scorer state, joint package key or other private card enters a delegate's input.

Every arm has a per-variant total cap of 770 generated tokens. Peer and solo share component caps of 120 per opening, 145 per revision and 240 for the final writer. The analyst has the same total cap in one call and the same 130-word final format contract. Actual input and output cost can differ. The mechanical endpoint checks the exact decision line against the private-mandate intersection. Separate language review checks each of the five final criteria and the fabrication guard.

This experiment runs the Syria family only, with no optimizer updates. The Iraq family remains available for a distinct source and case check. The single revision phase exposes a peer opening and cannot test iterative follow-up, honest disclosure incentives, trained policy transfer or representativeness across negotiation families.

## Measured results

| Variant | Arm | Required exact label | Observed label | Final words | Rubric / 70 | Critical guard |
|---|---|---|---|---:|---:|---|
| Agreement | Solo revisions → common writer | B | UNRESOLVED | 120 | 14 | Clear |
| Agreement | Peer revisions → common writer | B | B | 139 | 56 | Uncertain |
| Agreement | Full-information analyst | B | UNRESOLVED | 97 | 14 | Clear |
| Impasse | Solo revisions → common writer | IMPASSE | UNRESOLVED | 128 | 42 | Clear |
| Impasse | Peer revisions → common writer | IMPASSE | UNRESOLVED | 151 | 28 | Failed |
| Impasse | Full-information analyst | IMPASSE | UNRESOLVED | 101 | 42 | Clear |

Peer exposure helped the overlap case and hurt the source-grounded final record in the impasse case. On overlap, the peer final writer correctly chose B and explained its compatibility with the two conditions. It exceeded the word limit, omitted the UK affirmative vote on the first historical draft, and described a simulated consensus despite Brazil's reporting qualification. The scope of the consensus phrase remains uncertain. No arm met the complete final contract.

On impasse, all three final records identified the incompatible duration requirements somewhere in prose and still labeled the outcome `UNRESOLVED`. The peer final additionally stated that the UK previously opposed the actual nine-month draft, despite its recorded affirmative vote. All six narratives distinguished failure by permanent-member veto from failure to gain enough affirmative votes. Correct procedural history and complete ownership of national votes were separate scores. Final grading used opaque packets before the arm mapping was opened. The same assistant prepared the cases, saw interim delegate responses and graded the finals. [Verbatim judge deck](evidence/review/deck.json) · [Exact grades and evidence spans](evidence/review/verdicts.json) · [Scored comparison](evidence/review/scores.json)

## Was the decision information available?

Yes in all four writer inputs. The solo and peer submissions explicitly disclosed complete compatible sets. A manually coded, quote-validated replay intersects the visible sets before checking against the sealed-off reference. It derives B from either pair of overlap submissions, and an empty intersection from either pair of impasse submissions. These findings diagnose failure to use stated constraints in the final record even when sufficient constraints were already available. Compatibility statements establish simulated admissibility. They do not establish unanimous or binding assent. [Visible constraint replay](evidence/available.json) · [Exact supporting spans](evidence/availability-annotations.json)

At the revision stage, Brazil applied the peer's additional checkpoint requirement to explain the unique overlap. Its solo revision already favored B, so the supported effect is a better-grounded reason. In the impasse variant Brazil incorporated the six-month requirement and called it a deadlock, then proposed advancing A despite that conflict. The process annotation therefore withholds credit for a coherent change in disposition. [Two received-constraint checks](process-review.json)

All 16 raw completions ended normally within their token caps. Per-arm generated-token counts were 559/557/125 for overlap and 573/574/132 for impasse, in solo/peer/analyst order. Exact prompts, private routing, dependency text, budgets, tokenization and decision parsing replay. The run used CPU with the local Qwen3.5-4B checkpoint at revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Transformers 5.17.0 and torch 2.8.0. Two peer finals exceeded the word contract despite meeting their token caps. Zero weights were updated. [Run identity](evidence/launch.json) · [Mechanical replay and costs](evidence/replay.json) · [Raw transcript](evidence/transcript.jsonl)

The next discriminating comparison is the same writer with the same submissions plus a mechanically checked compatibility or impasse statement. Test whether it uses that statement while preserving historical votes and keeping admissibility separate from consent. For an RL policy this separates the payoff to obtaining missing facts from the payoff to correctly using facts already in the transcript.
