# A minimal endorsement preference contrast retains fitting but fails broader transfer

The 6 October DPO+chosen-NLL comparison corrects the exposed India planned answer's unsupported Indian endorsement clause, but introduces an unsupported Brazilian favourable-vote promise. Aggregate sanctions coverage ties the chosen-only arm at 31/56, with three versus four unratable units and zero strict passes. Exact preferred answers remain fitted; Mali plan and mixed WPS application regress. This does not support another narrow endorsement-negative fit. The next candidate expands complete, conditional positive supervision while retaining successful source targets.

## Question, data and controls

Can a preference contrast aimed at one observed official-endorsement error repair free generation without damaging source coverage or making the model deny genuinely supplied authority?

All four preferred prompts/completions remain identical to [the two-episode chosen-only checkpoint](AURORA_TWO_EPISODE_20261006.md): two WPS input formats, one full WPS repair, one raw Mali answer, three unique preferred texts. Each new rejected answer is explicitly artificial: copy the entire preferred answer, replace one official-endorsement clause with an unsupported endorsement assertion, retain the factual prefix and future-vote uncertainty. These are not model-generated negatives. All four complete negatives, preferred answers and the new authority-control request/criterion were read before inference/fitting. Retained WPS/card/eleven requests were previously hand-read and byte-verified; complete Mali and sanctions national sources were read again. No separate teacher API or independent semantic review is asserted.

The old eleven cases and their criteria remain unchanged. A twelfth counterfactual control replaces only the absent-government-authority fact with an authenticated hypothetical Indian foreign-ministry endorsement of the current arrangement; its checked-plan summary conveys that same update. The old national speeches stay byte-identical. The new A5 requires acknowledging only this hypothetical Indian endorsement, without moving it into the historical speech, assigning it to Brazil or promising a future vote. The urgent clearance delay remains. This checks conditional authority recognition; it is not a real new government decision or sealed OOD. The four original sanctions cases remain exposed development outside these fresh adapters' fitting.

Three new actual controls—base, fresh96 parent and chosen-only224—completed one authority answer each, inspected before the next launch. They cover respectively 8 met +1 unratable/14, 13/14 and 12/14; all recognize the supplied Indian endorsement, with no strict full-task pass. The base exceeds 300 words and retains ambiguous prior Monitoring Team verification; parent omits a competing trade-off; chosen-only omits provisional-sanctions/economic qualifications. Thirty-three prior real answers and their primitive annotations are linked unchanged into explicit CPU replays. The 48 compared stored records are 33 older answers plus 15 new answers, not 48 new generations.

## Matched intervention and implementation evidence

Same Qwen/Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, fresh96 parent bytes, rank8/alpha16 module layout, learning rate 5e-5, new AdamW, seed42, disabled dropout, batch/accumulation1 and 128 updates/32 presentations per pair. Native sigmoid DPO plus chosen-token mean NLL has equal weights and beta0.1. The frozen reference is an exact copy of that parent; no extra approximate KL or introspective SFT is added. Objective, negative texts and padding change together versus chosen-only; this is not an isolated objective-only effect or the full published Open Character Training recipe.

The four actual native component-loss checks reproduce the configured weighted sum. Both completion branches have nonzero logit gradients; prompt/padding/final prediction positions have zero direct loss gradient. The reference stays fixed. All128 real optimizer gradient checks are finite,496 adapter tensors change, and saved/reloaded tensors match after perturbation. Actual processing is496480 sequence tokens,92640 both-completion tokens and46240 chosen-supervised tokens. Fitted combined loss is0.000230; pair reward accuracy1.0 measures optimized fitted preferences, not generation quality.

All arms retain NVIDIA RTX PRO 6000 Blackwell Server Edition, pinned Torch2.8.0+cu128/Transformers5.17.0/TRL1.14.1/PEFT0.21.1, BF16 SDPA, the same generation helper, native thinking disabled and greedy2048 allowance. Training takes313.02 seconds and peaks at29.94GiB versus chosen-only312.45 seconds/19.87GiB. All15 new complete answers were read, uncapped, generating4611 tokens in110.64 seconds. Four positively owned GPU identities exited naturally; unfamiliar processes were untouched. New DPO branch96+128=224, chosen-only sibling224 retained, cumulative Aurora Qwen3.5 updates1054; historical sibling352 and Qwen2.5 reference582 remain separate.

## Inspected comparison

Counts are met content units, with unratable counts separate. Strict pass also requires every source/application/universal check and applicable output limits. The known-authority row uses its separately frozen A5; all other units are unchanged.

