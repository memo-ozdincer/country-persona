# Separate record coverage from source verification

The holistic live judge copied text from a source block into its candidate
citations and missed already present claims. Test two independent prompts
per record on the same frozen Qwen3.5-4B checkpoint. The coverage prompt
sees the criteria and numbered candidate paragraphs, with no historical
source excerpts. It returns the paragraph IDs for each satisfied criterion,
an empty list for an omission, or [-1] for uncertainty. The verification
prompt sees the candidate paragraphs and source excerpts, with no rubric,
weights or coverage verdict. It returns one supported, unsupported or
uncertain label per candidate paragraph.

Join the replies by paragraph ID. Count a criterion only when it is
marked present and all its paragraphs are supported. One unsupported
paragraph fails the whole-record guard. Any uncertainty or invalid output
keeps the previous routing grade. The prompt lengths and output budgets
are fixed before the run. No retries or repair of these raw replies.
The blinded objects contain no score, arm name, prior marks or outcome.

Use the same three contested pair records. Lock one control per case.
Introduce a false current-veto statement in the Emergency Session record.
For UNAMA use the archived public-only record with the same two source
cards still visible to the verifier. For Myanmar use the archived
full-receipt record, which adds the separate procedural chair role.
Preserve the historical word caps, archived criterion weights,
and public base for modular cases. These controls test contradiction
handling, absent source-only claims, and an added positive paragraph.
The only authored record is the Emergency Session contradiction.

Replay the 23 archived triggered conditions under the unchanged
route planner. Use an admitted two-stage grade for the contested
record and retain the previous score on invalid or uncertain results.
Do not use any control grades for route selection. Compare exact
agreement, control discrimination, route utility, call count and token
cost with the earlier live study. There are six records and twelve
short model calls. The cases and archived grades are exposed.
