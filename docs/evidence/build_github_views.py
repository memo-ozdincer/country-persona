"""Build GitHub-readable views of existing SFT evidence; no model imports or calls.

Run from any directory: python3 -B docs/evidence/build_github_views.py.
The checked-in offline HTML supplies the original minimum-country evidence.
Other inputs are the preserved, Git-tracked meeting-context records.
"""
from __future__ import annotations

import hashlib
import html
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
DEST = Path(__file__).resolve().parent
SHORT = DEST / 'minimal-country-sft-20261021'
MEETING = DEST / 'meeting-context-20261021'
PAGES = {}
INPUTS = {}
EXPECTED_BLOCKS = {}


def sha(data):
    return hashlib.sha256(data).hexdigest()


class EmbeddedJSON(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.data = ''
    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('id') == 'evidence':
            self.active = True
    def handle_data(self, data):
        if self.active:
            self.data += data
    def handle_endtag(self, tag):
        if tag == 'script':
            self.active = False


def load(path):
    p = ROOT / path
    data = p.read_bytes()
    INPUTS[path] = {'bytes': len(data), 'sha256': sha(data)}
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()] if p.suffix == '.jsonl' else json.loads(data)


def quote_text(text):
    lines = []
    for line in text.split('\n'):
        if not line:
            lines.append('>')
            continue
        escaped = html.escape(line, quote=False)
        escaped = re.sub(r'[ \t]+$', lambda m: ''.join('&#32;' if c == ' ' else '&#9;' for c in m.group()), escaped)
        lines.append('> ' + escaped)
    return '\n'.join(lines)


def block(text, kind, key):
    """Blockquotes wrap naturally on GitHub; entities keep protocol tokens visible."""
    assert (kind, key) not in EXPECTED_BLOCKS
    EXPECTED_BLOCKS[kind, key] = text
    quoted = quote_text(text)
    return '<!-- exact:' + kind + ':' + key + ' -->\n\n' + quoted + '\n\n<!-- /exact -->\n\n'


def messages(rows, prefix):
    return ''.join('**' + m['role'].upper() + '**\n\n' + block(m['content'], 'prompt', prefix + ':' + str(i)) for i, m in enumerate(rows))


def details(title, body):
    return '<details>\n<summary>' + html.escape(title) + '</summary>\n\n' + body + '\n</details>\n\n'


def raw_json(value):
    return '````json\n' + json.dumps(value, ensure_ascii=False, indent=2) + '\n````\n\n'


def relative(page, target):
    return Path(os.path.relpath(ROOT / target, page.parent)).as_posix()


def source_link(page, target, label='Original evidence'):
    return '[' + label + '](' + relative(page, target) + ')'


def write(page, text):
    assert page not in PAGES
    PAGES[page] = text.rstrip() + '\n'


def result(arm, case_id):
    run = bundle['runs'][arm]
    return (next(x for x in run['outputs'] if x['id'] == case_id),
            next(x for x in run['review']['reviews'] if x['id'] == case_id))


def answer(arm, c):
    output, review = result(arm, c['id'])
    count = sum(x['status'] == 'met' for x in review['ratings'].values())
    text = '### ' + bundle['runs'][arm]['label'] + '\n\n**' + str(count) + '/5 content checks** · ' + str(output['generated_tokens']) + ' output tokens\n\n'
    text += block(output['output'], 'answer', arm + ':' + c['id'])
    notes = review['additional_source_fidelity_observations']
    text += '**Original additional fidelity notes:**\n\n' + ('\n'.join('- ' + n for n in notes) if notes else 'None recorded.') + '\n\n'
    grades = '| Criterion | Original grade | Original reason |\n|---|---|---|\n'
    for unit, g in review['ratings'].items():
        grades += '| ' + unit + ' | ' + g['status'] + ' | ' + g['reason'].replace('|', '\\|').replace('\n', ' ') + ' |\n'
    return text + details('All original grades and reasons', grades) + 'Answer SHA-256: `' + review['output_sha256'] + '`\n\n'


def cases_page(page, title, description, cases, arms):
    text = '# ' + title + '\n\n[Evidence index](README.md)\n\n' + description + '\n\n'
    text += '\n'.join('- [' + c['id'] + '](#' + c['id'] + ')' for c in cases) + '\n\n'
    for c in cases:
        text += '## ' + c['id'] + '\n\n**' + c['country_iso3'] + '** · ' + c['family'] + ' · scenario: ' + c['scenario'] + '\n\n'
        text += '**Task before the shared source statements:**\n\n' + quote_text(c['prompt'][-1]['content'].split('\n\nCOMPLETE NATIONAL STATEMENT', 1)[0]) + '\n\n'
        prefix = page.stem + ':' + c['id']
        text += details('Full exact system/user prompt, including complete source statements', messages(c['prompt'], prefix))
        text += ''.join(answer(arm, c) for arm in arms)
    write(page, text)


