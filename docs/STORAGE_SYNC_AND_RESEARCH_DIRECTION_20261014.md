# Storage synchronization and research assessment — 14 October 2026

The latest research payload survived the reported mfs1 outage: all 14,958 manifest files / 6,140,263,018 bytes match their recorded SHA256 values. This audit adds no model calls, training updates or model-quality result. Code and audit receipts are a Git overlay over the unchanged v47 evidence snapshot, avoiding another full archive.

## Integrity and synchronization

- mfs1 is mounted read/write; filesystem reports about 80 TB available and 16% inode usage. Audit writes, reads and atomic metadata replacement succeeded. This does not certify underlying disks/replication or diagnose the previous outage.
- Git object verification exits successfully. Five dangling objects are harmless unreachable trees/blob, not corruption. Initially local HEAD and remote master both equal `97f0f3bbbdce291eb6444d0d82d1c0c53d1c6644`; the named research branch was 39 commits behind. The audit commit synchronizes both branch tips without forcing.
- All eleven pinned Qwen3.5-4B model/tokenizer/config files match the pre-outage model record, including both 5.33/3.99 GB weight shards. Saved experiment adapters/reference papers are covered by the payload verification. Other historical base/merged model bytes and every old snapshot were not rehashed.
- All 11,223 payload JSON files and 79,440 nonempty records in 645 JSONL files parse; compressed streams are excluded from this syntax check. All payload bytes, including compressed files, were hash-checked.
- The current private v47 release has all six expected assets; live GitHub sizes/SHA256 metadata matches its frozen receipt. Remote bytes were not downloaded again. Local whole archive, all four parts and ordered reassembly independently match their frozen hashes.
- No token/private-key pattern detected in 1,213 initially tracked files. This is a bounded pattern scan, not a complete secret detector. Largest tracked file is a 7.64 MB reference PDF; no model weights or huge archives are in Git. Git objects occupy about 22 MB.

Exact receipts are in `reports/storage-sync-20261014-v1/`; [aggregate audit](../reports/storage-sync-audit-20261014-v1.json). Byte integrity/software checks do not certify independent semantic review.

## Storage findings and fixes

Before cleanup, top-level delivery files occupied 170.13 GB: 100.32 GB of whole archives, 69.79 GB of parts and 0.02 GB of other files. This was excessive duplication. Historical stage inventory finds 91 manifest-bearing directories, including intermediate copies. Their apparent payload sizes must not be summed as physical allocation: many files are shared hardlinks. Historical stages were inventoried by manifest rather than recursively reverified.

After verifying the whole v47 archive, every part, ordered combined digest and live remote asset metadata, removed only its redundant 3,641,228,051-byte whole archive. All four local parts, original receipts, immutable stage and private release remain. Reassembly restores the exact original archive without downloading anything. External `CURRENT_HANDOFF.json` explicitly records the changed local archive state. Top-level delivery files are consequently about 166.49 GB; older delivery copies remain preserved, with further verified compaction possible. No dataset, adapter, historical release or experiment was deleted.

Other large files have identifiable purposes: Qwen3.5 model directory about 9.34 GB; published-reference base/merged models and assets about 48.19 GB; runtime/cache files are substantially hardlinked. Cache apparent size is 17.21 GB, but only about 0.49 GB of unique bytes is assigned to it after the environments are counted. These figures exclude unique historical-stage allocation and are not a project-wide physical total.

Three broken links belong to extracted development-package contents: two documentation links and a `libpython3.12.so` development link whose package-relative target was not extracted. They are outside the research payload, not damaged dataset/model files. Both training environments pass CPU package-import checks. No repair of pinned package provenance was needed; these links should not be treated as usable complete system-package installations. Partial-name candidates are setuptools `.tmpl` files and two zero-byte dataset lock files, not unfinished model downloads; locks were left untouched.

[Storage policy](STORAGE_POLICY.md) now separates immutable evidence snapshots from committed code/documentation overlays, retains one necessary delivery representation, prohibits blind retention purges and preserves hardlinked stages. The new pinned overlay verifier hashes unchanged evidence and all tracked files while allowing documented committed code changes. Seven focused tests cover real corruption, symlinks, manifest tampering, deletions, dirty checkouts and cached-index concealment. Session navigation no longer repeats the full chronology in AGENTS/START_HERE; original text remains in Git/v47. The scratch-root guide was also stale at v10/142 Qwen3.5 updates; it now points to current state, with a tracked template to keep it synchronized. No v48 archive is created for this code-only audit.

## Which research directions actually have evidence?

