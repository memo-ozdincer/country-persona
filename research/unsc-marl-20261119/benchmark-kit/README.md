# Authoring a UN task that can measure collaboration

Start with a question about an information dependency. For example, can a chair correctly preserve a reporting mandate and select a feasible briefing slot when each office knows only its own availability? One session produces a transcript, a decision, and a final memorandum. They have different units of analysis.

## Copy a card and change one dependency

1. Pick one dated negotiation family. Join the UNBench instrument and UNSC-Bench vote by symbol, date, stage and meeting. Store both release IDs, missing joins and the official meeting record. A native prediction uses only material available before its cutoff. The two examples here are retrospective workshops with separate invented constraints. [Mali join](../crossbench/mali/references.json) · [Myanmar join](../crossbench/myanmar/references.json)
2. Write the public question and the terminal action space first. Specify who decides, what can change, and when holding a decision is justified. Give each role a dated country–institution–capacity or an explicitly fictional office. Assign a private observation to its actual holder. Keep the national speaker, meeting president, and simulation chair distinct.
3. Copy either JSON card. List possible signal values and every acceptable action in each world. Rows use Cartesian product order, with the rightmost field changing fastest. To extend to many worlds, generate these sets with a documented mechanism and inspect boundary examples independently. A private preference, feasibility constraint and public legal authority are three different things. Name each in the brief.
4. Choose directed delivery edges and synchronous rounds. A message travels one edge per round. Choose where the final decision is made. The first role in this kit is the decision maker. Deliver only per-role views to candidates. Keep the case file, world index, row order, keys and audit report outside prompts. Supply the same public task to every arm. Release fixtures here are exposed development cases.
5. Before generating dialogue, run the audit. It partitions equally likely worlds by everything that could have reached the chair by round *t*. Within each class it chooses the action acceptable in the most worlds. Sum the successes and divide by the number of worlds. This gives the exact optimal accuracy for this finite experiment with unrestricted faithful relay, known distribution, no outside signals and a single final action. When worlds have multiple valid answers, count a success if the chosen answer belongs to the acceptable set. The JSON includes an ambiguous class whenever perfect accuracy is impossible. Retain cases with ceiling 1 at round zero as communication-unnecessary controls.
6. Write a correct final memo and near-misses before collecting candidates. Perturb one item at a time, including false authority, correct answer with unsupported reasons, an equivalent valid solution, fabricated consensus, dropped minority objection and a terse correct paraphrase. Freeze criterion weights, judge version and acceptance rules. Keep all branches of an event family in one split. Archive the role views, deliveries, final text and budget for replay.

### Run the examples

From this directory:

```sh
python3 audit.py mali.json --check-gold
python3 audit.py myanmar.json --check-gold
python3 audit.py myanmar.json --view 'UN office' --world 2
```

| Development family | Decision | No messages | One round | Two rounds |
|---|---|---:|---:|---:|
| Mali sanctions | Recommend a mutually acceptable package or record impasse | 1/2 | 1/2 | 1 |
| Myanmar oral report | Select any shared slot or request rescheduling | 1/2 | 3/4 | 1 |

Both use two independent, uniformly sampled private cards and the same three-seat relay. In Mali, learning the first mandate alone leaves an even choice between agreement on that package and impasse. In Myanmar, learning that the UN office has both slots makes late a guaranteed feasible choice. Thus the same extra turn has different decision value. A role may have contributed real information even when it did not increase expected accuracy. Compare each policy with its own topology's bound. Keep the absolute decision success visible. For stricter message length limits, loss, strategic disclosure or cost, the computed ceiling can be unattainable. [Mali class audit](mali.audit.json) · [Myanmar class audit](myanmar.audit.json)

## Compare systems fairly

