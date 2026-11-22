"""Build matched consistent and contradictory endorsements with visible proof."""
import json

from fit_balanced import E, fit

env = fit.env
HERE = env.HERE / "calibration"


def compatible(menu, ids, local):
    def matches(choice):
        _, text = choice.split(": ", 1)
        fields = dict(piece.split(" is ", 1) for piece in text.split("; "))
        return all(fields.get(k) == v for k, v in local.items())
    return [label for label, choice in zip(ids, menu, strict=True) if matches(choice)]


def run():
    main = E.read(env.HERE / "roster.json")
    out = {}
    for split in ("train", "held"):
        pairs = []
        for original in main[split]:
            speaker = json.loads(original["responder"][1]["content"])
            prompt = original["chair"][0]
            public = json.loads(prompt[1]["content"])
            ids = list(env.DECISIONS[:4])
            if split == "train":
                valid = compatible(public["menu"], ids, speaker["own_requirement"])
            else:
                case = E.cases()[original["id"].split("/")[0]]
                valid = sorted(env.allowed(case["options"], speaker["own_requirement"]))
            invalid = [label for label in ids if label not in valid]
            assert valid and invalid
            offset = len(pairs) // 2
            for kind, package, target in (
                ("consistent", valid[offset % len(valid)], original["gold"]),
                ("contradictory", invalid[offset % len(invalid)], ["U"]),
            ):
                payload = public | {"public_notes": [
                    public["public_notes"][0],
                    public["public_notes"][1] + f" One option I could accept is {package}."
                ]}
                pairs.append({"id": original["id"] + "/" + kind, "kind": kind, "endorsed": package,
                              "supported": target, "messages": [prompt[0], prompt[1] | {
                                  "content": json.dumps(payload, ensure_ascii=False)}]})
        out[split] = pairs
        assert len(pairs) == 2 * len(main[split])
    return out


if __name__ == "__main__":
    E.emit(run())
