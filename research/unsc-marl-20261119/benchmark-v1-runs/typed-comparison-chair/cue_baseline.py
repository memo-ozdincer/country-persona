"""Test two lexical shortcuts on the locked native relation fixtures."""
import json
from collect_typed import HERE, prior


def run():
    rows = {}
    for key, fixture in prior.read(HERE / "plan.json")["fixtures"].items():
        early = fixture["packet"]["delegate_statement"].casefold()
        late = fixture["packet"]["adopted_provision"].casefold()
        if "support" in early and "agreement" in early and "appointment terms" in late:
            topic = "conditions"
        elif "unama" in early and "unama" in late:
            topic = "mandates"
        else:
            topic = "none"
        if "withhold support" in early and "no consent requirement" in late:
            phrase = "conditions"
        elif "complement to unama" in early and "preserving the mandate and work of unama" in late:
            phrase = "mandates"
        else:
            phrase = "none"
        rows[key] = {"expected": fixture["expected"], "primary": "changed_from" not in fixture,
                     "topic_word_match": topic, "phrase_match": phrase}
    return {"rows": rows, "correct_of_four": {
        rule: {name: sum(x[rule] == x["expected"] for x in rows.values() if x["primary"] == primary)
               for name, primary in (("canonical", True), ("counterfactual", False))}
        for rule in ("topic_word_match", "phrase_match")
    }}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
