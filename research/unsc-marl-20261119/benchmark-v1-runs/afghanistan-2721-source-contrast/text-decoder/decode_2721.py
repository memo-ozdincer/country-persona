"""Collect or verify label-reversed native source choices on Resolution 2721."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = PARENT.parent
fixture_spec = spec_from_file_location("afghanistan_exact_replay", PARENT/"replay.py")
fixture = module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(fixture)

spec = spec_from_file_location("native_choice_runtime_2721",
                              RUNS/"reform-2553-transfer/native-decisions/live_choices.py")
runtime = module_from_spec(spec)
spec.loader.exec_module(runtime)

SYSTEM = (
    "You are checking evidence for a factual decision record. You may forward one "
    "of the two clauses from the adopted text. If an earlier explanation arrived, "
    "choose the clause that lets the chair substantiate the most specific comparison "
    "between that explanation and the adopted text. Keep a national position distinct "
    "from a decision of the Council. Use the delivered explanation to choose. Treat "
    "the separate background reminder, if present, only as orientation. If the relay "
    "did not supply an explanation, select a clause without assuming its content. "
    "Return only the letter of the selected clause."
)

INDIRECT = (
    "The speaker said it would back the naming of the new official only if the people "
    "currently exercising authority in Afghanistan agreed. It also expected the "
    "appointing official to hear those authorities and take account of the Council membership.",
    "The speaker saw a potential supporting role for the additional representative "
    "alongside the existing United Nations field operation in Afghanistan.",
)
BLIND = (
    "The speaker expected the de facto authorities to be consulted and all Council "
    "members’ views taken into account. The speaker would withhold support for the "
    "envoy appointment without agreement from the de facto authorities.",
    "The speaker described a Special Envoy as a potential complement to UNAMA’s work.",
)
BACKGROUND = (
    "The decision also preserves the mandate and work of UNAMA and the Special Representative.",
    "The decision also requests consultation with Afghan authorities, women and civil society.",
)
MODES = ("attributed", "anonymous", "indirect", "distractor")
MAPPINGS = {"ab":(0,1),"ba":(1,0)}


def requests():
    contents = tuple(row["text"] for row in fixture.CASE["early_statements"])
    cases = []
    for mode, truth in product(MODES, range(2)):
        observation = {"relay":"Earlier explanation arrived.", "explanation":{
            "attributed":contents,"anonymous":BLIND,"indirect":INDIRECT,"distractor":INDIRECT,
        }[mode][truth]}
        if mode == "distractor":
            observation["separate_background_reminder"] = BACKGROUND[truth]
        cases.append((mode,truth,observation))
    cases.extend((
        ("arrival_only",None,{"relay":"Earlier explanation arrived. Content is withheld."}),
        ("no_receipt",None,{"relay":"No earlier explanation arrived."}),
    ))
    result = []
    for mode,truth,observation in cases:
        for label,mapping in MAPPINGS.items():
            data = {"task":"Select one adopted-text clause for the Resolution 2721 decision record.",
                    "observation":observation,
                    "choices":{letter:fixture.CASE["late_clauses"][index]["text"]
                               for letter,index in zip(("A","B"),mapping,strict=True)}}
            result.append({"id":f"{mode}/{truth}/{label}","max_output_tokens":2, "messages":[
                {"role":"system","content":SYSTEM},
                {"role":"user","content":json.dumps(data,ensure_ascii=False)},
            ]})
    return result


def plan():
    paths = (Path(__file__),HERE/"protocol.md",PARENT/"case.json",PARENT/"results.json",
             PARENT/"plan.json",Path(runtime.__file__),Path(runtime.base.__file__),
             runtime.prior.RELEASE/"release.json")
    return {"requests":requests(),
            "checkpoint_index_sha256":fixture.pin(runtime.base.MODEL/"model.safetensors.index.json"),
            "sha256":{str(p.relative_to(RUNS.parent)):fixture.pin(p) for p in paths}}


def act(mode):
    lock = plan()
    assert lock == json.loads((HERE/"plan.json").read_text())
    with patch.object(runtime,"plan",return_value=lock), patch.object(runtime,"HERE",HERE), patch.object(
        runtime,"OUT",HERE/"evidence"
    ), patch.object(runtime,"CASE",fixture.CASE):
        if mode == "run":
            runtime.run()
        else:
            verified = runtime.verify()
            launch = json.loads((HERE/"evidence/launch.json").read_text())
            assert launch["checkpoint_index_sha256"] == lock["checkpoint_index_sha256"]
            assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
            print(json.dumps(verified,ensure_ascii=False,indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run","verify"))
    mode = parser.parse_args().mode
    if mode == "plan":
        print(json.dumps(plan(),ensure_ascii=False,indent=2))
    else:
        act(mode)
