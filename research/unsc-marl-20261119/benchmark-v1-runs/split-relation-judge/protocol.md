# Separate relationship coverage from factual support

Test the same twelve compiled records, four mutations and four cross-family
controls as the answer-witness study. The coverage judge receives the full
answer and the criterion. The factual guard receives the full answer and its
evidence. It does not see the criterion. Reuse the prior evidence arrays,
including the public, admitted early, and delivered late fields on 2721.
The criterion score asks whether the answer expresses every part of the
relationship. The guard asks whether any material claim is unsupported or
contradicted. Coverage, guard and their conjunction are reported separately.

Use the same frozen Qwen3.5-4B checkpoint. Read the first-token A/B margin
with both label mappings for each question on each record. The primary rule
averages the two mapped logit differences within each question and requires
both averages to be strictly positive. Report each mapping and agreement
as diagnostics. Record 80 calls and their exact prompts and outputs.

Use the original semantic relationship labels and keep the four mutations
and four cross-family controls out of the fit. Check guard clearance on
unmutated compiled records and rejection on the four contradictions,
then report weighted relationship error. Replay both coverage-only and the
conjunction on identical 128-episode sender calibration logs per docket.
Only change the relationship bonus in the replay. Keep the exact archival
guard and standalone scores, and compare against the full-record judge,
answer-witness judge and exact target in the same 1,152 held settings.
Measure native feedback for one component of a structured joint task.
The frozen documentary benchmark and all archived model evidence are
separate from these exposed cases.
