# UN deliberation and multi-agent reinforcement learning

This archive records how the UN simulations work, what was trained, and
what the experiments establish. Start with the [frozen benchmark v1.7](benchmark-v1.7/README.md)
to run the evaluation. Use the [experiment index](EXPERIMENTS.md) to find a
particular method, run, output or replay. The [research notebook](../../BENCHMARK.md)
keeps the dated design decisions and evidence, including failures and
superseded versions.

## How the evaluation works

V1.7 includes 11 episodes from five Security Council event families and 66
scored conditions. It draws on official meeting and draft records, UNBench,
and matching UNSC-Bench rows where available. Historical episodes assess
reconstruction from assigned evidence. Fictional workshops use sourced context
and simulated private mandates, with exact decision keys. All released cases
are exposed development material.

Two desks write short evidence notes, and a chair writes a single final
record. In **peer-informed drafting**, the second desk reads the first desk's
note before writing. In **independent drafts**, both desks write from their own
evidence. The chair reads both notes in either condition. The two conditions
reuse the same opening note within each speaker order. The **pooled solo**
analyst sees all assigned evidence from the beginning and has the same call
count and output budgets. The two desk orders test sensitivity to who sees
whose note. Input token costs are measured separately.

The final-record rubric assigns up to 70 points for factual disposition,
source attribution, material positions and objections, and limits on Council
authority. The judge cites exact evidence and answer spans. Material factual
errors or release failures can zero the released score. Transcript review
scores key points, arguments and peer engagement separately, alongside
turn counts, distinct ideas and token use. The primary comparison is the
within-order peer minus independent difference, averaged equally by event
family and reported separately for historical reconstruction and workshops.
See the [case packets](benchmark-v1.7/cases.json), [final judge](benchmark-v1.7/final-judge.md),
and [transcript judge](benchmark-v1.7/process-judge.md).

## How we simulate and train

| Setting | Private information and actions | Outcome and controls |
| --- | --- | --- |
| Negotiation workshop | Two roles have simulated mandates. They exchange proposals or requests, then choose an option or hold. | Exact feasibility and agreement checks distinguish finding agreement from correctly holding on an infeasible world. |
| Evidence routing | One desk holds a statement or passage. A second desk can choose a reply passage from a local menu. A chair receives the delivered evidence. | Shared reward uses released final-record points minus send costs. The simulator varies delivery loss, availability, prior, speaker order and downstream writer. |
| Text-conditioned routing | Frozen Qwen3.5-4B reads local source text to select a clause or assess a comparison. Trained routing heads receive the resulting local observation. | Tests compare learned decisions with a fixed source rule, the strongest arrival-only route, and exact informational ceilings. Record quality uses source checks or explicit review. |

The main learning comparisons use decentralized decisions with a shared
terminal reward. The studies include sampled policy gradients, causal
send-versus-withhold comparisons, and receipt-value estimation from a
single observed outcome per episode. Some train on scored archives; others
use fresh language-model calls with a frozen writer or reader. Each experiment
identifies which components were trained, which model calls were fresh, and
which evidence was replayed. The [initial pilot](README.md),
[general evaluation](GENERAL_EVALUATION.md), and [MARL handoff](MARL_HANDOFF.md)
explain the evolution from workshop decisions to source-grounded routing.

## What the results support

| Experiment | Result | Scope |
| --- | --- | --- |
| Gulf of Guinea and Libya brief crossover | Peer exposure improved final Gulf of Guinea briefs by 20 and 30 points across the two speaker orders. Libya tied in both orders. | Twelve briefs, two exposed dockets, and assistant review. [Evidence](benchmark-kit/reader-use/chair-brief-crossover/README.md) |
| Learning from one observed outcome on Resolution 2744 | The learned peer route reached 40.42 net, versus 39.38 for best arrival-only and 38.54 for the fixed rubric route. It fell to 22.68 with a different writer. | Deterministic archived rewards and held transport, price and prior settings. [Evidence](benchmark-v1-runs/terminal-feedback-routing/README.md) |
| Writer change on Resolution 2744 | Screened peer routing reached 38.24 in a mixed writer pool, versus 38.08 for the exact arrival-only ceiling and 31.55 for stale pair approvals. | The cache reuses exact reviewed records. The mixed pool used two archived writers. [Evidence](benchmark-v1-runs/writer-refresh-feedback/README.md) |
| Resolution 2417 | After source-bound assembly, learned peer routing scored 40.56 versus 39.46 for best arrival-only. The fixed source rule matched the learner. Direct relative choice also reached the peer ceiling on reworded cards. | An exposed docket with registered source links. Calibrating on four donors added no measured gain. [Assembly](benchmark-v1-runs/hunger-2417-transfer/witness-routing/README.md) · [Relative choice](benchmark-v1-runs/relative-routing-transfer/README.md) |
| Judge reward audit | An automatic guard produced apparent peer gains of 3.22 and 4.85 points on the tribunals case. Both gains were zero against archived review. | The guard wrongly released five eligible briefs. [Evidence](benchmark-v1-runs/guard-reward-selection/README.md) |

These experiments establish case-specific benefits from peer evidence and
working training methods for structured routing. A reliable advantage on
unseen UN event families, robust improvement in open-ended deliberation, and
agreement across independent human reviewers remain unverified. Where an
unfitted rule matches or beats the learner, the detailed report gives it
equal visibility.

## What is recorded and how to reproduce it

Git includes the frozen v1.7 archive and its unpacked files, earlier
benchmark versions, source packets and provenance, evaluator and runner
code, prompts, generated notes and records, transcript and token traces,
saved small policy and adapter artifacts, raw verdicts, score tables,
and replay receipts. The related [WTO peer pilot](../diplomatic-peer-pilot-20261118/README.md)
and [discussion metrics](../../docs/DISCUSSION_METRICS_20261118.md) are
also included. Published source datasets are pinned by references and
checksums. Some historical run commands refer to local data trees or model
checkpoints. The [data guide](../../docs/onboarding/DATA_AND_RESTORE.md)
covers the separate dependencies. Runtime caches and base model files
are outside this publication.

From a clone, verify the frozen release with the standard library:

```bash
cd research/unsc-marl-20261119/benchmark-v1.7
set -o pipefail
python3 -B verify.py | cmp verification.json -
python3 -B replay.py | cmp replay.json -
```

From the repository root, verify publication bytes with
`sha256sum -c research/unsc-marl-20261119/PUBLICATION.sha256`.
Individual experiment readmes give the commands and environment requirements
for their score or token replays. Byte and arithmetic replays establish
reproducibility of the saved evidence. Semantic grades retain their
original review provenance.
