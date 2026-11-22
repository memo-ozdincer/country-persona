# Fit a shared team on one docket and transfer to the other

The sender gets the public forwarding price, both transport rates, the
standalone rubric coverage of its own document, and the frozen witness
verdict for that source. The receiver gets only the verdict if the
source arrives, or a missing-message symbol. Both actors use the same
weights on every docket and private view. Neither sees docket or view
IDs, feasible pair rewards or the alternative action's return. The
coverage field comes from the already-reviewed standalone source card.

Use the same outcome tables and REINFORCE constants as the earlier
per-docket fit. For each of the two training directions, fit on 512
batches of one docket only. Evaluate frozen on all 96 held transport,
price and mixture conditions of the other docket. Also swap one actor
at a time for an exact best response on the target. This separates
losses in forwarding from losses in reply selection.

After the frozen test, give the two actors 32 target batches. Compare
source warm start and zero initialization using the same exploratory
random draws. Reset optimizer moments in both cases. Report a no-send
control and the exact best policy with the same observation interface.
The main held result is zero-shot. The 32-batch results describe
adaptation within the target docket. Use one fixed seed family and no
sweep. This is archival policy training over one verified bit and
source-template rewards, with no change to the language model or
frozen release.
