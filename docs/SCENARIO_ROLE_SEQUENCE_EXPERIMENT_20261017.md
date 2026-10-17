# Scenario-conditioned delegation sequences — 17 October 2026

The user proposes representing each Council meeting as a scenario followed by ordered country/delegation messages, then applying SFT to authentic speeches with explicit role markers. This is a useful change of learning target from the recent extraction/application/memo tasks. Some current prompts already contain issue context; what is new is making the original meeting setting, speaker capacity and chronological history first-class training inputs.

Status: research definition and CPU representation prototype complete; no model inference, training, model-quality result or GPU allocation. The prototype is explicitly not a fitting release. Cumulative Qwen3.5 remains 3,934 updates; separate Qwen2.5 reproduction remains 582. Earlier adapters, Germany/China work and the unrun explicit seed-only control are preserved.

## Closest research and what to borrow

**CoSER, ICML 2025**, is the closest precedent. Its given-circumstance training conditions on scene/profile information and authentic dialogue; selected-character utterances receive the loss while other characters' messages provide context. Appendix B specifies ShareGPT conversion, varied context formats, separate environment/next-speaker tasks and general SFT mixing. It develops 8B and 70B models. We should borrow the selected-speaker objective and scene-based evaluation, while replacing fictional character profiles with dated institutional metadata. Its book pipeline can infer thoughts; public diplomatic records do not justify inventing private motives or inner monologues. Reviewed §4.2 and Appendix B plus pinned released-format/code examples. [Paper](https://proceedings.mlr.press/v267/wang25dk.html), [code](https://github.com/Neph0s/CoSER).

