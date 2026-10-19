"""One scope/partial-state target, with five previous targets preserved verbatim."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / "research/native-application-writer-20261019-v1"
REVERSE = ROOT / "research/native-reverse-state-control-20261019-v1"
OUT = ROOT / "research/native-scope-partial-writer-20261019-v1"
PARTIAL = ("Hypothetical workshop plan Q funds timely basic-needs aid through specified organizations, ordinary eligibility checks, "
           "a monthly diversion review, and a defined proactive 1267 Monitoring Team liaison. Q contains no standardized diversion-reporting "
           "or risk-prioritized verification/reporting workflow to that Team.")
RULE = ("Preserve Q's funded aid, eligibility checks and monthly review. If a proactive Team liaison already exists, retain it rather than appointing another; "
        "otherwise add one. If standardized diversion reporting and a risk-prioritized verification/reporting workflow are missing, add them alongside delivery; "
        "otherwise retain them. Reporting consumes staff and can slow aid; use proportionate triage without a new per-delivery approval veto. "
        "State recommendations only as workshop analysis, not an observed Indian endorsement of Q or an established future vote. "
        "Write only the application paragraph, not the full source speech.")
TARGET = ("Workshop analysis: Q already funds timely basic-needs aid through specified organizations, eligibility checks, a monthly diversion review "
          "and a proactive 1267 Monitoring Team liaison. Retain those mechanisms. Standardized diversion reporting and a risk-prioritized "
          "verification/reporting workflow are still missing; add them alongside delivery without appointing another liaison. Reporting consumes staff "
          "and can slow aid; proportionate triage preserves access without a new per-delivery veto. These analytical recommendations do not establish "
          "Indian endorsement of Q or an unspecified future text, or any future vote.")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_case(dest, row, rubric, cfg, protocol):
    dest.mkdir(exist_ok=False)
    for name, obj in [("example", row), ("rubric", rubric), ("config", cfg), ("protocol", protocol)]:
        (dest / (name+".json")).write_text(json.dumps(obj, indent=2, ensure_ascii=False)+"\n")
    (dest / "example.txt").write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")


def reverse():
    source = ROOT / "research/native-state-decomposition-20261019-v1/missing-outside"
    row = json.loads((source / "example.json").read_text())
    before = "and their representatives inside Libya. The channel does not cover those groups outside Libya."
    after = "and their representatives outside Libya. The channel does not cover those groups inside Libya."
    assert row["messages"][1]["content"].count(before) == 1
    row["messages"][1]["content"] = row["messages"][1]["content"].replace(before, after)
    row["id"] = "state-9469-BRA-missing-inside"
    rubric = json.loads((source / "rubric.json").read_text())
    old = rubric["units"]["state-9469-BRA-missing-outside"]
    units = dict(old)
    units["A1"] = "Recognize R's funded cooperation/public update and EXISTING protected outside-Libya channel; inside coverage is missing, not outside coverage."
    units["A2"] = "Extend the EXISTING protected channel to the specified inside-Libya groups and request the missing line-by-line four-inquiry detail; preserve outside coverage rather than creating/extending it as if missing."
    rubric["units"] = {row["id"]: units}
    cfg = json.loads((source / "config.json").read_text())
    protocol = json.loads((source / "protocol.json").read_text())
    protocol.update(case_id=row["id"], state="missing-inside", question="Does partial-state behavior transfer when the missing geography is reversed?",
        intervention="Reverse only geographic coverage in the explicit plan: outside service exists, inside service is absent. Sources/map/system/rule unchanged.",
        fresh_control="Freeze and inspect base/native40 before the proposed scope/partial-state fit; no fitting on Brazil/Libya.")
    protocol["unchanged_file_bindings"].update({str((source / "example.json").relative_to(ROOT)): sha(source / "example.json")})
    write_case(REVERSE, row, rubric, cfg, protocol)
    reference = ("Workshop analysis: R already funds Libyan cooperation, a public update and protected two-way outreach for victims, witnesses, affected communities "
                 "and representatives outside Libya; inside coverage is missing. Extend the existing channel to those groups inside Libya and request a line-by-line "
                 "update on all four inquiries. Outreach/reporting needs staff and witness-privacy safeguards; narrower outreach costs less but risks selectivity. "
                 "These recommendations do not establish Brazilian endorsement of R or a future vote.")
    (REVERSE / "feasibility-not-for-model.json").write_text(json.dumps(dict(author="same assistant", not_model_input_or_target=True,
        not_official_quote_or_model_output=True, text=reference, words=len(reference.split())), indent=2)+"\n")
    print(json.dumps(dict(case=row["id"], reference_words=len(reference.split()))))


def training():
    # Freeze only after the fresh reverse-case controls really exist and were read.
    for arm in ["base", "adapter"]:
        review = json.loads((REVERSE / "runtime" / arm / "inspection.json").read_text())
        assert review["complete_outputs_read"] is True
    parent = json.loads((PARENT / "examples.json").read_text())
    fitting = [copy.deepcopy(r) for r in parent if r["split"] == "train"]
    assert len(fitting) == 5
    original = next(r for r in fitting if r["id"] == "application-9214-IND")
    partial = copy.deepcopy(original)
    system = json.loads((REVERSE / "example.json").read_text())["messages"][0]
    context = original["messages"][1]["content"].split("\nHYPOTHETICAL APPLICATION Q\n")[0]
    partial.update(id="partial-9214-IND", target=TARGET, messages=[system, dict(role="user", content=context+
        "\nEXPLICIT HYPOTHETICAL WORKPLAN Q\n"+PARTIAL+"\nCOMMON WORKSHOP DECISION RULE\n"+RULE+"\nREQUESTED ROLE: IND national delegation.")],
        units=dict(A1="Retain funded timely aid, eligibility/monthly review and the existing proactive1267Team liaison; accurately identify missing standard diversion reporting/verification workflow.",
            A2="Keep the existing liaison without appointing another; add ONLY missing standard diversion reporting and staffed risk-prioritized verification/reporting alongside delivery.",
            A3="Reporting needs staff/can slow aid; use proportionate triage without new per-delivery approval veto.",
            A4="Label workshop analysis; Indian endorsement of Q/unspecified future text and any future vote remain unestablished."),
        output_scope="application_only")
    fitting.append(partial)
    for row in fitting[:-1]:
        prior = next(r for r in parent if r["id"] == row["id"])
        assert all(row[k] == prior[k] for k in ["messages", "target", "units"])
        row["output_scope"] = "source_only" if not row["id"].startswith("application-") else "source_and_application"
    evaluations = []
    for row in parent:
        if row["split"] in {"source_eval", "application_eval"}:
            row = copy.deepcopy(row)
            row["split"] = "wps_source" if row["split"] == "source_eval" else "wps_application"
            row["output_scope"] = "source_only" if row["split"] == "wps_source" else "source_and_application"
            evaluations.append(row)
    def add_case(path, split, scope):
        row = json.loads((path / "example.json").read_text());row["split"] = split;row["output_scope"] = scope;evaluations.append(row)
    add_case(ROOT / "research/native-source-control-20261019-v1", "brazil_source", "source_only")
    for name in ["missing-outside", "existing-outside"]:
        add_case(ROOT / "research/native-state-decomposition-20261019-v1" / name, "brazil_state", "application_only")
    add_case(REVERSE, "brazil_state", "application_only")
    full = copy.deepcopy(next(r for r in parent if r["id"] == "application-9469-BRA"))
    full.update(split="brazil_full", output_scope="source_and_application");evaluations.append(full)
    rows = fitting + evaluations
    assert len(rows) == 15 and all(r["target"] is None for r in evaluations)
    cfg = json.loads((PARENT / "config.json").read_text())
    cfg.update(updates=48, case_countries={r["id"]: r["country"] for r in rows}, fitting_ids=[r["id"] for r in fitting],
               cumulative_updates_before=4134, evaluation_stages=["fitting", "wps_source", "wps_application", "brazil_source", "brazil_state", "brazil_full"])
    rubric = json.loads((PARENT / "rubric.json").read_text())
    rubric["units"] = {r["id"]: r["units"] for r in rows}
    for name, path in [("missing-outside", ROOT / "research/native-state-decomposition-20261019-v1/missing-outside"),
                       ("existing-outside", ROOT / "research/native-state-decomposition-20261019-v1/existing-outside"),
                       ("missing-inside", REVERSE)]:
        rubric["units"].update(json.loads((path / "rubric.json").read_text())["units"])
    rubric["source_map_units"] = {r["id"]: r.get("source_map_units", {}) for r in rows if r.get("source_map_units")}
    rubric["scope_contract"] = "Besides the frozen material/six-guard rubric, record requested output scope. Full contract passes only if rubric strict AND scope correct. Application-only outputs must not prepend the full source statement."
    comparators = []
    def comparator(name, folder, actual, launch, decoder):
        comparators.append(dict(name=name, responses=str((folder / "responses.jsonl").relative_to(ROOT)),
            inspection=str((folder / "inspection.json").relative_to(ROOT)), actual_inputs=str(actual.relative_to(ROOT)),
            launch=str(launch.relative_to(ROOT)), decoder=str(decoder.relative_to(ROOT))))
    prior = ROOT / "research/native-plan-writer-20261019-v1/runtime-initial"
    comparator("base-wps-source", prior / "base-source", prior / "actual-inputs-and-masks.json", prior / "launch.json", prior / "decoder.json")
    current = PARENT / "runtime"
    comparator("native40-wps-source", current / "adapter-source", current / "actual-inputs-and-masks.json", current / "launch.json", current / "decoder.json")
    appbase = ROOT / "research/native-plan-writer-application-20261019-v1/runtime"
    comparator("base-wps-application", appbase / "base", appbase / "actual-inputs.json", appbase / "launch.json", appbase / "decoder.json")
    comparator("native40-wps-application", current / "adapter-application", current / "actual-inputs-and-masks.json", current / "launch.json", current / "decoder.json")
    for arm, stage in [("base", "base-new"), ("native40", "adapter-new")]:
        comparator(arm+"-brazil-full", current / stage, current / "actual-inputs-and-masks.json", current / "launch.json", current / "decoder.json")
    for name, path in [("brazil-source", ROOT / "research/native-source-control-20261019-v1/runtime"),
                       ("missing-outside", ROOT / "research/native-state-decomposition-20261019-v1/missing-outside/runtime"),
                       ("existing-outside", ROOT / "research/native-state-decomposition-20261019-v1/existing-outside/runtime"),
                       ("missing-inside", REVERSE / "runtime")]:
        for arm in ["base", "adapter"]:
            comparator(("native40" if arm == "adapter" else arm)+"-"+name, path / arm, path / "actual-input.json", path / "launch.json", path / "decoder.json")
    bindings = {str((PARENT / "examples.json").relative_to(ROOT)): sha(PARENT / "examples.json")}
    for spec in comparators:
        for key in ["responses", "inspection", "actual_inputs", "launch", "decoder"]:
            bindings[spec[key]] = sha(ROOT / spec[key])
    OUT.mkdir(exist_ok=False)
    for name, value in [("examples", rows), ("rubric", rubric), ("config", cfg), ("comparators", comparators)]:
        (OUT / (name+".json")).write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n")
    protocol = dict(question="Does ONE application-only partial-mechanism example teach scope and remaining-gap repair across source family, while five full-source targets are retained?",
        manipulation="Five old messages/targets/units byte-identical; add one India partial-Q target. Same8presentations, fresh48updates; data/scope/state/dose/order change together, not an isolated causal factor.",
        old_fitting_examples=5, new_fitting_examples=1, new_target_words=len(TARGET.split()), fitting_updates=48,
        source_grounding="New row reuses exactly the complete source/map/procedure prefix of application-9214-IND; Q is an explicitly fictional implementation plan. No Brazil/Libya/WPS target is fitted.",
        changed_supervision="Only application paragraph required on new row; liaison exists, standard reporting missing. Conditional rule supplied, so this is source-bound scope/state compliance, not hidden national utility discovery.",
        unchanged_file_bindings=bindings, independent_review_complete=False,
        scope="Adaptive historically exposed development, exact-input base/native40 controls and fresh reversed-geography fixture frozen/inspected before fitting. No independent, sealedOOD, forecast, persona or collective claim.",
        launch_sequence="Inspect all reverse controls and preflight. One explicit fresh fit. Inspect fitting, WPS source, WPS application, Brazil source, three state answers and original full Brazil in separate operations.",
        old_seed_control="preserved/unrun", no_next_fit_or_sweep=True)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2)+"\n")
    for r in rows:
        (OUT / (r["id"]+".txt")).write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in r["messages"])+
            ("\n\nTRAINING TARGET\n"+r["target"] if r["target"] else "\n\nNO FITTING TARGET")+"\n")
    print(json.dumps(dict(fitting_examples=6, eval_examples=9, updates=48, new_target_words=len(TARGET.split()))))


if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("kind", choices=["reverse", "training"])
    args=p.parse_args();reverse() if args.kind=="reverse" else training()
