"""Render selected claims exactly, with public authority and provenance kept separate."""
import json

from run_transfer import PACKET, variants, read


def records():
    packet = read(PACKET)
    result = {}
    for receipt in (3, 7):
        selected = variants(packet, receipt, 70)["selected"]
        body = "\n".join(f"{group['desk']}: " + " ".join(group["statements"]) for group in selected["evidence"])
        assert len(body.split()) == selected["words"] <= 70
        result[f"{receipt}/selected"] = {"body": body, "record": packet["public"] + "\n\n" + body,
                                          "words": selected["words"], "points": selected["points"],
                                          "retained_cited_claims": selected["ids"],
                                          "construction": "Literal concatenation of source-reviewed curator paraphrases."}
    return result


if __name__ == "__main__":
    print(json.dumps(records(),ensure_ascii=False,indent=2))
