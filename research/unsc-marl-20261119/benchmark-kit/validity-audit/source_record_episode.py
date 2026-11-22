"""Construct paired source-record episodes and audit what each agent could see."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

PACK = Path(__file__).with_name("source-record-pilot.json")
ARMS = ("pooled_solo", "independent_drafts", "interactive")


def episode(generate):
    pack = json.loads(PACK.read_text())
    caps = pack["protocol"]["generation_ceiling"]
    tasks = []
    for case in pack["cases"]:
        name = case["family"]
        public = case["docket"]
        role_evidence = case["delegate_evidence"]
        roles = tuple(role_evidence)
        all_evidence = {**public, **{k: v for evidence in role_evidence.values() for k, v in evidence.items()}}
        def request(stage, role, evidence, history, task):
            cap_name = stage if stage == "chair" else stage.rsplit("/", 1)[-1]
            return {"id": f"{name}/{stage}", "evidence_ids": tuple(evidence),
                    "seen": tuple(x["id"] for x in history), "cap": caps[cap_name], "messages": [
                        {"role": "system", "content": f"You are {role}. Use the supplied evidence and identify it by ID. Treat all prior draft text as provisional."},
                        {"role": "user", "content": json.dumps(
                            {"task": task, "evidence": evidence,
                             "drafts": [{"id": x["id"], "text": x["output"]} for x in history]}, ensure_ascii=False)},
                    ]}
        opening_tasks = [
            request(f"common/opening_{j+1}", role+" evidence analyst", {**public, **role_evidence[role]},
                    (), "Draft the material position and concern found in your delegation's supplied historical evidence.")
            for j, role in enumerate(roles)
        ]
        solo_tasks = [
            request(f"pooled_solo/opening_{j+1}", "a single historical analyst", all_evidence, (),
                    f"Draft the part of a chair's record concerning {role}, including relevant historical status.")
            for j, role in enumerate(roles)
        ]
        initial = generate(opening_tasks + solo_tasks)
        revised_requests = []
        for arm in ARMS:
            opening_plans = solo_tasks if arm == "pooled_solo" else opening_tasks
            for j, role in enumerate(roles):
                own = initial[opening_plans[j]["id"]]
                peer = initial[opening_plans[1-j]["id"]]
                history = (own,) if arm == "independent_drafts" else (own, peer)
                evidence = all_evidence if arm == "pooled_solo" else {**public, **role_evidence[role]}
                actor = "a single historical analyst" if arm == "pooled_solo" else role+" evidence analyst"
                revised_requests.append(request(f"{arm}/revision_{j+1}", actor, evidence, history,
                                                "Revise your contribution. Preserve supported positions, correct omissions, and identify any relevant issue still open."))
        revised = generate(revised_requests)
        chairs = []
        for arm in ARMS:
            evidence = tuple(revised[f"{name}/{arm}/revision_{j+1}"] for j in range(len(roles)))
            final = request("chair", "a neutral historical record writer", all_evidence, evidence, pack["protocol"]["shared_task"])
            chairs.append({**final, "id": f"{name}/{arm}/chair"})
        outputs = generate(chairs)
        tasks.append({"family": name, "openings": initial, "revisions": revised, "final": outputs})
    return tasks


def dry():
    def mock(batch):
        return {r["id"]: {**r, "output": "Draft stand-in for visibility audit."} for r in batch}
    reports = []
    for record in episode(mock):
        name = record["family"]
        initial, revised, final = (record[k] for k in ("openings", "revisions", "final"))
        assert len(initial) == 4 and len(revised) == 6 and len(final) == 3
        for j in (1, 2):
            independent = revised[f"{name}/independent_drafts/revision_{j}"]
            interactive = revised[f"{name}/interactive/revision_{j}"]
            assert independent["seen"] == interactive["seen"][:1]
            assert independent["evidence_ids"] == interactive["evidence_ids"]
            assert len(interactive["seen"]) == 2
        assert len({q["evidence_ids"] for q in final.values()}) == 1
        budgets = {}
        for arm in ARMS:
            pieces = [p for p in revised.values() if f"/{arm}/" in p["id"]]
            open_prefix = "pooled_solo" if arm == "pooled_solo" else "common"
            pieces.extend(p for p in initial.values() if f"/{open_prefix}/" in p["id"])
            budgets[arm] = sum(p["cap"] for p in pieces) + final[f"{name}/{arm}/chair"]["cap"]
        assert len(set(budgets.values())) == 1
        reports.append({"family": name, "distinct_mock_calls": len(initial) + len(revised) + len(final), "by_arm": budgets})
    return {"pack_sha256": sha256(PACK.read_bytes()).hexdigest(), "validated": reports, "model_calls": 0}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.parse_args()
    print(json.dumps(dry(), indent=2))