| Direction | What the results support | What is missing |
|---|---|---|
| Diplomatic reasoning | Small source-conditioned application repairs, including retained-versus-removed proposal clauses. | Better admissible decisions or negotiation outcomes on untouched events against strong prompting. |
| Persona adoption | Published Qwen2.5 humorous-character recipe reproduced: default recognition 10.4%→58.6%, strongest neutrality 4.2%→35.2%. | Validated dated national/institutional preferences. Humor/style persistence is a different construct; its classifier is dependent on the paper's evaluation questions. |
| Multi-agent improvement | A controlled starting-draft/peer protocol and inspectable attribution failures. | Positive collective benefit. Latest adapter peer revisions make zero corrections and one regression versus seed-only; all twelve strict answers fail. Mode ambiguity prevents a clean causal diagnosis. |
| Evaluation | Concrete tests of source polarity, actor/authority attribution, repaired states, warranted updates and peer corrections/regressions. | Independent construct/rubric validation, natural held-event families, blinded review and meaningful decision outcomes. |
| Useful component | Given complete compact plans, a trained writer preserves fourteen required meanings on several bounded examples; paired application training fixes two excluded Brazilian clause combinations. | Reliable raw-source end-to-end transfer. Exact fitting-target reproduction is not generalization. |

Sources: [character reproduction](OPEN_CHARACTER_REPRODUCTION_20261004.md), [paired Brazilian application](AURORA_PAIRED_BRAZIL_APPLICATION_20261007.md), [latest interaction](AURORA_SANCTIONS_INTERACTION_20261007.md), [compact planner](AURORA_COMPACT_PLANNER_20261007.md), [goal-gap research](PERSONA_GOAL_GAP_RESEARCH_20261001.md). Same-assistant curation/grading, repeated historical exposure, compound criteria and changing tasks/doses limit attribution. No strong OOD, native prediction or independent persona claim follows from the current results.

## Most promising next direction

My recommendation is to study **whether an institutional agent changes its commitments for the right reasons**. It should retain source-supported constraints under unsupported peer pressure, accept an authenticated change of mandate, notice when a proposal has actually been repaired and avoid inventing another country's endorsement. This joins the useful part of persona persistence with evidence-sensitive reasoning and a necessary condition for reliable collaboration. It is a research hypothesis, not an established new method or novelty claim.

The concrete lead is the contrast between local repaired-state success and interaction failure. The eight-example model passes excluded Brazilian L/M at 85/82 words, yet in discussion falsely attributes a criticism to India and calls fictional safeguards historical. That suggests the problem may be maintaining who said what, what currently holds and who can authorize an update, rather than insufficiently diplomatic phrasing. Structured evidence/authority supervision may help; stronger prompting may explain all the gain. We should test that distinction before another objective search.

Published work reinforces the controls, not a claim of novelty. [Open Character Training](https://arxiv.org/abs/2511.01689) studies persistent persona behavior; our question additionally requires justified change. [Debate or Vote, NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/934252acd87f254d5d4672fbde283bd2-Abstract-Conference.html) finds simple majority voting explains much of the benefit across its seven benchmarks, supporting a strong independent-answer baseline rather than equating discussion with improvement. [CICERO's original project](https://github.com/facebookresearch/diplomacy_cicero) ties dialogue to strategic planning in an executable game; this motivates checking feasible decisions/outcomes here, while recognizing that public institutional statements do not reveal governments' private utilities.

## First decisive study to propose

Before further fitting, freeze a small screen on **two whole event families outside the application fit**, with two dated institutional roles each. Have a source-informed independent reviewer audit material constraints and acceptable choices where available; otherwise explicitly retain same-assistant-development status. Four versions per role give sixteen inputs:

1. A proposal with a material defect relative to the supplied mandate.
2. The minimally repaired proposal, with all other facts fixed.
3. A policy/mandate update authenticated within a clearly fictional institutional fixture.
4. Identical update content asserted only by a peer, without institutional authority.

The last pair must differ only in authority/provenance, not persuasive quality or facts. Keep documentary history separate from new fictional events. Allow multiple source-compatible allocations; do not invent a unique national preference label. Use a comfortable common output allowance and make correct decisions/commitments primary, with detailed source coverage as diagnostics rather than one overloaded word-budget gate. Freeze new criteria prospectively; preserve old grades.

Compare base+sources, the saved adapter+identical sources, and a strong base prompt requiring explicit source/authority/current-state fields on those same sources: 48 answers, no initial training. Retain existing base+checked-plan realization controls as privileged diagnostics, not an end-to-end comparator with hidden answers. Inspect complete outputs and report paired corrections/regressions and results by event; two events are a development screen, not a population-level estimate.

A useful signal would be consistent repaired-state and valid-update decisions without accepting peer-invented commitments, beyond the equally informed strong base prompt. A surprising result would be an adapter that improves factual coverage yet worsens these decisions, or a prompt-only control that solves the failures entirely. Either should change the plan. If no distinction remains after protocol repair, stop claiming a training-method lead. If a reproducible distinction remains, supervise a small set of complete contrasting decisions and reserve another untouched family before fitting. Only then test whether actual exchange improves joint feasibility beyond self-revision, independent proposals and a single analyst with pooled information.

The already prepared four-answer explicit-mode control can close the old protocol ambiguity if that protocol is resumed on a genuinely free GPU. It is not itself the decisive test of this larger direction, and this audit launches neither it nor a new experiment.
