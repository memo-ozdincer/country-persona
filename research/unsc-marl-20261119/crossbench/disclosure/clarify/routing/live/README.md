# Live role replies and the learned routing policy

This test inserts frozen Qwen3.5-4B role responses into the previously verified routing loop. The policy uses its own role's structured mandate and the public evidence to select a package and nominate the next speaker. The answering model receives the corresponding local values, the public claims and the dated history. It must emit one signed JSON reply for the selected package. The verifier discards a malformed, off-package, or wrong-sign reply, consumes the slot and then hands off. The downstream ledger accepts only actual valid disclosures. Prompt reuse is exact by content hash across matched arms, and both arms have two independent openings and at most seven continuation slots. The model does not choose the next speaker.

| Case and opening | Exact-reply script | Exact-reply learned policy | Live Qwen script | Live Qwen learned policy |
|---|---|---|---|---|
| Sanctions impasse AC | Unresolved | Impasse | Unresolved | Unresolved |
| Membership overlap AB | Agreement | Agreement | Unresolved | Unresolved |
| Membership impasse AE | Impasse | Impasse | Impasse | Impasse |

The 25 distinct model requests yielded 25 exclusions. Seventeen were correct. The other eight corresponded to packages satisfying the delegate's own stated condition, including all five distinct opening requests. These replies were rejected as untruthful. Both policies therefore traversed the same public paths in the live run. No response hit the 56-token ceiling. The result separates an operation-level model failure from the simulated policy's routing gains. It also tests how the system reacts to a silent or incorrect delegate without crediting nonexistent evidence.

The six rendered records use only the public historical facts and admitted disclosures. They preserve unresolved status when the evidence is incomplete. The result is a fixed-format record with source-derived fields, with no model writing pass. [Raw replies](evidence/transcript.jsonl) · [Ledger and admission outcomes](evidence/metrics.json) · [Diagnostic comparison](evidence/diagnosis.json) · [Rendered final records](evidence/final-records.json) · [Exact replay](evidence/replay.json)
