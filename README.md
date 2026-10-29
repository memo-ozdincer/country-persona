# Country Persona research

**New collaborator? Start with [the onboarding guide](docs/onboarding/README.md).**

**Data download:** [public Hugging Face dataset](https://huggingface.co/datasets/memo-ozdincer/country-persona-aurora-data) — [browse/download instructions](docs/onboarding/PRIVATE_HF_DATA.md). Aurora access is not required.

**Added 29 October:** [China/Germany original pilot](docs/onboarding/CHINA_GERMANY_PILOT.md): 37,094 canonical records and 16,373 SFT-format candidates, with original splits, full answers and provenance.

We study small models that can represent dated country–institution–role behavior, preserve documented positions and respond appropriately when a diplomatic proposal changes. The working model is Qwen3.5-4B. France, the UK, India and Brazil are the active extension; earlier Germany/China work is preserved.

| What you want | Open this |
|---|---|
| Understand the project and join | [Onboarding](docs/onboarding/README.md) |
| Understand each experiment simply | [SFT Trial 1–7: context, format, example answers, evals and results](docs/onboarding/SFT_TRIALS.md) |
| Read actual model answers | [Master evidence index](docs/evidence/README.md) |
| Understand scores and remaining failures | [Evaluation guide](docs/evidence/EVALUATION_GUIDE.md) |
| Set up Python and run CPU checks | [Environments](docs/onboarding/ENVIRONMENTS.md) |
| Find frozen data and model adapters | [Data access and restore](docs/onboarding/DATA_AND_RESTORE.md) |
| See the next proposed experiment | [Next steps](docs/onboarding/NEXT_STEPS.md) |
| See what was actually verified | [Onboarding checks](docs/onboarding/CHECKS.md) |
| Read the full research history | [Consolidated results](docs/CONSOLIDATED_RESULTS_20261019.md) and [full handoff](docs/PROJECT_HANDOFF.md) |

## Current status

Research is **paused at the user's request**. The latest training checkpoint is 19 October 2026; the onboarding/evidence pages were prepared on 21 October. All started model trials are complete. Historical next-step paragraphs and prepared controls are not an experiment queue.

Small supervised trials improved source coverage and selected proposal-state behaviors. The separate published humorous-persona reproduction produced clear persistent-style gains. Dependable broad national personas, diplomatic reasoning, multi-agent improvement and strong OOD gains remain unproved. The newest adapter is not a universal upgrade; failed and ambiguous results are retained.

## What is available

A plain clone contains the code, configuration, environment definitions, readable outputs and recent bounded research evidence. Older selected frozen data/transcripts/adapters are in the public Hugging Face dataset and GitHub release assets. **Both GitHub and the Hub dataset are publicly readable. The Hub was made public at the project owner's request on 24 October.** Base weights, credentials, installed environments and caches are separate. Large older/Reddit corpora are not fully included. See the data guide before assuming a clone reproduces the entire historical workspace.

## First check, no GPU or dependencies

```bash
git clone https://github.com/memo-ozdincer/country-persona.git
cd country-persona
python3 -B docs/onboarding/verify_starter.py
```

This checks the saved text and original score arithmetic, not new model quality. For full CPU setup use the environment guide. Before any experiment read [AGENTS.md](AGENTS.md), [START_HERE.md](START_HERE.md), and the handoff. On Aurora, never alter unfamiliar processes, even under the same username.

The [previous README](https://github.com/memo-ozdincer/country-persona/blob/5e701ffb0a23ec280140404bdff6481f176e3972/README.md) is preserved as historical documentation; its dated status and setup commands are not the current onboarding path.
