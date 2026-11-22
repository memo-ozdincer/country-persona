# Fit one paid recheck after the first source read

After inspecting the balanced mapping results, fit a proposer and a
remote reviewer on the recorded channels. The proposer sees only
the identity-order read and can withhold, publish its local relation,
or buy one of the two cyclic checks. The reviewer sees its own logits
and the first categorical relation. It may withhold, keep the first
relation, or substitute its own decisive relation. The shared reward
is +1 for a correct decisive judgment, −2 for a wrong decisive
judgment, and 0 for withholding. Each requested read costs 0.1.

Fit two small heads jointly with exact expectations over the legal
choices, 160 fresh updates, step size .2 and L2 penalty .02. Weight
archival families equally. Report both held-family fits and transfer
of the four-family fit to the eight Myanmar rows. Hold all gold
judgments outside policy inputs. Compare to first read alone, two
equal-call-budget fixed second readers, a fixed confidence rule
selected on fitting families alone, and the cost-adjusted three-read
unanimous control. The confidence control searches a prespecified
finite grid of one cycle, margin threshold and response rule. It
receives the same first local confidence and reviewer labels.
The new protocol follows the decoder analysis, reuses all measured
logits and adds no generation. Existing authors and event families
remain exposed.
