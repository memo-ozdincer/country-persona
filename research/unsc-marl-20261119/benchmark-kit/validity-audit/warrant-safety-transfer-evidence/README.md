# Prospective transfer of the conservative workshop chair

The [previous conservative-receiver replay](../warrant-request-safety-evidence/README.md) used already examined disclosure behavior. Here a new seed supplies two grade domains before inference. Frozen Qwen3.5-4B selects a package for the veto-first and highest-grade roles and transcribes an authorized grade for the third role. The sender compiles each chosen grade from its own card. Each output is evaluated against its private authorization. The receiver uses its previously frozen model of what partner policies remain compatible with public histories. [Locked protocol](protocol.md) · [Runnable generation and replay](../warrant_safety_transfer.py)

Evaluation crosses the two domains with both priors and enumerates the entire joint distribution of card types and link outcomes. A sampled history contains earlier openings only. The comparison includes grade-only, fixed role-factored, blended and true-partner planners. A domain with any inadmissible report triggers the default for the conservative arm. This tests the model's stationary valid-sends assumption on the complete per-type table, which is available only in this laboratory benchmark. The release certificate remains a separate computation over all grade-compatible card worlds.

## Full replay

All 24 role/type outputs yield authorized grade receipts. D1 selects A on all eight types and follows its veto-first instruction on two. D2 follows its highest-grade instruction on six of eight. The eight D3 transcriptions match their fitted assignments. The comparison uses the observed choices, including the departures from convention. [Admitted reports and branch scores](results.json)

| Domain and inventory prior | Grade only | Blended, 16 histories | Conservative, 16 histories | Actual partner known |
| --- | ---: | ---: | ---: | ---: |
| 0, uniform | 0.716305 | 0.710897 | 0.716305 | 0.730480 |
| 0, correlated | 0.817180 | 0.816172 | 0.817239 | 0.825041 |
| 1, uniform | 0.804988 | 0.806280 | 0.809071 | 0.809203 |
| 1, correlated | 0.709227 | 0.709857 | 0.711128 | 0.711206 |
| Mean | 0.761925 | 0.760802 | 0.763436 | 0.768982 |

With zero histories the conservative rule matches grade-only in all four conditions. At four histories its mean reaches 0.762977. At 16 it improves three conditions and ties the fourth, with no negative expected-history returns. The domain 0 uniform chair leaves its requests unchanged because compatible partner tables disagree on their value, even though the true-partner planner has a 0.014175-point advantage. This deliberately forgoes some potential gains under uncertainty. These are exact conditional expected returns averaged across synthetic histories built from the measured model choices, not a population estimate from independent live conversations.

The first runner stopped after eight outputs because it mixed requests with different token ceilings in one batch. The separate-ceiling rerun reproduces all eight stored rows byte for byte and completes the 24-call panel. The [partial transcript](partial-launch/transcript.jsonl) is retained alongside the complete [trace](transcript.jsonl).

## Execute the first improving request contrast

The first eligible state occurs in domain 0 with correlated inventories after the first 16-receipt history. The only admitted opening is D3's grade 3 for B. Grade-only planning asks D2 about A. The conservative receiver stops because every surviving policy gives stopping a conditional expected advantage of at least 0.028625. In the selected successful-delivery branch, Qwen returns the authorized reply “D2 reports grade 0 for A.” That reply reduces the compatible worlds from 32 to eight. Both final workshop certificates say UNRESOLVED. A separate enumeration verifies both from the exact grade receipts. [Selected branch and both final records](reply-audit/results.json) · [Reply-audit protocol](reply-audit/protocol.md)

The worked trace checks one actual reply and its effect on the record. The table above uses the complete prospective distributions. It retains the stable, deterministic partner, known prior and independent loss assumptions. The combined policy is an implemented workshop mechanism with synthetic preferences, actual model-selected openings, one selected live reply, and a deterministic final certificate. Broader diplomatic deliberation with independent process and prose judgments remains unverified.

## Replay

Use the project Python environment from `benchmark-kit/validity-audit`.

```sh
python warrant_safety_transfer.py verify warrant-safety-transfer-evidence
python warrant_safety_transfer.py score warrant-safety-transfer-evidence
python warrant_safety_transfer_reply.py score warrant-safety-transfer-evidence/reply-audit
```
