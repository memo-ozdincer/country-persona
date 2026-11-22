# Learn when to send and how to reply from terminal record rewards

**Two learned desks reach 33.376 in mean held utility, within 0.075
points of the exhaustive ceiling.** Each first desk decides whether to
forward its private source given the transmission cost and rates.
Each second desk chooses between its existing reply cards using the
docket and the observed result of the frozen claim checker. Missing
messages have their own observation. The actors receive a shared final
reward from an archived source-bound record after both decisions.
[Protocol](protocol.md) · [Weights, traces, and held settings](results.json)

| Policy over 192 held conditions | Factual release /70 | Mean send cost | Mean utility |
| --- | ---: | ---: | ---: |
| No send, fixed default reply | 31.469 | 0.000 | 31.469 |
| Always send, fixed default reply | 38.249 | 11.333 | 26.916 |
| Best sender with fixed default reply | 34.148 | 1.925 | 32.223 |
| Always send, learned reply | 40.707 | 11.333 | 29.374 |
| Learned sender, fixed default reply | 34.859 | 3.444 | 31.415 |
| Both desks learned | 36.820 | 3.444 | **33.376** |
| Exact ceiling with the same observations | 37.192 | 3.742 | 33.451 |

Both actors start from uniform Bernoulli choices and update with
on-policy REINFORCE on 131,072 simulated episodes (512 batches of 256).
Only the terminal score minus attempted forwarding cost enters the
advantage. The baseline is a running mean from prior batches for
each docket. The experiment uses one fixed seed. The analysis
evaluates greedy deployments and integrates delivery exactly.
It holds out transport probabilities, send prices, and private-view
prevalence. The underlying two dockets and six possible views are
seen during training.

The pair matches exact utility on 162 of the 192 settings. Replacing
the learned reader with a fixed partner drops utility by 1.960.
In the worst held setting, 90% delivery in both directions and a
price of eight, the fitted 2553 sender still withholds the Belgium
view. Sending it can earn the Germany–Belgium comparison. The
high prevalence of that view makes the regret 2.004 points in that
setting. This identifies an action the two-actor fit still misses
within its own environment.

The archived compiler gives known source cards and their registered
comparisons fixed scores. Each delivered message is represented to
the reply actor by a frozen verdict bit. The compiler uses actual
registered receipts separately from that bit. The second actor
cannot see a private document that failed to arrive. Both context
and communication are bounded by the experiment. Forwarding cost
is constructed in score points. This run learns lightweight actors
over authentic-document observations and archived rewards. It does
not update Qwen or measure live dialogue performance, novel partner
behavior beyond the fixed replacement, or transfer to new dockets.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B train_team.py --plan | cmp plan.json -
python -B train_team.py | cmp results.json -
```

[2553 documentary outcome table](../reform-2553-transfer/documentary-routing/README.md)
· [2721 documentary outcome table](../afghanistan-2721-source-contrast/documentary-routing/README.md)
· [Indexed claim reader](../indexed-witness-routing/README.md)
