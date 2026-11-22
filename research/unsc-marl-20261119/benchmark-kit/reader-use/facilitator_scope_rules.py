"""Conservative compatibility checks for scoped coverage and recorded votes."""
import re

OPEN = "open"
CONFLICT = "conflict"

# The three states are zero, some-but-not-all, and all, for a nonempty set.
# These sets express compatibility of reported content. They do not certify
# that a speaker used a different formulation of that content.
COVERAGE = {
    "fully addressed": {"all"},
    "addressed all of": {"all"},
    "addressed some of": {"part", "all"},
    "addressed some but not all of": {"part"},
    "addressed none of": {"zero"},
    "did not fully address": {"zero", "part"},
}
# Longer alternatives precede their prefixes independently of insertion order.
FORCE = "|".join(sorted(map(re.escape, COVERAGE), key=len, reverse=True))
VOTE = r"voted in favou?r of|voted against|abstained on"
ACTOR = r"[A-Z][A-Za-z .'-]{0,48}?"
OBJECT = r"[A-Z][A-Za-z .'-]{0,48}"
COVERAGE_CLAIM = re.compile(
    rf"(?P<actor>{ACTOR}) said the text (?P<force>{FORCE}) (?P<topic>{OBJECT})[’']s concerns\.?"
)
COVERAGE_EVIDENCE = re.compile(
    rf"(?P<actor>{ACTOR})(?: supported [^.!?;:\n]+ but)? said the text "
    rf"(?P<force>{FORCE}) (?P<topic>{OBJECT})[’']s concerns\."
)
VOTE_CLAIM = re.compile(rf"(?P<actor>{ACTOR}) (?P<force>{VOTE}) resolution (?P<res>\d{{1,4}} \(\d{{4}}\))\.?")
VOTE_EVIDENCE = re.compile(
    rf"(?P<actor>{ACTOR}) (?P<force>{VOTE}) resolution (?P<res>\d{{1,4}} \(\d{{4}}\))"
    r"(?: while describing [^.!?;:\n]+ work as important and necessary)?\."
)


def evidence_sentence(source, witness):
    """Only use unique literal witnesses beginning the card's lead statement."""
    if not witness or not source.startswith(witness) or source.count(witness) != 1:
        return None
    # If the model excerpted the beginning, keep the rest of that sentence.
    # Disallow extra sentences inside the witness so its frame is unambiguous.
    sentence, separator, _ = source.partition(".")
    text = sentence + separator
    return text if separator and text.startswith(witness) else None


def inspect(assertion, witness, source):
    """Return a scoped decision or None when the input falls outside the grammar."""
    quoted = evidence_sentence(source, witness)
    if quoted is None:
        return None
    for claim_grammar, source_grammar, feature in (
        (COVERAGE_CLAIM, COVERAGE_EVIDENCE, "coverage"),
        (VOTE_CLAIM, VOTE_EVIDENCE, "vote"),
    ):
        claim = claim_grammar.fullmatch(assertion)
        record = source_grammar.fullmatch(quoted)
        if claim is None or record is None or claim["actor"] != record["actor"]:
            continue
        key = "topic" if feature == "coverage" else "res"
        # The witness has to reach the object of the act. The remaining
        # sentence is still checked in full for scope and qualifiers.
        if claim[key] != record[key] or record.end(key) > len(witness):
            continue
        if feature == "coverage":
            possible = sorted(COVERAGE[claim["force"]] & COVERAGE[record["force"]])
        else:
            proposed = claim["force"].replace("favour", "favor")
            recorded = record["force"].replace("favour", "favor")
            possible = [recorded] if proposed == recorded else []
        return {"rule": feature, "decision": OPEN if possible else CONFLICT, "common_states": possible,
                "claim_scope": claim["force"], "record_scope": record["force"], "matched_sentence": quoted}
    return None
