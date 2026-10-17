# Country Persona research

Read `AGENTS.md`, then [the full handoff](docs/PROJECT_HANDOFF.md). Use [current state](docs/CURRENT_STATE.md) for the latest boundary and [14 October audit and research assessment](docs/STORAGE_SYNC_AND_RESEARCH_DIRECTION_20261014.md) for storage findings and the proposed direction. Dated reports are the evidence; historical next-step paragraphs are not a run queue.

## Current research

Newest work: [source-audited scenario/delegation SFT setup](docs/SCENARIO_ROLE_SFT_READINESS_20261017.md), following the [CoSER-grounded design](docs/SCENARIO_ROLE_SEQUENCE_EXPERIMENT_20261017.md). Four authentic fitting speeches, two fit-excluded development speeches, complete source maps, a frozen small-fit config and separate-operation harness are prepared. Thirty-five software/runtime checks and an eight-step random tiny-Qwen CPU trace/reload pass. Zero new production answers/updates; actual 4B execution and independent semantic review remain pending. Next checkpoint is two base Ukraine replies and inspection, before any dependent fit; no automatic queue.

Qwen3.5-4B small training works. The strongest recent local result is source-conditioned application of repaired versus unrepaired proposal clauses, including two excluded Brazilian combinations. This does not establish national persona, diplomatic reasoning or multi-agent gains. The latest measured interaction has twelve strict failures and a prompt-mode caveat. A four-answer explicit seed-only control is prepared but unrun; inspect base answers before adapter answers, with no automatic launch or fit.

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
