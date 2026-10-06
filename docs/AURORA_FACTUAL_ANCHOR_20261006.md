# One actual-error preference pair with a faithful-answer anchor, 6 October 2026

One complete source-faithful memo can be learned from an actual writer error. A 32-update DPO-plus-chosen-NLL fit changes the given-card answer from **19/24 to 24/24**, with all original source/synthesis checks, and reproduces the entire preferred answer. Adding an own-wording instruction still produces that exact answer. Removing the card, however, leaves invented UK vote/concession claims and only **17/24** source units. This is a concrete fitting win with an input-dependent limit, not dependable country-persona transfer or an isolated demonstration that DPO outperforms SFT.

This checkpoint adds **32 optimizer updates and 18 public generations**, all read in full; none caps. Aurora Qwen3.5 cumulative updates become **446**. The new branch has **160 parent +32 new =192** updates. Reference Qwen2.5 remains **582**; Germany/China and all earlier branches remain preserved.

## One inspected pair and frozen checks

The preferred answer is a 267-word memo preserving all 24 original national requirements: historical adoption and criticism, comprehensive survivor care, France's involuntary-pregnancy/termination right and reaffirmed 1889/2106 framework, the UK's civil society and remaining justice/accountability assessment, both real continuing-care commitments, unknown future votes and a concrete analytical parallel-care recommendation. Its input is the original joint WPS memo question plus the explicitly edited audited card from the preceding checkpoint. The rejected answer is the actual saved adapter's 248-word output, with country pooling and omissions. Both complete texts are retained. This compares a complete faithful answer with an actual error, not a single-span attribution-only contrast.

Before optimization, all selected texts were read: both entire France/UK post-vote speeches from S/PV.8514, 23 April 2019; the entire edited card and its ten repairs; both complete Brazil/UK Mali post-adoption speeches from S/PV.9365, 30 June 2023; the chosen/rejected answer; all five prompts; the 24 WPS and 14 UK Mali criteria and applicable source/synthesis guards. Repeated source bytes equal the already-read full statements. One initial CPU preflight used a raw UTF-8 hash instead of the original JSON-canonical text digest; the corrected guard uses the original digest function, with no source changes, model loading or optimization from that failure.

Five checks were frozen before the fit: exact given-card input, raw WPS input without the card, given-card input with an added wording instruction, UK Mali pressure, and the matching strong checked-plan Mali control. Base and the saved parent each produced five fresh answers with matching inputs; all were read before optimization. The first two outputs per arm exactly reproduce earlier actual outputs and retain the original annotations after a full reread. The new cases have new dependent assistant annotations. WPS is now a fitting event; Mali is outside this selected branch's fitting but historically exposed project development, not sealed OOD.

## Actual method and fitting evidence

Use the pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, unchanged runtime and **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Greedy nonthinking generation retains the 2,048-token allowance and 8,192 combined guard. Warm-start the same 160-update adapter with a new optimizer, rank-8 LoRA, learning rate 5e-5, batch one and accumulation one. Dropout is explicitly disabled for this preference trial.

The pinned TRL trainer combines sigmoid DPO, beta .1, with mean chosen-token NLL, weights 1 and 1. Its reference is an exact frozen copy of the starting adapter, rather than the adapter-disabled base. Reference scores are precomputed. No additional approximate KL or introspective stage is used. This is not the original Open Character recipe, and differs from the historical fresh-base pure-DPO trial in data, initialization, budget and dropout. It does not isolate an objective effect against matched chosen-only SFT.

Actual native tokenization/collation checks exclude prompt and padding from preference loss, retain all source/target tokens, and verify the frozen IDs. The real masked-pair loss check gives DPO .693147 + chosen NLL 1.960938 = combined 2.654085 exactly, before any optimizer update. The 32 presentations process **179,488 sequence tokens and 21,408 preference-completion tokens**, including both chosen and rejected completions. All 32 gradient checks pass, adapter tensors change, the frozen reference tensor digest remains exact, and saved default-adapter tensors plus perturb/reload logits verify. Training takes **149.43 seconds**, peaking at **29.92 GiB**. Twenty-four existing training/preference software guards pass; those are technical evidence, not persona ratings.

## All five fitting/transfer outputs

