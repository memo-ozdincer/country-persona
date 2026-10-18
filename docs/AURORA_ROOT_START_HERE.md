# Country Persona research on Aurora

Authoritative workspace: `/mfs1/u/memo/country-persona-research/workspaces/persona-20260929-v1`.
Stable shortcut: `/mfs1/u/memo/country-persona-research/current`.
Read that workspace's `AGENTS.md`, `START_HERE.md`, `docs/PROJECT_HANDOFF.md` and `docs/CURRENT_STATE.md`. This scratch-root guide is navigation, not a second experiment chronology. Its tracked source is `docs/AURORA_ROOT_START_HERE.md` in the workspace.

Latest measured result: `docs/SCENARIO_ROLE_CHECKPOINT_20261018.md`. Fourteen inspected outputs and one authentic four-speech/128-update Qwen3.5-4B fit. Four fitting speeches exact; both Ukraine development cases fail in raw/native adapter formats and source NLL worsens. No persona/agent gain; do not scale or start atomic tokens. All 128 traces/reload checks pass; all five owned GPU workers exited. Cumulative Qwen3.5 4,062; fresh branch128; older paired-Brazil256/reference Qwen2.5 582 preserved. Next candidate: native-chat/source-bound pre-target evidence and role/topic controls before more fitting; no next queue. Old explicit seed-only control remains unrun.

The immutable v47 evidence snapshot remains available as a staging tree, ordered local archive parts and a private GitHub release. The redundant whole archive was intentionally removed after verification; restore it from parts if needed. Subsequent code/documentation/audit changes live in Git. `CURRENT_HANDOFF.json` distinguishes snapshot base commit, current workspace commit, archive lifecycle and final verification/sync receipts.

From the workspace, after committing changes:

```bash
python3 scripts/verify_workspace_overlay.py --root . \
  --manifest-sha256 fafbe6a52c944fe7ceb9abc473b7f7924566c1260d8d925691aedf20a915ea9b
```

The original snapshot verifier is for an unchanged snapshot; see `docs/STORAGE_POLICY.md` for the two-layer restore and verification contract. Preserve all historical experiment artifacts and Germany/China work. Keep model/cache/bulky files under this scratch root. Credentials stay outside Git and snapshots; source `/h/405/memo/.config/country-persona/aurora-env.sh` for private paths without displaying values.
