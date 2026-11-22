# Local field grounding for workshop replies

The frozen Qwen3.5-4B comparison reuses all 16 queried histories from the previous Iraq and Syria pilot. It adds the delegate's own requirement values and corresponding fields from the single queried package, plus a literal comparison instruction. Both sets of fields were already present in the full role view. The added object contains neither a compatibility label nor the other role's private mandate. The role view, prior admissions, query, output schema, model and 64-token reply cap are otherwise fixed. Batch composition differs from the saved baseline. The treatment combines field selection and a decision instruction, so it cannot isolate their individual effects.

For each fixed prompt, compare the signed claim against the original on the same question. An adaptive check can reuse the same two openings, router and four continuation calls, applying the treatment on the questions the new transcript actually generates. Corrected answers may change which questions the facilitator asks. Fixed-prompt correctness therefore cannot establish live episode outcomes.

## Results

In the fixed comparison, all five previously truthful answers stayed truthful and all eleven wrong answers were corrected. The 16 recorded replies cover 11 distinct case–role–option combinations. Several unsuccessful original questions were re-asked with identical visible evidence. Inspecting this result supported running the adaptive follow-up in the same loaded model process.

| Workshop | Original routed questions | Grounded routed questions |
|---|---|---|
| Iraq overlap | Agreement at opening | Agreement at opening |
| Iraq impasse | Unresolved | Impasse on reply 4 |
| Syria overlap | Unresolved | Agreement on reply 2 |
| Syria impasse | Unresolved | Impasse on reply 4 |

All 16 adaptive replies were truthful, including replies to questions that became possible only after earlier corrections. The certificate timing matches the prior truthful scripted-answer diagnostic. The four episode paths used 19,810 input tokens and 240 generated tokens, including the same original shared openings. The prior routed paths used 18,299 input tokens and 240 generated tokens. The projection costs implementation work and 1,511 additional input tokens over these episodes.

These are exposed development cases with explicit, machine-readable fictional mandates. The result establishes that making already available evidence easier to apply can repair the workshop responses and public decision ledger under these conditions. The router remained scripted, Qwen weights stayed frozen, and no final written response was generated. [Fixed comparisons](evidence/fixed-metrics.json) · [Adaptive outcomes](evidence/adaptive-metrics.json) · [Replay](evidence/replay.json)