parser = EmbeddedJSON()
offline = SHORT / 'viewer.html'
parser.feed(offline.read_text())
bundle = json.loads(parser.data)
assert bundle['new_model_calls'] == bundle['new_optimizer_updates'] == 0
assert sum(len(r['outputs']) for r in bundle['runs'].values()) == 94
assert sum(len(r['step_metrics']) for r in bundle['runs'].values()) == 144
for f in bundle['source_files'].values():
    assert sha(f['text'].encode()) == f['sha256']
INPUTS[str(offline.relative_to(ROOT))] = {'bytes': offline.stat().st_size, 'sha256': sha(offline.read_bytes())}

write(DEST / 'README.md', '''# Full SFT examples and model answers

Read these pages directly in GitHub. All answers come from preserved runs; this publication made no new model calls or training updates. Research remains paused.

| Experiment | Start here | What it established |
|---|---|---|
| Tiny complete-answer country SFT | [All eight before/after comparisons](minimal-country-sft-20261021/comparison.md) | Base → four-example → eight-example: **23/40 → 34/40 → 38/40** content checks; **7/16 → 15/16 → 15/16** application/commitment checks. Same exposed source event; assistant grading. |
| Scenario + ordered meeting history + requested delegation | [Meeting-context experiment](meeting-context-20261021/README.md) | Four authentic fitting speeches exact; both Ukraine development cases fail. Full earlier history only fit for sanctions. |
| Context attribution and reader/writer follow-up | [All eleven saved outputs](meeting-context-20261021/grounded-context.md) | Full dossier 12/18; attributed cards 15/18; cards + actual model map 18/18. One provisional strict pass; no additional training. |

The short-answer experiment and authentic-speech experiment are separate branches. Their scores use different criteria and cannot be pooled.

- [Short-answer SFT: complete index, training data, metrics, and all 94 answers](minimal-country-sft-20261021/README.md)
- [Meeting-context SFT: complete index, training sequences, all 14 answers, and the context follow-up](meeting-context-20261021/README.md)
- [Original consolidated research report](../CONSOLIDATED_RESULTS_20261019.md)
''')

write(SHORT / 'README.md', '''# Tiny complete-answer country SFT — full evidence

[All experiments](../README.md)

Qwen3.5-4B, India and Brazil, complete national statements from S/PV.9214 (9 December 2022). Source-conditioned hypothetical policy application; no private bullet plan in training.

| Same eight new-wording cases | Base | Four examples / 64 steps | Eight examples / 64 steps |
|---|---:|---:|---:|
| Required-content checks | 23/40 | 34/40 | 38/40 |
| Application + commitment checks | 7/16 | 15/16 | 15/16 |

These are dependent assistant annotations, not independently validated response-success rates. The five checks do not cover every possible unsupported claim or word-limit violation. Original fidelity observations and regressions remain visible.

1. **[All eight before/after comparisons](comparison.md)** — complete base, four-example and eight-example answers, exact full prompts, grades and errors (24 answers).
2. **[All eight complete SFT conversations](training.md)** — full system/user/assistant targets, including both source statements.
3. **[Training trajectories](training-metrics.md)** — configurations, losses, all 144 recorded step metrics and gradient checks.
4. **[Early ten-case evaluation](early-fits.md)** — first base, identical matched baseline rerun, 16-step and 64-step fits (40 answers).
5. **[Expanded exact and checked-plan controls](controls.md)** — all remaining controls (18 answers).
6. **[Literal-mechanism wording diagnosis](wording-diagnosis.md)** — follow-up qualifying the active/proactive ambiguity (12 answers; no new training).
7. **[Complete sources and rubric](sources-and-rubric.md)**.

All **94** saved generation records are included. They include a repeated baseline and are not 94 independent cases. The three fits started fresh: 16 + 64 + 64 = **144 updates**. Intermediate answers and adapters at every training step were not saved; none are reconstructed here.

**Offline version:** [download the complete HTML viewer](viewer.html?raw=true), then open it locally. GitHub renders the Markdown pages above directly. The HTML embeds full JSON, original token records, reviews, logs, source files and archived code, with download buttons; GitHub does not execute it inside a repository page.

[Original dated report](../../AURORA_MINIMAL_COUNTRY_20261005.md) · [Original HTML verification](export-verification.json) · [Fresh stored-evidence CPU replay](replay.json) · [GitHub export integrity receipt](../github-export-verification.json)
''')

