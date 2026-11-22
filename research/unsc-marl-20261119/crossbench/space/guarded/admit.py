"""Admit only owner-bound, independently verified claims to the public ledger."""


def admit_masks(accept, exclude, approved_accept, approved_exclude, *, atomic=False):
    """Return admitted masks and withheld package IDs, represented as one bitset."""
    ambiguous = (accept & exclude) | (approved_accept & approved_exclude)
    yes = accept & approved_accept & ~ambiguous
    no = exclude & approved_exclude & ~ambiguous
    withheld = (accept & ~yes) | (exclude & ~no)
    if atomic and withheld:
        return 0, 0, accept | exclude
    return yes, no, withheld


def submit(envelope, *, actor, receipt, labels, atomic=False):
    """Convert a role-local evidence receipt into a public claim and an audit record."""
    if not isinstance(envelope, dict) or set(envelope) != {"id", "role", "accepts", "excludes"}:
        raise ValueError("Expected an explicit claim envelope")
    id_ = envelope["id"]
    if not isinstance(id_, str) or not id_.strip() or envelope["role"] != actor or receipt["role"] != actor:
        raise ValueError("Claim identity does not match the verified sender")
    labels = tuple(labels)
    if len(set(labels)) != len(labels):
        raise ValueError("Duplicate package identifiers")
    indexes = {name: 1 << slot for slot, name in enumerate(labels)}

    def mask(items):
        if not isinstance(items, list) or any(not isinstance(x, str) or x not in indexes for x in items):
            raise ValueError("Expected a list of known package identifiers")
        if len(set(items)) != len(items):
            raise ValueError("Duplicate identifiers in a sign list")
        return sum(indexes[k] for k in items)

    def names(bits):
        return [k for k in labels if bits & indexes[k]]

    yes, no, rejected = admit_masks(
        mask(envelope["accepts"]), mask(envelope["excludes"]),
        mask(receipt["accepts"]), mask(receipt["excludes"]), atomic=atomic,
    )
    accepted = {"id": id_, "role": actor, "accepts": names(yes), "excludes": names(no)}
    return accepted, {"id": id_, "role": actor, "withheld": names(rejected)}
