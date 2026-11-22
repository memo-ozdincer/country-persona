# Let the language model choose the sign of a reply

Give Qwen3.5-4B a fictional mandate in text, a published menu, the prior
public claims and one queried package. Decode one token among compatible,
incompatible or pass. The model's selected sign enters the simulator
unaltered in the primary experiment. The public ledger evaluates that
claim and the environment checks its truth against the role's typed
card. Delivery has a modeled 80% probability at test time. The chair's
query is fixed per presentation.
[Predeclared protocol](protocol.md) · [Prompt roster and branch values](roster.json)

| Reply policy on 44 held prompts | True new proof if delivered | False signed replies | Wrong commitment if delivered | Mean net |
| --- | ---: | ---: | ---: | ---: |
| Frozen Qwen | 5 | 0 | 0 | 0.292 |
| Matched bias-only fit | 0 | 0 | 0 | 0.226 |
| Reward-fitted residual | 12 | 4 | 4 | 0.289 |
| Separate sign estimate and send gate | 12 | 4 | 3 | 0.285 |
| Residual with a local sign check | 12 | 0 | 0 | 0.397 |
| Separate estimate and gate with deterministic sign completion | 15 | 0 | 0 | 0.436 |
| Always send the exact truthful sign | 16 | 0 | 0 | 0.440 |
| Exact sign and exact send decision | 16 | 0 | 0 | 0.462 |

Train 96 full-batch CPU updates per head on 144 synthetic prompts. Both
Iraq and Syria workshop families are excluded from fitting. The 44
held prompts include repeated presentations of their four private
mandate pairs. The reward fit makes more useful replies and introduces
false public claims. Training a factorized sign and send gate with an
additional local compatibility loss leaves four false replies. Three
of them would cause an incorrect common decision. It also increases
forced-sign errors from seven to eight. With the sign frozen, the
factorized gate passes on all 16 available proof opportunities.
[First fit](results.json) · [Dependent factorized fit](factor-protocol.md) · [Separate-head results](factor.json)

The main factorized errors are in interpreting Iraq's term requirement.
One asserts incompatibility between retention and option A. Three
assert compatibility between shortening and a proposal that retains
the existing mandate. The local verifier recomputes compatibility
from the responding role's typed requirement and the public menu.
It either rejects the inconsistent signed claim or constructs the
right sign if the policy chose to send. The residual plus rejection
retains 12 positive opportunities and blocks the four false claims.
The factorized policy plus sign completion captures 15 of 16
opportunities and sends 14 unnecessary replies. The exact control
shows the remaining benefit of deciding when to speak. The verifier
requires an authenticated typed local card and public package fields.
This replay leaves free-language extraction outside the role-local
guard's scope.
[Guard protocol](local-guard-protocol.md) · [Guard implementation](local_guard.py) · [Matched decisions](local-guard.json)

The capture records 188 native-token prompts and their three action
logits from NVIDIA RTX PRO 6000 Blackwell Server Edition. Qwen's
backbone stays frozen. The CPU replay fits heads over saved
representations and performs no new text generation. An import name
collision made the first verifier and factorized runner reference an
older experiment's fit module. The corrected import order binds both
to the local fit and the prompt artifacts remain the same.
[Run receipt](evidence/launch.json) · [Verification](verification.json)

## Verify

From this directory in the project inference environment:

```bash
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python cases.py | cmp roster.json
python verify.py | cmp verification.json
python factor.py | cmp factor.json
python local_guard.py | cmp local-guard.json
```