| Comparison | What varies | What the result supports |
|---|---|---|
| Chair-only, deliberative solo revision, pooled solo | Give the chair only its original view for the first two. Give pooled solo the union of observations. Match available total generation budget. | Private-information floor, solo revision benefit and centralized reasoning capacity. |
| Independent drafts + synthesis vs interactive delegates | Same private cards, candidate model, evidence, aggregation rights and total budget. Include synthesis in both budgets. | Value of allowing delegates to read peers and revise. A pooled synthesizer that sees all drafts has a different graph from a chain chair. Compute its ceiling separately. |
| Same team, randomized delivery | Before generation, pair seeds/worlds and randomize delivery or withholding of the informative message, with equal-length neutral control. Generate downstream responses anew. | Effect of making that message available under this intervention. A later repetition by itself establishes only exposure and recurrence. |
| Frozen MARL policy with familiar and unfamiliar partners | Hold case and role fixed, cross independently trained partners and rotate focal seats. Report outcomes per focal role, worst partner and shared return. | Reliance on a convention or a particular partner. Action-label permutations must preserve semantics and move the matching decoder. [Melting Pot](https://proceedings.mlr.press/v139/leibo21a.html) · [Other-Play](https://arxiv.org/abs/2003.02979) |
| Swarms of different sizes and graphs | Hold distinct evidence, decision rights and total token budget fixed. Add redundant observers before adding new facts. Compare broadcast, hub and chain with a single frozen stopping rule. | Sensitivity to population, bottlenecks and duplicated information. Record sent tokens and delivered token-copies, distinct active speakers, latency and success at each round. |

Log realized calls, input/output tokens, delivery copies and wall time including synthesis. Predeclare the primary resource constraint and report whichever costs could not be matched. Allow early stopping and give each arm the same maximum budget. Report paired differences within worlds and uncertainty across **negotiation families**. Show each family when there are too few independent families for meaningful intervals. Cross-play partner pools, document families and benchmark-author development cases need distinct holdouts. Full-information solo and truthful relay are useful positive controls. Majority prior, mute chair and redundant observations expose tasks solvable without collaboration. A public historical answer can be memorized, so score matched fictional reversals separately. Treat private mandate satisfaction as a separate outcome per delegate in mixed-motive cases. A shared reward for sounding agreeable would discard precisely that information.

## Score a discussion and its final record

For solo and group comparisons, publish identical final-artifact scores out of 70 and a separate mechanical decision score. For interactive sessions also publish the 30 process points below. Leave peer uptake inapplicable for solos and for episodes offering no peer opportunity. Compare process totals only across comparable opportunities. Do not renormalize an inapplicable axis into a cross-arm ranking.

| Axis | Units and anchors |
|---|---|
| Final record, 70 | Five × 14 for disposition, operative action, positions and reasons, common ground/open issues, and authority/scope. Pre-allocate each component into atomic claims with evidence, permissible alternatives, and a contradiction example. Publish critical authority errors beside the total. |
| Key points, 10 | Fraction of predeclared material propositions accurately expressed anywhere in visible discussion. Deduplicate by owner, scope and modality. Report correct novel ideas outside the key separately for review. |
| Arguments, 10 | Score each predeclared reasoning opportunity 0 absent/contradicted, 1 relevant premise, 2 supported premise linked to its practical consequence. Divide by twice the number of opportunities. Multiply by ten. |
| Interactions, 10 | Use the same normalization over predeclared recipient opportunities. Score 0 ignored or distorted, 1 accurately acknowledged, 2 correctly acted on, challenged or reconciled with a named proposal. Count only delivered turns visible before the response. |

**Instruction to the blinded judge.** Read the frozen task, authority map, role views and chronological delivery log. First score the final text alone against each final criterion. Return its ID, verdict, exact output quote, evidence ID and reason. For an omission return an empty quote and the missing claim. If evidence cannot settle a criterion, mark uncertain and report the lower and upper attainable scores. Accept any licensed action. Next read the transcript and code each distinct proposition with its owner, first turn, exact span, type and evidence status. Link a response to the particular earlier message the recipient saw. Mark independent simultaneous mentions as co-origins and count the global proposition once. Credit a peer correction even if the final chair drops it. Lastly trace each material proposition to a quoted final span or mark it omitted. Never infer a private preference, authorization, consensus or causal effect from fluency. Return per-axis records before aggregation. [Final judge protocol](../judge/instructions.md) · [Transcript protocol](../discussion/process-judge.md)

For each speaker report observed turns, substantive turns, distinct supported propositions introduced, independently co-originated propositions, repeated mentions, peer ideas taken up and original ideas surviving in the final text. Publish counts and opportunity denominators. A silent delegate with no delivery opportunity has a different interpretation from a delegate ignoring a delivered objection. Validate exact spans mechanically. Have two blinded reviewers independently code event-stratified samples and all critical authority reversals, report per-axis agreement and confusion by anchor, then adjudicate. Pre-register minimum acceptable agreement and sensitivity for the intended use **before** scoring candidate policies. Until calibrated, report semantic judgments as provisional. The research notes link the Discourse Quality Index, contribution-quality ratings, and studies comparing group statements and objective decisions. [Deliberation research](../../../BENCHMARK.md#research-to-borrow-from) · [Decision-oriented dialogue](https://aclanthology.org/2024.tacl-1.50/)

### Worked grading contrast

In Myanmar world 2, the UN office holds “both” and the liaison holds “late only.” In round 1 the liaison says “Our office can attend late only.” In round 2 the UN office reports “We can do either. The liaison can attend late only, so propose late.” The final record says “Schedule the simulated briefing late. Both offices can attend. The Council's oral reporting request remains in force.” There are two delegate turns, one new calendar fact per speaker, one feasible-slot inference introduced by the UN office, and one peer fact used in that inference. The final contains the shared availability at the selected slot but omits the full calendars. Whether that omission costs points depends on the frozen criterion. The mechanical answer earns full credit. Replacing the final sentence with “The Council approved the late slot” leaves the action score intact and fails the authority criterion. These are authored anchors. Judge reliability and learned coordination require independent measurements.

### Case-specific scoring key for these two workshops

The role-view command includes the following common deliverable instruction. Preserve it for every arm in a scored session. “Submit one allowed action and a short chair's record. Give the action, next step, both card holders' relevant positions or availability, the decisive overlap or conflict, and the source and limits of authority. Mark unavailable evidence explicitly.” At intermediate rounds allow a separate *insufficient information* confidence report and log it. The action ceilings above apply to a forced choice among the listed actions. They do not measure how responsibly a chair handles uncertainty.

| 14-point final component | Mali, two claims worth 7 each | Myanmar, two claims worth 7 each |
|---|---|---|
| Disposition | Identifies selected package or impasse. Identifies it as the workshop result. | Names a feasible slot or reschedule. Identifies this as a scheduling result. |
| Operative action | Recommends the agreed package or returns the incompatible terms to delegates. Identifies the chair as recommending or referring. | Proposes the feasible slot to the offices or requests new availability. Retains the oral reporting request. |
| Positions and reasons | Attributes the first delegate's card accurately. Attributes the second delegate's card accurately. | Attributes the UN office's availability accurately. Attributes the liaison office's availability accurately. |
| Overlap and open issues | Correctly compares the actual mandates. Explains why that comparison licenses the terminal choice. | Correctly identifies the intersection, including both slots when both are available. Explains why the selected action follows. Either feasible slot receives full action credit. |
| Authority and scope | Acknowledges that neither historical draft was adopted. Keeps workshop mandates distinct from official country positions. | Grounds the oral report in resolution 2669. Identifies the specific slot or rescheduling request as a simulation decision outside the Council's recorded instruction. |

Apply the full-information content key to final two-round records and report the evidence available to the writer. For earlier prefixes also report whether each claim was knowable and whether the writer expressed appropriate uncertainty. Keep claims about wrong official authority visible as a separate critical error even if other claims earn credit. For both tasks, fix the process opportunity list at the two private facts (key points), the relation between them and its implication (one argument), and the first delegate/office's use of the second holder's delivered fact (one peer opportunity in the chain). If a graph changes, publish its new opportunity list and keep the final key fixed. For evaluating diplomatic persona fidelity use the historical role dossiers and independent position ratings separately. These fictional card holders measure collaboration and authority handling.

### Train a two-round relay with explicit private facts

The far delegate can send its own card to the relay in round one. The relay can send one card to the chair in each round. It can forward the far delegate's card only after receiving it. Each transmission counts against the same three-message budget, including forwarding. The chair sees the delivered cards and the public set of possible cards. The environment scores both whether the choice was valid and whether it would remain valid in every world compatible with that visible record.

One small shared CPU policy trains with an outcome reward and a matched policy with an evidence-warranted outcome reward. Each uses 100 updates on the same generated sequence of synthetic menus and worlds. In the Mali and Myanmar fixtures, both reach all eight valid and warranted decisions, matching the scripted truthful relay. The initial policy warrants zero. Muting either source reduces Mali from four warranted decisions to zero, while the model still guesses two correctly. On Myanmar the same intervention leaves two warranted and three valid decisions. The task audit checks dependence per world and finds both sources necessary in four Mali worlds and one Myanmar world. Role ownership remains visible when a peer forwards a card. [Actor and reward](../relay_marl.py) · [Fit, frozen policy and controls](evidence/relay-marl/results.json) · [Rendered transcripts and exact cut audit](evidence/relay-marl/readout.json)

The chair originally received a per-action warrant flag calculated from its visible record. Removing that flag drops the unbalanced policy to seven of 16 warranted outcomes across the four linked fixtures. Both cards still arrive in every world. The remaining inputs include per-package signs and whether the two delivered menus intersect. The fit never chooses impasse on these fixtures. [Matched warrant-input ablation](evidence/relay-marl/raw.json)

Rebalancing the synthetic sampler from about 23% to 50% expected impasses makes the reward choice matter. The outcome-only run sends zero messages and always chooses hold or reschedule. It happens to get nine of 16 actions right and warrants none. The policy rewarded for warranted outcomes sends both facts and gets all 16 decisions right across Mali, Myanmar, Venezuela and outer space. The last two use seven options and the training generator uses at most four. Their independent private cards are fictional workshop variations. The result matches the scripted truthful relay on the original two fixtures. It uses a small typed neural policy and one paired training seed. [Class-balanced fit and wider transfer](evidence/relay-marl/balanced.json) · [Role-owned transcripts](evidence/relay-marl/balanced-readout.json) · [Exact policy reload and held-out replay](evidence/relay-marl/replay.json)

Cross-play swaps the frozen outcome-only and warranted-reward policies into the far delegate, relay and chair seats independently. Both communication seats must use the warranted-reward policy to deliver both cards in all 16 tested worlds. With both cards delivered, the outcome-only chair warrants nine decisions and the warranted-reward chair warrants all 16. The mixed teams expose a decision-stage failure separately from silence or missing relay delivery. These are two reward-trained policies from one seed. [All eight seat assignments and message traces](evidence/relay-marl/crossplay.json)

### Test the relay with model-scored prose actions

Qwen3.5-4B scores a constrained action letter from each role's prose observation. The far delegate and relay see their own card and the messages they actually received. The chair sees only what the relay delivered. The 69 cached contexts cover four training worlds in an invented archive-review task and four evaluation worlds each from the Mali and Myanmar fixtures. They use 9,604 input tokens. Delivery mechanically carries the source-owned card corresponding to the selected action. This test measures a model-backed action policy. [Actual prompts, token IDs and logits](evidence/relay-text/actions.jsonl)

The learned head adjusts Qwen action scores using exact expected team return across all 24 legal terminal paths per synthetic training world. The two flat heads train with outcome and warranted-outcome rewards, and make the same greedy decisions on the named fixtures. Both learn to deliver both cards, but a single impasse bias improves Mali and harms Myanmar. The 26-parameter conditional head keeps Qwen's ranking among substantive options and allows the impasse adjustment to vary across incomplete, fully delivered disjoint, and fully delivered overlapping pairs of cards. The extra state is calculated from the chair's delivered cards. No per-option warrant label enters the model input. [Flat and conditional training code](../relay_text_train.py) · [Conditional head](../relay_text_context.py)

| Policy | Mali warranted /4 | Myanmar warranted /4 | Both sources received /8 |
|---|---:|---:|---:|
| Frozen Qwen | 2 | 3 | 6 |
| Flat learned head | 3 | 1 | 8 |
| Conditional head, learned communication only | 2 | 3 | 8 |
| Conditional head, learned chair only | 2 | 4 | 6 |
| Conditional head on all roles | 4 | 4 | 8 |
| Learned communication with fixed public overlap rule | 4 | 4 | 8 |

The fixed rule with frozen Qwen communication warrants six of eight decisions. The public overlap rule changes only whether the chair can choose impasse after both cards arrive. It matches the full learned head with the learned communication. Under sampling restricted to the legal letters, the conditional policy's expected warranted rates are 98.3% on Mali and 80.3% on Myanmar, despite perfect greedy scores on these four-world fixtures. The Qwen backbone and token logits are frozen. Results cover one small synthetic training task and two named evaluation fixtures. [Component-level results and rendered dialogue](evidence/relay-text/report.json) · [Exact head-training replay](evidence/relay-text/replay.json)

### Test the final prose after a checked decision

Qwen3.5-4B writes a memo for a confirmed Mali impasse and a feasible early Myanmar slot. In each family, compare cards delivered by the learned relay, the same cards pooled directly, and the far card withheld. Also run the frozen relay's delivered evidence. A checked status accompanies all arms. The frozen relay exactly matches the withheld-evidence prompt in Mali and the learned-relay prompt in Myanmar. Identical prompts share one generation, giving eight records and six unique outputs. Only the writer stage is compared across the matched inputs. [Inputs and raw generations](evidence/relay-memo/memos.jsonl)

| Writer evidence | Mali out of 70 | Myanmar out of 70 |
|---|---:|---:|
| Learned relay | 49 | 49 |
| Same cards pooled directly | 56 | 49 |
| Far card withheld | 35, guard failed | 21, guard failed |
| Frozen relay | 35, guard failed | 49 |

All six memos omit the requested standalone status line. The incomplete Mali memo begins with UNRESOLVED and then asserts workshop impasse and a false cause for the failure of S/2023/639. The incomplete Myanmar memo assigns a late-only schedule to an office whose card was never delivered, and inserts Mali material. The final-record review checks the body for contradictions even when the leading status has the right label. Scores are same-assistant annotations of the arm-free deck with exact spans checked in code. [Frozen rubric](relay-final-rubric.json) · [Review deck](evidence/relay-memo/review-deck.json) · [Scored annotations](evidence/relay-memo/scores.json)

Removing the irrelevant family's instruction eliminates the cross-family material in the Myanmar retest. All four retests, including the two with an explicit missing-evidence rule, still fail a critical guard. The errors concern either the cause of the separate Mali draft's failure or an invented Myanmar card. A case-specific reference renderer uses the same checked input fields and emits four distinct source-bounded memos, each within 100 words with the exact status line. It supplies a deployable control for these fixed cases and demonstrates that the requested format and evidence are compatible. [Prompt control and scores](evidence/relay-memo/prompt-control/scores.json) · [Reference records](evidence/relay-memo/reference-render.json) · [Input, token and quote replay](evidence/relay-memo/replay.json)

### Audit the memo gate against sound unresolved records

Frozen Qwen3.5-4B judges six original memos, four retests and four authored controls in both answer-label orders. At the locked zero threshold, pooled margins reject all six flawed memos and four of eight sound ones. Both sound unresolved reference memos are rejected. Requiring agreement between the answer orders instead clears one sound memo, rejects three sound memos and abstains on four. The accepted-token mass is above 99.5% for every probe. This measures agreement with same-assistant annotations on an exposed two-family panel, including both procedural and missing-card errors. [Judge instructions and label-order replay](../relay_memo_guard_judge.py) · [Per-record outcomes](evidence/relay-memo/frozen-judge/metrics.json)

The Mali midpoint rejects one sound Myanmar memo. The Myanmar midpoint admits one flawed Mali memo. The score distributions overlap across families. On the ten unique actual generations, using the locked pooled guard alone keeps two sound bodies and replaces eight with matched reference records. Combining the guard with exact title and length requirements replaces all ten. The transferred midpoint releases one flawed memo. These are decisions replayed on existing scores, and the fallback is matched by the delivered cards and checked result. [Threshold transfers](evidence/relay-memo/frozen-judge/thresholds.json) · [Release counterfactual](evidence/relay-memo/guarded-release.json)

The generic compiler is a separate baseline. It validates routing and ownership, uses only delivered cards to check the proposed action against every compatible world, and reproduces curated official claims from exact source spans. An unsupported action produces UNRESOLVED. It passes the title and 100-word cap in all 96 recorded replays across four families, including 32 Qwen-head traces across Mali and Myanmar. All 12 tests that alter routes, card ownership, receipt continuity or an official quote are rejected. Its replay checks the decision independently of the actor's reported warrant. The historical source selections are curated and do not cover unlisted matters. [Compiler and input contract](../relay_compiled_record.py) · [Records and rejection witnesses](evidence/compiled-record/records.json) · [Exact replay](evidence/compiled-record/replay.json)

### Transfer the frozen relay to seven-option workshops

Score 46 local Qwen3.5-4B observations on the Venezuela and outer-space workshop cases. Each has seven packages, an impasse action, and four private-card worlds with one feasible agreement and three impasses. Rotate the package labels by three and two positions respectively, preserving the choices and evidence in each world. Reuse the head fitted on the synthetic archive task with zero updates. The model scores one-token responses to prose prompts with listed legal actions. [Scorer and replay](../relay_text_transfer.py) · [Raw prompts and logits](evidence/relay-text-wide/actions.jsonl)

| Greedy policy | Both cards delivered | Warranted agreement | Warranted impasse | Total warranted |
|---|---:|---:|---:|---:|
| Frozen Qwen | 4/8 | 1/2 | 0/6 | 1/8 |
| Learned communication only | 8/8 | 2/2 | 0/6 | 2/8 |
| Learned chair only | 4/8 | 1/2 | 6/6 | 7/8 |
| Both learned components | 8/8 | 2/2 | 6/6 | 8/8 |
| Learned communication with fixed overlap rule | 8/8 | 2/2 | 6/6 | 8/8 |

Forcing both cards to reach the unadapted chair still leaves all six impasses unwarranted. On outer space, the learned chair can warrant three impasses using the relay card alone, and the agreement requires the far card. With both learned components, one round or either muted source leaves four of eight warranted, all impasses. Muting both sources leaves zero warranted even though six choices are correct guesses. Under sampling restricted to the listed letters, the learned policy's expected warranted rates are 82.5% for Venezuela and 92.4% for outer space. The fixed overlap rule with learned communication gives 82.7% and 92.7%. The six impasses share the structure of disjoint menus and the two agreements each have exactly one common package. [Full scores and trajectories](evidence/relay-text-wide/report.json)

The compiler independently checks all 40 greedy peer dispositions using delivered cards. It labels every unwarranted choice UNRESOLVED and produces source-bound memos of at most 99 words. Replay reproduced the saved scores and records byte for byte from 7,509 scored input tokens. The authored menus and constrained actions measure controlled transfer. Open-ended deliberation, choice among several viable agreements, and independently reviewed memo quality remain separate endpoints. [Replay receipt](evidence/relay-text-wide/replay.json)

### Choose among several feasible compromises

Reuse the seven Venezuela and outer-space packages with three new fictional scorecards per seat. A score of zero rules out the package. Among feasible packages, the announced rule maximizes the lower of the delegates' two scores, then their sum. Give full credit to any exact tie. A disposition is warranted only if it is optimal in every world consistent with both the public card domains and the actually delivered cards. There are five agreement worlds and four impasses in each family. All agreements have more than one feasible package.

For example, on Venezuela, a relay card scoring B=3, D=2, F=1 gets a far card scoring B=1 and D=3. The winner is D, with a minimum score of two against B's one. Change the far card to B=3 and D=1 and B becomes the sole winner, while both proposals remain feasible. On outer space, scores of D=2 and F=3 for one role and D=3 and F=2 for the other produce an exact tie when all other packages score lower. A final explanation can choose either and should preserve the tie. [Fixture definitions](../relay_compromise.py)

Train the same small CPU action policy twice on 216 procedural worlds across 24 synthetic tasks with three or four packages. The chair sees raw scores on the received cards. Neither a warrant flag nor the computed comparison enters its observations. Both fits share initialization, exposure and a per-message cost. They differ in whether the terminal success bonus requires warranted feasibility or warranted optimality. The seven-package fixtures stay out of training.

| Greedy policy | Warranted optima on agreement | Warranted impasses | Total warranted optima |
|---|---:|---:|---:|
| Full delivery, first feasible package | 5/10 | 8/8 | 13/18 |
| Learned for feasibility | 9/10 | 0/8 | 9/18 |
| Learned for optimality | 10/10 | 8/8 | 18/18 |
| Full delivery, fixed compromise rule | 10/10 | 8/8 | 18/18 |

Both fitted policies deliver both cards in every clean case. Swapping in the fixed chair or fixed transport preserves all 18 warranted optima for the successful fit. Each one-source mute eliminates all warranted optima. A separate decision-rule implementation verifies all 540 saved dispositions from the delivered traces, and the frozen policy passes 252 package-rotation and seat-swap replays including the unchanged panels. The two optimizer traces reproduce byte for byte. These are typed scores with stipulated utilities and a fixed rule. Final prose and the language model's ability to extract or negotiate preferences have separate evaluation requirements. [Fits and per-case choices](evidence/relay-compromise/report.json) · [Decision and permutation audit](evidence/relay-compromise/audit.json)

### Give the ranked chair prose cards

Score frozen Qwen3.5-4B on the same preferences written as “acceptable,” “preferred,” and “strongly preferred,” with an explicit grading rule. Test all complete and incomplete chair views on both workshops and two synthetic reference tasks, giving 64 observations and 14,000 input tokens. When a card is absent, give its public alternatives and include an unresolved response option. Rotate package order in each UN-linked family and score one-token responses over the listed actions. The caller sees package identifiers and preference text. The underlying clauses stay in the case dossier. [Prompts and logits](evidence/relay-compromise-language/actions.jsonl)

The information ceilings assume nine equally likely worlds and a fixed protocol that delivers the relay card in round one and the far card in round two. Correct-choice ceilings allow guessing and count any actual optimum. Certification requires a choice to remain optimal across all worlds compatible with the delivered evidence.

| Workshop | Correct with zero cards | Correct after one round | Correct after two rounds | Certifiable by round |
|---|---:|---:|---:|---|
| Venezuela | 4/9 | 4/9 | 9/9 | 0/9, 0/9, 9/9 |
| Outer space | 4/9 | 5/9 | 9/9 | 0/9, 0/9, 9/9 |

| Workshop | Best package, both cards | Correct impasse, both cards | Correctly unresolved, distinct incomplete views |
|---|---:|---:|---:|
| Venezuela | 2/5 | 4/4 | 0/7 |
| Outer space | 2/5 | 2/4 | 0/7 |

Across the ten agreement views, Qwen chooses a feasible package in six and a best package in four. Filtering the saved scores to feasible options raises best-package selection to five of ten. A separate prose parser and decision oracle recover the accepted decisions from the actual model input for all 64 observations. The replay uses the previously fitted relay to deliver both prose cards in all 18 clean worlds. Choosing from saved Qwen scores after those deliveries yields the same 10/18 completed decisions as direct pooling. Under a one-round cut or either mute, its knowledge remains insufficient and it never reports unresolved. Six of the 14 distinct incomplete views assert impasse and eight name a package. [Scores, ceilings and routed replay](evidence/relay-compromise-language/audit.json)

The model weights are frozen and all observations use constrained action responses. This experiment tests choice and uncertainty from supplied scorecard prose. Negotiating or eliciting preferences and defending the decision in generated prose remain separate endpoints.

### Train communication and ranked decisions on a shared return

Train the two senders' shared policy and the chair's action head together on exact expected team return. The chair uses Qwen's frozen action scores and per-package grades parsed from the text of delivered cards. It receives neither the winning package nor an overlap or warrant flag. A warranted decision earns one point, a warranted unresolved report earns 0.25, and a send costs 0.04. Both fits use 100 CPU updates on the 18 worlds from the two synthetic reference tasks. The 18 Venezuela and outer-space test worlds stay outside the optimizer. Their prompts and Qwen scores are reused without additional inference.

The uniform fit gives all 18 training worlds equal weight. Only one of those worlds is an impasse. The coverage fit gives agreement and impasse equal total weight and masks the chair's cards after transport. It leaves the delivered view unchanged 60% of the time, masks either seat alone 15% of the time each, and masks both 10% of the time. This is one bundled intervention, so the result cannot isolate the effect of either change.

| Greedy policy | Best compromise on clean agreement worlds | Correct impasse on clean impasse worlds | Warranted unresolved with one card muted | Warranted unresolved with both cards muted |
|---|---:|---:|---:|---:|
| Frozen Qwen, fixed transport | 4/10 | 6/8 | 0/36 | 0/18 |
| Uniform joint fit with Qwen scores | 10/10 | 0/8 | 0/36 | 0/18 |
| Coverage joint fit with Qwen scores | 10/10 | 8/8 | 0/36 | 18/18 |
| Coverage joint fit using grades alone | 0/10 | 0/8 | 36/36 | 18/18 |
| Checked decision, fixed transport | 10/10 | 8/8 | 36/36 | 18/18 |

The grade-only coverage policy sends no cards and opts for unresolved in all 18 clean worlds. The Qwen-backed coverage policy delivers both cards in all 18 clean worlds. With just the trained chair and fixed senders, it reaches the same scores across all five delivery conditions. With learned delivery and the frozen chair, it matches the frozen baseline. Its mean probability of a warranted decision across legal actions is 98.2% for complete agreements and 86.3% for complete impasses. The tested failure is overclaiming with one visible card, including on the one-round cut. This persists despite masking during training.

All decisions and both optimizer records reconstruct exactly. An oracle using the delivered traces verifies 540 stored outcomes per fit across the routed arms. This is an adaptive development comparison using two procedural training families and two exposed, UN-linked evaluation families. [Uniform fit](evidence/relay-compromise-joint/uniform.json) · [Coverage fit](evidence/relay-compromise-joint/coverage.json) · [Replay receipt](evidence/relay-compromise-joint/replay.json)

### Distinguish missing evidence from an unresolved decision

The original incomplete views all require an unresolved report, so a policy that abstains whenever a card is absent would pass that panel. Add eight one-card views by narrowing the missing card's public alternatives. Each workshop contributes two warranted decisions, an agreement and an impasse, and two unresolved views. The visible scores and the declared compromise rule stay fixed for each matched contrast. [Prompt construction](../relay_compromise_public.py)

An equally sized pair of joint fits compares raw delivered grades and presence flags with the addition of per-package minimum and maximum grades over public alternatives. Both use the balanced reward schedule and masking from the coverage fit. In the clean worlds, the capacity control keeps 18/18 warranted decisions and the added bounds fit reaches 10/18. Under a one-card outage, both get 18/36 right on the original panel, along opposite missing-seat directions. The ranges result sacrifices the eight complete impasses without improving the aggregate outage score.

Per-package ranges can lose decisive information. With one card fixed at (3,3,3), the domains [(1,1,1), (1,2,2)] and [(1,1,2), (1,2,1)] induce identical score ranges. Both B and C are optimal in every completion of the first domain. The second domain yields B or C depending on which card is missing, so its decision remains unresolved. [Exact counterexample](evidence/relay-compromise-public/completions.json)

A separate readout keeps the original coverage-fit weights. It scores each intact public completion using the saved complete-view logits and makes a definite recommendation only if those predictions agree. It keeps all 18 complete decisions and correctly abstains in all 14 original incomplete views. It also gets seven of eight narrowed views right. In the remaining outer-space agreement, one possible card permits an exact D/F tie and the model prefers F, while the other requires D. Comparing each completion's two highest ranked actions recovers D, but creates two falsely definite decisions on the narrowed ambiguous views and five on the original incomplete views. The artifact includes the completion cards and the predicted and independently checked choices for each. No new training or inference is used for this readout, since both workshops' complete views were already scored. [Readout and witnesses](evidence/relay-compromise-public/completions.json)

| Readout on the eight narrowed one-card views | Warranted agreement | Warranted impasse | Warranted unresolved |
|---|---:|---:|---:|
| Frozen Qwen on partial prose | 0/2 | 0/2 | 0/4 |
| Capacity control on partial prose | 0/2 | 0/2 | 2/4 |
| Public grade bounds on partial prose | 2/2 | 0/2 | 0/4 |
| Agreement across complete-view top choices | 1/2 | 2/2 | 4/4 |
| Intersection of the two highest choices per completion | 2/2 | 2/2 | 2/4 |

Direct partial-prose evaluation uses eight fresh frozen Qwen3.5-4B observations, 1,796 input tokens and the existing action-letter interface. This exposed development panel holds the package menus and scorecards fixed and varies the public alternatives. The completion readout uses only those public alternatives and computes one score per possible completion unless a cached score exists. [Prompts and logits](evidence/relay-compromise-public/actions.jsonl) · [Joint fits and outcomes](evidence/relay-compromise-public/bounds.json) · [Exact replay](evidence/relay-compromise-public/replay.json)

### Recover and disclose a ranked mandate

Give each delegate its own ranked mandate in prose and use the existing Venezuela and outer-space package clauses. The 12 mandates cover conditions such as consent, coordination, instrument, forum and review. A delegate chooses one of three complete disclosures or withholds its card. Two answer orders give 24 frozen Qwen3.5-4B observations. A separately annotated clause projection checks that each authored mandate matches its intended card. The learned senders and the complete-view readout then replay their actual routes using the cards the delegate selected. Each world combines independently scored delegate observations, so the replay tests error propagation from local reading through routing and decision. It does not include new peer dialogue or multi-turn inference.

The initial prompt shows package attributes in a public table and lists preference grades by package ID. The model recovers 6/12 cards in each answer order. In the first order, it makes three inaccurate disclosures and withholds three. Rotation turns every error into a withheld card, with a different set of six correct reads. Passing only disclosures that agree across the two orders retains five correct cards. In the 18-world replay, the first order puts nine false cards at the chair, produces eight actual optima including guesses, and yields five definite decisions unsupported by the truthful evidence. The rotated order yields four actual optima without false cards. Agreement between orders yields three completed decisions and 15 justified unresolved reports. With truthful cards supplied, the same fitted senders and readout reach 18 completed decisions. [Raw observations and decision replay](evidence/relay-ranked-mandates/report.json)

An oracle that drops every incorrect card establishes four warranted decisions in the first-order replay. Dropping only contradicted grades and retaining individually correct grades establishes eight. This measures the value of verifying individual claims. The verification uses the privately authored ground truth and serves as an upper-bound diagnostic for a source verifier. [Per-card and per-grade corroboration](evidence/relay-ranked-mandates/report.json)

A matched prompt control puts the public package terms directly beside their preference grades in each disclosure choice. The private mandate, action set and rotations stay fixed. Correct readings rise from 6/12 to 11/12 in each order. The delegate misreads the same Venezuela profile both times. It ranks staged joint coordination above broad joint coordination, contrary to the mandate. The first-order scores tie the correct and incorrect cards, with the displayed-order tie break selecting the incorrect card. The rotated scores favor the same incorrect card outright.

| Layout-consensus replay | Correct disclosed profiles | Wrong cards delivered across 18 worlds | Correct actual decisions | Decisions warranted by fully verified cards |
|---|---:|---:|---:|---:|
| Package IDs and separate clause table | 5/12 | 0 | 3/18 | 3/18 |
| Terms next to each grade | 11/12 | 3 | 18/18 | 15/18 |
| Truthful card control | 12/12 | 0 | 18/18 | 18/18 |

The three remaining public decisions are correct despite the mislabeled card. Corroborating individual grades would support all three without retaining the inaccurate grades. Thus outcome-only scoring would hide the remaining preference error, while dropping the whole receipt would hide the evidence it still carries. Both prompt sets and all 144 routed records replay exactly. The second prompt set is an adaptive control on the same mandates. It uses constrained selection among authored complete disclosures and has no new optimizer updates or free-form memo. [Prompt control](evidence/relay-ranked-mandates/grounded/actions.jsonl) · [Routed and corroborated outcomes](evidence/relay-ranked-mandates/grounded/report.json) · [Replay receipt](evidence/relay-ranked-mandates/replay.json)

### Check a targeted clarification against its source

Starting from the terms-next-to-grades disclosures, let the chair see the two leading profile choices and their score margin for each delegate. Choose the delegate with the smallest margin, with a fixed relay-first tie break. Ask for one grade on a package that distinguishes the delegate's two leading profiles. The delegate answers from its own mandate with no feedback about the expected grade. The model answers 7/12 queries correctly in one answer order and 8/12 in the other. The two orders produce 24 reply observations and 3,474 input tokens. Replay one query per world, and use fixed relay and far targets as comparisons. The learned senders and chair remain frozen. [Exact questions, replies and routes](evidence/relay-ranked-clarification/report.json)

| One-query policy on 18 workshop worlds | Decisions warranted by truthful received cards | Unsupported definite decisions | False cards received |
|---|---:|---:|---:|
| Keep the original disclosure | 15 | 3 | 3 |
| Lowest margin, replace from agreed replies | 12 | 6 | 6 |
| Fixed relay target, verify a revision against the mandate | 18 | 0 | 0 |
| Fixed far target, verify a revision against the mandate | 15 | 3 | 3 |
| Lowest margin, verify a revision against the mandate | 18 | 0 | 0 |

The successful answer identifies the staged package with joint coordination as a fallback. The verified update preserves the explicit host-consent requirement. The same one local correction appears in three Venezuela worlds. Other replies agree across orders while introducing inaccurate grades, so consistency alone is insufficient. The local verifier admits a revision only when both orders agree, the grade identifies one public profile, and literal source spans establish the queried terms and grade. It uses the verbatim mandate at the responding seat and does not fill missing grades. Its conservative matching is specific to these authored phrases and can withhold valid revisions that use different wording. The result matches a fixed relay target on this panel. [Source checks and retained spans](evidence/relay-ranked-clarification/guard.json) · [Replay receipt](evidence/relay-ranked-clarification/replay.json)

### Write a final memo from the verified ranked record

Generate eight free-form Qwen3.5-4B memos. In three Venezuela worlds, pair the originally reported and verified receipts while holding the recommended package or impasse fixed. Add one withheld-card memo and one outer-space agreement with a verified tie. Every packet carries exact historical source spans. The reviewer grades disposition, operative reasoning, positions, remaining issues, official procedure and authority on the 70-point rubric. Use an exact heading, a 120-word cap and an authority and factual guard. The semantic judgments are from the same assistant using arm-free review IDs. The replay checks exact spans, prompt reconstruction and token decoding. [Frozen rubric](ranked-final-rubric.json) · [Memos](evidence/relay-ranked-final/memos.jsonl) · [Scored review](evidence/relay-ranked-final/scores.json)

| Evidence at the writer | Rubric points out of 70 | Factual and authority guard |
|---|---:|---|
| D, reported → verified | 49 → 21–28 | Failed → failed |
| B, reported → verified | 49 → 56 | Failed → clear |
| Impasse, reported → verified | 49 → 35 | Failed → clear |
| United States card withheld | 56 | Failed |
| Verified outer-space tie | 14 | Failed |

All three verified Venezuela memos preserve the corrected fallback. The D memo prints the right heading and then selects B. The B memo omits the sum used to break the tie on lower grades. The impasse memo names one package per role and does not establish that the full acceptable sets are disjoint. The withheld-card memo invokes separate historical votes to confirm a workshop impasse, and the outer-space memo uses official rejection to deny the feasible tie. Six memos meet the exact heading and six meet the word cap, with one ending at the token limit. No memo passes all three requirements of heading, cap and guard.

A deterministic reference writes from the same packets and keeps the reported card explicitly provisional. It derives the comparing grades, ties and missing-card request, and renders both archived source claims with their instrument numbers. All eight reference memos preserve the exact heading and fit in 80–99 words. This establishes a source-bounded reference for the final writer. The free-form writer's failures remain visible even when the upstream decision certificate is correct. [Compiled reference records](evidence/relay-ranked-final/reference.json)

### Keep verified facts fixed while generating the explanation

Compose the heading, attributed grades, corrected grade, historical evidence and authority limit directly from the verified packet. Qwen receives only a decision certificate and contributes an unedited reasoning paragraph. That certificate supplies the selected and alternative packages and their lower grades and sums, the disjoint sets for an impasse, or the missing card owner. Neither prompt asks the writer to recalculate the decision or rewrite the official record.

The first writer explains the relevant comparison in five of eight cases. Five paragraphs exceed the assigned word limit, and only the outer-space tie passes the combined factual, reasoning and length check. One impasse is incorrectly labeled provisional and one unresolved explanation asks the missing-card owner to request its own card.

A matched one-sentence prompt replaces the provisional Boolean with an instruction and explicitly states who should request a missing card. All eight comply with the shorter length limit. Four numeric comparisons pass the full check. The two impasse explanations introduce unsupported claims, the unresolved explanation invents a package identifier and omits the request, and the tie leaves out both numerical values. The prompt comparison uses the same cases and same-assistant review with exact quoted spans. [First prompt and scores](evidence/relay-ranked-reason/report.json) · [One-sentence control](evidence/relay-ranked-reason/short/report.json)

A release check allows only recognized sentence forms whose package IDs, decisive grades or sums, and provisional wording agree exactly with the certificate. It keeps four unedited model sentences and uses the compiled reference for the other four. The eight released memos are 80–104 words with unchanged headings and official claims. All 20 tested mutations of an admitted sentence are blocked, including switched packages, changed numeric grades and appended claims of official authority. The grammar is an adaptive contract for the admitted numeric comparisons. The fallback remains responsible for unrecognized wording and other dispositions on this panel. [Released records and mutations](evidence/relay-ranked-reason/release.json) · [Exact replay](evidence/relay-ranked-reason/replay.json)
