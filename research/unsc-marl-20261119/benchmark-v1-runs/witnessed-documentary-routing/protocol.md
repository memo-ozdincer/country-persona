# Require a source witness before routing a documentary claim

Reuse the twelve official-document views of Resolutions 2553 and 2721.
Add one precise Afghanistan deletion that removes only the sentence
stating the condition for Russia's own support. Preserve the remaining
Russian statement. Keep the two claim hypotheses unchanged.

Ask a frozen model to provide a single exact excerpt that states the
speaker's position and the required condition or objection. Require
completion, visible contiguous text and a length of at most 75 words.
A matched outer pair of quotes may be removed. Otherwise reuse the span
verbatim. If a span passes this mechanical check, ask the previous
claim verifier to evaluate just that excerpt under both label mappings,
with the unchanged zero cutoff. Score the raw extractor, exact-span
gate, and exact-span plus semantic verifier. Preserve unsupported or
incomplete evidence attempts. An assistant independently checks
semantic sufficiency of every supplied excerpt for the purpose of
this experiment. This is a same-assistant second grading step, with no
independent reviewer claim.

Compare the locked prior claim output on the twelve original views. Map
each new binary judgment to the same two reply choices in each docket and
use the previous exact-record scores. Treat the Afghanistan deletion as
a source-neutral tie under the fixed record compiler. Report attribution and
release metrics separately. This measures evidence quality and decision
transfer on two exposed dockets. No model or policy weights change.
