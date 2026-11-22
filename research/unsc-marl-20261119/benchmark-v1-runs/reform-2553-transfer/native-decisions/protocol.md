# Native passage decisions with and without a visible receipt

Use the locked Resolution 2553 written-vote docket and the earlier
private two-card experiment. Test both UK–Germany orders, receipt
rates 0.55 and 0.95, and a 0.75 chance of the early desk having
card 1. The early desk is forced to send the privately drawn card.
The later desk chooses one of its own two passages. The third desk
chooses one of its own passages without receipt feedback. Use frozen
Qwen3.5-4B in both decision roles.

A role sees its exact local passages, the public standalone scores
and joint requirements, receipt probabilities, and its legal view.
It never sees text from an undelivered peer. For the receiver,
compare exact content, an arrival bit and no feedback. The two
feedback arms share the absent observation. Reuse the same third
desk decision for all three. Award credit through the fixed
source-bound renderer for every realized branch. Use the prior
matched fixed, learned structured, and observation-matched
informed oracle references. Verify a component substitution with
the earlier exact partner plans after scoring.

Each logical request is evaluated twice with the answer letters
swapped. Score only next-token A and B logits. The main decoder
averages the two mapped margins. Compare each letter order and a
consensus variant that falls back to local coverage on disagreement.
The output interface only emits legal card IDs. There are 24
logical contexts and 48 model forwards. Lock all inputs before
inference. No language or structured weights are updated. This is
an exposed rule-and-text integration test with authored menu and
rubric weights and a simulated receipt channel.
