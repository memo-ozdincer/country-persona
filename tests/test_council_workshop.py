import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research" / "council_workshop"))

from codex_runner import CodexRunner, MODELS, failure_detail
from local_baseline import input_for
from mandate_smoke import policy
from mandates import Mandates
from meeting import BALLOT, FLOOR, SPEECH, Meeting, run_meeting
from replay import replay
from review import packet as review_packet, report as review_report
from run import HERE, main, simulate


CASE = json.loads((HERE / "climate.json").read_text())
COUNTRIES = list(CASE["delegations"])


def speech(action, version=1, text="Because of the wording."):
    return {"action": action, "version": version, "text": text}


class WorkshopTests(unittest.TestCase):
    def test_revision_clears_acceptances_and_requires_current_version(self):
        m = Meeting(COUNTRIES, CASE["draft"])
        m.apply("GBR", speech("accept"))
        m.apply("IND", speech("propose", text="Invite voluntary reports."))
        self.assertEqual(m.accepted, [])
        with self.assertRaisesRegex(ValueError, "stale"):
            m.apply("FRA", speech("accept", version=1))
        for country in COUNTRIES:
            m.apply(country, speech("accept", version=2))
        self.assertEqual(m.status, "unanimous_acceptance")

    def test_same_poll_snapshot_and_queue_priority(self):
        polls, speakers = [], []

        def decide(country, instruction, public, schema):
            if schema is FLOOR:
                polls.append((country, public["queue"].copy(), len(public["history"])))
                return {"action": "request_floor"}
            self.assertIs(schema, SPEECH)
            speakers.append(country)
            return speech("reply")

        result = run_meeting(CASE, COUNTRIES, 5, decide)
        self.assertEqual(speakers, ["GBR", "IND", "FRA", "GBR", "IND"])
        self.assertEqual(polls[:3], [("IND", [], 1), ("FRA", [], 1), ("GBR", [], 1)])
        self.assertEqual(result["status"], "turn_cap")

    def test_passes_end_discussion_and_ballots_are_private(self):
        def decide(country, instruction, public, schema):
            if schema is FLOOR:
                return {"action": "pass"}
            if schema is BALLOT:
                self.assertNotIn("ballots", public)
                return {"version": 1, "vote": "no", "reason": "Funding is unclear."}
            return speech("ask")

        result = run_meeting(CASE, COUNTRIES, 6, decide, True)
        self.assertEqual(result["status"], "all_passed")
        self.assertEqual(list(result["ballots"]), COUNTRIES)
        self.assertEqual(result["accepted"], [])

    def test_walkout_ends_discussion(self):
        result = run_meeting(CASE, COUNTRIES, 5, lambda *args: speech("walk_away"))
        self.assertEqual(result["status"], "walkout")
        self.assertEqual(len(result["history"]), 1)

    def test_call_cap_reserves_ballots_and_keeps_floor_rounds_intact(self):
        for cap, expected_floor_count in ((6, 0), (7, 3)):
            schemas = []

            def decide(country, instruction, public, schema):
                schemas.append(schema)
                if schema is FLOOR:
                    return {"action": "request_floor"}
                if schema is BALLOT:
                    return {"version": 1, "vote": "yes", "reason": "Approved."}
                return speech("reply")

            with self.subTest(cap=cap):
                result = run_meeting(CASE, COUNTRIES, 6, decide, True, cap)
                self.assertEqual(result["status"], "call_cap")
                self.assertEqual(result["calls"], 4 + expected_floor_count)
                self.assertEqual(schemas, [SPEECH] + [FLOOR] * expected_floor_count + [BALLOT] * 3)
                self.assertEqual(result["queue"], ["IND", "FRA", "GBR"] if expected_floor_count else [])

    def test_solo_and_independent_information_boundaries(self):
        def decide(country, prompt, schema):
            for role, quotes in CASE["delegations"].items():
                self.assertEqual(quotes[0] in prompt, role == country or country == "analyst")
            return {"text": "Invite contributions.", "reason": "Voluntary participation."}

        for mode, count in (("independent", 3), ("solo", 1)):
            result = simulate(CASE, COUNTRIES, mode, 1, False, decide)
            self.assertEqual(len(result["drafts"]), count)

    def test_delegate_prompt_contains_only_own_source_packet(self):
        def decide(country, prompt, schema):
            for role, quotes in CASE["delegations"].items():
                self.assertEqual(quotes[0] in prompt, role == country)
            return speech("reply") if schema is SPEECH else {"action": "pass"}

        simulate(CASE, COUNTRIES, "meeting", 2, False, decide)

    def test_each_excerpt_comes_from_its_named_speaker(self):
        text = (HERE.parent / "scenario-role-sft-20261017-v1/sources/record-8923.txt").read_text()
        receipt = HERE.parents[1] / "reports/role-contrast-design-20261019-v1.json"
        spans = {r["country"]: r["full_source_span"]
                 for r in json.loads(receipt.read_text())["source"]["statements"]}
        start = text.index("Mr. De Rivière (France) (spoke in French):")
        spans["FRA"] = (start, text.index("Mr. De la Fuente Ramírez (Mexico)", start))
        for country, quotes in CASE["delegations"].items():
            start, end = spans[country]
            for quote in quotes:
                self.assertIn(quote, text[start:end])


