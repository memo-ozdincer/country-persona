# Transfer a case-neutral evidence check to Resolution 2719

The first judge uses the same exact-span prompt as the Resolution 2504 study. It reads 18 distinct held source-and-draft pairs from the existing Resolution 2719 retained-reply benchmark. The second prompt carries the categories from the earlier error audit without the case-specific wording. Both use the same frozen Qwen3.5-4B. They see the authorized source, numbered requirements and candidate, with prompt conditions and prior judgments hidden. The primary phase uses 6,571 input and 1,384 generated tokens. The eight second-phase calls use 2,919 input and 16 generated tokens. [Protocol](protocol.md) · [First judgments](first.json) · [Second judgments](challenge.json)

The exact-span gate admits five of eight reviewed passes and three of ten reviewed failures. One output fails the format check. Two false approvals accept general statements about funding limits as evidence of the US interpretation of the original draft. The third accepts the French statement about clarity while it omits predictability. The three false rejections include accurate amendment tallies and a French statement that preserves both points. The second judge returns CLEAR for all eight first-stage admissions. Both the mandatory and selective second-stage rules leave every selected reply unchanged. [Decision traces](replay.json)

## Score after applying the gate

The same model generations can produce an apparent score from automated approvals and an audited score from the prior reviews. The following comparisons use the frozen ideal-trained policy and hindsight no-request on the same gate.

| Question set and prior | Automated score | Audited score | Audited gain |
| --- | ---: | ---: | ---: |
| Archived, uniform | 57.209 | 51.132 | −0.206 |
| Archived, correlated | 54.720 | 50.327 | −0.184 |
| Alternate, uniform | 57.209 | 53.967 | +2.629 |
| Alternate, correlated | 54.720 | 51.214 | +0.703 |

Automated credit overstates the four audited scores by 3.24–6.08 points. In the archived-question uniform setting, 44.5% of simulated episodes deliver a card with an incomplete required field. The audited losses come from missing qualifications. For this learned policy the replay forwards zero replies with reviewed material factual errors. The weaker comparative result under automated gating combines missing evidence in the learned arm with a different no-request response choice. [Automatic and audited score matrices](replay.json)

The selective rule adds 0.26–0.52 judge calls per episode above the first gate's 1.75, compared with 0.76–0.81 for checking every positive. It leaves accuracy unchanged alongside the full check. At a modeled price of one point per author or judge call, none of the learned comparisons beat the reoptimized no-request baseline. These prices are benchmark units and both author and judge calls are counted from the recorded context law. [Expected resources and price sensitivity](replay.json)

An oracle that removes every false approval among the initial positives would restore 2.624 points under uniform inventories and 3.125 under correlated inventories. On the archived questions, the first judge's false rejections would still cost 3.053 and 1.271 points respectively against full reviewed selection. This diagnostic keeps the policy fixed and gives the upper credit possible by screening only the existing positives. The candidate bank is from one exposed UN event and the reference labels are from the same assistant as the earlier draft review. [Positive-only ceiling](positive-bound.json)

## Reproduce from the parent directory

```sh
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
python facilitator_judge_transfer.py score primary facilitator-judge-transfer-evidence/primary
python facilitator_judge_transfer.py score challenge facilitator-judge-transfer-evidence/challenge
python facilitator_judge_transfer_replay.py
python facilitator_judge_transfer_bounds.py
```
