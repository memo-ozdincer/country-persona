import unittest
from country_persona.io import digest
from country_persona.preference_checks import validate_pair,audit_preference_masks,use_torch_preference_logprobs


class PreferenceChecksTests(unittest.TestCase):
    def fixture(self):
        original={'prompt':[{'role':'user','content':'Evidence.'}],'completion':[{'role':'assistant','content':'The position is qualified.'}]}
        pair={'prompt':original['prompt'],'chosen':original['completion'],'rejected':[{'role':'assistant','content':'The position is absolute.'}]}
        a={'pair_sha256':digest(pair),'edit':{'start':16,'end':25,'before':'qualified','after':'absolute'},'prompt_ids':[6,7], 'chosen_ids':[1,2,3],'rejected_ids':[4,5]}
        return original,pair,a

    def test_minimal_edit_and_positive_preservation(self):
        original,pair,a=self.fixture();validate_pair(original,pair,a)
        pair['rejected'][0]['content']+=' Another edit.';a['pair_sha256']=digest(pair)
        with self.assertRaisesRegex(ValueError,'beyond'):
            validate_pair(original,pair,a)

    def test_actual_collator_and_truncation(self):
        from trl.trainer.dpo_trainer import DataCollatorForPreference
        _,_,a=self.fixture()
        row={k:a[k] for k in ('prompt_ids','chosen_ids','rejected_ids')}
        report=audit_preference_masks([row],DataCollatorForPreference(pad_token_id=0,max_length=8),[a])
        self.assertTrue(report['prompt_and_padding_excluded'])
        with self.assertRaisesRegex(ValueError,'truncated'):
            audit_preference_masks([row],DataCollatorForPreference(pad_token_id=0,max_length=3),[a])

    def test_chosen_or_prompt_change_rejected(self):
        original,pair,a=self.fixture();pair['chosen']=[{'role':'assistant','content':'Other.'}]
        with self.assertRaisesRegex(ValueError,'Preferred'):
            validate_pair(original,pair,a)

    def test_torch_fallback_scores_masks_and_gradients(self):
        import torch
        import trl.trainer.dpo_trainer as dpo
        use_torch_preference_logprobs()
        logits=torch.randn(2,4,7,requires_grad=True)
        ids=torch.tensor([[1,2,3,4],[4,3,2,1]])
        mask=torch.tensor([[0,1,1,0],[0,0,1,1]],dtype=torch.bool)
        logps,entropy=dpo.selective_log_softmax_and_entropy(logits,ids,row_mask=mask,entropy_requires_grad=False)
        full=torch.log_softmax(logits,dim=-1)
        reference=full.gather(-1,ids.unsqueeze(-1)).squeeze(-1).masked_fill(~mask,0)
        self.assertTrue(torch.allclose(logps,reference))
        self.assertTrue(torch.isfinite(entropy).all())
        logps.sum().backward()
        self.assertEqual(float(logits.grad[~mask].abs().sum()),0)
        self.assertGreater(float(logits.grad[mask].abs().sum()),0)

    def test_cached_dataset_evaluation_skips_duplicate_precomputation(self):
        from unittest.mock import patch
        from trl import DPOTrainer
        from transformers import Trainer
        trainer=object.__new__(DPOTrainer)
        trainer._is_vision_dataset=False
        trainer.eval_dataset={'already_cached_reference_columns':True}
        with patch.object(Trainer,'evaluate',return_value={'verified':True}) as parent:
            self.assertEqual(trainer.evaluate(),{'verified':True})
        parent.assert_called_once_with(eval_dataset=None,ignore_keys=None,metric_key_prefix='eval')


if __name__=='__main__':
    unittest.main()
