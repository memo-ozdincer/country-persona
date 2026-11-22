# Give the reward-optimal reply direct credit in native training

The first native reward update suppresses held useful replies from six
to one. Reinitialize the exact layer-27/31 rank-four adapter and use the
same native prompts, shuffled minibatches, seed and optimizer settings.
Replace direct expected-reward maximization with class-balanced
cross-entropy on the action with the greatest exact team return in
each synthetic example. Keep the KL penalty. This is a supervised
counterfactual-credit control derived from the team utility, with no
change to the held prompts or runtime action space. Compare the raw
model, typed sign guard, and same frozen chair replay. Run 12 updates
and inspect the result.
