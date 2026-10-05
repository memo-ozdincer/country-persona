"""Summarize the six saved arms without treating repeated questions as independent tests."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


def rows(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads((args.root / 'configs/posttraining/open-character-humor-20261004.json').read_text())
    run = args.root / config['run']
    folders = ['base-robustness', 'prompted-base-robustness', 'author-robustness',
               'reproduction-dpo-robustness', 'reproduction-full-robustness']
    arms, scores = {}, {}
    for folder in folders:
        source = run / folder
        summary = json.loads((source / 'classifier-summary.json').read_text())
        for arm, metrics in summary['metrics'].items():
            outputs = rows(source / (arm + '.jsonl'))
            predictions = json.loads((source / (arm + '.scores.json')).read_text())
            if len(outputs) != 4500 or len(predictions) != 4500:
                raise ValueError('Incomplete published-protocol arm: ' + arm)
            scores[arm] = {x['id']: x for x in predictions}
            arms[arm] = {'metrics': metrics, 'generations': len(outputs),
                         'output_caps': sum(x['finish_reason'] == 'length' for x in outputs)}
    comparisons = {}
    for treatment, control in [('reproduction-dpo', 'base'), ('reproduction-dpo', 'prompted-base'),
            ('reproduction-full-sequential', 'base'), ('reproduction-full-sequential', 'prompted-base'),
            ('reproduction-full-sequential', 'reproduction-dpo'),
            ('reproduction-dpo', 'author-dpo'), ('reproduction-full-sequential', 'author-full-sequential')]:
        if scores[treatment].keys() != scores[control].keys():
            raise ValueError('Unpaired comparison')
        result = {}
        for variant in arms[treatment]['metrics']:
            ids = [key for key, value in scores[treatment].items() if str(value['variant']) == variant]
            gained = sum(scores[treatment][key]['prediction'] == 'humor' and
                         scores[control][key]['prediction'] != 'humor' for key in ids)
            lost = sum(scores[treatment][key]['prediction'] != 'humor' and
                       scores[control][key]['prediction'] == 'humor' for key in ids)
            result[variant] = {'questions': len(ids), 'gained_humor_labels': gained,
                               'lost_humor_labels': lost, 'net_percentage_points': (gained - lost) / 5}
        comparisons[treatment + '_versus_' + control] = result
    fits = {stage: json.loads((run / (stage + '-fit/fit.json')).read_text()) for stage in ['dpo', 'sft']}
    result = {'status': 'six_arm_published_protocol_comparison_completed',
              'created_utc': datetime.now(timezone.utc).isoformat(), 'paper': config['paper'],
              'run': config['run'], 'model': config['model'], 'persona': 'humor',
              'arms': arms, 'paired_classifier_label_comparisons': comparisons,
              'unique_questions': 500, 'variants_per_question': 9, 'full_generations': 27000,
              'additional_pilot_generations': 24,
              'optimizer_steps': {stage: fit['successful_optimizer_steps'] for stage, fit in fits.items()},
              'gpu': 'NVIDIA RTX PRO 6000 Blackwell Server Edition',
              'training_seconds': {stage: fit['elapsed_seconds'] for stage, fit in fits.items()},
              'peak_allocated_gpu_gib': {stage: fit['peak_allocated_gpu_gib'] for stage, fit in fits.items()},
              'scope': 'One-persona classifier recognition and style-removal robustness; no independent semantic-quality, country-policy or multi-agent claim.',
              'dependence': 'The released classifier was trained on default generations for the same first 500 questions. Nine variants repeat each question; no independent-sample significance claim.',
              'fidelity': 'Exact released raw records and original training recipes; explicitly disclosed runtime, hardware, shuffle, seed and launch differences. Qualitative reproduction, not a bitwise or eleven-persona macro-F1 replication.',
              'historical_aurora_qwen35_optimizer_steps_unchanged': 142,
              'next_fit_prepared': False}
    if args.output.exists():
        raise ValueError('Use a fresh measured receipt')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'full_generations': 27000,
                      'reference_optimizer_steps': sum(result['optimizer_steps'].values())}))


if __name__ == '__main__':
    main()
