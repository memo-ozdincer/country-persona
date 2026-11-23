# Evaluate the workshop with unfamiliar partners

Training with different partners produced **29 new successes and two
losses** across 5,418 paired evaluations relative to the frozen policy.
It brought no large improvement on its own. With a partner that always
signed, the mixed-trained team increased its invalid agreements from
71 to 74. Blocking those signatures at the moderator removed the
invalid results. Publishing the verified exclusions also improved
correct outcomes, from **823 to 966 out of 1,290**.

## Partner-diverse training

Both arms start from the earlier budget-aware weights and see the same
8,192 three-seat training worlds and sampled speech limits. The self-play
arm trains every seat. The mixed arm rotates one frozen partner through
the seats and updates the two learned seats from the verified shared
reward. The mixed arm encounters a checked-exchange script, a script
that prioritizes the final signature, and a partner that accepts every
draft. Learners see local mandates and public actions. They receive no
partner-type flag. Both learned arms keep the local acceptance check.
The always-signing partner bypasses that check in the base comparison.

Evaluation freezes each fit, selects new five-seat worlds with three
or four packages, and rotates one scripted partner through every seat.
A partner that reacts only to the current draft and another that yields
every turn are omitted from training. Self-play continuation produced
two new successes against the frozen policy. The mixed fit's 29 gains
and two losses count paired trials, including the homogeneous arms and
two exposed climate cases. Seat rotations reuse each world. They do
not constitute independent samples.

Some outcomes are unreachable with the assigned partner. A silent
seat never signs a valid agreement. Also, when a silent or always-signing
seat has the only mandate that excludes a particular package, the
others cannot certify an impasse through their own disclosures.
The diagnostic detects these two conditions. Other failures may arise
from the cap or the policies' actions. The diagnosis does not assert
that all other cases are reachable.

## What the moderator knows

| Response to an incompatible signature from the scripted partner | Valid agreement | Certified impasse | Invalid agreement | Unresolved |
| --- | ---: | ---: | ---: | ---: |
| Record the attempted signature | 319 | 504 | 74 | 393 |
| Refuse it and keep the turn spent | 319 | 505 | 0 | 466 |
| Refuse it and publish a checked exclusion | 376 | 590 | 0 | 324 |

This post-fit comparison holds the policy and worlds fixed. In the
last arm the simulator moderator knows the exact synthetic mandate.
It can publish a checked exclusion for the specific package the
partner tried to sign, without exposing the rest of that mandate.
This is moderator action. The partner receives no credit for choosing
to disclose. The institution's additional information recovers
70 of the 96 cases where the partner held a required exclusion.
The same inspection and rotation leave unresolved outcomes visible.

For example, in the original impasse workshop the mixed team and an
always-signing Kenya seat agreed to context. Refusing Kenya's signature
prevented the false agreement and exhausted the nine-speech cap.
Recording the checked context exclusion on that turn let the UK seat
declare a certified impasse on speech six.

This is structured cross-play under one training seed, with fixed
speech order and scripted partners. The always-signing behavior is a
stress case inspired by the earlier frozen run. These are no new live
Qwen, Astra or Sol results. Extending the moderator protocol to live
text would require evidence about which commitments can be enforced
and what the moderator has authority to disclose.

[Training traces and paired results](results.json) · [Moderator comparison and replay](guard-audit.json)

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-crossplay-20261123
python3 -B research/council_workshop/crossplay.py | cmp "$out/results.json" -
python3 -B "$out/guard_audit.py" | cmp "$out/guard-audit.json" -
```
