"""Bind a reading of opaque final packets to the published judge schema."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE/name).read_text())


def verdicts():
    packets = read("packets.json")
    reading = read("reading.json")
    assert packets.keys()==reading.keys()
    grades = {}
    for key, packet in packets.items():
        row = reading[key]
        evidence = {item["id"]:item["text"] for item in packet["evidence"]}
        labels = {item["id"]:item for item in packet["rubric"]}
        assert set(row["met"]).isdisjoint(row.get("uncertain",{}))
        assert (set(row["met"])|set(row.get("uncertain",{}))) <= set(labels)

        def bind(which):
            return [{"block":name,"quote":evidence[name]} for name in which]

        units = []
        for name, definition in labels.items():
            if name in row["met"]:
                quote, sources = row["met"][name]
                mark = {"status":"met","source":bind(sources),"response":quote,
                        "reason":"The cited response span and source cover this criterion."}
            elif name in row.get("uncertain",{}):
                quote, sources, reason = row["uncertain"][name]
                mark = {"status":"uncertain","source":bind(sources),"response":quote,"reason":reason}
            else:
                reason = row.get("omissions",{}).get(name,"The answer lacks the full required detail.")
                mark = {"status":"unmet","source":[],"response":"","reason":reason}
            units.append({"id":name} | mark)
        if row.get("guard"):
            status, quote, sources, reason = row["guard"]
            guard = {"status":status,"source":bind(sources),"response":quote,"reason":reason}
        else:
            guard = {"status":"clear","source":[],"response":"",
                     "reason":"The answer omits some details but no material invented fact or authority was found."}
        grades[key]={"id":key,"units":units,"guard":guard}
    return grades


if __name__ == "__main__":
    print(json.dumps(verdicts(),ensure_ascii=False,indent=2))
