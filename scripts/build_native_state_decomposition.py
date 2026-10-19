"""Freeze an application-only paired state control, with no ambiguous inside coverage."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/native-state-decomposition-20261019-v1"
RULE = ("Apply Brazil's supplied positions to R using this workshop decision rule. Preserve features already present. "
        "Extend a missing geographic coverage area; if both areas are covered, keep the channel and do not recommend creating or extending it. "
        "In either case request the missing line-by-line inquiry detail. Explain staffing and witness-privacy costs of the resulting outreach/reporting "
        "versus cheaper narrower outreach and its selectivity risk. Distinguish a recommendation for this exercise from an observed Brazilian endorsement "
        "of R or an established future vote. Write only the application paragraph; do not repeat the full source statement.")
COMMON = ("For this workshop exercise, R already funds cooperation with Libyan authorities, a generic public progress update, "
          "and a protected two-way outreach channel for victims, witnesses, affected communities and their representatives inside Libya. ")
TAIL = " R requests no line-by-line progress detail on the four key lines of inquiry."
STATES = {
    "missing-outside": "The channel does not cover those groups outside Libya.",
    "existing-outside": "The channel also covers those groups outside Libya.",
}
REFS = {
    "missing-outside": "Workshop analysis: R already funds Libyan cooperation, a public update and protected two-way outreach inside Libya; outside coverage is missing. Extend that existing channel to victims, witnesses, affected communities and representatives outside Libya, and request a line-by-line update on all four inquiries. Outreach and reporting need staff and witness-privacy safeguards; narrower outreach costs less but risks selectivity. This recommendation is not recorded Brazilian endorsement of R or an established future vote.",
    "existing-outside": "Workshop analysis: R already funds Libyan cooperation, a public update and protected two-way outreach for victims, witnesses, affected communities and representatives inside and outside Libya. Retain that channel; request the missing line-by-line update on all four inquiries. Maintaining outreach and reporting needs staff and witness-privacy safeguards; narrower outreach costs less but risks selectivity. These recommendations do not establish Brazilian endorsement of R or a future vote.",
}


def build():
    source_path = ROOT / "research/native-source-control-20261019-v1/example.json"
    original = json.loads(source_path.read_text())
    context = original["messages"][1]["content"].removesuffix("\nREQUESTED ROLE: BRA national delegation.")
    system = original["messages"][0]["content"]
    old = "Preserve EVERY own-country point in the supplied checked fact map, including qualifications and ongoing commitments."
    assert old in system
    system = system.replace(old, "For this diagnostic, write only the requested hypothetical application paragraph, using the own-country fact map as constraints rather than reproducing the full source statement.")
    cfg = json.loads((ROOT / "research/native-source-control-20261019-v1/config.json").read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    bindings = {str(p.relative_to(ROOT)): sha(p) for p in [source_path, ROOT / "research/native-application-writer-20261019-v1/grounding.json"]}
    cases = {}
    for name, sentence in STATES.items():
        row = dict(id="state-9469-BRA-"+name, country="BRA", episode="9469", split="application_only_state_control", target=None,
            messages=[dict(role="system", content=system), dict(role="user", content=context+
                "\nEXPLICIT HYPOTHETICAL WORKPLAN R\n"+COMMON+sentence+TAIL+
                "\nCOMMON WORKSHOP DECISION RULE\n"+RULE+"\nREQUESTED ROLE: BRA national delegation.")])
        units = dict(A1="State R's existing cooperation/public update/protected inside channel and correct outside-coverage state; do not invent a missing inside service.",
            A2=("Extend the EXISTING protected two-way channel to the specified outside-Libya groups; request missing line-by-line detail on all four inquiries. Do not replace the existing inside channel with a newly invented service." if name=="missing-outside" else
                "Retain the EXISTING protected channel serving the specified inside/outside groups, without creating/extending a duplicate; request the missing line-by-line detail on all four inquiries."),
            A3="Give concrete staffing and witness-privacy costs of the resulting outreach/reporting versus cheaper narrower outreach's selectivity risk. Existing service maintenance is a real cost; do not call it a missing channel.",
            A4="Label the recommendation as exercise analysis, not an observed Brazilian endorsement of R or an established future vote; do not erase real source positions/hope.")
        rubric = json.loads((ROOT / "research/native-source-control-20261019-v1/rubric.json").read_text())
        rubric["units"]={row["id"]:units};rubric["source_map_units"]={}
        rubric["scope"]="Application-only diagnostic on explicit paired states, not a full source-realization endpoint. Dated sources/maps/rule unchanged across states; one state clause differs."
        protocol=dict(question="Can the model distinguish extending a missing outside service from retaining an existing one, when full source reproduction is removed?",
            case_id=row["id"], state=name, planned_answers=2, optimizer_updates=0,
            intervention="Only the channel's outside-coverage sentence changes between the two frozen cases. Same complete source dossier/map, system240word application-only scope and conditional workshop rule.",
            unchanged_file_bindings=bindings, runner="scripts/run_native_writer_revision.py",
            runner_reuse="Unmodified data-defined one-case/two-arm runner; no revision/draft or peer task here.",
            decision_sequence="One base answer and inspection, then one saved40 adapter answer and inspection. Only launch second state after first pair is inspected. No fitting/automatic queue.",
            source_reading="Complete reused BRA/FRA sources/maps already hand-read. All new explicit state sentences, shared decision rule, four criteria and feasibility references hand-read before calls.",
            scope="Same-assistant, adaptive historically exposed source/state diagnostic with supplied conditional action rule. Not hidden national utility, independent evaluation, sealedOOD, full-source endpoint or multi-agent benefit.",
            independent_review_complete=False, old_seed_control="preserved/unrun")
        cases[name]=(row,rubric,copy.deepcopy(cfg),protocol)
    first=cases["missing-outside"][0];second=cases["existing-outside"][0]
    assert first["messages"][0] == second["messages"][0]
    assert first["messages"][1]["content"].replace(STATES["missing-outside"],STATES["existing-outside"]) == second["messages"][1]["content"]
    return cases


if __name__ == "__main__":
    assert not OUT.exists(), "Fresh pack required; preserve original controls"
    OUT.mkdir()
    for name,(row,rubric,cfg,protocol) in build().items():
        dest=OUT/name;dest.mkdir()
        for key,value in [("example",row),("rubric",rubric),("config",cfg),("protocol",protocol)]:
            (dest/(key+".json")).write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")
        (dest/"example.txt").write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+"\n")
        (dest/"feasibility-not-for-model.json").write_text(json.dumps(dict(author="same assistant",not_model_input_or_target=True,
            not_official_quote_or_model_output=True,text=REFS[name],words=len(REFS[name].split())),indent=2)+"\n")
        print(json.dumps(dict(case=row["id"],scope="application only",reference_words=len(REFS[name].split()))))