**Ditto, ACL 2024**, trains role-play from contextual self-generated dialogue and distinguishes learnable role style from knowledge/capability limits. That supports testing policy content separately from diplomatic phrasing, rather than treating recognizable voice as sufficient evidence. Its synthetic character data and evaluation do not validate national-policy simulation. [Paper](https://aclanthology.org/2024.acl-long.423/).

Two related NeurIPS 2025 papers are adjacent design references, not reproduced methods: [Thinking in Character](https://proceedings.neurips.cc/paper_files/paper/2025/hash/aacca7b6a20d157112205a44f42821c8-Abstract-Conference.html) studies role-aware reasoning; [Codifying Character Logic](https://proceedings.neurips.cc/paper_files/paper/2025/hash/15294ba2dcfb4521274f7aa1c26f4dd4-Abstract-Conference.html) makes role behavior depend on scene-dependent rules. Only their proceedings abstracts were checked here. Neither establishes that a Council transcript reveals a government's internal reasoning.

The existing [Open Character reproduction](OPEN_CHARACTER_REPRODUCTION_20261004.md) remains the successful persistent-style control. The [14 October assessment](STORAGE_SYNC_AND_RESEARCH_DIRECTION_20261014.md) identified source/authority/state failures. This proposal addresses a different part of the gap: learning directly from authentic situated institutional speech, rather than learning our assistant's rewritten answer targets. Special tokens alone are not a novelty claim. The promising question is whether the learned behavior changes appropriately across topic, institutional capacity and new evidence.

## Representation and objective

Represent the data logically as:

```text
<scenario>
  meeting, date, agenda, public documents and information available at this point
<country/delegation/capacity message>
  actual earlier speech
<record event>
  an event that has already occurred, if relevant
<requested country/delegation/capacity>
  [predict the selected authentic speech]
```

Preserve actual speaking order, not alphabetical country order. Country, institution, date, national-versus-chair capacity and representative are separate fields. A delegate's national stance is not the Council president's institutional authority. These represent public institutional behavior, not population values or an individual's private personality. English translations can reflect UN translation conventions; stylistic differences require care. Authentic statements can also contain disputed claims: source fidelity and factual truth are separate evaluation axes. A national utterance is not a verified neutral finding.

The conditional target is `P(speech | scenario, preceding turns, requested institutional role)`. Both scenario and role should affect substance as well as phrasing; a prefix does not architecturally disentangle them. Use ordinary causal response-only cross-entropy on the selected speech and existing end-of-message token. Mask scenario, history and target header from direct loss. Gradients from the speech still pass through contextual role embeddings. One target turn per example makes masks and exposure easy to audit; a shared model learns different countries across examples. Predicting the next speaker is a separate task, not required for the first experiment.

A scenario must be compiled from information available before the target. A summary generated from the complete meeting could leak the target or later outcome. Do not provide future speeches, votes or post-hoc explanations to pre-vote examples. When a vote already precedes a speech, including it is correct reconstruction context, but the example cannot measure vote forecasting. Later meeting state belongs in observed events or an explicitly dated state card.

For long meetings, freeze one common context policy after inspecting CPU lengths. Prefer full preceding history when it fits. Otherwise retain a contiguous suffix of complete past turns and explicitly record omitted history; never truncate inside a speech or select context using the target. Earlier state cards must be source-grounded and available before the target. Match the policy in every arm.

## Special-token implementation on our pinned model

The actual Qwen3.5 template rejects an all-custom `scenario`/country role list and rejects `France` even after a valid user message. Changing JSON role names alone therefore fails. A custom serializer over the causal LM is required for the user's exact format; a CoSER-style native-chat wrapper is a useful comparison.

The CPU implementation uses three structural markers and four country markers. The same literal strings can be tokenized as existing subwords or registered as seven atomic tokens. No base tokenizer/model file is modified. Marker exposure must be recorded separately: unused or context-only country markers are not evidence of learned national behavior.

Important measured details: native tokenizer length 248,077; atomic length 248,084; model embedding rows 248,320. The seven token IDs fit in existing capacity. Do not blindly resize to tokenizer length, which would shrink this padded matrix. Verify capacity and tied input/output weights explicitly. The model is tied; the installed PEFT exposes selective token training. Before an actual fit, validate trainable row gradients, tied output behavior, initialization and adapter-plus-tokenizer reload on the actual architecture. LoRA with frozen new embedding rows is not a proper test of learned role markers. Use [PEFT selective trainable-token guidance](https://huggingface.co/docs/peft/package_reference/trainable_tokens), checked against installed code; avoid saving the full large embedding matrix accidentally.

If new rows are initialized from semantic subword averages, freeze and record that rule before comparing arms. The token treatment includes new trainable row parameters and shorter inputs, so equal target presentations do not imply equal FLOPs or isolate token segmentation alone. Preserve original special-token flags and target tokenization. Each arm needs its own untrained, identically initialized baseline.

## What was actually inspected and built

The same root assistant read the complete existing S/PV.9214 extracted record: 32,718 characters / 32,785 bytes, including every earlier speech and the three selected national targets. No independent review is implied. Its literal transitions yield eighteen chronological segments: national speeches, chair interventions and recorded events.

Concrete source checks matter:

- The agenda is general issues relating to sanctions; draft S/2022/925 is before the Council at opening.
- The US statement precedes the vote. UK, Brazil and India's selected national statements follow it. The pre-vote prototype context excludes the later vote event.
- Mrs. Kamboj explicitly changes from chair to India's representative and resumes chair functions afterward. These are separate segments/capacities.
- France appears in attendance and voting, but has no recorded national speech in this meeting. No French target is invented.

The [full UK rendering](../research/scenario-role-20261017/example-GBR.txt) shows the first scenario, genuine ordered history and precisely separated target. [Preview receipt](../research/scenario-role-20261017/preview.json) records source spans, hashes, token IDs and both representations. Full-sequence plain/atomic lengths are UK 2,289/2,208, Brazil 2,767/2,674 and India 6,363/6,208. Supervised speech-plus-end token counts stay identical: 261, 436 and 574. All three prefixes leave room for a 2,048-token answer inside 8,192. Tokenizer-only save/reload reproduces IDs/masks; actual model/adapter reload is not tested.

The extraction retains soft-hyphen/line-wrap artifacts and at least one apparent printed/extraction typo. Preserve the raw source, then audit any normalization against the PDF with a versioned transformation ledger before using it as a fitting target. The preview is historical development, not a held-out benchmark, and is deliberately not training-ready. Seven sequence tests plus seven existing overlay tests pass; these are software checks. No output-quality improvement is claimed.

Two CPU preparation failures were resolved: the installed Transformers API uses `extra_special_tokens`/`replace_extra_special_tokens`, and system Python lacks pytest. The latter checks ran in a separate scratch-cached pinned pytest environment without modifying either training runtime. Paper/code acquisitions and hashes are retained; an unexpectedly 88 MB released example file was inspected for schema, then removed with its URL/hash/schema audit preserved. No existing research dataset was removed.

## Smallest informative training experiment

Select **UK and India in two different meeting topics**, provisionally the existing sanctions and climate records, giving four complete authentic target speeches. Hand-audit all four, their exact prior context, source normalization and public scenario fields before fitting. Freeze one third whole policy episode for development evaluation first. Do not split turns from the same meeting across train/test, and group linked debates/votes/drafts together. Existing familiar events remain exposed development; unknown pretraining overlap prevents a claim of clean unseen historical data.

Start from the same pinned Qwen3.5-4B base and fresh rank-8 LoRA, not the eight-example application adapter. Keep the verified response-only objective. A bounded candidate budget is 32 presentations per target (128 actual updates with batch/accumulation one), not 128 distinct examples. Exact LR/context/initialization must be locked after data inspection; no runnable fit config or queue is prepared here.

First fit the readable-marker stream. Inspect all four fitting replies and a small frozen held-episode comparison before deciding anything else. If it cannot learn the basic task or preserves no relevant behavior, fix that issue before a token experiment. If it provides a useful reference, fit one matched atomic-marker arm using identical strings, targets, histories and target exposure, then inspect it. This is one conditional comparison, not a sweep. Retain strong ordinary-chat/role prompting controls with the same information.

The first substantive question is whether the model learns role-and-scenario-sensitive behavior from authentic speeches beyond formatting. The matched token comparison is secondary. Four targets can support a development decision, not population-level persona improvement.

## Make the evaluation distinguish the explanations

1. **Authentic continuation:** score common target speech tokens on whole held meetings; inspect complete generations for material stance/fact preservation, temporal status and invented commitments. Report base-to-fit changes within each representation. Lower speech loss or verbatim fitting reproduction alone is insufficient.
2. **Role sensitivity on the same issue:** use source-verified contrasting priorities, aligned country/representative/capacity fields and a common admissible context. Remove explicit target-name/signature shortcuts from scored material. A diagnostic role-likelihood margin is supplementary; it measures authorship discrimination, not uniquely correct policy. Do not require different decisions when agreement is source-compatible.
3. **Scenario sensitivity for one role:** pair a proposal containing an actual defect with a minimally repaired version. Require the agent to recognize the change while preserving supported priorities and uncertainty. Construct new fictional applications, clearly separate from recorded historical decisions.
4. **Institutional capacity:** test national delegation versus Council chair with their distinct authorities. Keep target-identity information coherent. A role ablation that leaves the representative's name or an upcoming-speaker announcement untouched does not remove the role signal.
5. **Interaction, only if the individual behavior transfers:** compare revision with a real peer against self-revision, independent proposals and a single analyst with pooled information. Council speeches alone do not prove spontaneous negotiation; many may be prepared statements. Score actual corrections and valid constraints rather than agreement or rhetorical distinctiveness.

Use prospectively frozen material criteria and blinded source-informed review where available; retain same-assistant-development status otherwise. Keep style/readability separate from policy fidelity, inference from documented commitments and software checks from quality. Do not change old grades to suit this experiment.

**A strong positive signal:** better held-episode policy/role fidelity plus appropriate responses to new scenario changes, beyond strong base prompting, without increased invented authority. If the atomic arm also helps under matched exposure, learned role markers become a useful implementation result.

**A surprising and informative result:** speech likelihood/style improves but role swaps or repaired scenarios leave policy behavior unchanged. That would show we learned diplomatic surface form more than situated institutional behavior. If plain markers match atomic tokens, use the simpler representation. If native data works where our rewritten targets failed, the data/learning-target change deserves follow-up, without claiming it isolates data authenticity from every changed factor.

The compelling long-term project is a source-auditable model of how institutional positions depend on situations and authority, with native transcript training as the starting point. This could inform persona and multi-agent work; a special-token formatting gain alone would be a limited contribution.
