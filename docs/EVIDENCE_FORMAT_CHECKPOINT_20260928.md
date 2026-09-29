# Evidence-format checkpoint — 28 September 2026

**Prepared and locally tested: a nine-call synthesis comparison, including a new South Sudan event. No new model generations or training ran at this checkpoint.** The purpose is to settle a manageable part of the evaluation before the already prepared four-GPU training smoke test: can the final answer preserve supported country positions and uncertainty without inventing consensus?

## What this adds

The [48-generation baseline and diagnostic](DELIBERATION_BASELINE_20260928.md) showed that correct national caveats can disappear during synthesis, and that a source-check instruction can repair one error while introducing another. This comparison separates two possible changes:

| Arm | Required output | What the comparison can diagnose |
|---|---|---|
| Prose control | Country answers, common ground, differences and proposed next steps | Reference behavior with adequate output room |
| Evidence prose | Same substantive task, plus explicit claims, quotations and unresolved positions | Effect of adding evidence requirements |
| Evidence JSON | Same evidence requirements, serialized as a country/claim/evidence ledger | Effect of structured output plus schema instructions |

Each arm has the same **2,048-token output cap and 700-word limit**, and identical sources, national questions and prior notes within its context. The earlier 300-word instruction is relaxed in **all** three arms. Thus the prose control is not byte-identical to the original baseline. Schema instructions add input tokens, and actual generated lengths may differ; this is not equal actual compute.

Three contexts yield nine calls:

1. Climate/security: frozen peer-revision notes from the diagnosed baseline.
2. Ukraine: frozen single-analyst notes containing known errors that the synthesizer must check against the source.
3. South Sudan: a fresh issue, with four full national statements and no generated notes.

The first two contexts were selected after inspecting errors. South Sudan adds an issue, but uses the same UN-record genre and country set, and lacks the prior notes present in the other two. Analyze changes **within each context**. These three dependent, authored development contexts cannot support a generalization claim or a statistical ranking of methods.

## New source checks and what they teach us

The new source is the UN's **S/PV.9067, 20 June 2022**, containing full statements from France, the UK, India and Brazil. The PDF is pinned by hash; each speech retains its source, date, country, exact document offsets and page/column locations. The seven relevant pages were rendered and visually checked for column order and speaker boundaries. Thirteen proposed content criteria link to exact supporting spans or the entire speech for bounded absence checks. Independent review remains pending.

Useful distinctions in this record include:

- France cites an increase in **EU** humanitarian assistance to EUR 72 million. That is not evidence of a French national pledge of that amount.
- The UK welcomes specific progress while explicitly stating that critical benchmarks remain unmet. A positive phrase alone cannot justify “implementation complete.”
- India urges addressing South Sudan's concerns about sanctions, the arms embargo and targeted measures. That wording does not explicitly establish an unconditional commitment to lift all sanctions immediately.
- Brazil sets out security, humanitarian and peace-process priorities. Its full statement does not establish an embargo-lifting timetable; that absence also does not establish opposition to one.

The earlier candidate, S/PV.9070, was excluded: these countries appeared in its attendance roster but did not deliver attributable speeches in that record. This is a concrete acquisition check to preserve in future data preparation.

[Read the source-linked criteria and complete national statements](../data/review/evidence-format-20260928-v1/source-review.md). These are assistant-authored review proposals, not human-approved labels or training targets.

## What the automated checker does—and what needs review

The JSON checker rejects malformed or fenced JSON, duplicate keys, missing countries/answers, wrong-country evidence IDs, altered quotations, missing country coverage for shared claims, and proposals labeled as documented commitments. Whitespace alone may be normalized when locating a quotation. A capped answer remains a delivery failure, even if its JSON happens to parse. No repair is performed silently.

**Exact quotation matching does not establish entailment.** An adversarial test attaches “France rejects access” to the real fixture quote “We support access.” Location checks pass, while semantic validity and answer completeness remain **null**. That outcome is intentional: the checker is not an automatic policy judge. The entire answer, including uncited assertions and internal contradictions, still needs review against the national criteria.

