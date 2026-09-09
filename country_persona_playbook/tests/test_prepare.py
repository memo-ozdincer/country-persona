import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare',ROOT/'src/prepare.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.path=self.root/'task4.json'
        # Entirely invented fixture. No actual national position or UN document.
        self.path.write_text(json.dumps([{'Date':'1 May 2020','ID':'DEMO/1','Content':'Fictional proposal.',
          'Statements':[{'representative':'Example speaker','country':'Example Republic',
                         'statement':'We support the fictional proposal subject to a public review.'}]}]))
        self.rows=p.task4(self.path)
    def tearDown(self): self.temp.cleanup()
    def approve(self,r):
        r.update(split='train',review_status='approved',train_permission='approved',
                 approved_by='fixture-only',source_verified=True,context_asof_verified=True,
                 country_iso3='XEX',speaking_capacity='national_representative',phase='post_vote',
                 source_url='https://example.org/fictional-source')
        return r
    def test_raw_conversion_quarantines(self):
        self.assertEqual(self.rows[0]['split'],'quarantine')
        self.assertEqual(self.rows[0]['phase'],'unknown')
        self.assertEqual(self.rows[0]['event_date'],'2020-05-01')
    def test_pending_data_cannot_train(self):
        with self.assertRaises(ValueError):p.build(self.rows,self.root/'out',set())
    def test_approved_exports_prompt_completion(self):
        r=self.approve(self.rows[0]); report=p.build([r],self.root/'out',set())
        self.assertEqual(report['exported_sft'],1)
        sample=p.read_jsonl(self.root/'out/train.sft.jsonl')[0]
        self.assertEqual(set(sample),{'prompt','completion'})
        self.assertEqual(sample['completion'][0]['role'],'assistant')
    def test_reserved_group_fails(self):
        r=self.approve(self.rows[0])
        with self.assertRaises(ValueError):p.build([r],self.root/'out',{r['group_id']})
    def test_group_split_leak_fails(self):
        r=self.approve(self.rows[0]); other=copy.deepcopy(r)
        other.update(id='different',split='test')
        self.assertTrue(p.audit([r,other])['errors'])
    def test_long_text_cross_split_duplicate_fails(self):
        r=self.approve(self.rows[0]);r['target']['text']='Fictional long example. '*20
        other=copy.deepcopy(r);other.update(id='different',group_id='different',split='test')
        self.assertTrue(p.audit([r,other])['errors'])
    def test_short_repeated_vote_labels_are_not_duplicates(self):
        r=self.approve(self.rows[0]);r['target']['text']='yes'
        other=copy.deepcopy(r);other.update(id='different',group_id='different',split='test')
        self.assertFalse(p.audit([r,other])['errors'])
    def test_unknown_phase_rejected(self):
        r=self.approve(self.rows[0]);r['phase']='unknown'
        with self.assertRaises(ValueError):p.training_example(r)
    def test_task2_draft_join(self):
        c=self.root/'votes.csv';c.write_text('Country,Original_id,Authors,Voting,Date\nExample Republic,42,Example,A,2020-05-01\n')
        d=self.root/'drafts/42';d.mkdir(parents=True)
        (d/'draft.json').write_text(json.dumps({'Date':'1 May 2020','ID':'DEMO/2','Title':'Demo draft','Authors':'Example','Content':'Fictional draft text'}))
        rows=p.task2(c,self.root/'drafts')
        self.assertEqual(rows[0]['target']['text'],'abstain')
        self.assertEqual(rows[0]['group_id'],'unsc:DEMO/2')
    def test_task2_missing_draft_fails(self):
        c=self.root/'votes.csv';c.write_text('Country,Original_id,Authors,Voting,Date\nExample Republic,42,Example,A,2020-05-01\n')
        with self.assertRaises(ValueError):p.task2(c,self.root/'missing')
    def test_ungdc_preserves_year_precision(self):
        d=self.root/'corpus';d.mkdir();(d/'XEX_75_2020.txt').write_text('Fictional annual address')
        r=p.ungdc(d)[0]
        self.assertEqual(r['date_precision'],'year');self.assertEqual(r['event_date'],'2020')
        self.assertEqual(r['task'],'domain_text')
    def test_unrecognized_date_fails(self):
        with self.assertRaises(ValueError):p.exact_date('yesterday')
if __name__=='__main__': unittest.main()