cases = bundle['packs']['eight']['cases.jsonl']
main = [c for c in cases if c['family'] not in ('exact_control', 'strong_checked_plan_control')]
cases_page(SHORT / 'comparison.md', 'All eight before/after comparisons',
           'Every complete answer behind **23/40 → 34/40 → 38/40**. The evaluation prompts differ from fitting prompts but reuse the same historical sources. Scores are the original five-check content grades, not full-fidelity guarantees.', main,
           ['extension-base', 'extension-four', 'extension-eight'])
cases_page(SHORT / 'early-fits.md', 'Early ten-case evaluation: all 40 answers',
           'The first and matched base runs produced identical outputs. The 16-step and 64-step fits are separate fresh runs, not successive checkpoints of one optimization trajectory.',
           bundle['packs']['four']['cases.jsonl'], ['first-base', 'matched-base', 'four-target-16', 'four-target-64'])
cases_page(SHORT / 'controls.md', 'Exact and checked-plan controls: all 18 answers',
           'Exact fitting controls and supplied-plan controls are excluded from the eight-case 40-check headline comparison.',
           [c for c in cases if c['family'] in ('exact_control', 'strong_checked_plan_control')],
           ['extension-base', 'extension-four', 'extension-eight'])
cases_page(SHORT / 'wording-diagnosis.md', 'Literal-mechanism diagnosis: all 12 answers',
           'Evaluation only, with the two saved adapters. The original partial-state prompt said active while the source requested proactive; this clarification preserves original grades and tests explicitly specified mechanism states. No new training.',
           bundle['packs']['literal']['cases.jsonl'], ['literal-base', 'literal-four', 'literal-eight'])

text = '# All eight complete SFT conversations\n\n[Evidence index](README.md)\n\nThe first four are unchanged across both data sets. The last four add attribution/shutdown contrasts. Only the assistant completion receives direct next-token loss; the full prompt is context. These are supplied training targets, not automatically generated answers from the fitted model.\n\n'
for i, (meta, row) in enumerate(zip(bundle['packs']['eight']['train.manifest.jsonl'], bundle['packs']['eight']['train.jsonl'])):
    text += '## ' + str(i + 1) + '. ' + meta['id'] + '\n\n' + ('Original four; retained unchanged.' if i < 4 else 'Added in the eight-example set.') + '\n\n'
    text += details('Full system and user messages, including both source statements', messages(row['prompt'], 'sft:' + meta['id']))
    for j, m in enumerate(row['completion']):
        text += '**ASSISTANT — supervised target**\n\n' + block(m['content'], 'target', meta['id'] + ':' + str(j))
    text += 'Chat-template options: `' + json.dumps(row['chat_template_kwargs']) + '`\n\n'
write(SHORT / 'training.md', text)

text = '# Full recorded training metrics\n\n[Evidence index](README.md)\n\nThree fresh Qwen3.5-4B rank-8 LoRA SFT fits. BF16; alpha 16; dropout 0.05; all linear layers; AdamW; peak learning rate 5e-5 with linear decay; microbatch one; accumulation two; seed 42; completion-only loss; no packing. Context 4,096 tokens; greedy generation with thinking disabled; output cap 384. Hardware: NVIDIA RTX PRO 6000 Blackwell Server Edition.\n\nChanging the step budget also changes the learning-rate schedule. No intermediate answers, intermediate adapter checkpoints, or exact per-step sample-order log were saved. All recorded optimizer metrics and gradient checks are preserved below.\n\n'
for arm in ['four-target-16', 'four-target-64', 'extension-eight']:
    item = bundle['runs'][arm]; r = item['run']; checks = r['optimization_checks']['rank_checks'][0]
    text += '## ' + item['label'] + '\n\n'
    text += f"Training-target NLL: **{r['loss_before']['token_weighted_loss']:.6f} → {r['loss_after']['token_weighted_loss']:.6f}**. Training time: **{r['training_seconds']:.2f} seconds**; peak allocation: **{r['peak_allocated_gpu_gib']:.2f} GiB**. Actual sequence/supervised tokens: **{checks['actual_sequence_tokens']:,} / {checks['actual_target_tokens']:,}**.\n\n"
    text += '| Step | Epoch | Logged loss | Learning rate | Logged grad norm | Finite grads | Post-clipping gradient L2 |\n|---:|---:|---:|---:|---:|---|---:|\n'
    for row, grad in zip(item['step_metrics'], checks['gradient_trace']):
        m = row['recorded_console_metrics']
        text += '| ' + ' | '.join(str(x) for x in [row['step'], m['epoch'], m['loss'], m['learning_rate'], m['grad_norm'], grad['finite'], grad['gradient_l2_after_clipping']]) + ' |\n'
    text += '\n' + details('Full configuration, masks, per-target losses, gradient traces and saved-weight checks', raw_json(r))
