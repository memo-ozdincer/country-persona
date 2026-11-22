"""Review the exact selected sentences for standalone semantic sufficiency."""
import json

from indexed_study import HERE, read

APPROVED = {
    "reform/uk-explanation": "The sentence identifies the timing objection for the resolution under discussion.",
    "reform/uk-negotiations": "The letter's preceding view names the draft, and this sentence states that its negotiations received inadequate time.",
    "afghanistan/russia-full": "The range states the envoy appointment and makes agreement a condition for the speaker's own support.",
}

REJECTED = {
    "afghanistan/russia-consultation-only": "The range discusses consultation and consideration of views. It does not require agreement for support.",
    "afghanistan/china-full": "The source asks for communication, respect for views, and consultations. It includes no condition about China withholding its support.",
    "afghanistan/russia-agreement-deletion": "This is the same consultation language as the clipped control. The agreement condition was removed.",
}


def marks():
    archived = read(HERE / "verified.json")["cases"]
    assert {key for key, row in archived.items() if row["span"]} == set(APPROVED) | set(REJECTED)
    output = {}
    for key, row in archived.items():
        if key in APPROVED:
            reason = APPROVED[key]
        elif key in REJECTED:
            reason = REJECTED[key]
        elif row["id_reply"]["text"] != "NONE":
            reason = "The selected range fails the 100-word mechanical limit."
        else:
            reason = "The selector does not submit a witness."
        output[key] = {"sufficient": key in APPROVED,
                       "witness": row["span"]["text"] if key in APPROVED else "", "reason": reason}
    return output


if __name__ == "__main__":
    print(json.dumps(marks(), indent=2, ensure_ascii=False))
