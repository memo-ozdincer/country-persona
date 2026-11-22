"""Project public, role-private and reviewer views of one UN workshop."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def inputs():
    source = HERE / "workshops.json"
    refs = json.loads((HERE / "references.json").read_text())
    if hashlib.sha256(source.read_bytes()).hexdigest() != refs["workshop_file_sha256"]:
        raise ValueError("The audited workshop source changed")
    return json.loads(source.read_text()), refs


def private_card(role, conditions):
    return {"role": role, "kind": "fictional private workshop instructions", "conditions": conditions}


def packet(item, variant, boundary, view):
    public = {
        "scope": boundary,
        "historical_context": {"draft": item["draft"], "meeting": item["meeting"], "date": item["date"]},
        "evidence": item["public_evidence"],
        "role_names": item["roles"],
        "fictional_packages": item["packages"],
    }
    cards = [private_card(role, requirements)
             for role, requirements in zip(item["roles"], variant["private_conditions"], strict=True)]
    if view in {"role-1", "role-2"}:
        return {
            **public, "private_instruction": cards[int(view[-1]) - 1],
            "task": "State your own workshop position and why. Mark every compatible proposal as hypothetical. Do not infer the other role's private requirements.",
        }
    if view == "writer":
        return {
            **public,
            "task": "Write the final decision record from the supplied conversation. Identify the historical decision, substantive proposal or evidenced impasse, role positions, outstanding conditions and authority boundaries. An unresolved proposal is distinct from a verified impasse.",
        }
    if view == "analyst":
        return {
            **packet(item, variant, boundary, "writer"),
            "private_instructions_disclosed_for_full_information_control": cards,
        }
    if view == "judge":
        return {
            "mode": "FINAL",
            "task": packet(item, variant, boundary, "writer")["task"],
            "evidence": [{"id": r["id"], "text": r["text"], "source": r["source"], "location": r["location"]}
                         for r in item["public_evidence"]] + [
                {"id": f"workshop-card-{i}", "text": json.dumps(card, ensure_ascii=False)}
                for i, card in enumerate(cards, start=1)
            ] + [{
                "id": "workshop-packages",
                "text": json.dumps(item["packages"], ensure_ascii=False),
            }],
            "rubric": [{"id": k, "category": "final", "weight": 14, "rule": v}
                       for k, v in item["required_content"].items()],
        }
    raise ValueError(f"Unknown view: {view}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("family")
    parser.add_argument("variant")
    parser.add_argument("view", choices=("role-1", "role-2", "writer", "analyst", "judge"))
    args = parser.parse_args()
    data, _ = inputs()
    family = next(r for r in data["families"] if r["id"] == args.family)
    variant = next(r for r in family["variants"] if r["id"] == args.variant)
    print(json.dumps(packet(family, variant, data["boundary"], args.view), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