The completed-run audit binds outputs to the frozen pack, case hashes, input token digests and declared cap. It keeps failed JSON, all delivered outputs and cost measurements, and creates blank semantic-review checklists. Mechanical JSON results are reported only for the JSON arm; they cannot be used to penalize the prose arms for their requested format. All arms require the same substantive source review.

## Verified locally

- **81 tests passed** across the new source/format checks and existing deliberation, policy and inference tests. Tests use clearly identified engineering fixtures, not empirical model-quality ratings.
- All nine real prompts passed the pinned tokenizer preflight: **37,823 total input tokens**, maximum **5,669** per prompt. The longest prompt plus its full 2,048-token allowance uses **7,717 of 8,192** context tokens. No sources or notes were truncated.
- A fresh inference payload contains **17 hash-verified files, 16,128,010 bytes**. Gold references are not needed in the inference payload. It is prepared locally, not uploaded or submitted.
- Four new full speeches and 13 source-linked proposed criteria are ready for inspection. No new model-quality score is reported.

Artifacts:

- [Frozen cases and manifest](../data/prepared/evidence-format-20260928-v1/manifest.json)
- [Tokenizer preflight](../runs/evidence-format-20260928-preflight-v1/preflight.json)
- [Staging manifest](../runs/evidence-format-staging-20260928-v1/staging-manifest.json)
- [Checkpoint receipt](../reports/evidence-format-readiness-20260928.json)
- [Builder](../scripts/build_evidence_format_probe.py), [mechanical checker](../src/country_persona/evidence_ledger.py), [completed-run audit](../scripts/audit_evidence_format_probe.py)

## Compute status and the next bounded experiment

The previous one-H100 job, 999389, had a recorded wall deadline of **19:08:16 Toronto on 28 September**. At the 19:23 check that deadline had passed, the local SSH multiplex socket was absent, and a fresh connection timed out. Its final scheduler state and current node health were therefore not observed. No new allocation was submitted; no current GPU availability is claimed.

The staged inference allocation uses **`def-zhijing`, one H100 and `sleep infinity`**, with the existing three-hour wall cap for reuse across experiments. Test the scheduler request before submitting it. The separate four-H100 training recipe remains prepared and previously scheduler-tested, with a one-hour retained allocation.

After restoring cluster access, upload the staged directory to a fresh remote destination. From that destination, validate the request with `sbatch --test-only scripts/trillium_eval_probe.sbatch`, then submit the same script and inspect the assigned job/node. On the allocated node, from the staged directory:

```bash
srun --input=/dev/null --jobid=JOB_ID --overlap --ntasks=1 --gpus=1 --cpus-per-task=24 \
  bash scripts/trillium_eval_probe.sh \
  --pack data/prepared/evidence-format-20260928-v1 \
  --case-cap 9 --max-new-tokens 2048 --output runs/evidence-format-base-v1
```

The inference runner re-verifies the model bytes and actual prompt budgets. Retrieve the completed run before auditing locally:

```bash
PYTHONPATH=src .venv/bin/python scripts/audit_evidence_format_probe.py \
  --pack data/prepared/evidence-format-20260928-v1 \
  --run runs/evidence-format-base-v1 --output reports/evidence-format-base-v1
```

## Decision before training

Inspect complete outputs, not just the two known errors. Compare country fidelity, retained qualifications, unsupported assertions, false consensus and useful proposed next steps across all three formats, alongside stopping behavior and cost. Resolve ambiguous reference criteria before calling a response right or wrong. Freeze the chosen prompt/budget combination and review rules for the paired base/adapter evaluation; do not change them after seeing the adapter results.

Then use the [prepared two-step, four-GPU smoke test](TRAINING_READINESS_20260928.md). Its first purpose is to verify distributed optimization, finite loss, real adapter updates, save/reload and repeatable evaluation. If clean, the ten-case fit probe diagnoses learning versus regressions. Neither tiny run establishes better national personas or better deliberation; those claims require reviewed, distinct training/evaluation families and paired semantic results.
