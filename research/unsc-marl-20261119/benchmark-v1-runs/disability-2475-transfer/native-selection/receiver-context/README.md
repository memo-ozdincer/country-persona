# Give the selector the chair's existing information

France still chooses the participation-and-safety passage under
both receiver-context prompts and both menu orders. The first prompt
adds the chair's public lead. The second adds that same lead and a
focused request for a distinct national position on an instrument's
scope or implementation. The four prompts keep the local menu, one-ID
capacity, frozen Qwen3.5-4B checkpoint, system instructions and
whole-message decoder fixed. Russia and the UK reuse their original
choices. All outcomes below therefore reflect changes to the France
selection alone. [Protocol](protocol.md) · [Matched requests](plan.json)

| France input | Chosen passage, normal / reversed | Treaty minus participation log mass, normal / reversed | Full receipt |
| --- | --- | ---: | ---: |
| Original local menu | Participation / Participation | −0.062 / −1.425 | 56 |
| Public lead | Participation / Participation | −0.081 / −1.320 | 56 |
| Public lead and focused request | Participation / Participation | −0.444 / −0.770 | 56 |

Looking at the canonical wire spelling alone flips the reversed
focused-request call to the treaty passage. Its normal-order
counterpart still selects participation. The locked protocol
uses likelihood over the permitted spellings. On that readout,
the choice and final record stay unchanged in all four conditions.

The four calls score 32 candidate sequences, with 1,246 input tokens
and 16 tokens in the rendered selected messages. Inference takes
2.31 measured seconds on NVIDIA RTX PRO 6000 Blackwell Server
Edition, excluding checkpoint load. Both this run and the preceding
six-call run finish with zero optimizer updates.
[Native responses and likelihoods](evidence/likelihood.jsonl) ·
[Token-verified selections](verified.json) · [Complete score banks](scores.json)

All four banks match the original native bank exactly. The original
routing replay therefore applies unchanged, with mean nominal
documentary release of 43.57. Crossing the selected notes with the
prior receipt probabilities gives zero change before pricing the
extra context. The original adaptive policy puts France's card in
6.68% of modeled receipt mass. The focused prompt was authored after
observing the France omission on this exposed docket. This measures a
directed question's effect on evidence selection with simulated
delivery. The route does not price the new context or the request.
[Receipt and value crossover](value.json)

## Reproduce

From this directory with the same Python environment as the parent
experiment:

```bash
set -o pipefail
"$py" context_test.py plan | cmp plan.json -
"$py" context_test.py verify | cmp verified.json -
"$py" context_test.py score | cmp scores.json -
"$py" value.py | cmp value.json -
```
