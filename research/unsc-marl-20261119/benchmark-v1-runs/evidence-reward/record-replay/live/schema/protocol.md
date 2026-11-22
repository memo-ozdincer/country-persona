# Clarify the field and value extraction contract

All four original live replies used the correct outer JSON keys and
put the input key own_card and the whole private card in their values.
The role-local validator rejected them. Keep the original prompt
payloads, actions, first-stage signs, model, generation ceilings and
decoder fixed. Append one system instruction explaining how to extract
the two substrings from the card, with a worked example in an unrelated
domain. Collect a single fresh answer at each of the same four states.
Compare to the unedited earlier answers under the identical strict
validator. Keep the final records and prior rubric marks unchanged.

Also verify a deterministic control that parses the already authorized
local card directly for this registered grammar. This control uses no
model and shares the same public interface. It bounds any claim that
the model is required for this particular input format.
