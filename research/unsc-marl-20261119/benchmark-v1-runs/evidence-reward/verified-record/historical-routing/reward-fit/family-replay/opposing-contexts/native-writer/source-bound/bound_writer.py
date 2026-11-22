"""Write independently attributed UNIFIL fragments and assemble legal receipt masks."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import natural_writer as n

e = n.matched.e
OUT = HERE / "evidence"
ROLES = ("Brazil", "China", "Russia")
ASSESSMENTS = ("some", "insufficient", "sufficient")


def request(system, sources, limit):
    return {"messages": [{"role": "system", "content": system},
                         {"role": "user", "content": json.dumps(sources, ensure_ascii=False)}],
            "max_output_tokens": limit}


def plan():
    _, case, _ = n.setup()
    evidence = {b["id"]: b["text"] for b in case["evidence"]}
    public = request(
        "Write one paragraph, at most 68 words, using only these official vote and operative blocks. "
        "Include date, exact draft and sponsor, adopted resolution, explicit full vote tally and abstainers. "
        "Preserve the mandate end date, independence without prior permission within the mandate, "
        "and continued coordination with the Government under the status-of-forces agreement. "
        "Omit optional votes and commentary. Return only the paragraph.",
        {key: evidence[key] for key in ("vote", "operative")}, 150)
    system = (
        "Return a JSON object with keys summary, mission_support_quote, and host_concerns. "
        "In summary give one attributed sentence of at most 23 words, starting with the delegation name. "
        "Preserve the source's material reason, specific qualifiers, and support for the mission. "
        "Write solely about this delegation. Retain differences between the mission and the text. "
        "For mission_support_quote give a short exact source substring explicitly supporting the mission, "
        "or an empty string. For host_concerns give null if the source does not assess how much the "
        "text addressed the host country's concerns. Otherwise give an object with assessment "
        "(some, insufficient or sufficient) and quote (the exact supporting substring from the source). "
        "Quote from the source, with no ellipsis. Return only the JSON object."
    )
    rows = [{"part": "public", "request": public}]
    rows.extend({"part": role, "request": request(system, {"delegation": role, "source": evidence[role.lower()]}, 230)}
                for role in ROLES)
    paths = (Path(__file__), HERE / "protocol.md", n.CASE_PATH, n.WITNESS, HERE.parent / "plan.json")
    return {"requests": rows, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


def collect(generate, directory):
    current = plan()
    assert current == n.read(HERE / "plan.json")
    for row in current["requests"]:
        n.base.suite.append(directory / "calls.jsonl", row | {"response": generate(row["request"])})


def admit(part, response, source):
    """Bind each fragment to the source and report all mechanical gates."""
    text = response["text"].strip()
    result = {"summary": "", "mission_support_quote": "", "host_concerns": None, "issues": []}
    if response["termination"] != "complete":
        return result | {"issues": ["incomplete"]}
    if part == "public":
        return result | {"summary": text} if text else result | {"issues": ["empty_public"]}
    try:
        row = json.loads(text)
    except json.JSONDecodeError:
        return result | {"issues": ["invalid_json"]}
    if not isinstance(row, dict) or set(row) != {"summary", "mission_support_quote", "host_concerns"}:
        return result | {"issues": ["invalid_schema"]}
    summary, mission, host = (row[k] for k in ("summary", "mission_support_quote", "host_concerns"))
    if isinstance(summary, str) and summary.startswith(part + " ") and "\n" not in summary:
        result["summary"] = summary
    else:
        return result | {"issues": ["misattributed_summary"]}
    if type(mission) is str and (mission == "" or mission.strip() and mission in source):
        result["mission_support_quote"] = mission
    else:
        result["issues"].append("invalid_mission_quote")
    if host is not None:
        if (isinstance(host, dict) and set(host) == {"quote", "assessment"}
                and host["assessment"] in ASSESSMENTS and isinstance(host["quote"], str)
                and host["quote"].strip() and host["quote"] in source):
            result["host_concerns"] = host
        else:
            result["issues"].append("invalid_host_quote")
    return result


def render(fragments, mask):
    present = [role for bit, role in zip(n.BITS[1:], ROLES) if mask & bit and fragments[role]["summary"]]
    lines = [fragments["public"]["summary"], *(fragments[r]["summary"] for r in present)]
    for first, second in combinations(present, 2):
        pair = [fragments[role] for role in (first, second)]
        if not all(row["mission_support_quote"] and row["host_concerns"] for row in pair):
            continue
        if pair[0]["host_concerns"]["assessment"] != pair[1]["host_concerns"]["assessment"]:
            lines.append(f"{first} and {second} backed UNIFIL but differed on accommodating Lebanese concerns.")
            break
    return "\n\n".join(line for line in lines if line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    if parser.parse_args().mode == "plan":
        print(json.dumps(plan(), ensure_ascii=False, indent=2))
    else:
        with patch.object(n.base.suite, "collect", collect), patch.object(
                n.base, "roster", return_value={"matched-unifil-source-bound-writer": None}):
            n.base.run(OUT)
