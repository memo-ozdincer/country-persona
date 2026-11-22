"""Apply reviewed writer scores to exactly the same forecast receipt distributions."""
import json

import writer
import reverse_writer

HERE = writer.HERE


def evaluate():
    packet = writer.read(writer.PACKET)
    forecast = writer.read(HERE / "forecast.json")["budgets"]["70"]
    marks = writer.read(HERE / "marks.json")
    atom_weights = {atom["id"]: atom["points"] for card in packet["cards"] for atom in card["atoms"]}
    owners = {atom["id"]: s for s, card in enumerate(packet["cards"]) for atom in card["atoms"]}
    needs = set(packet["joint"]["needs"])
    routes = {}
    outcomes = {}
    for order, directory in (("forward", writer.EVIDENCE), ("reverse", reverse_writer.EVIDENCE)):
        rows = writer.read(directory / "final-records.json")[writer.FAMILY]
        transcript = {row["id"]: row for row in
                      map(json.loads, (directory / "transcript.jsonl").read_text().splitlines())}
        complete = writer.read(directory / "complete.json")
        assert writer.runner.digest(directory / "final-records.json") == complete["final_records_sha256"]
        assert writer.runner.digest(directory / "transcript.jsonl") == complete["transcript_sha256"]
        assert complete["records"] == len(rows) == len(transcript)
        requests = writer.requests() if order == "forward" else reverse_writer.requests()
        for req in requests:
            assert all(transcript[req["id"]][key] == val for key, val in req.items())
        assert marks[order].keys() == rows.keys()
        scored = {} if order == "forward" else {k: outcomes["forward"][str(k)] for k in ("1", "2", "4")}
        scored["0"] = {"raw": 0, "released": 0, "words": 0, "release": True, "guard": "clear"}
        for key, answer in rows.items():
            assert answer == transcript[key]["output"]
            mark = marks[order][key]
            met = mark["met"]
            for item, quote in met.items():
                assert int(key) & (1 << owners[item])
                assert quote.strip() and quote in answer
            raw = sum(atom_weights[k] for k in met) + packet["joint"]["points"] * (needs <= met.keys())
            words = len(answer.split())
            guard = mark["guard"]
            release = guard == "clear" and 0 < words <= 70 and transcript[key]["ended"]
            scored[key] = {"raw": raw, "released": raw if release else 0,
                           "words": words, "release": release, "guard": guard}
        assert set(scored) == set(map(str, range(8)))
        outcomes[order] = dict(sorted(scored.items()))
        routes[order] = {}
        for law, row in forecast["laws"].items():
            forecast_arms = row["arms"]
            result = {}
            for name, stats in forecast_arms.items():
                mass = stats["receipt_mass"]
                assert abs(sum(mass) - 1) < 1e-12
                assert "cost" in stats
                expectation = lambda metric: sum(p * scored[str(i)][metric] for i, p in enumerate(mass))
                cover = expectation("released")
                result[name] = {"raw_28": expectation("raw"), "release_probability": expectation("release"),
                                "released_28": cover, "released_net": packet["base_points"] + cover - stats["cost"]}
            base = result["same_responder_silence"]["released_net"]
            for stats in result.values():
                stats["net_over_same_responder_silence"] = stats["released_net"] - base
            routes[order][law] = result
    return {"literally_available_28": [score - packet["base_points"] for score in forecast["excerpt_scores"]],
            "records": outcomes, "same_frozen_route_distributions": routes}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
