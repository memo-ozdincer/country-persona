# Live question intervention on the climate-security dossier

The archived request is generated from the target role alone. The first note is generated from the requesting desk's Russian annex. The responder sees both local annexes and either the generated question or an empty question field. The typed learned plan selects the question and first send. The responder interprets the question text and writes through a prompted rule. The public vote record and the chair rubric are frozen.

This development sample was selected for a different expected receipt under request erasure. The original and attribution-focused chair conditions each have identical generation caps across the two receipts. The erased condition still attempts the question. Generated tokens include the attempted question in both arms. The transcript stores local prompts, generated token IDs, text, and source IDs. Replays recompute tokenization, validate generated IDs and text, reconstruct delivery, and verify the source and run hashes. Scoring verifies exact quote substrings. The semantic judgments are same-assistant annotations.

The two isolated writing conditions use one 80-token call per distinct annex. If both desks send Russia, the first admitted note wins and the duplicate is withheld. Both conditions can use up to 160 chair tokens, with only 80 reachable when there is one distinct annex. No text is generated to compare national positions in these two conditions. Each sentence must terminate within 36 words before the assembled supplement can release. The coverage intervention exposes the existing one-source rubric rule from the frozen task for each local sentence.

Review per condition from the benchmark kit's `validity-audit` directory using the existing frozen model environment and local tokenizer.

```bash
"$MODEL_PY" routing_climate_live_review.py ../evidence/climate2021-live-exchange ../evidence/climate2021-live-exchange/annotations.json
"$MODEL_PY" routing_climate_live_review.py --attribution ../evidence/climate2021-live-attribution ../evidence/climate2021-live-attribution/annotations.json
"$MODEL_PY" routing_climate_live_review.py --isolated ../evidence/climate2021-live-isolated ../evidence/climate2021-live-isolated/annotations.json
"$MODEL_PY" routing_climate_live_review.py --coverage ../evidence/climate2021-live-coverage ../evidence/climate2021-live-coverage/annotations.json
"$MODEL_PY" routing_climate_live_projection.py
```

The attribution evidence includes the byte-exact launch script. The verifier checks that snapshot against the launch hash. The current replay fixes a recursive function reference in verification that had no effect on the launched generation.

The projection compares the literal responder instruction, assuming the language model obeys it perfectly, with the exact original learned table for one component. It enumerates every pair of three-bit inventories and reuses the seven archived priors, the declared packet loss and the announced rubric values.
