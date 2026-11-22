# Update Qwen's reply policy in its native language layers

Use the signed-reply protocol's exact 144 synthetic development prompts
and 44 Iraq/Syria held prompts. Preserve role-private text, public
package wording and action tokens Y, N and P. Use one shuffled exposure
to each synthetic prompt, in 12 minibatches of 12. Fit rank-four LoRA
on the query and value projections of full-attention layers 27 and 31.
Optimize exact expected shared reward over the three candidate tokens,
with a 0.02 KL penalty toward that prompt's same-device frozen policy.
Use a fixed seed, 0.0002 AdamW rate, and no weight decay. Keep every
backbone tensor frozen. No rendered discussion text is added to fitting.

Replay the same native tokens with and without the saved adapter on
both splits. Score raw signs, wrong commitments, useful and unnecessary
replies, and utility. Compare the existing feature head and frozen
native model. Record the effect of the same public planner with each
responder and with typed sign verification. The held examples are
excluded from the optimizer yet already exposed by prior analysis.
The budget and procedure are locked before the GPU run.