class RecoveryTests(unittest.TestCase):
    def test_mixed_model_run_and_call_cap_extension_replay(self):
        with tempfile.TemporaryDirectory() as temp, patch("run.CodexRunner") as provider:
            first, longer = Path(temp) / "first", Path(temp) / "longer"
            calls = []

            def factory(model, executable, timeout):
                def runner(prompt, schema):
                    packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
                    calls.append((packet["role"], model, schema))
                    if schema is FLOOR:
                        return {"action": "pass"}
                    if schema is BALLOT:
                        return {"version": 1, "vote": "yes", "reason": "Approved."}
                    return speech("reply")
                runner.executable = "/test/codex"
                return runner

            provider.side_effect = factory
            settings = ["run.py", "--seat-model", f"IND={MODELS[1]}", "--vote"]
            with patch("sys.argv", [*settings, "--call-cap", "4", "--out", str(first)]):
                main()
            self.assertEqual(replay(first)["status"], "call_cap")
            self.assertEqual(calls, [("GBR", MODELS[0], SPEECH)] + [
                (c, MODELS[int(c == "IND")], BALLOT) for c in COUNTRIES
            ])

            calls.clear()
            with patch("sys.argv", [*settings, "--extend-from", str(first), "--call-cap", "7",
                                   "--out", str(longer)]):
                main()
            result = replay(longer)
            self.assertEqual(result["status"], "all_passed")
            self.assertEqual(result["calls"], 7)
            self.assertEqual(len(calls), 6)
            self.assertEqual(calls[0], ("IND", MODELS[1], FLOOR))
            settings_path = longer / "settings.json"
            data = json.loads(settings_path.read_text())
            data["seat_models"]["IND"] = MODELS[0]
            settings_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "Saved request differs for IND"):
                replay(longer)

    def test_extend_carries_public_turn_and_collects_new_private_ballots(self):
        with tempfile.TemporaryDirectory() as temp, patch("run.CodexRunner") as provider:
            first, longer = Path(temp) / "first", Path(temp) / "longer"
            runner = provider.return_value
            runner.executable = "/test/codex"
            old_vote = {"version": 1, "vote": "no", "reason": "Pilot ballot only."}
            runner.side_effect = [speech("reply"), *[old_vote for _ in COUNTRIES]]
            with patch("sys.argv", ["run.py", "--turn-cap", "1", "--vote", "--out", str(first)]):
                main()

            def new_decision(prompt, schema):
                self.assertNotIn("Pilot ballot only.", prompt)
                if schema is FLOOR:
                    return {"action": "pass"}
                self.assertIs(schema, BALLOT)
                return {"version": 1, "vote": "abstain", "reason": "Final position."}

            runner.side_effect = new_decision
            args = ["run.py", "--extend-from", str(first), "--turn-cap", "2", "--vote", "--out", str(longer)]
            with patch("sys.argv", args):
                main()
            result = replay(longer)
            self.assertEqual(result["history"], replay(first)["history"])
            self.assertEqual(result["status"], "all_passed")
            self.assertTrue(all(b["vote"] == "abstain" for b in result["ballots"].values()))

    def test_resume_preserves_completed_decisions_and_replays_exactly(self):
        with tempfile.TemporaryDirectory() as temp, patch("run.CodexRunner") as provider:
            root = Path(temp)
            runner = provider.return_value
            runner.executable = "/test/codex"
            runner.side_effect = [speech("reply"), RuntimeError("provider timeout")]
            first = root / "partial"
            args = ["run.py", "--out", str(first)]
            with patch("sys.argv", args), self.assertRaisesRegex(RuntimeError, "timeout"):
                main()
            original = (first / "calls.jsonl").read_bytes()
            self.assertFalse((first / "result.json").exists())

            resumed = root / "resumed"
            runner.side_effect = [{"action": "pass"} for _ in COUNTRIES]
            args = ["run.py", "--resume-from", str(first), "--out", str(resumed)]
            with patch("sys.argv", args):
                main()
            self.assertEqual(runner.call_count, 2 + len(COUNTRIES))
            self.assertEqual((first / "calls.jsonl").read_bytes(), original)
            self.assertEqual(replay(resumed)["status"], "all_passed")

            log = resumed / "calls.jsonl"
            log.write_text(log.read_text().replace("You have the floor", "Different prompt", 1))
            with self.assertRaisesRegex(ValueError, "Saved request differs"):
                replay(resumed)


