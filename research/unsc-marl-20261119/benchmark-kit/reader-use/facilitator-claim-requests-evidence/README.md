# Ask for the claim that the earlier reply omitted

The prior learned UNIFIL route delivered a China reply that
kept its objection and sovereignty position while omitting
its support for the mission. The Myanmar fixed-request route
delivered a UK reply that kept sponsorship and consultation
but lost specific policy priorities. This experiment keeps
the two selected cards, opening evidence and route decisions
fixed. It tests a change to the request on those known branches.

Each case has three calls. The generic call uses the archived
question with a source-completeness instruction. The targeted
call uses the same instruction and asks for the omitted category
alongside the other relevant claims. The withheld call uses the
same targeted question and removes the sentence that supports
the omitted claim. The questions identify categories of evidence.
The reply still has to establish the answer from its card.
Each call uses the same output cap. Input lengths can differ.

Score exact supporting spans and source fidelity in each new
reply. Rerender all affected claims and retain the unchanged
earlier evidence. The scoring correction restores earlier
approved witnesses that had not appeared in the printed
record. For example, Brazil's mission support was approved
but withheld from the overlap clause while China's support
was missing. The new comparison checks that this already
approved Brazilian evidence can be used after the China reply
changes. The earlier outcomes and model inputs remain archived.
[Locked protocol](protocol.md) ·
[Prior source witnesses and final records](../facilitator-live-claims-evidence/README.md)

## Results

All six replies end within the call and word limits. Both
questions recover the previously omitted fact on each full source.
Neither targeted withheld-source reply introduces the withheld
claim. The China targeted reply retains the explicit qualification
that the draft failed to *fully* address Lebanon's concerns.
The generic reply says it “missed” those concerns. Both meet the
earlier criterion on inadequacy, while the targeted wording is
more precise.

| Routed test | Previous live reply | Generic with completeness instruction | Targeted | Targeted with evidence withheld |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL learned route | 56/70 | 63/70 | 63/70 | 56/70 |
| Myanmar fixed request route | 49/70 | 63/70 | 63/70 | 49/70 |

The China improvement restores the supported overlap with
Brazil. The UK improvement restores the supported sponsorship
and national position, and the comparison with India's regional
concerns. The matched targeted and generic arms reach the same
record scores. The historical reply used a different system
instruction, so the recovery cannot be assigned to one isolated
phrase in the common new instruction.

The original reassembler used claims printed in the old record
as its carryover. That would leave both China full-source results
at 56 despite an existing approved witness for Brazil's mission
support. The preflight exposed this behavior. The corrected
scorer restores the earlier approved, unprinted witness and
preserves the original scorer's result for comparison. It makes
no changes to generation prompts or exact-span review.

The test has six actual generations, no model updates, and
same-assistant review. The question edits respond to known
failures. The branches and their transport policies are fixed
for this comparison. The test establishes recovery of two
specific omitted categories on supplied historical cards.
[Raw replies and prompt locks](transcript.jsonl) · [Exact reviewed spans](marks.json) ·
[Record scores and carryover audit](results.json)

```bash
python facilitator_claim_requests.py verify facilitator-claim-requests-evidence
python facilitator_claim_requests_replay.py facilitator-claim-requests-evidence --marks facilitator-claim-requests-evidence/marks.json
```
