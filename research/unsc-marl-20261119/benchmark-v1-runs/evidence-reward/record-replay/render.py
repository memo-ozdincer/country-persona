"""Render a final from signed evidence and explicitly mark inferred mandates."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import environment as env

BASE = env.CHAIR
e = env.E


def final(packet, signs, full):
    menu = packet["options"]
    amended = list(signs)
    roles = dict(zip(env.ROLES, packet["roles"], strict=True))
    for role, req in full.items():
        chosen = env.options(menu, req)
        amended.append({"id": f"complete:{role}", "role": role, "accepts": sorted(chosen),
                        "excludes": sorted(set("ABCD") - chosen)})
    state = env.state(menu, amended)
    decision = {"I": "IMPASSE", "U": "UNRESOLVED"}.get(state["decision"], state["decision"])
    _, history, _, scope = BASE.render(packet, [])["text"].split("\n\n")
    if decision == "UNRESOLVED":
        workshop = "The signed workshop record does not certify a compatible package or an impasse."
    else:
        statements = []
        for role, name in roles.items():
            short_name = name.removesuffix(" workshop delegate")
            if len(state["candidates"][role]) > 1:
                statements.append(f"{short_name}'s workshop mandate remains ambiguous.")
            else:
                field, value = state["candidates"][role][0]
                source = "disclosed" if role in full else "inferred"
                statements.append(f"{short_name} ({source} workshop mandate): {BASE.VALUE_LABELS[value]}.")
        if decision == "IMPASSE":
            proposal = "The signed exclusions rule out every package."
            if state["known"] == 2:
                fields = {x[0][0] for x in state["candidates"].values()}
                spare = [label for field, label in BASE.FIELD_LABELS.items()
                         if field in menu[0] and field not in fields]
                if spare:
                    proposal += f" Changing {' or '.join(spare)} cannot resolve the conflict."
        else:
            proposal = next(p["text"] for p in menu if p["id"] == decision)
            if "both access modalities" in proposal:
                public_menu = next(b["text"] for b in packet["public"] if b["id"] == "menu")
                access = "cross-border and cross-line channels"
                assert access in public_menu
                proposal = proposal.replace("both access modalities", access)
            proposal = f"Package {decision} is compatible under the signed workshop proof. {proposal}"
        workshop = f"{' '.join(statements)} {proposal}"
    answer = f"Decision: {decision}\n\n{history}\n\nFictional workshop. {workshop}\n\n{scope}"
    assert len(answer.split()) <= packet["word_cap"]
    return {"text": answer, "decision": decision, "known": state["known"],
            "signed_evidence": amended, "full_declarations": sorted(full)}
