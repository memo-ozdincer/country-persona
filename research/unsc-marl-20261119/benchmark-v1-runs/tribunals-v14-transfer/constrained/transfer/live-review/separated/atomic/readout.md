# Diagnose sensitivity to the answer-letter mapping

Add a diagnostic for the two fixed mappings using their saved logits.
Relabel each logit by its semantic status and take the mean of the two
logits for each status. The largest mean supplies the diagnostic choice.
This uses the same saved model scores and no new requests. Apply the
same guard and routing logic. The protocol's agreement rule remains
primary. The mean diagnostic can distinguish a useful ranking across
mappings from uncertainty created by hard label agreement.
