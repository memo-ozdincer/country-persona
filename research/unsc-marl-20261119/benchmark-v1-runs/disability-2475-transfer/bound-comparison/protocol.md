# Test a source-bound comparison under matched evidence controls

The previous chairs generated a fluent relation sentence but lost
the object and owner of the claim. Use one authored relation candidate
at a time and ask frozen Qwen3.5-4B whether the supplied note excerpts
establish it. Lock ten positive and negative cases and the primary
aggregation before scoring. The present experiment evaluates
classification and constrained rendering from already available notes.

Score supported and unsupported with both letter orders. Require both
mappings to agree on support before accepting the candidate. Record
single-order results and the mean mapped logit as diagnostics.
The chair sees candidate clauses, note owners and note text.
It receives no truth label, criterion IDs, hidden notes or scores.

For this diagnostic the renderer additionally requires source IDs
for the French treaty position and Russian operative-paragraph
interpretation before it prints the prewritten contrast. Each ID is
tied to one note excerpt in the declared source registry. Enable a
prespecified rule-only control that uses those same IDs. The renderer
can express the safe authored contrast and abstain. It cannot render
the misleading alternatives, even if the chair accepts them.
The UK-only source is sufficient for the separately measured claim
about agreement on obligations. It does not authorize a new comparison
about the treaty or Council procedure.

Report candidate classification, renderer behavior, exact released
scores and legal-scope errors separately. Compare the two previous
free-form prompts and verbatim records on the same original and
restored notes. Replay routing only on the resultant written
banks, using the same matched alphabet, fees and score information.
The templates and source IDs are authored, and all cases belong
to one exposed docket. This is a controlled representation test.
