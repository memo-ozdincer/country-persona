"""Build a workshop final record from public blocks and complete declarations."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "crossbench"))
from decision_ledger import readout

FIELD_LABELS = {
    "term": "mandate term",
    "documentation": "consultation documentation",
    "duration": "duration",
    "checkpoint": "review checkpoint",
}
VALUE_LABELS = {
    "retain": "retain the adopted term",
    "shorten": "shorten the term",
    "public": "public summary without a confidential annex",
    "annex": "public summary with a confidential annex",
    "nine": "nine months",
    "six": "six months",
    "ordinary": "ordinary reporting",
    "additional": "an extra formal review checkpoint",
}


def project(case):
    return {key: case[key] for key in ("roles", "public", "options", "word_cap")}


def allowed(menu, requirement):
    if (not isinstance(requirement, dict) or len(requirement) != 1
            or not all(k in FIELD_LABELS and isinstance(v, str) and v in VALUE_LABELS
                       for k, v in requirement.items())):
        raise ValueError("Expected exactly one registered requirement")
    compatible = [row["id"] for row in menu if all(row.get(k) == v for k, v in requirement.items())]
    if not compatible:
        raise ValueError("Requirement is absent from the published menu")
    return compatible


def filter_local(menu, declaration, local_requirement):
    """Called by the delivering role's gate, before sending to the public chair."""
    allowed(menu, declaration["requirement"])
    return declaration["requirement"] == local_requirement


def render(packet, declarations):
    if set(packet) != {"roles", "public", "options", "word_cap"}:
        raise ValueError("The chair accepts a public projection")
    public = {block["id"]: block for block in packet["public"]}
    roles = packet["roles"]
    menu = packet["options"]
    options = [p["id"] for p in menu]
    by_option = {p["id"]: p for p in menu}
    if public["menu"]["text"] != "\n".join(f"{p['id']}: {p['text']}" for p in menu):
        raise ValueError("Structured menu and the public text differ")
    log = []
    requirements = []
    for item in declarations:
        claim = item["requirement"]
        accepts = allowed(menu, claim)
        log.append({"id": item["id"], "role": item["role"], "accepts": accepts,
                    "excludes": [o for o in options if o not in accepts]})
        requirements.append((item["role"], *next(iter(claim.items()))))
    proof = readout(options, roles, log)
    if proof["state"] == "IMPASSE":
        choice = "IMPASSE"
    elif proof.get("verified_options"):
        choice = next(o for o in options if o in proof["verified_options"])
    else:
        choice = "UNRESOLVED"

    # Documentary and fictional text are assembled from separate records.
    official = [block for block in packet["public"] if block.get("source")]
    if not official:
        raise ValueError("A sourced historical record is required")
    history = " ".join(block["text"] for block in official)
    scope = "A workshop proposal or impasse establishes no official vote, authority or commitment."
    if "term" in menu[0]:
        scope += " A change to the adopted mandate term would require Council authorization."
    citations = {"history": [b["id"] for b in official], "mandates": [r["id"] for r in log],
                 "workshop": ["menu"], "authority": ["scope"]}
    parts = [f"Decision: {choice}", f"Historical record. {history}"]
    if choice == "UNRESOLVED":
        state_message = ("The workshop declarations conflict." if proof["state"] == "CONTRADICTORY_DISCLOSURE"
                         else "The received declarations do not establish a jointly acceptable package or an impasse.")
        parts.extend([f"Fictional workshop. {state_message}", scope])
    else:
        attributed = " ".join(
            f"The {role} requires {FIELD_LABELS[field]}: {VALUE_LABELS[value]}."
            for role, field, value in sorted(set(requirements))
        )
        if choice == "IMPASSE":
            binding = {field for _, field, _ in requirements}
            fields = [label for field, label in FIELD_LABELS.items() if field in menu[0] and field not in binding]
            alternative = f" Changing {' or '.join(fields)} cannot reconcile these requirements." if fields else ""
            decision = "No menu option satisfies both requirements." + alternative
        else:
            proposal = by_option[choice]["text"]
            access = "cross-border and cross-line channels"
            if "both access modalities" in proposal and access in public["menu"]["text"]:
                proposal = proposal.replace("both access modalities", access)
            decision = f"Package {choice} is a workshop proposal acceptable to both roles. {proposal}"
        parts.extend([f"Fictional workshop. {attributed} {decision}", scope])
    text = "\n\n".join(parts)
    if len(text.split()) > packet["word_cap"]:
        raise ValueError("Record exceeds the case word cap")
    return {"decision": choice, "proof": proof, "citations": citations, "text": text}
