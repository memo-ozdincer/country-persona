# Decide whether a proposed source relationship should release

Test the existing one-forward-pass Qwen3.5-4B support-judgment runtime on
two new relation families. Verify what the evidence says about each
attributed actor and the precise scope of the claimed relationship. Use
ten locked candidate/source pairs, each under both yes/no letter mappings,
for 20 physical calls. Include narrow valid paraphrases, claims that are
too broad with both source cards in view, and source removals that keep
the proposed sentence unchanged. The model sees no gold labels or scores.

Report each label assignment, average mapped logit and agreement gate at
a zero threshold. Test transfer of a stricter cutoff set solely on the
other docket's unsupported margins. Separately report deployment against
the matched author-reviewed fixed records. The renderer may add only
the exact canonical candidate and requires both registered source cards
under their original identities. Report what the additional model gate
does relative to the exact-source renderer and to standalone release.
Positive and negative probes are authored on previously exposed events.
This measures ability to verify a candidate comparison available to the
system. It adds no automatic candidate generator, policy learning or
benchmark release changes.
