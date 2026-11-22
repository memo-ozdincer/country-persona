# Admission after drafting

Can a gate see that a native rewrite should be discarded before its evaluation
score is available? Fit ridge regressions on archived, paired draft-minus-fallback
release scores from other dockets. Use strict released points. Include the complete
four-docket matched panels and hold out each docket in turn. In a second check, fit
on the non-2553 panels and two of the three 2553 writers, then test on the third.
Report how many improved drafts each fit has seen, as well as scores, decisions
and the oracle ceiling. Writer variants share receipt contexts. They are dependent.

Use equal mass per training docket, then per writer within docket, then per receipt
context within writer. Standardize nonconstant features with training weights
and fit the intercept without penalty. Set the ridge penalty to 0.1 on the
weighted mean squared error. Admit when predicted improvement exceeds 0.5 points
on the 70-point release scale. This margin is fixed and does not represent a
writing fee. Reports average uniformly over held receipt contexts and over held
writers for a docket summary. Judge marks and release labels serve only as
training targets or evaluation outcomes.

Compare always fallback, always native, a fallback-only length regression,
a draft-aware regression, and the hindsight oracle. The text features use
draft length, length difference, bag-of-words retention and novelty, number
set differences, and whether the fallback is a literal prefix of the draft.
They see no identity, receipt ID, grade, or grade annotation. Both candidate
texts are already available, so this tests release selection and spends the
same drafting budget. It neither tests communication nor saves a writer call.

The 2553 panel uses matched delivered input IDs in three writer banks and the
scored literal fallback from the split writer comparison. The 2721 panel
compares the appended native sentence with the same public and received rows
without that sentence. The 2686 panel uses the scoped and verbatim banks that
share the public lead and incoming notes, rather than earlier banks with other
inputs. The 2475 panel compares two native bridge prompts with the same
authored notes and no bridge. Include unchanged outputs and failed releases.
No new generation or evaluation calls. Archive annotations are existing
assistant judgments, with a heterogeneous rubric across dockets.
