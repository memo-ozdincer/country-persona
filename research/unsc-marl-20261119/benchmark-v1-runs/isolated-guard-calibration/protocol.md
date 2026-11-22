# Isolate the factual guard from JSON verdict construction

Use the 21 final anchor packets and the 12 opaque final packets from
the historical model slice. Give the judge only the final answer and
published evidence. Ask one guard question. Restrict the next-token
comparison to the three legal labels and swap the clear and failed
positions in a second prompt. Aggregate each label's two
unnormalized logits and keep disagreements visible.

Compare the original bundled judge's raw guard labels on anchors.
Compare to the previously stored single-assistant guard on each
historical final. Historical answers do not enter any prompt design
as examples. They are exposed development material, and the marks
are not independent human judgments. Report false clearance of
failed or uncertain records and false blocks. This test evaluates
the guard alone. It emits no quote-backed final rubric verdicts and
does not change the published evaluator or archive.
