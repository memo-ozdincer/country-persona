"""Bind mutually exclusive roll-call acts to one actor and resolution."""
import re

ACTS = {
    "voted in favour of": "yes", "voted in favor of": "yes", "voted against": "no",
    "abstained on": "abstained", "recorded an abstention on": "abstained",
    "did not participate in the vote on": "nonparticipating",
}
VERBS = "|".join(sorted(map(re.escape, ACTS), key=len, reverse=True))
VOTE = re.compile(rf"(?P<actor>[A-Z][A-Za-z .'-]+?) (?P<act>{VERBS}) resolution (?P<id>\d{{1,4}} \(\d{{4}}\))\.")


def typed_vote(text):
    match = VOTE.fullmatch(text)
    return (match["actor"], match["id"], ACTS[match["act"]]) if match else None


def check(assertion, cited_words, official_card):
    """Return a relation only for a unique quote and the same roll-call target."""
    if not cited_words or official_card.count(cited_words) != 1:
        return None
    if cited_words not in re.split(r"(?<=\.)\s+", official_card):
        return None
    query, witness = typed_vote(assertion), typed_vote(cited_words)
    if query is None or witness is None or query[:2] != witness[:2]:
        return None
    return "open" if query[2] == witness[2] else "conflict"


def tests():
    reference = "Algeria did not participate in the vote on resolution 2797 (2025)."
    card = reference + " It commented on decolonization."
    outcome = {
        reference: "open",
        "Algeria recorded an abstention on resolution 2797 (2025).": "conflict",
        "Pakistan recorded an abstention on resolution 2797 (2025).": None,
        "Algeria recorded an abstention on resolution 2767 (2024).": None,
        "Algeria objected to the draft.": None,
    }
    for claim, expected in outcome.items():
        assert check(claim, reference, card) == expected
    claim = "Algeria recorded an abstention on resolution 2797 (2025)."
    assert check(claim, reference, f"{card} {reference}") is None
    assert check(claim, reference, "A hypothetical reading says " + reference) is None
    assert check(claim, reference, "Someone quoted “" + reference + "”") is None
    assert check(claim, reference, "The workshop is over. " + reference) == "conflict"
