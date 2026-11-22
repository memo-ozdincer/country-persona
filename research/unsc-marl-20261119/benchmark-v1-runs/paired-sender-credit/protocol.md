# Compare paired sender credit with sampled broadcast reward

Use the same native-reward simulator, initial weights, seed, held
settings, features, Adam settings and 512 updates as the joint fit.
At each sampled training context, compare committing to send against
withholding under the same delivery draws and the same uniform
receiver draw. Apply the receiver policy appropriate to the
observation in each branch. Charge the sending cost on the send
branch even if delivery fails. The weight on the sender feature
gradient is the return difference times p(send) times one minus
p(send). The receiver keeps its original score-function update on the
single sampled on-policy branch. Both actors still optimize the
shared outcome utility.

Compare with original REINFORCE and a REINFORCE control with twice its
batch size. The doubled control matches the nominal two simulator
scores per paired context. The paired branches can share the score
on undelivered sends, and all variants reuse the same frozen native
model judgments without additional language model calls. Run a single
seed. Save the six scheduled checkpoints and full held comparisons,
including exact arrival-only and content-aware oracle utility, held
raw release, cost, and sender disagreements with its own reply
policy held fixed. Select no checkpoint using held outcomes. Report
the settings in each docket separately.