text += '## Earlier failed preparations\n\nBoth attempts made zero optimizer updates. The first was refused because an unfamiliar process occupied the GPU; it was left untouched. The second failed before optimization due to an iterator-handling error; the loader was fixed and the baseline rerun.\n\n' + ''.join(details(x['path'], raw_json(x['failure'])) for x in bundle['failed_attempts'])
write(SHORT / 'training-metrics.md', text)

text = '# Complete supplied sources and frozen rubric\n\n[Evidence index](README.md)\n\nS/PV.9214, 9 December 2022. Source fidelity means attribution to the actual statement; it does not independently establish the truth of every government assertion. Hypothetical recommendations and unknown future votes remain separate from recorded historical actions.\n\n'
for country, row in bundle['packs']['eight']['sources.json']['statements'].items():
    text += '## ' + country + '\n\n' + block(row['text'], 'source', country)
text += '## Original operational rubric\n\n' + raw_json(bundle['packs']['eight']['criteria.json'])
write(SHORT / 'sources-and-rubric.md', text)

write(MEETING / 'README.md', '''# Meeting-context / delegation experiment

[All experiments](../README.md)

The proposed task was **scenario + earlier meeting turns in chronological order + requested country/institution/role → authentic next speech**. This is separate from the assistant-written short-answer SFT experiment.

| Stage | Result |
|---|---|
| Four authentic UK/India targets, sanctions and climate; fresh 128-update fit | All four training speeches reproduce exactly; 20/20 fitting content units. |
| Two Ukraine development speeches | Both fail in raw and corrected native formats; reference NLL worsens after fitting. |
| Later source-conditioned context study; no new training | Full dossiers 12/18; attributed cards 15/18; cards + actual unedited model map 18/18, one provisional strict pass. |

**Context limitation:** full preceding history fit for sanctions. For climate/Ukraine it exceeded the fixed 6,144-token prompt allowance, so the declared fallback retained the immediately preceding complete speech plus scenario metadata. Some expected historical facts were absent. This was not a complete-history test of the original proposal. Invented policies/events and an extra fabricated speaker remain actual failures. Learned atomic role tokens were not trained.

- **[All four complete authentic SFT sequences](training.md)** — exact masked scenario/history prefix and supervised completion.
- **[All fourteen original outputs](continuation-answers.md)** — base controls, exact fitting outputs and failed development outputs, including original raw markers and thought traces.
- **[All eleven context-follow-up outputs](grounded-context.md)** — full dossiers, cards, actual reader map, both writers and shorter-budget regression.
- [Original authentic-speech result](../../SCENARIO_ROLE_CHECKPOINT_20261018.md)
- [Original context follow-up](../../GROUNDED_ROLE_CHECKPOINT_20261019.md)
- [Data/context policy and readiness](../../SCENARIO_ROLE_SFT_READINESS_20261017.md)

Same-assistant exposed development; independent review and broad persona/diplomatic/multi-agent/strong OOD gains remain unproved. All text below is preserved historical output; this GitHub publication launches no run. Research remains paused.
''')

train_path = 'research/scenario-role-sft-20261017-v1/pack/train.jsonl'
eval_path = 'research/scenario-role-sft-20261017-v1/pack/eval.jsonl'
train = load(train_path); held = load(eval_path)
pack = {x['id']: x for x in train + held}
page = MEETING / 'training.md'
text = '# Four complete authentic scenario/delegation SFT sequences\n\n[Evidence index](README.md)\n\nThe readable-marker sequence below was the actual fitting representation. Prefix and target header are masked; the full authentic completion plus existing record-end token is supervised. These are four targets repeated 32 times: 128 updates, not 128 unique examples.\n\n' + source_link(page, train_path, 'Original tokenized training pack') + '\n\n'
for row in train:
    assert sha(row['prefix'].encode()) == row['prefix_sha256']
    assert sha(row['body'].encode()) == row['target_sha256']
    assert row['completion'] == row['body'] + '<|im_end|>'
    text += '## ' + row['id'] + '\n\n'
    text += details('Complete masked scenario, chronological history and requested-role prefix', block(row['prefix'], 'prompt', 'scenario-training:' + row['id']))
    text += '**Complete supervised authentic target, including record-end marker:**\n\n' + block(row['completion'], 'target', 'scenario:' + row['id'])
    text += details('Original history-window provenance', raw_json(row['provenance']))
