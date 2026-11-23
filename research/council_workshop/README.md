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

Use `--countries IND GBR FRA` to change the opener, or `--countries GBR IND` to test the same dispute without France. Add a country by including its ID and sourced excerpts in a copy of `climate.json` and passing `--case`. Repeat `--seat-model COUNTRY=MODEL` to assign a different model to a seat. Remaining seats use `--model`. Each request in a mixed-model run records its assigned model.

For an equal-call comparison, set the same `--call-cap` and `--turn-cap` in every arm. The call budget covers speeches, floor polls and ballots, including decisions reused from an earlier run. When voting is enabled, the runner reserves one call per participant for the final ballots. The budget must cover those calls and the opening speech. If the remaining discussion budget cannot cover the next complete floor poll, the meeting ends with `call_cap` and preserves the recorded queue. A capped result records actual calls consumed. Token usage is a separate comparison.

```sh
python3 research/council_workshop/run.py --model gpt-6.2-astra \
  --seat-model IND=gpt-6.2-sol --turn-cap 20 --call-cap 40 --vote --out runs/mixed
```

You can extend a call-capped meeting by increasing `--call-cap`. Keep the
same seat assignments and keep or increase the other budget. An extension
reuses discussion decisions and collects fresh advisory ballots.

Use `--mode independent` for one draft per country from its own packet, or `--mode solo` for one analyst drafting from all selected packets. These are one-pass drafting comparisons with different call budgets. Compare models within the same mode, country order and turn cap. For qualitative review, hide model names, check each position against its source, and trace whether a particular objection changed the actual clause.

`result.json` contains the outcome and turn-by-turn text. `settings.json` stores the case and run configuration. `calls.jsonl` preserves each prompt and structured reply, including floor requests. To recover from a timeout, repeat the same flags with `--resume-from runs/partial --out runs/retry`. The runner compares the case, settings and each full prompt before reusing a reply. Only missing decisions consume another call. Slow responses can be given more time with `--call-timeout SECONDS` (default 360). Both logs are preserved. Replay checks prompts, speakers, decision schemas and the reconstructed final state without contacting Codex.

## Review the final clause

The meeting records acceptance and advisory ballots. The clause reviewer separately grades the exact final wording for source-backed coverage. It exports the clause, dated excerpts and criteria without the model, speaking order, ballots or meeting outcome. Give the exported request to a reviewer and save their JSON verdict. The scoring command replays the original meeting, checks exact quotes and allowed sources for each criterion, then reports the 70-point score range alongside the procedural outcome.

```sh
python3 research/council_workshop/review.py runs/mixed > /tmp/clause-review.json
python3 research/council_workshop/review.py runs/mixed --verdict /tmp/verdict.json
```

The bundled climate rubric covers the three-country roster. Supply `--rubric` with a case- and roster-matched rubric for another workshop. Freeze its criteria before using them for a new comparison. The [retrospective Astra and Sol review](../../reports/council-workshop-clause-review-20261123/README.md) includes exact source and clause spans.

## Test feasible agreements and impasses

The finite package cases use the same meeting, floor and replay protocol.
Each delegate sees the common menu and only its own fictional list of
allowed packages. The five-seat [feasible case](climate-packages-feasible.json)
has one valid package. Changing one private list produces the
[impasse case](climate-packages-impasse.json) with zero valid packages.
The mandates are fictional and carry no claims about historical national
positions.

A delegate can `rule_out` an option outside its mandate. The engine
checks the exclusion and records the package and speaker publicly.
`declare_impasse` requires one verified exclusion for every package.
The terminal reward is one for a unanimously accepted feasible option
or a certified impasse. Invalid agreement, a walkout, all passing and the
budget stops earn zero. The full feasibility set appears in the scored
result after the meeting. Ballots remain advisory.

```sh
python3 research/council_workshop/run.py \
  --case research/council_workshop/climate-packages-feasible.json \
  --seat-model IND=gpt-6.2-sol --turn-cap 20 --call-cap 50 --out runs/packages
python3 -B research/council_workshop/mandate_smoke.py
```

The finite cases run in meeting mode. The [offline baseline report](../../reports/council-workshop-mandates-20261123/README.md)
records all five opener rotations under each of three scripts.

The [frozen Qwen baseline](../../reports/council-workshop-qwen-20261123/README.md)
uses native token scores over structured actions in the same engine.
Both runs ended after the first floor poll. Its report includes the
exact model inputs, scoring traces and replay commands.
The [floor diagnostic](../../reports/council-workshop-floor-diagnostic-20261123/README.md)
swaps the floor labels and tests the same opening under a fixed rotation.
The [shared-policy training experiment](../../reports/council-workshop-mandate-training-20261123/README.md)
compares true terminal reward and unanimity reward under the same speech
rotation. It includes held-roster transfer, mandate contrasts, and a replay
through the production engine.
The [budget-aware policy study](../../reports/council-workshop-budget-policy-20261123/README.md)
measures transfer across speech limits and checks a local mandate guard
against the same learned policy.
The [partner study](../../reports/council-workshop-crossplay-20261123/README.md)
rotates visibly different scripted partners through every seat and
compares two moderator responses to an incompatible signature.

Run the offline checks from the repo root:

```sh
python3 -m unittest discover -s tests -p test_council_workshop.py
```
