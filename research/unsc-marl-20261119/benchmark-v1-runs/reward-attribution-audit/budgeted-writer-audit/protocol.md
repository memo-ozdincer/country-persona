# Budgeted audit for an unfamiliar composition writer

Use all 69 paired alternatives from the earlier draft-aware composition
replay and the five Resolution 2664 source-preserving compositions. Divide
rows by docket and writer. For each held docket, fit the earlier draft-aware
ridge model using other docket families only. Keep the existing feature
definition, weighting, penalty and 0.5-point admission threshold.

When no further grade is available, compare the transferred gate with the
source-preserving fallback. Then reveal at most 1, 2, or 4 existing paired
grades per target writer. Costs count one archived native-versus-fallback
evaluation per selected draft. Exact text copies are exempt from audit
because release can use the already verified fallback for them. Cap the
audit budget at the number of eligible distinct receipt contexts in that
writer. Measure two uses of the feedback.

- Direct audit releases an inspected draft only when its grade improves on
  its fallback. Every other context keeps the fallback. Compare uniform
  selection with targeting by highest score from the transferred model,
  using lexical context ID as a stable tiebreak.
- Writer-level calibration audits a uniform subset, following the same
  direct rule for inspected drafts. It admits unseen drafts from that writer
  when its inspected drafts have mean improvement above the same threshold.

Average over every equally likely uniform audit subset without random
sampling. Score untouched candidates with their existing grades, and count
separately whether native improvements were kept and whether harmful
drafts were admitted. Use equal context weights within a writer and equal
writer weights within a docket. Expose the oracle and native-everywhere
controls. This is a post-draft release policy. The reconstruction charges
neither generation nor grading in score points and reports the actual
number of label lookups separately. It tests reuse of archived feedback,
with assistant annotations and dependent receipts, and adds no new
generations or evaluations.