class ClauseReviewTests(unittest.TestCase):
    def test_blind_packet_keeps_exact_draft_and_excludes_meeting_metadata(self):
        root = HERE.parents[1] / "reports/council-workshop-20-20261123/astra"
        result = replay(root)
        settings = json.loads((root / "settings.json").read_text())
        rubric = json.loads((HERE / "climate-review.json").read_text())
        packet = review_packet(settings, result, rubric)
        self.assertEqual(set(packet), {"id", "mode", "task", "evidence", "rubric", "answer"})
        self.assertEqual(packet["answer"], result["draft"])
        self.assertEqual(packet, review_packet(
            settings | {"model": "hidden", "countries": list(reversed(COUNTRIES))},
            result | {"ballots": {}, "status": "walkout"}, rubric,
        ))
        self.assertNotEqual(packet["id"],
                            review_packet(settings, result | {"draft": "New wording."}, rubric)["id"])

    def test_quote_must_come_from_criterion_scope(self):
        root = HERE.parents[1] / "reports/council-workshop-20-20261123/astra"
        result = replay(root)
        settings = json.loads((root / "settings.json").read_text())
        rubric = json.loads((HERE / "climate-review.json").read_text())
        packet = review_packet(settings, result, rubric)
        review = HERE.parents[1] / "reports/council-workshop-clause-review-20261123"
        verdict = json.loads((review / "astra-verdict.json").read_text())
        self.assertEqual(review_report(packet, verdict, result)["released_points"], 35)
        wrong_source = next(row for row in packet["evidence"] if row["id"] == "FRA-2")
        verdict["units"][0]["source"] = [{"block": wrong_source["id"], "quote": wrong_source["text"]}]
        with self.assertRaisesRegex(ValueError, "Evidence outside the allowed scope"):
            review_report(packet, verdict, result)