write(page, text)

page = MEETING / 'continuation-answers.md'
text = '# All fourteen authentic-continuation outputs\n\n[Evidence index](README.md)\n\nFull raw outputs are reproduced, including protocol markers and any visible thought text. Model assertions are not endorsed historical facts. Exact fitting recall and development results are shown separately. Original review records are linked for each arm.\n\n'
scenario_root = 'research/scenario-checkpoint-20261018-v1'
arms = [('base-sequence', 'Base: raw sequence', 'base-sequence-review-before-fit.json'),
        ('base-native', 'Base: original native wrapper', 'base-native-review.json'),
        ('base-native-boundary', 'Base: corrected native wrapper', 'base-native-boundary-review.json'),
        ('adapter-fitting', 'Adapter: all four fitting speeches', 'adapter-fitting-review.json'),
        ('adapter-held', 'Adapter: raw Ukraine development', 'adapter-held-review.json'),
        ('adapter-native-boundary', 'Adapter: corrected native Ukraine', 'adapter-native-boundary-review.json')]
for arm, label, review_name in arms:
    path = scenario_root + '/' + arm + '/responses.jsonl'
    outputs = load(path); review = load(scenario_root + '/' + review_name)
    assert INPUTS[path]['sha256'] == review['responses_sha256']
    native_inputs = load(scenario_root + '/' + arm + '/actual-inputs.json') if 'boundary' in arm else None
    text += '## ' + label + '\n\n' + source_link(page, path, 'Original responses') + ' · ' + source_link(page, scenario_root + '/' + review_name, 'Original complete review') + '\n\n'
    for output in outputs:
        c = pack[output['id']]
        text += '### ' + output['id'] + '\n\n'
        if native_inputs:
            inp = next(x for x in native_inputs if x['id'] == output['id'])
            prompt = messages(inp['messages'], arm + ':' + output['id'])
        elif arm == 'base-native':
            prompt = messages(c['native_messages'], arm + ':' + output['id'])
        else:
            prompt = block(c['prefix'], 'prompt', arm + ':' + output['id'])
        text += details('Full exact input text', prompt)
        text += block(output['output_raw'], 'answer', 'scenario:' + arm + ':' + output['id'])
        text += 'Generated tokens: **' + str(output['generated_tokens']) + '**. At cap: **' + str(output['at_cap']) + '**. Reference target NLL: **' + str(output.get('target_nll')) + '**.\n\n'
        original = next(x for x in review['cases'] if x['id'] == output['id'])
        text += details('Original case review, without regrading', raw_json(original))
write(page, text)

page = MEETING / 'grounded-context.md'
text = '# All eleven context-follow-up outputs\n\n[Evidence index](README.md)\n\nZero optimization updates. These are adaptive source-conditioned development tests using an explicitly specified coverage rubric, not a regrade of authentic speech reconstruction. Both the sources and model map are supplied to the writers. Original output, input and review records are linked.\n\n'
stages = [
    ('grounded-role-20261019-v1', 'runtime/base/responses.jsonl', 'Full earlier-country dossier: base, 12/18'),
    ('grounded-role-20261019-v1', 'runtime/adapter/responses.jsonl', 'Same full dossier: saved adapter, 12/18'),
    ('grounded-role-cards-20261019-v2', 'runtime/base/responses.jsonl', 'Attributed quote cards: base, 15/18'),
    ('grounded-role-pipeline-20261019-v1', 'runtime/reader-response.json', 'Actual unedited model reader map'),
    ('grounded-role-pipeline-20261019-v1', 'runtime/writer-responses.jsonl', 'Cards plus unedited map: base writers, 18/18; one provisional strict pass'),
    ('grounded-role-budget-20261019-v1', 'runtime/base/responses.jsonl', 'Smaller requested word target: base, 16/18; regression retained'),
]
grounded_records = 0
for folder, filename, label in stages:
    path = 'research/' + folder + '/' + filename
    value = load(path); outputs = value if isinstance(value, list) else [value]
    text += '## ' + label + '\n\n' + source_link(page, path, 'Original complete response record') + '\n\n'
    example_path = 'research/' + folder + '/examples.json'
    examples = load(example_path) if (ROOT / example_path).exists() else None
    review_path = str((Path(path).parent / ('inspection.json' if filename.endswith('/responses.jsonl') else 'reader-inspection.json' if filename.endswith('reader-response.json') else 'writer-inspection.json')).as_posix())
    text += source_link(page, review_path, 'Original complete review') + '\n\n'
    for output in outputs:
        grounded_records += 1
        key = folder + ':' + filename.replace('/', ':') + ':' + output['id']
        inp = output.get('messages')
        if inp is None:
            inp = next(x['messages'] for x in examples if x['id'] == output['id'])
        text += '### ' + output['id'] + '\n\n' + details('Full exact system/user input', messages(inp, 'grounded:' + key))
        text += block(output['output_raw'], 'answer', 'grounded:' + key)
        text += 'Generated tokens: **' + str(output['generated_tokens']) + '**. At cap: **' + str(output['at_cap']) + '**.\n\n'
