# Aurora access and experiment workflow

**Latest continuation, 30 September:** [Adaptive Qwen3.5-4B results](AURORA_QWEN35_ADAPTIVE_RESULTS_20260930.md) include two fresh 20-step fits and 14 inspected comparison answers on one NVIDIA RTX PRO 6000 Blackwell Server Edition. The short-target recipes optimize but do not resolve key synthesis errors; complete synthesis-task supervision is the next replan. Explicit Aurora runners support fresh outputs, GPU UUID ownership records and configuration locks. The latest process exited and its GPU returned to zero memory use. No unfamiliar process was changed. This verifies single-GPU CUDA, not NCCL/distributed training or validated persona quality. The [earlier smoke](AURORA_QWEN35_TRAINING_SMOKE_20260930.md), [September 29 portability](AURORA_EVALUATION_READINESS_20260929.md) and access observations below remain dated evidence.

Verified 29 September 2026, approximately 16:21 Toronto. [Access receipt](../reports/aurora-access-20260929-162128.json). No experiment, model download or GPU reservation was launched during this check.

## Connection

The Codex remote host `remote-control:env_e_6abc1b75af70832bb5f4e478cf4b2335` responds to the app's host-targeted metadata query. Aurora's Codex app-server daemon reports running, version 0.159.0. This existing chat still executes locally on the Mac: direct remote shell execution through the Codex connection has not been demonstrated. Hardware/storage checks below used the existing SSH alias successfully.

SSH alias `aurora` resolves to `memo@aurora.ais.sandbox` through `toronto-login`. A login shell is available:

```bash
ssh aurora 'bash -l'
```

The connection check does not imply a new chat was created or this chat was moved. The [official remote-work guide](https://developers.openai.com/blog/mastering-codex-remote-for-engineering) describes selecting the connected host and workspace for execution.

## GPU snapshot

Aurora exposes eight NVIDIA RTX PRO 6000 Blackwell Server Edition GPUs, each reporting 97,887 MiB of memory (approximately 96 GiB).

- GPUs **1, 2, 3, 4, 5 and 7** reported zero memory used and zero utilization.
- GPU **0** held roughly 88.6 GB in another user's vLLM process; GPU **6** held roughly 0.6 GB in another user's llama-server process.
- Availability is a snapshot, not a reservation. Recheck memory, process ownership and utilization immediately before each run. Do not terminate other users' processes. Start with the smallest useful device count and set explicit device visibility for the selected experiment.
- **User instruction: a medical agent may also run on Aurora under `memo`.** Account ownership alone does not establish that a process or allocation belongs to this project. Leave unfamiliar jobs, processes and GPU allocations untouched, even under the same username. Manage or terminate only resources positively traced to this project's own recorded launches. Record host, launch time, command, run directory, GPU UUIDs and PID/job identity; verify these still match before stopping anything. Do not use account-wide cancellation or broad process-kill commands on Aurora. The earlier one-time request to cancel all Trillium jobs does not authorize cleanup here.
- `squeue` and `sinfo` were not found on the login-shell PATH. Do not assume Trillium's Slurm procedure applies here.

## Storage and reusable environment

Use `/mfs1/u/memo/country-persona-research` for model/data caches, temporary files and bulky outputs. It is under the verified writable user directory, outside the CSlab home filesystem. The shared `/mfs1` filesystem reports about 40 TB available; that is not a verified personal quota. It is non-backed-up storage.

Aurora's local ZFS pool is mounted at `/aurora` and reports about 20 TB available. Its root is owned by root and is not writable by `memo`. Do not provision disks, change mount permissions or use it until an appropriate user directory is provided. The observed available pool space need not equal the disks' summed raw capacities.

The private environment profile is already installed on Aurora:

```bash
source /h/405/memo/.config/country-persona/aurora-env.sh
```

It points `HF_HOME`, `HF_HUB_CACHE`, `HF_DATASETS_CACHE`, `TORCH_HOME`, `XDG_CACHE_HOME` and `TMPDIR` into the scratch project directory. `HF_TOKEN_PATH` points to the private credential below. It does not contain a token value and is not automatically sourced globally. Save source code, manifests, important evaluation outputs and durable checkpoints somewhere backed up before relying on scratch data long term.

## Hugging Face credential

The user-supplied token is stored separately from code, reports and caches:

- **Mac:** macOS Keychain, service `country-persona.huggingface`, account `memo-ozdincer`. Retrieval was verified without displaying the token.
- **Aurora:** `/h/405/memo/.config/country-persona/secrets/huggingface.token`, owned by `memo`, mode **0600**, within private **0700** project/secret directories.
- Authentication from both machines was verified against Hugging Face's `whoami-v2` endpoint: account `memo-ozdincer`, reported token role `write`. This verifies identity/authentication; it does not guarantee access to every gated model or repository.

Use the environment profile or read the secret directly in-process. Do not print it, put it in shell command arguments, commit it, include it in staging payloads, or copy it into the shared model-cache directory. Existing global Hugging Face credentials were not overwritten. No weights were downloaded or uploaded during this check.

## Experiment requirements reaffirmed by the user

Each run, including the smallest technical probe, must answer a concrete question and produce a usable observation that informs the next decision. Specify the question, comparison and stop/continue criterion before launch; inspect the results before choosing the next run.

Do not queue a stack of speculative experiments. Do not run multiple seeds of the same experiment at this stage. Prioritize useful methodological distinctions, diagnosis and trustworthy evaluation. More GPUs do not change the evaluation-first gate or turn repeated outputs into independent evidence. The [checkpoint plan](RESEARCH_CHECKPOINT_PLAN.md) and [current source-review findings](DELIBERATION_SOURCE_REVIEW_20260928.md) remain the research reference points.
