# Council negotiation workshop

Two or more delegates negotiate one clause. Each sees its own dated source excerpts, the public discussion and the current draft. Python manages the floor and records decisions. The bundled case imagines a UK, India and France workshop on 10 December 2021 using statements from the previous day. The opening clause and any resulting agreement are fictional. [Official meeting record](https://docs.un.org/en/S/PV.8923)

The [first live run and transcripts](../../reports/council-workshop-20261123/README.md) show how the queue, revisions and final ballots behaved.

## Run it

From the repo root, with Python 3.11+ and Codex signed in through ChatGPT:

```sh
python3 research/council_workshop/run.py --model gpt-6.2-astra --turn-cap 4 --vote --out runs/astra
python3 research/council_workshop/run.py --model gpt-6.2-sol   --turn-cap 4 --vote --out runs/sol
python3 research/council_workshop/replay.py runs/astra
```

Each invocation runs one condition and needs a new output directory. On macOS the runner prefers the CLI bundled with ChatGPT. Elsewhere it uses the CLI on PATH. Override with `--codex /absolute/path/to/codex`. The runner checks the login method, forces ChatGPT authentication, removes API-key environment variables and requests the exact selected model. A model access error stops the run.

To continue a meeting that reached its cap, pass `--extend-from runs/astra --turn-cap 20 --vote --out runs/astra-20` with the same model, case and country order. The limit counts the original turns. The runner replays the public decisions, carries forward the queue and collects fresh ballots.

## How turns work

1. The first listed country opens. The default order is GBR, IND, FRA.
2. After each speaking turn, delegates outside the queue privately choose `request_floor` or `pass` from the same public snapshot. Existing requests stay ahead. New requests enter in seating order starting after the previous speaker. The speaker can rejoin at the back.
3. The next delegate sees the latest discussion. It chooses `ask`, `reply`, `propose`, `accept`, `yield_floor` or `walk_away`. Codex returns a schema-constrained action. Python checks and applies it. A proposal replaces the entire clause and clears prior acceptances. Even the proposer must explicitly accept the new version.
4. The discussion ends on unanimous acceptance, a walkout, an empty queue or the speaking-turn cap. With `--vote`, each delegate privately votes yes, no or abstain on the same final wording. Ballots are advisory. The discussion outcome and votes are saved separately.

Each decision is a fresh Codex call. The program reconstructs the delegate's view each time. Only public remarks carry between delegations. A pass or floor request costs a call but does not consume a speaking turn.

## Compare runs

Use `--countries IND GBR FRA` to change the opener, or `--countries GBR IND` to test the same dispute without France. Add a country by including its ID and sourced excerpts in a copy of `climate.json` and passing `--case`.

Use `--mode independent` for one draft per country from its own packet, or `--mode solo` for one analyst drafting from all selected packets. These are one-pass drafting comparisons with different call budgets. Compare models within the same mode, country order and turn cap. For qualitative review, hide model names, check each position against its source, and trace whether a particular objection changed the actual clause.

`result.json` contains the outcome and turn-by-turn text. `settings.json` stores the case and run configuration. `calls.jsonl` preserves each prompt and structured reply, including floor requests. To recover from a timeout, repeat the same flags with `--resume-from runs/partial --out runs/retry`. The runner compares the case, settings and each full prompt before reusing a reply. Only missing decisions consume another call. Slow responses can be given more time with `--call-timeout SECONDS` (default 360). Both logs are preserved. Replay checks prompts, speakers, decision schemas and the reconstructed final state without contacting Codex.

Run the offline checks from the repo root:

```sh
python3 -m unittest discover -s tests -p test_council_workshop.py
```
