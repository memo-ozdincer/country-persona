# Council negotiation workshop

Two or more delegates negotiate one clause. Each sees its own dated source excerpts, the public discussion and the current draft. Python manages the floor and records decisions. The bundled case imagines a UK, India and France workshop on 10 December 2021 using statements from the previous day. The opening clause and any resulting agreement are fictional. [Official meeting record](https://docs.un.org/en/S/PV.8923)

The [first live run and transcripts](../../reports/council-workshop-20261123/README.md) show how the queue, revisions and final ballots behaved.
The [benchmark scorecard](SCORECARD.md) consolidates verified results,
registered coverage, clause scores and the information ceiling with a
single offline rebuild command.

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
The [blinded model regrade](../../reports/council-workshop-blind-judge-20261123/README.md)
reproduced the archived labels and withheld points on a false-adoption control.

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
  --countries KEN GBR IND FRA BRA --model gpt-6.1-sol --seat-model KEN=gpt-6-astra \
  --turn-cap 10 --call-cap 50 --out runs/packages
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
The [live mixed-model pilot](../../reports/council-workshop-live-crossplay-20261123/README.md)
uses GPT-6-Astra for one seat and GPT-6.1-Sol for the other four.
It records a certified impasse and a valid agreement after a
one-speech continuation.
The [matched all-Sol control](../../reports/council-workshop-sol-control-20261123/README.md)
changes Kenya's model and compares both cases at the original budget.

## Evaluate on additional case families

The [held-case suite](held-cases.json) adds three-seat Gulf of Guinea and
six-seat Iraq workshops. Each has a feasible and an infeasible version
that differ in one seat's private mandate. The Gulf of Guinea feasible
case allows two choices. In its twin, one seat holds the only exclusions
for both. The Iraq twin changes a single private permission. The cases
use fictional tasks and packages. Their topics come from the project's
existing benchmark joins. [Gulf of Guinea vote join](../unsc-marl-20261119/benchmark-kit/reader-use/facilitator-new-meetings-evidence/provenance.json) ·
[Iraq scenario and joins](../unsc-marl-20261119/benchmark-v1.7/cases.json)

For each case, the plan fixes two opening orders and four model
assignments. Use all-Sol and all-Astra teams as the references. Swap the
model only in the seat whose mandate changes to produce two mixed
teams. Compare each swap to its matching reference. The two orders
put the same seat first or last. They reuse one case and count as
order comparisons. The case families were held from the workshop policy
fits. Their source records appeared in earlier drafting evaluations.

```sh
set -o pipefail
kit=research/council_workshop
python3 -B "$kit/held_suite.py" audit | cmp "$kit/held-control-audit.json" -
python3 -B "$kit/held_suite.py" case guinea impasse > /tmp/council-guinea-impasse.json
python3 -B "$kit/run.py" --case /tmp/council-guinea-impasse.json \
  --countries GHA CHN NOR --model gpt-6.1-sol --turn-cap 10 --call-cap 30 \
  --call-timeout 90 --out runs/guinea-impasse-sol
python3 -B "$kit/held_suite.py" score runs/guinea-impasse-sol
```

For the matched swap, add `--seat-model NOR=gpt-6-astra` and a fresh
output directory. Pass both run directories to `score`. It replays each
meeting, checks registration and reports coverage, endpoint, calls,
speeches, signatures, checked exclusions and incompatible signatures.
Pass archived aborted runs to `score` as well. A replayed protocol
rejection scores zero. A recorded call with no model reply stays in the
coverage report with no reward, and pairs involving that call are excluded
from reward comparisons. An unfinished log without a recorded error
cannot be scored.
Add `--trace` after `score` to see which seats alone could exclude a
package, their speeches before disclosure, and proposals for packages
that had already been excluded. It separates all opportunities to rule
out a package from turns when that package was already the current draft.
The [scripted audit](held-control-audit.json) verifies that the correct
outcome is reachable for all eight case and order combinations under
the registered budgets. The matrix has 32 live cells. A partial pilot
reports only its completed cells and explicitly matched swaps.
The [first held-case live comparison](../../reports/council-workshop-held-pilot-20261123/README.md)
covers both Gulf of Guinea variants. Both rosters reached agreement in
five speeches when Norway's mandate allowed it. In the impasse variant,
the Astra seat supplied both required exclusions and the Sol seat
supplied one within the ten-speech cap.
The [Norway-opening rotation](../../reports/council-workshop-norway-opening-20261123/README.md)
certified impasse with all Sol. The provider interrupted both attempts
to complete the matched Astra-seat arm.
The [six-seat Iraq report](../../reports/council-workshop-iraq-pilot-20261123/README.md)
shows an unresolved all-Sol impasse and a scripted replay that certifies
it within the original cap. Both mixed-roster attempts ended on a
provider rate limit.
The [all-Sol matrix](../../reports/council-workshop-all-sol-matrix-20261123/README.md)
covers both openers in both families. All four feasible cells agreed,
and one impasse was certified within the registered limits. The
UAE-opening Iraq impasse obtained its certificate in a separate
continuation with one extra call.
The [prompt comparison](../../reports/council-workshop-exclusion-prompt-20261123/README.md)
finds that explicitly prioritizing an available exclusion changed the
action at France’s last turn. A live continuation with the other seats
on the original instructions certified the impasse within the cap.
Use `run.py --prioritize-exclusions` on a finite-mandate meeting to append
that instruction to each speaking prompt. These runs save the setting for
replay and resume. The registered model-assignment score uses standard
prompts. The [whole-meeting report](../../reports/council-workshop-exclusion-policy-20261123/README.md)
compares the two instructions in the Iraq workshop.
The [Gulf of Guinea transfer](../../reports/council-workshop-exclusion-transfer-20261123/README.md)
uses the same instruction in a three-seat workshop. It produced a
certified impasse where the archived standard run remained unresolved.
In the feasible twin, both runs agreed, with one additional speech and
call in the priority run.
In the [opening-agreement stress case](../../reports/council-workshop-opening-agreement-20261123/README.md),
the five-speech deadline left time for three opening signatures. The
priority run recorded three exclusions first and stopped one signature
short. The scripted controls reproduced the difference.
The [conditional instruction](../../reports/council-workshop-conditional-exclusions-20261123/README.md)
uses the current draft until a checked rejection is public. Start it
with `--prioritize-exclusions-after-rejection`. On the two cases that
informed the instruction, it matched the standard prompt's three-speech
opening agreement and certified the Gulf impasse in seven speeches.
The [rejected-opening test](../../reports/council-workshop-rejected-opening-20261123/README.md)
changes only the opening draft of the five-speech case. The standard run
found the feasible replacement and secured all three signatures. The
conditional run recorded all exclusions first and reached the deadline
with one signature. A scripted replacement-first witness also succeeds
after the first checked rejection.
The [matched rejection fork](../../reports/council-workshop-rejection-fork-20261123/README.md)
holds China's second-speech prompt fixed while changing a permission in
Norway's mandate. Under five speeches, that shared decision can preserve
agreement or impasse, depending on the hidden world. A six-speech
scripted policy succeeds in both by branching on Norway's public reply.
The [live six-speech trial](../../reports/council-workshop-live-rejection-fork-20261123/README.md)
holds the opening and speaker routing fixed. Sol agreed in the feasible
world and missed the impasse after Norway made a counterproposal. A
scripted substitution at that speech let the remaining live delegates
complete the certificate within the cap.

Run the offline checks from the repo root:

```sh
python3 -m unittest discover -s tests -p test_council_workshop.py
```
