# Fit the send decision from observations of the public ledger

The binary Qwen feature head misses two positive signed replies that
would open productive follow-ups. Add public ledger observations:
whether a terminal proof exists, whether the queried package is
unresolved, how many packages remain unresolved, and whether the
other role already accepts the queried package. Keep the local
verified sign, costs, action targets, 144 synthetic and 44 held
presentations, and 96 CPU updates. Use separate coefficient rows
for the two verified sign directions. The inputs describe the
current ledger without applying the counterfactual reply.

Fit a ledger-only control and a ledger-plus-Qwen residual. Compare
with the previous Qwen-only head and the exact local policy. Check
all 24 package-letter permutations and role-order exchange for the
ledger observations. Cached language features are unchanged and
only the ledger-only policy can be tested for actual invariance
without recapturing the model. Report final-record points, useful
proofs, unnecessary sends and reach to the four live contexts.
