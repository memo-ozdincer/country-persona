# Calibrate only the sender after the actor swap

After observing the transfer results, freeze the zero-shot receiver.
Draw 128 target episodes with uniformly sampled private views, half
probability of sending, and independent 0.75 probabilities for the two
deliveries. Use one deterministic seed, the same uniforms for both target
dockets, and the already fixed archive. Observe the factual record score
and delivery flags. Since forwarding cost is public and separable, use
the record score to estimate expected benefit and subtract the price
only at decision time. Pool first-absent scores across private views
within each final-delivery state. Condition first-present scores on the
available sender inputs, standalone source coverage and claim bit, and
the final-delivery state. No counterfactual scores enter the update.

At deployment multiply the estimated value of arrival by its probability,
then choose send if estimated benefit exceeds cost. Reuse all 96 held
settings per docket. Compare to the zero-shot fixed receiver, the
gradient warm start, and the best sender with that receiver. This is an
adaptive follow-up on known target dockets. The fitted sender has access
to 128 exploratory outcomes from the target and a stated delivery model.
