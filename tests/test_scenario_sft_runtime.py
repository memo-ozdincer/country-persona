"""Run with the pinned ML Python and unittest; no pytest installation required."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


class RuntimeChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import torch
            import peft
            import transformers
        except ImportError:
            raise unittest.SkipTest("Pinned ML environment required")
        if not hasattr(transformers, "Qwen3_5ForCausalLM"):
            raise unittest.SkipTest("Qwen3.5 runtime checks require the separate pinned Transformers 5 environment")
        torch.set_num_threads(1)

    def test_cpu_optimization_and_cold_reload(self):
        from run_scenario_sft import cpu_check
        with tempfile.TemporaryDirectory() as temp:
            result = cpu_check(Path(temp))
            self.assertEqual(result["steps"], 8)
            self.assertTrue(result["cold_separate_base_reload_exact"])
            events = [json.loads(x) for x in (Path(temp) / "optimization.jsonl").read_text().splitlines()]
            self.assertEqual([e["step"] for e in events], list(range(1, 9)))
            self.assertTrue(all(e["gradient"]["finite"] for e in events))

    def test_first_and_final_target_tokens_receive_loss(self):
        import torch
        from run_scenario_sft import tiny_model, fresh_adapter
        from country_persona.scenario_sft import completion_loss
        model = fresh_adapter(tiny_model(), rank=2)
        row = dict(input_ids=[3, 4, 5, 6, 7, 2], labels=[-100] * 3 + [6, 7, 2], prefix_tokens=3)
        baseline = float(completion_loss(model, row, "cpu").detach())
        for index in [3, 5]:
            changed = {k: list(v) if isinstance(v, list) else v for k, v in row.items()}
            changed["input_ids"][index] = 8
            changed["labels"][index] = 8
            self.assertNotEqual(baseline, float(completion_loss(model, changed, "cpu").detach()))

    def test_generation_receives_no_gold_completion(self):
        import torch
        from run_scenario_sft import tiny_model
        from country_persona.meeting_sequence import END, header, tokenize_example
        from country_persona.scenario_sft import evaluate
        class Tok:
            pad_token_id = 0
            def encode(self, s, **kwargs): return [3 + ord(c) % 120 for c in s]
            def convert_tokens_to_ids(self, s): return 2
            def decode(self, ids, **kwargs): return repr(ids)
        class Spy:
            def __init__(self): self.model = tiny_model(); self.seen = []
            def eval(self): self.model.eval()
            def __call__(self, **kwargs): return self.model(**kwargs)
            def generate(self, input_ids, **kwargs):
                self.seen.append(input_ids[0].tolist())
                return torch.cat([input_ids, torch.tensor([[2]])], dim=1)
        tok, rows, model = Tok(), [], Spy()
        for country, name in [("IND", "A"), ("GBR", "B")]:
            turn = dict(country=country, representative=name, institution="UNSC", capacity="national_delegation", phase="discussion")
            prefix = "past\n" + header(turn)
            completion = "gold" + END
            rows.append(dict(id=country, source="test", country=country, prefix=prefix,
                             completion=completion, provenance={"turns": [turn]},
                             **tokenize_example(tok, dict(prefix=prefix, completion=completion))))
        with tempfile.TemporaryDirectory() as temp:
            result = evaluate(model, tok, rows, temp, "cpu", max_new_tokens=4)
        self.assertEqual(result["calls"], 2)
        self.assertEqual(model.seen, [r["input_ids"][:r["prefix_tokens"]] for r in rows])


if __name__ == "__main__":
    unittest.main()
