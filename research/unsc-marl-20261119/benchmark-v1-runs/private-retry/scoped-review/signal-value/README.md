# What can dispatch learn from the reviewer messages?

Compute the best achievable return on the Resolution 2422 archive when a
dispatcher sees the received sources, checked singleton scores, and the
recorded binary-checklist replies. The source order is latent and the two
orders have equal weight. An exact optimizer can buy any recorded reply
one at a time and then publish any available subset. The results are
upper bounds for policies using the stated observations on these two
archived variants.

| Available observations | Shared-delivery net at 0.15 per answer |
| --- | ---: |
| Checked fallback | 50.2160 |
| Public mechanical checks, archive-calibrated dispatch | 51.0800 |
| Public mechanical checks plus any recorded review replies | 51.0800 |
| Hidden mechanical checks plus any recorded review replies | 51.0584 |
| All exact grades, unpriced ceiling | 51.3600 |

With public mechanical checks, the old reviewer replies add zero even
when free. On full receipt the archived 72-word Peru–Russia draft is a
public clue to the order. An archive-calibrated dispatcher can then
choose the 55-point triple in the forward order and the 55-point
Peru–Serbia pair in reverse. The gain from this clue depends on knowing
the two archived payoff tables. It measures an information ceiling.

When mechanical checks are hidden, the optimal policy asks for a
Peru–Russia pair review on full receipt. An unavailable response
separates the same two variants through the known cap, and the
returned review text supplies no extra distinction. At receipt 5
the owner and pooled responses to the Peru–Serbia pair are byte
identical across orders. The best possible route using those messages
keeps the 50-point singleton. Exact grades raise that receipt to
52.5 points in expectation. That single receipt accounts for the
0.28-point ceiling gap on the shared delivery mixture.

The output includes all eight receipt masks, three delivery laws,
three answer fees, all allowed review channels and the query trees.
The exact two-world check independently verifies that any informative
query must separate the variants, and that selecting the cheapest such
query suffices. A dispatch replay checks each tree's realized return.
[Protocol](protocol.md) · [Upper bounds and review policies](bounded.json)

From this directory:

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 bound.py | cmp bounded.json -
```

## Test a question about unsupported relationships

We collected 52 frozen Qwen3.5-4B answers to one binary check, comparing
a general attribution guard with a direct question about relationships.
The two questions used identical evidence, draft, output caps and
swapped label mappings. The test included seven in-limit archival
drafts and six authored controls based on the pinned Mali and Myanmar
evidence. In each control family, plain and explicitly contrasted
factually warranted statements serve alongside a contrast on
different questions. The control keys represent the intended relation
checks.

The relation-specific prompt answered A on all 26 calls. All 13
decisions remained unresolved when the mappings were required to agree.
The general prompt resolved two archival cases as supported, one
correctly and one incorrectly. It sent the forward Peru–Serbia pair
and withheld the reverse, giving 25 points across the two equal
receipt-5 variants before paying for the two calls. Its raw answers
separate the two variants, but they are reversed as judgments of
support. A fitted reversal on that pair would use the exposed labels.
Both prompts left all six controls unresolved. All 52 responses
parsed as complete single letters. The experiment isolates a response
bias that a more sophisticated dispatcher cannot remove by using the
stated semantics of the letters.
[Locked protocol](relation-review/protocol.md) · [Answers and receipt replay](relation-review/results.json)

## Require a verbatim phrase instead of a letter

The follow-up requires `CLEAR` or `FLAG` followed by a verbatim draft
span. All 13 outputs begin with FLAG. Three hit the output cap and
three other replies used a comma where the declared format required a
space. Seven replies pass. Only three of the 13 final decisions match
the keys. One is an archival draft and two are authored controls. The
reader flags “By contrast” verbatim on all four controls that contain
it, including both warranted contrasts. Exact span membership validates
the quote's provenance. Here it does not validate the interpretation.

Both Peru–Serbia replies fail to produce a usable verdict, so dispatch
keeps the checked fallback at 50 gross. The 0.15 model-call charge
reduces this to 49.85 on those receipts and costs 0.0168 points over the
shared delivery mixture. The existing oracle identifies an opportunity
of 2.5 points on that receipt before model costs. The attempted
review formats did not realize it.

The two GPU launches used frozen Qwen3.5-4B and NVIDIA RTX PRO 6000
Blackwell Server Edition. These are model-quality diagnostics on
seven drafts from one exposed archive and six authored controls.
Archival guards are same-assistant judgments. The delivery distribution
and call prices are simulated. No learning updates occur.
[Quote protocol](quote-review/protocol.md) · [Raw reply verdicts and replay](quote-review/results.json) ·
[Letter launch](relation-review/evidence/launch.json) · [Quote launch](quote-review/evidence/launch.json)

To verify both model runs with the local Qwen environment:

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python relation_control.py plan | cmp relation-review/plan.json -
python quote_control.py plan | cmp quote-review/plan.json -
python relation_control.py verify | cmp relation-review/results.json -
python quote_control.py verify | cmp quote-review/results.json -
```
