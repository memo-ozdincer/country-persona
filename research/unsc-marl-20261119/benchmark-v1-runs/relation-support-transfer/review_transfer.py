"""Collect native relation-support logits on two source-contrast dockets."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
OLDER = RUNS / "afghanistan-2721-source-contrast/bound-review/review.py"
REPORT = RUNS / "reporting-2739"
HUMAN = RUNS / "humanitarian-2664-admission"
CASES = {"2739": REPORT / "docket.json", "2664": HUMAN / "case.json"}


def load(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior = load("prior_bound_relation_judge", OLDER)
runtime = prior.runtime
SYSTEM = (
    "Decide whether the candidate comparison is fully supported by the delivered evidence. "
    "Check the attribution of every stated reason and the exact scope of any agreement, "
    "objection, vote, or adopted requirement. Reasons for voting and reasons for supporting "
    "a particular mechanism can be different. A common purpose can be expressed in different "
    "words, but every actor named must have a source for that purpose. A procedural outcome "
    "does not establish a delegation's stated reason. Missing evidence or any overstatement "
    "means unsupported. Return only the letter of the decision."
)


def read(path):
    return json.loads(path.read_text())


def cards(docket):
    case = read(CASES[docket])
    rows = case["evidence"] if docket == "2664" else [
        *case["public"], *(card for desk in case["owned"] for card in desk)
    ]
    return {row["id"]: row["text"] for row in rows}


def probes():
    rows = read(HERE / "probes.json")
    assert len(rows) == 10 and len({row["id"] for row in rows}) == 10
    return rows


def requests():
    output = []
    for row in probes():
        evidence = cards(row["docket"])
        for order, labels in prior.LABELS.items():
            payload = {
                "delivered": [{"id": key, "text": evidence[key]} for key in row["cards"]],
                "candidate_comparison": row["claim"], "responses": labels,
            }
            output.append({
                "id": f"{row['id']}/{order}", "max_output_tokens": 2, "messages": [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            })
    return output


def plan():
    files = (Path(__file__), HERE / "protocol.md", HERE / "probes.json", *CASES.values(),
             REPORT / "anchor.json", REPORT / "source-preserving-transfer/scores.json",
             HUMAN / "anchors.json", HUMAN / "source-preserving/scores.json",
             OLDER, Path(runtime.__file__), Path(runtime.base.__file__), runtime.prior.RELEASE / "release.json")
    return {"requests": requests(),
            "checkpoint_index_sha256": prior.fixture.pin(runtime.base.MODEL / "model.safetensors.index.json"),
            "sha256": {str(p.relative_to(RUNS.parent)): prior.fixture.pin(p) for p in files}}


def act(mode):
    data = plan()
    if mode == "plan":
        return data
    assert data == read(HERE / "plan.json")
    with patch.object(runtime, "plan", return_value=data), patch.object(runtime, "HERE", HERE), patch.object(
        runtime, "OUT", HERE / "evidence"
    ), patch.object(runtime, "CASE", {"id": "2739-and-2664-relation-support"}):
        if mode == "run":
            runtime.run()
        else:
            verified = runtime.verify()
            launch = read(HERE / "evidence/launch.json")
            assert launch["checkpoint_index_sha256"] == data["checkpoint_index_sha256"]
            assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
            assert set(verified["outputs"]) == {row["id"] for row in data["requests"]}
            return verified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    output = act(mode)
    if mode != "run":
        print(json.dumps(output, ensure_ascii=False, indent=2))