assert grounded_records == 11
write(page, text)

for page, text in PAGES.items():
    assert len(text.encode()) < 500_000, str(page) + ' exceeds the chosen GitHub-readable size bound'
    page.parent.mkdir(parents=True, exist_ok=True)
    # The paths are dedicated generated documentation, never historical payloads.
    if page.exists():
        assert page.stat().st_nlink == 1
    page.write_text(text, encoding='utf-8')

parsed_blocks = {}
linked_files = []
for page, text in PAGES.items():
    for match in re.finditer(r'<!-- exact:([^:]+):([^\n]+) -->\n\n(.*?)\n\n<!-- /exact -->', text, re.S):
        key = match.group(1), match.group(2)
        assert key not in parsed_blocks
        lines = match.group(3).split('\n')
        assert all(line == '>' or line.startswith('> ') for line in lines)
        parsed_blocks[key] = html.unescape('\n'.join('' if line == '>' else line[2:] for line in lines))
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('https:', '#')):
            continue
        resolved = (page.parent / target.split('?', 1)[0].split('#', 1)[0]).resolve()
        linked_files.append(resolved)
        assert resolved.is_file() or resolved == DEST / 'github-export-verification.json', (str(page), target)
assert parsed_blocks == EXPECTED_BLOCKS
assert sum(k[0] == 'answer' for k in parsed_blocks) == 119
assert sum(k[0] == 'target' for k in parsed_blocks) == 12
all_content = '\n'.join(PAGES.values()) + offline.read_text()
for pattern in [r'hf_[A-Za-z0-9]{20,}', r'gh[pousr]_[A-Za-z0-9]{20,}', r'github_pat_[A-Za-z0-9_]{30,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----']:
    assert not re.search(pattern, all_content), 'Potential credential pattern in export'
receipt = {'status': 'github_readable_export_bytes_and_links_verified',
           'source_model_commit': bundle['source_commit'], 'new_model_calls': 0,
           'new_optimizer_updates': 0, 'research_goal_status': 'paused',
           'exact_short_answer_records': 94, 'exact_scenario_answer_records': 14,
           'exact_grounded_followup_records': 11, 'exact_training_targets': 12,
           'recorded_short_sft_optimizer_steps': 144,
           'full_text_blocks_round_trip_exact': len(parsed_blocks),
           'all_relative_file_links_resolve': True,
           'pages': {str(p.relative_to(ROOT)): {'bytes': p.stat().st_size, 'sha256': sha(p.read_bytes())} for p in PAGES},
           'input_files': INPUTS,
           'limits': 'Historical evidence export and byte checks; no new inference, optimization, regrading, independent review or OOD claim.'}
destination = DEST / 'github-export-verification.json'
if destination.exists():
    assert destination.stat().st_nlink == 1
destination.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
assert all(path.is_file() for path in linked_files)
print(json.dumps({k:receipt[k] for k in ['status', 'exact_short_answer_records', 'exact_scenario_answer_records', 'exact_grounded_followup_records', 'exact_training_targets', 'full_text_blocks_round_trip_exact']}, indent=2))
print(json.dumps({'markdown_pages': len(PAGES), 'markdown_bytes': sum(p.stat().st_size for p in PAGES), 'largest_page_bytes': max(p.stat().st_size for p in PAGES)}, indent=2))
