# What we propose to do next

[Start here](README.md) · [SFT trials](SFT_TRIALS.md)

**Status:** research is paused. These are proposed decisions, not launched experiments or a training queue. The old explicit seed-only control and atomic-token arm remain unrun; neither is a prerequisite for this plan.

## First, make the evidence trustworthy to new people

Have a collaborator independently read the complete selected sources and grade the existing complete answers. The current targets, criteria and scores were largely produced by the same assistant. Preserve disagreements and uncertain cases. In particular, inspect cases receiving all five content checks despite an additional fidelity error, and the active/proactive partial-state ambiguity.

This review should identify which failures concern missing source information, mistaken attribution, proposal-state reasoning, authority, or mere wording/length. Those failures require different interventions.

## Next proposed model test: change only the requested country

**Question:** with the same complete evidence and the same proposed policy, does asking for India versus the UK appropriately change the source-backed recommendation, without handing the model a decision rule?

**Context:** complete India/UK climate statements from S/PV.8923 (9 December 2021), with relevant meeting context and clear country/date/capacity attribution. India opposed a separate Council climate/security track and favored inclusive UNFCCC consensus. The UK supported Council reporting and a Council role. Both supported Glasgow climate action. Do not equate national governments with populations or infer private utilities from public statements.

**Format:** native chat with one common source dossier and task. Change only the requested delegation within each draft. No completed fact map, action rule, target answer or future vote label.

**Two draft conditions:**

- **Draft A:** adds a Council reporting track while retaining UNFCCC negotiations. This should expose the documented institutional difference.
- **Draft B:** supports voluntary country-owned Glasgow implementation through the existing UNFCCC process without adding a Council track. This allows legitimate agreement and tests an “India always rejects” shortcut.

**First execution, if resumed:** generate only two base-model answers for Draft A, then read them. If sources or criteria are ambiguous, fix the task before comparing weights. If a real failure remains, compare the saved Trial 6 (`native40`) adapter on identical inputs, then inspect. Test Draft B before crediting a gain. At most eight answers across two roles × two drafts × two weight arms, with inspection between stages; no fit is implied.

**Why Trial 6 as the comparator:** its recorded direct full-Brazil coverage is stronger than Trial 7's. The newest adapter is not automatically the best one.

**What we grade:** preserve the requested country's position, recognize the actual draft, connect a source-backed reason to advice, and distinguish analytical recommendations from official authority. Preserve uncertainty; do not insist on one arbitrary vote label or manufacture disagreement.

**Decisions from the result:**

- Base succeeds: this test does not justify more training. Seek a harder source-identifiable case or independently held episode.
- Both weight arms misread the same supplied evidence: repair reading/context attribution before changing the optimizer.
- Evidence is read correctly but advice ignores the proposal change: consider a minimal contrastive complete-answer example after independent source review.
- Adapter improves Draft A but wrongly forces disagreement on Draft B: reject a broad persona gain.

The sources already appeared in earlier training. This first diagnostic is exposed development, not sealed OOD. A later substantive claim needs a new event/family, controlled information availability, a strong base-plus-evidence baseline and independent review. Interactive negotiation comes after the individual behavior is dependable; we have not demonstrated a multi-agent advantage.

[Original source-verified design](../ROLE_CONTRAST_DESIGN_20261019.md) · [Design receipt and verified spans](../../reports/role-contrast-design-20261019-v1.json)
