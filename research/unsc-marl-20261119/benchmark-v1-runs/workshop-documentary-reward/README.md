# Reward complete workshop records as well as correct decisions

The team trained on released documentary points produces fuller
records than the team paid only for a supported correct decision.
Average released coverage rises from **50.033 to 53.710** out of 70.
The gain after the same send fee is **0.853 points**. The two reward
choices change forwarding in ten of 24 settings.

| Policy | Released /70 | Certified decisions | Sends attempted | Documentary net |
| --- | ---: | ---: | ---: | ---: |
| Learned, decision reward | 50.033 | 76.78% | 1.560 | 35.116 |
| Learned, documentary reward | 53.710 | 79.13% | 1.817 | **35.969** |
| Always disclose both | 54.565 | 79.13% | 2.000 | 34.565 |
| Stop after an opening certificate | 52.001 | 79.13% | 1.788 | 34.126 |

The distinction is visible when France opens in Iraq, or Brazil
opens in Syria, at 95% delivery and a four-point send price. Both
learned policies certify 92.625% of worlds. The decision-trained
team averages 58.188 released points and the documentary-trained
team averages 64.505. The second desk can still add its own
fictional mandate after the opening has already justified a choice.
At higher prices the two reward objectives can also differ in
whether they attempt delivery in the first place.

The public chair gets only received cards and the declared domains
of possible mandates. It intersects the feasible actions across
compatible worlds, then combines sourced historical text with the
fictional decision and known constraints. All eight complete
records pass the original score. Within each family, two of the
four worlds can be certified after seeing only the first role's
card, and none can be certified after seeing only the other role's
card. Certified partial records receive 56 and preserve the missing
condition as unknown. Other partial records release zero. An exact
invariance check covers all 32 receipt states to confirm that
identical public evidence yields identical text. [Protected records and verdicts](bank.json)

The same reward difference persists if certified partial records
also lose the open-issues criterion. With partial credit reduced
to 42, documentary net is 34.868 after fitting on it versus
31.401 after decision-reward fitting. These are authored score
sensitivities. [Conservative replay](sensitivity.json)

Each arm fits two local categorical actors from zero for 256 exact
expected-reward updates in each cell. The second actor can see the
opening only when it arrives. Each learned policy reaches the same
greedy value as its objective's exact decentralized optimum. Iraq
and Syria share the same mechanical information structure and
scoring weights, so their aggregate results duplicate. The 24
settings vary order, delivery and cost within this fixed simulation.
The experiment uses no generated model output or independent
human grades. It identifies a reward-design effect on the
communication schedule under known mechanics.

[Locked protocol](protocol.md) · [Inputs and hashes](plan.json) ·
[Policy weights, exact controls and results](results.json)

Run in the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B build.py | cmp bank.json -
python -B fit.py --plan | cmp plan.json -
python -B fit.py | cmp results.json -
python -B sensitivity.py | cmp sensitivity.json -
```
