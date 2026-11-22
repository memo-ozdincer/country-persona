# Verify one-step policy improvement under asymmetric delivery

Use the unchanged Mali workshop, its frozen learned router and public
delivery law. The proposed policy values each first query by enumerating
its two delivered observations and the loss branch. Each continuation uses
the frozen router. The deployed policy repeats this evaluation after every
observation. It may stop. Both the baseline router and its wrapper receive
exactly the same inputs. Include fixed order and exact public planning as
comparators. The wrapper does not use the learner's predicted value as a
calibrated return.

Evaluate all eight hidden worlds and all delivery branches at budgets one
through three. Use the three earlier rate profiles, all their role
permutations, and all permutations of the stress profile 0.96, 0.57, 0.12.
Report net, mechanical accuracy, call count, opening actions, worst exact
regret and maximum wall-independent planning effort in visited public
states. The wrapper should weakly improve on the frozen policy in expected
net under the true supplied law. An exact tie on this small case remains a
planning result. We use a separate model-mismatch control with the weakest
rate reported as 0.90 in the two asymmetric profiles from the earlier
trial, while replaying the unchanged true branches. No language actor or
model checkpoint is changed.

After inspecting the first result, add a continuation-policy ablation
with the same branch computation. Use fixed order or one-step greedy for
the continuations and apply the same wrapper at every deployed step.
This identifies how often the fitted continuation improves on simple
alternatives given the planning operation.
