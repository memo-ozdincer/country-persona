# Choose one extra review using downstream team reward

Learn which pair or triple of notes to review from the net utility of
the entire team after receiving that review and replanning. Keep the
opening policies, delivery, planner, legal review actions and review
budget from the prior one-review replay. At test time expose only
the reviewed empty and singleton outputs, the public inventory law and
planner-derived opportunities. The held pair and triple scores remain
hidden until after a review is selected. The archived expected team
return allows exact gradients over the four possible review actions.

Hold out each entire historical event family in turn, including every
writer variant, order and inventory law. Weight each training family
equally and average both inventory laws. Train softmax policies from
zero for 160 full batch updates with step size 0.2 and L2 penalty 0.02.
The main policy has four features per action: expected net gain if the
candidate earns its singleton-additive predicted score, gain at an
optimistic score of 70, released singleton severity, and a triple flag.
Divide point gains and singleton severity by 10. Fit an action-identity
policy from the same returns as a comparison. Evaluate the greedy and
stochastic versions without selecting between them from held results.
Use deterministic tie-breaking by lowest mask. Compare to no review,
uniform review, all four fixed-mask policies, best fixed mask on the
training families, prior ridge, pure additive utility, optimistic
utility and hindsight. Also compare against forwarding all immediately.
True review costs are unknown. Report net return before review cost,
plus break-even extra review cost against forwarding all.

Primary quantities are greedy team return versus the training-selected
fixed mask and the strongest pre-existing fixed mask, separately by
inventory law. Report family results and the range of leave-one-family-out
aggregate effects. Verify fold isolation, that test features depend on
only known grades and that baseline net results agree with the former
one-review replay. This is offline learning of a review decision in a
cooperative team with fixed opening and routing mechanisms. Archive
grades, action effects and simulated transport have prior exposure.
