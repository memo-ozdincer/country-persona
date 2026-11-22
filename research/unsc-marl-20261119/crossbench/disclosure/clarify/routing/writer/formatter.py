"""Render a concise decision record using verified public evidence only."""
import json
from instrument import suite


def render(public):
    proof = public["checked_public_evidence"]
    state = proof["state"]
    roles = public["roles"]
    claims = {row["id"]:row for row in public["admitted_disclosures"]}
    title = state
    selected = []
    if state == "AGREEMENT_POSSIBLE":
        option, support = next(iter(proof["verified_options"].items()))
        title += f" {option}"
        spec = next(o for o in public["packages"] if o["id"]==option)
        convener = {"monitoring-team":"Monitoring Team", "erc":"ERC", "committee":"committee"}[spec["convener"]]
        interval = "annually" if spec["interval"] == "annual" else f"every {spec['interval']}"
        evidence = f"Under package {option}, the {convener} would convene, with {spec['public_report']} public reporting {interval}."
        selected = [support[role][0] for role in roles]
    elif state == "IMPASSE":
        blocked = proof["blocked_options"]
        evidence = f"At least one delegate excludes each of the {len(blocked)} offered packages."
        # Prefer scoped exclusions as the examples explaining this proof.
        for role in roles:
            ids = [ref for by_role in blocked.values() for ref in by_role.get(role, [])]
            selected.append(ids[-1] if ids else next(k for k,c in claims.items() if c["role"]==role))
    else:
        assert state == "UNRESOLVED"
        notes = []
        for option in proof["unresolved_options"]:
            missing = [r.split(" workshop")[0] for r in roles if not any(
                c["role"]==r and option in c["accepts"]+c["excludes"] for c in claims.values())]
            notes.append(f"Package {option} lacks a disclosure from {' and '.join(missing)}.")
        evidence = " ".join(notes)
        for role in roles:
            ids = [k for k,c in claims.items() if c["role"]==role and
                   any(o in proof["unresolved_options"] for o in c["accepts"])]
            selected.append(ids[-1] if ids else next(k for k,c in claims.items() if c["role"]==role))
    signed = []
    for role, ref in zip(roles,selected,strict=True):
        c = claims[ref]
        sign, option = next((f, items[0]) for f,items in (("accepts",c["accepts"]),("excludes",c["excludes"])) if items)
        signed.append(f"{role.split(' workshop')[0]} {sign} {option} ({ref})")
    official = " ".join(row["fact"] for row in public["history"] if row["id"] in ("roll","india"))
    assert official.startswith("The Council adopted the draft")
    draft = public["historical_instrument"]["draft"]
    official = official.replace("the draft", f"draft {draft}", 1)
    body = (f"History: {official}", f"Workshop: {title}", f"Evidence: {evidence}",
            "Positions: " + ". ".join(signed) + ".",
            "Authority: These are fictional proposals. They do not amend resolution 2664 or record a new national decision.")
    return "\n".join(body)


if __name__=="__main__":
    print(json.dumps([{"id":row["id"],"output":render(json.loads(row["messages"][1]["content"]))}
                      for row in suite()],indent=2,ensure_ascii=False))
