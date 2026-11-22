# Include unusable source cards in synthetic training

Repeat the same joint fitting recipe, seed, optimizer, objective and
144-bank budget. Keep 72 of the dense synthetic training banks.
For another 36 banks make one card irrelevant to every terminal
score, and for 36 make two cards irrelevant. Draw these banks from
the other original synthetic draws and additional synthetic draws if
needed for distinct examples. Rotate affected cards using a fixed
random generator. Erasing a card removes all of its contribution,
including any joint criterion. The training set contains no historical
bank or exact centered historical score vector.

Compare the old and sparse fits using only singleton estimates on the
four historical archives. Use the same opening policies, held priors,
and public one-request-removal rule. Report exact no-request and best
fixed request under the true bank. Use the actual historical scores only
at evaluation for learned arms. Replay the same heads on separate
synthetic sparse and dense controls. No new native model calls or
post-fit threshold searches.
