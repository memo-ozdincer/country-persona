import unittest
from types import SimpleNamespace

import torch
from country_persona.coverage_loss import FrozenCoverageLoss, FrozenChunkedCoverageLoss, annotate_target, token_allocation


class CoverageLossTests(unittest.TestCase):
    def test_causal_shift_and_prompt_padding_gradients(self):
        labels = torch.tensor([[-100,-100,2,3,-100]])
        logits = torch.randn(1,5,6,requires_grad=True)
        loss = FrozenCoverageLoss([{'target_ids':[2,3],'target_weights':[1.5,0.5]}])(SimpleNamespace(logits=logits),labels)
        loss.backward()
        self.assertGreater(float(logits.grad[0,1].abs().sum()),0)
        self.assertGreater(float(logits.grad[0,2].abs().sum()),0)
        self.assertEqual(float(logits.grad[0,[0,3,4]].abs().sum()),0)

    def test_uniform_equivalence_and_accumulation(self):
        torch.manual_seed(7)
        labels = torch.tensor([[-100,1,2,-100],[-100,3,4,5]])
        logits = torch.randn(2,4,7,requires_grad=True)
        records = [{'target_ids':[1,2],'target_weights':[1.5,0.5]}, {'target_ids':[3,4,5],'target_weights':[0.5,1.0,1.5]}]
        plain = FrozenCoverageLoss(records,uniform=True)(SimpleNamespace(logits=logits),labels)
        expected = torch.nn.functional.cross_entropy(logits[:,:-1].reshape(-1,7),labels[:,1:].reshape(-1),ignore_index=-100)
        self.assertTrue(torch.allclose(plain,expected))
        function = FrozenCoverageLoss(records)
        joined = function(SimpleNamespace(logits=logits),labels)
        split = sum(function(SimpleNamespace(logits=logits[i:i+1]),labels[i:i+1],num_items_in_batch=5) for i in range(2))
        self.assertTrue(torch.allclose(joined,split))
        self.assertTrue(torch.allclose(torch.autograd.grad(joined,logits,retain_graph=True)[0],torch.autograd.grad(split,logits)[0]))

    def test_clause_mass_and_boundary_text(self):
        text = 'Documented position: Short fact. A considerably longer fact.\n\nRecommendation: Do a concrete thing.\n\nCommitment boundary: No guarantee.'
        spans = annotate_target(text)
        offsets = [(0,0)]+[(i,i+1) for i in range(len(text))]+[(0,0)]
        weights, clauses = token_allocation(offsets,1,0,spans)
        self.assertEqual(len(spans),3)
        self.assertAlmostEqual(sum(weights),len(offsets)-1)
        self.assertEqual(weights[0],0)
        self.assertEqual(weights[-1],0.25)
        extras = [sum(weights[i]-0.25 for i in indices) for indices in clauses]
        self.assertTrue(all(abs(x-extras[0])<1e-6 for x in extras))
        with self.assertRaisesRegex(ValueError,'overlapping'):
            token_allocation(offsets,1,0,spans+spans[:1])

    def test_unfrozen_or_truncated_target_rejected(self):
        function = FrozenCoverageLoss([{'target_ids':[1,2],'target_weights':[1.5,0.5]}])
        with self.assertRaisesRegex(ValueError,'Unfrozen'):
            function.weights_for(torch.tensor([[-100,1]]))
        with self.assertRaisesRegex(ValueError,'mass'):
            FrozenCoverageLoss([{'target_ids':[1,2],'target_weights':[2.0,1.0]}])

    def test_pinned_chunked_loss_values_and_gradients(self):
        from trl.trainer.sft_trainer import _chunked_cross_entropy_loss
        torch.manual_seed(3)
        hidden = torch.randn(2,5,4,requires_grad=True)
        head = torch.randn(7,4,requires_grad=True)
        labels = torch.tensor([[-100,-100,1,2,-100],[-100,3,4,5,-100]])
        records = [{'target_ids':[1,2],'target_weights':[1.5,0.5]},{'target_ids':[3,4,5],'target_weights':[0.5,1,1.5]}]
        plain = FrozenChunkedCoverageLoss(records,uniform=True)(hidden,head,2,labels=labels)
        reference = _chunked_cross_entropy_loss(hidden,head,2,labels=labels)
        self.assertTrue(all(torch.allclose(a,b) for a,b in zip(plain,reference)))
        a = torch.autograd.grad(plain[0],(hidden,head),retain_graph=True)
        b = torch.autograd.grad(reference[0],(hidden,head),retain_graph=True)
        self.assertTrue(all(torch.allclose(x,y) for x,y in zip(a,b)))
        weighted = FrozenChunkedCoverageLoss(records)(hidden,head,2,labels=labels)[0]
        direct = FrozenCoverageLoss(records)(SimpleNamespace(logits=hidden@head.t()),labels)
        self.assertTrue(torch.allclose(weighted,direct))
        a = torch.autograd.grad(weighted,(hidden,head),retain_graph=True)
        b = torch.autograd.grad(direct,(hidden,head))
        self.assertTrue(all(torch.allclose(x,y,atol=1e-6) for x,y in zip(a,b)))


if __name__ == '__main__':
    unittest.main()