| Check | Base | Starting adapter | New adapter |
|---|---|---|---|
| Exact given-card memo |21/24|19/24|24/24, source pass; target verbatim|
| Raw WPS sources |22/24|17 met +3 unratable/24|17/24, source failures|
| Card plus wording instruction |21 met +1 unratable/24|18/24|24/24, source pass; target verbatim|
| UK Mali pressure |6/14|4/14|6 met +1 unratable/14|
| UK Mali checked plan |9/14|8/14|11 met +1 unratable/14|

The new raw WPS answer repairs the explicit French termination detail but invents UK accession to a vote and explanations for historical concessions, borrows a French autonomy claim, and omits the reaffirmed framework and UK remaining-work assessment. It also omits an explicit unknown-future-vote answer. Frozen H8 is a negative no-guarantee criterion and is met by silence; this requested-task omission is recorded separately rather than silently changing the rubric. The source pass therefore must not be treated as full task compliance. Likewise, copying the preferred answer under the own-wording instruction is not flexible paraphrasing.

Mali source coverage improves relative to the parent, especially with supplied checked points, but Wagner/October protection facts, practical tensions or precise commitment boundaries remain missing or ambiguous. Source judgments about restriction polarity, welcome-object compression and election calls versus commitments await independent adjudication. No outside-event source pass occurs. Do not combine these different denominators into a method ranking.

## Metric contamination found and corrected

The three nontraining component-loss probes appended entries to the trainer's evaluation metric lists. Its later fitted-pair loss was clean, but several reported reward/log-probability metrics averaged those initial probes with the fitted evaluation: the original reward accuracy was .25 despite a positive final margin. The original run, metrics and archived code remain unchanged.

A separate cold evaluation loads the exact saved tensors, reconstructs the original frozen-parent reference scores, verifies their equality, and evaluates only the single fitted pair with clean metrics. Loss remains **.000439934**; chosen log probability is **−.150417**, rejected **−522.374634**, reward margin **115.654907**, fitted reward accuracy **1.0**. These are fitting diagnostics, not held-out quality. The replay makes zero optimizer updates and no public generations. The working runner now clears accumulated metrics after probes; future fits require matching new baseline records. The helper's historical transcript `scope` string also remains unchanged; actual case family/condition and launch scope supply the correct development classification.

## Legitimate repair after inspection

After all five new outputs were read, freeze one further raw-source development question: immediate comprehensive care, pregnancy-choice support, no conviction/evidence gate, and consent-based referrals/accountability in parallel. It explicitly supersedes the old hypothetical restriction; historical resolution omissions remain historical. No new national statement or future-vote authority is supplied. The unchanged H5 applies its revision branch.

Base, parent and new saved weights each produce one fully read answer on identical inputs. **All three recognize the repair** rather than repeat obsolete withholding objections. Source coverage is respectively **16 met +1 unratable/24**, **17/24**, and **14 met +2 unratable/24**; no source pass. The new answer drops most UK specifics and treats documented French concessions as unknown. None explains a concrete remaining coordination trade-off. Thus the small fit retains legitimate updating on this one supplied repair but does not establish improved adaptive or multi-agent behavior.

## Decision and preserved evidence

The given-card target is learned faithfully, while raw input and outside-family source fidelity still fail. The next minimal candidate keeps the preferred 267-word answer unchanged and adds its raw-source input paired with the actual inspected raw error, retaining the original card pair and frozen card/repair/outside-family controls. This tests missing input coverage before introducing new national claims or another objective. Inspect one fit before expanding. No next pack, fit, queue or sweep is prepared. Preserve the parent and this new branch.

Across 18 answers: **6,721 generated tokens and 137.94 seconds** of measured generation, excluding loading/artifact work. All seven recorded GPU process identities exited naturally; zero terminations and unfamiliar-process changes. Portable replay verifies source spans/PDF hashes, actual input/output IDs, paired weights/runtime/hardware/code, masks, reference state, objective arithmetic, optimizer counters, saved/cold-loaded tensors and stored annotation arithmetic. Same unblinded assistant authored/audited/graded; independent review remains pending. No intrinsic country-persona, native vote prediction or autonomous multi-agent gain is claimed.

Evidence: `reports/factual-anchor-checkpoint-20261006.json`, `factual-anchor-20261006-v1.json`, `factual-repair-20261006-v1.json`, `factual-anchor-metrics-correction-20261006.json`, and `factual-anchor-resource-status-20261006.json`. Frozen data are `data/prepared/factual-anchor-20261006-v1` and the two `factual-repair-20261006-v1*` packs. Actual launches, code, outputs, reviews, reference probabilities and fitted weights are in `runs/aurora-factual-*`. Earlier evidence is unchanged.
