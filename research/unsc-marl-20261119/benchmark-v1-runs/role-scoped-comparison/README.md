# Verify each side of a typed Council comparison

The source-scoped verifier restores the trained team's **2.57-point
advantage** on the real 2721 receipts and clears both crossed pairs.
Each source card is judged independently against a role-specific
proposition. The renderer adds a relation only when both cards support
its propositions. The fixed-reply partner also recovers the authored
record's utility, which matters because the earlier typed writer
could score well by routing around its invalid claims.

| Decision rule | Real pairs /4 | Prior fictional controls /4 | New paraphrases /4 | New quoted reversals /4 |
| --- | ---: | ---: | ---: | ---: |
| Previous multiclass with label agreement | 3 | 3 | — | — |
| Phrase match | 4 | 4 | 0 | 0 |
| Source-scoped with averaged margins | **4** | 2 | **4** | **4** |
| Source-scoped with label agreement | **4** | 3 | **4** | **4** |

The primary averaged rule misses two controls. When the adopted clause
is edited to require Afghan consent, the model still endorses the
consultation-without-consent proposition at a margin of +1.313.
When the clause transfers UNAMA's mandate and work, the model
endorses the preservation proposition at +0.250. Label agreement
rejects the first erroneous match and retains the second. The
thresholds were fixed before looking at the new margins.
The eight new controls defeat the literal phrase rule. They test
valid paraphrases and words that occur in an earlier version, a
rejected position or a quoted claim. They are authored contrast
probes, outside the policy replay.

| Policy on the same 48 held settings | Mean utility |
| --- | ---: |
| Both desks learned | **43.291** |
| Best arrival-only sender and reply | 40.723 |
| Learned sender with fixed UNAMA reply | 38.929 |
| Best content-aware sender and reply | 43.321 |

The trained pair beats arrival-only in 36 settings, ties in nine
and loses in three. The source-scoped values match the archived
reference, including the fixed-reply swap. They align because the
verifier and renderer produce the same scored relation on each real
receipt pair. This measures one exposed task with two pre-authored
relation types, a frozen classifier and simulated delivery. The
propositions and rendering templates are authored, and the deployed
desks were already trained. This leaves transfer and learning with live
free-text rewards unmeasured.

The accelerator attempt stopped before collection because its target
NVIDIA RTX PRO 6000 Blackwell Server Edition became occupied between
preflight and its internal device check. The locked 64 first-token
reads completed on an eight-thread AMD EPYC 9575F 64-Core Processor
worker on Aurora. The checkpoint and prompts are unchanged. The prior
multiclass run used the accelerator and generated its label,
so hardware and decoding differ in that comparison. No optimizer
updates were made in this run.

[Locked protocol](protocol.md) · [Inputs](plan.json) ·
[Verified token traces and margins](verified.json) ·
[Exact policy replay](results.json) · [CPU launch receipt](evidence-cpu/launch.json)

From this directory in the existing Aurora Qwen3.5 environment:

```bash
set -o pipefail
python -B collect_roles.py plan | cmp plan.json -
python -B collect_cpu.py verify | cmp verified.json -
python -B score.py | cmp results.json -
```

The verification command works with the stored CPU evidence and model
tokenizer. It does not forward the model a second time.
