# Country Persona research

**For collaborators:** [onboarding](docs/onboarding/README.md), [SFT Trials 1–7](docs/onboarding/SFT_TRIALS.md), [environment/data setup](docs/onboarding/ENVIRONMENTS.md), and [the master evidence index](docs/evidence/README.md). The guides separate completed results from proposed next work.

**Direct private data:** [Hugging Face dataset](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data) and [download/verification instructions](docs/onboarding/PRIVATE_HF_DATA.md). The export adds no model work. The Hub dataset is private; GitHub currently reports public repository visibility, which this task did not change.

The recursive research goal is **paused at the user's request**. Read the [complete work/results report](docs/CONSOLIDATED_RESULTS_20261019.md) for the reconciled experiment ledger, best results, failures and remaining unrun designs. All started latest model trials are complete; no new model run was needed for this report.

Read `AGENTS.md`, then [the full handoff](docs/PROJECT_HANDOFF.md). Use [current state](docs/CURRENT_STATE.md) for the latest boundary and [14 October audit and research assessment](docs/STORAGE_SYNC_AND_RESEARCH_DIRECTION_20261014.md) for storage findings and the proposed direction. Dated reports are the evidence; historical next-step paragraphs are not a run queue.

## Current research

Newest training/evaluation: [19 October scope/partial-state checkpoint](docs/NATIVE_SCOPE_PARTIAL_CHECKPOINT_20261019.md). One fresh48-update fit adds one81-word scoped partial-plan example with five old targets unchanged. All25 answers/two composed documents hand-read. Source retention WPS18/18/Brazil9/9; application-only scope0/3→3/3. Full Brazil regresses to8met/3unmet/2uncertain; France257words still fails240cap. Separate typed composition is233words/13material+6guards met, but misses a required heading. One adaptive provided-rule prototype, not a general persona/collective/strongOOD result. CumulativeQwen3.5 4182; six owned workers exited; no next pack/fit/queue. Metadata/restore manifests separate Git evidence from adapter assets. Prior [native40](docs/NATIVE_APPLICATION_WRITER_CHECKPOINT_20261019.md) and [native32](docs/NATIVE_PLAN_WRITER_CHECKPOINT_20261019.md) remain original evidence.

[Earlier grounded-role decomposition](docs/GROUNDED_ROLE_CHECKPOINT_20261019.md) and [18 October raw-speech fit](docs/SCENARIO_ROLE_CHECKPOINT_20261018.md) remain original evidence. Keep all branches/failures; do not scale the failed raw-speech branch or start atomic tokens. [Source-audited setup](docs/SCENARIO_ROLE_SFT_READINESS_20261017.md) and [CoSER-grounded design](docs/SCENARIO_ROLE_SEQUENCE_EXPERIMENT_20261017.md) remain method evidence. New bounded metadata is in Git; the native32 adapter has a separate delivery manifest/receipt.

Earlier application-state results remain useful components, not validated national persona or multi-agent gains. The four-answer explicit seed-only control remains preserved and unrun; the latest request does not auto-launch it.

- [Latest measured interaction](docs/AURORA_SANCTIONS_INTERACTION_20261007.md)
- [Prepared, unrun explicit-mode control](docs/EXPLICIT_SEED_PREPARATION_20261007.md)
- [Eight-example application result](docs/AURORA_PAIRED_BRAZIL_APPLICATION_20261007.md)
- [Published persona reproduction](docs/OPEN_CHARACTER_REPRODUCTION_20261004.md)
- [Research goal-gap audit and papers](docs/PERSONA_GOAL_GAP_RESEARCH_20261001.md)
- [Original 42-response source review](docs/DELIBERATION_SOURCE_REVIEW_20260928.md)

## Verify this workspace

The complete private v47 snapshot contains 14,958 files / 6,140,263,018 bytes at base commit `97f0f3bbbdce291eb6444d0d82d1c0c53d1c6644`. Code/documentation changes after that snapshot are preserved in Git. Verify both layers without regenerating snapshot hashes:

```bash
python3 scripts/verify_workspace_overlay.py --root . \
  --manifest-sha256 fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b
```

The original `scripts/verify_research_handoff.py` checks an unchanged v47 snapshot. Intentional committed overlays will make that original verifier fail in this live checkout; this is expected and must not be hidden by changing its manifest. The overlay verifier still hashes all unchanged ignored payloads and all committed Git files, and rejects unexplained changes.

External `/mfs1/u/memo/country-persona-research/CURRENT_HANDOFF.json` records the immutable snapshot, Git overlay and audit receipts. Restore instructions and storage retention are in [handoff operations](docs/HANDOFF_OPERATIONS.md) and [storage policy](docs/STORAGE_POLICY.md). Credentials/base weights/runtime environments stay outside Git and the handoff. Source `/h/405/memo/.config/country-persona/aurora-env.sh` for private credential paths and scratch caches; never display credential values.

Aurora hardware is NVIDIA RTX PRO 6000 Blackwell Server Edition. Another medical project shares the account: leave unfamiliar jobs and processes untouched. Old free/occupied observations and job deadlines are historical.