| Request | Base | Fresh96 | Chosen-only224 | DPO+NLL224 |
|---|---:|---:|---:|---:|
| WPS card |21/24|24/24|24/24|24/24|
| WPS raw |22/24|24/24|24/24|24/24|
| WPS full repair |16+1 unratable/24|24/24|24/24|24/24|
| WPS wording variation |21+1 unratable/24|24/24|24/24|24/24|
| WPS partial repair |17+2 unratable/24|20/24|22/24|20+2 unratable/24|
| Mali raw |6/14|9+1 unratable/14|14/14|14/14|
| Mali plan |9/14|11+1 unratable/14|14/14|11+1 unratable/14|
| Sanctions Brazil raw |6+1 unratable/14|6/14|6+2 unratable/14|9/14|
| Sanctions Brazil plan |8/14|8/14|11/14|12/14|
| Sanctions India raw |6/14|6+1 unratable/14|5+1 unratable/14|5+3 unratable/14|
| Sanctions India plan |8+1 unratable/14|6+2 unratable/14|9+1 unratable/14|5/14|
| India hypothetical known authority |8+1 unratable/14|13/14|12/14|10+1 unratable/14|

Five new answers reproduce their preferred text exactly: WPS card/raw/wording/full repair and Mali raw. Their prior source audits replay unchanged; the own-wording instruction remains unmet, separately from source coverage.

Mali plan omits October and SOFA detail. “Some movement/import concessions ... in exchange” may bargain over source-required access or mean ordinary coordination; lost-mandate temporal scope is also unclear. No full source pass. Partial WPS correctly acknowledges restored services, removed conviction and remaining validation, then says “This does not restore the omitted comprehensive services.” Current inclusion/effective access versus historical omission is unratable. Its four narrow state/application units fall from chosen-only4/4 to2 met +2 unratable/4; both concrete trade-offs remain omitted.

Brazil raw improves supplied sanction-harm details and urgent release with subsequent reporting, but drops explicit favourable-vote meaning, legitimate-tool/Indian-request ownership/ICJ detail and the future-vote uncertainty answer. Brazil plan retains the past favourable vote and correctly attributes Indian requests; two source details still fail. India raw projects recipient verification into the historical textual requests that were not fully addressed and proposes prior risk reporting with uncertain urgent-access scope. “Endorsement ... belongs to the two supplying countries” may describe competence or assert commitment, so it is unratable.

India plan now denies Indian official endorsement but states “Brazil ... promised a favourable vote.” Brazil's actual historical yes vote does not establish that promise. The later uncertainty clause does not certify the invented pledge. This answer fails all four universal source checks and drops substantial Indian detail. The known-authority answer correctly acknowledges the hypothetical Indian endorsement, but omits source qualifications/trade-off and has unclear national-ban/other-country scope. The narrow authority component succeeds across all four arms; none passes the whole new control.

Original sanctions totals: base28 met +2 unratable/56, parent26+3/56, chosen-only31+4/56 and DPO31+3/56. All four outside-family strict passes remain false. The local correction is not a source-faithful persona, native vote, autonomous multi-agent or independent OOD gain.

## Decision and reproducibility

Keep every arm. Prefer the chosen-only arm's stronger Mali/partial-state retention as the development reference. Candidate: add two complete source-audited raw India sanctions positives for absent versus explicitly supplied hypothetical authority, sharing national facts and preserving past-Brazil-vote/future-promise distinctions, immediate urgent access and a concrete competing risk. Rehearse the unchanged four positives with chosen-only training from the original fresh96 parent,32 presentations each across six pairs=192 new updates. Data/dose changes would be coupled. Freeze a separate outside-fitting family and strong base-plus-plan controls before calls/optimization; inspect results before further scaling. No next pack, fit, queue or sweep is prepared.

Portable source/token/pair/control/reference/update/weight/annotation replay passes. The verifier initially rejected a historical optional empty `partial_state_ratings` field; it now normalizes only that absent/empty field while requiring unchanged primitive ratings, reasons and other metadata. Failed code/traceback/receipt are preserved; zero new model calls, optimizer steps or GPU launches were caused by that failure. No fresh ML software-test count, independent review or NCCL validation is claimed.

Evidence: [target audit](../reports/minimal-endorsement-target-audit-20261006.json), [preparation](../reports/minimal-endorsement-preparation-20261006.json), [measured checkpoint/ownership](../reports/minimal-endorsement-checkpoint-20261006.json), [portable replay](../reports/minimal-endorsement-20261006-v1.json). Packs: `data/prepared/minimal-endorsement-20261006-v1`, `data/prepared/endorsement-authority-eval-20261006-v1`. Actual launches: `runs/aurora-endorsement-authority-{base,parent,chosen}-20261006-v1`, `runs/aurora-minimal-endorsement-fit-20261006-v1`. Parent/learned/other retained weights and every full output/review remain in their recorded directories.