class MandateWorkshopTests(unittest.TestCase):
    @unittest.skipUnless(sys.version_info >= (3, 12), "The local Qwen replay uses Python 3.12")
    def test_floor_diagnostic_preserves_view_and_rotates_request(self):
        from floor_diagnostic import reversed_floor, scheduled_floor

        case = json.loads((HERE / "climate-packages-feasible.json").read_text())
        seats = list(case["delegations"])
        floor = []

        def decide(country, prompt, schema):
            if schema is FLOOR:
                original, messages = input_for(prompt, schema)
                swapped, changed = reversed_floor({"prompt": prompt})
                self.assertEqual(swapped, {"A": original["B"], "B": original["A"]})
                self.assertEqual(json.loads(messages[1]["content"])["meeting"],
                                 json.loads(changed[1]["content"])["meeting"])
                answer = scheduled_floor({"countries": seats}, country, prompt)
                floor.append((country, answer["action"]))
                return answer
            return speech("yield_floor")

        result = simulate(case, seats, "meeting", 2, False, decide, call_cap=7)
        self.assertEqual([entry["country"] for entry in result["history"]], seats[:2])
        self.assertEqual([country for country, action in floor if action == "request_floor"], [seats[1]])
        self.assertEqual(result["calls"], 7)

    def test_local_choice_table_only_offers_checkable_exclusions(self):
        case = json.loads((HERE / "climate-packages-feasible.json").read_text())
        seats = ["IND", "GBR", "FRA", "BRA", "KEN"]

        def inspect(country, prompt, schema):
            options, _ = input_for(prompt, schema)
            rule_outs = [row["text"] for row in options.values() if row["action"] == "rule_out"]
            self.assertEqual(rule_outs, ["assessment"])
            self.assertNotIn("declare_impasse", {row["action"] for row in options.values()})
            return next(row for row in options.values() if row["action"] == "accept")

        result = simulate(case, seats, "meeting", 1, False, inspect, call_cap=1)
        self.assertEqual(result["mandate_score"]["reward"], 0)

    def test_certificate_requires_checked_public_exclusion_for_every_option(self):
        case = json.loads((HERE / "climate-packages-impasse.json").read_text())
        seats = list(case["delegations"])
        meeting = Meeting(seats, case["draft"], mandates=Mandates.from_case(case, seats))
        with self.assertRaisesRegex(ValueError, "every package"):
            meeting.apply("KEN", speech("declare_impasse"))
        with self.assertRaisesRegex(ValueError, "outside the speaker's mandate"):
            meeting.apply("KEN", speech("rule_out", text="assessment"))
        meeting.apply("KEN", speech("rule_out", text="context"))
        meeting.apply("KEN", speech("rule_out", text="convention"))
        meeting.apply("IND", speech("rule_out", text="assessment"))
        meeting.apply("GBR", speech("declare_impasse"))
        self.assertEqual(meeting.status, "certified_impasse")

    def test_private_mandates_and_scoring_survive_logged_replay(self):
        with tempfile.TemporaryDirectory() as temp, patch("run.CodexRunner") as provider:
            directory = Path(temp) / "run"
            case_path = HERE / "climate-packages-feasible.json"
            case = json.loads(case_path.read_text())
            decide = policy("checked_exchange")

            def scripted(prompt, schema):
                packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
                country = packet["role"]
                self.assertEqual(packet["private_mandate"],
                                 {"allowed_packages": sorted(case["mandate_game"]["allowed"][country])})
                self.assertEqual(set(packet["evidence"]), {country})
                self.assertNotIn("allowed", packet["public"])
                self.assertNotIn("mandate_score", packet["public"])
                return decide(country, prompt, schema)

            provider.return_value.executable = "/test/codex"
            provider.return_value.side_effect = scripted
            args = ["run.py", "--case", str(case_path), "--turn-cap", "20", "--call-cap", "50",
                    "--out", str(directory)]
            with patch("sys.argv", args):
                main()
            result = replay(directory)
            self.assertEqual(result["mandate_score"], {
                "feasible_packages": ["context"], "selected_package": "context",
                "outcome": "valid_agreement", "reward": 1,
            })


class SubscriptionTests(unittest.TestCase):
    def test_timeout_preserves_provider_error_with_partial_last_event(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "events.jsonl").write_text(
                '{"type":"error","message":"model unavailable"}\n{"type":'
            )
            self.assertEqual(failure_detail(root, ""), "model unavailable")

    @patch("codex_runner.subprocess.run")
    def test_refuses_api_login_before_generation(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, "", "Logged in using API key")
        with self.assertRaisesRegex(RuntimeError, "ChatGPT"):
            CodexRunner(MODELS[0], "/path/to/codex")
        self.assertEqual(run.call_count, 1)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "unused", "CODEX_API_KEY": "unused"})
    @patch("codex_runner.subprocess.run")
    def test_subscription_invocation(self, run):
        def fake(command, **kwargs):
            self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
            self.assertNotIn("CODEX_API_KEY", kwargs["env"])
            if "login" in command:
                return subprocess.CompletedProcess(command, 0, "", "Logged in using ChatGPT")
            self.assertIn('forced_login_method="chatgpt"', command)
            self.assertIn(MODELS[1], command)
            Path(kwargs["cwd"], "answer.json").write_text('{"action":"pass"}')
            return subprocess.CompletedProcess(command, 0, "", "")

        run.side_effect = fake
        runner = CodexRunner(MODELS[1], "/path/to/codex")
        self.assertEqual(runner("Choose", FLOOR), {"action": "pass"})


if __name__ == "__main__":
    unittest.main()
