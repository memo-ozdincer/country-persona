"""Audit one local UNBench release and compute training-only empirical baselines.

No model, network request or downloaded notebook is executed. Exact-text checks
are deliberately not advertised as semantic-family or contamination clearance.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path

from country_persona.action_eval import VOTES, classification_metrics
from country_persona.io import digest, sha256, write_json

TARGETS = ("CHINA", "GERMANY", "FRANCE", "UNITED KINGDOM", "INDIA", "BRAZIL")
CORE = ("task1_train.json", "task1_test.json", "task2_train_author.csv", "task2_test_author.csv",
        "task3_train.json", "task3_test.json", "run_task1.ipynb", "run_task2.ipynb", "run_task3.ipynb")


def text_hash(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Empty/non-text draft")
    return digest(" ".join(value.split()))


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def draft_index(root, directory):
    by_folder, by_text = defaultdict(list), defaultdict(list)
    for path in sorted((root / directory).glob("*/*EN.json")):
        data = json.loads(path.read_text())
        item = {"path": str(path.relative_to(root)), "file_sha256": sha256(path),
                "document_id": data.get("ID"), "date": data.get("Date"),
                "text_sha256": text_hash(data["Content"])}
        by_folder[path.parent.name].append(item)
        by_text[item["text_sha256"]].append(item)
    return by_folder, by_text


def date_iso(value):
    try:
        return datetime.strptime(value.strip(), "%d %B %Y").date().isoformat()
    except (ValueError, AttributeError):
        return None


def joins(rows, by_folder, id_key, date_key):
    issues, texts, documents, files = [], set(), set(), {}
    for row in rows:
        key = str(row[id_key])
        matches = by_folder.get(key, [])
        if len(matches) != 1:
            issues.append({"event_id": key, "kind": "nonunique_join", "matches": len(matches)})
            continue
        item = matches[0]
        texts.add(item["text_sha256"])
        documents.add(item["document_id"])
        files[item["path"]] = item["file_sha256"]
        draft_date = date_iso(item["date"])
        if draft_date is None or draft_date > row[date_key]:
            issues.append({"event_id": key, "kind": "date_unparsed" if draft_date is None else "draft_after_event",
                           "event_date": row[date_key], "draft_date": item["date"]})
    unique_issues = {digest(x): x for x in issues}
    return {"issues": list(unique_issues.values()), "unique_texts": len(texts),
            "unique_documents": len(documents), "joined_file_manifest_sha256": digest(files)}, texts, documents


def vote_summary(rows):
    dates = [r["Date"] for r in rows]
    pairs = Counter((r["Original_id"], r["Country"]) for r in rows)
    groups = Counter(r["Original_id"] for r in rows)
    return {"rows": len(rows), "events": len(groups), "labels": dict(Counter(r["Voting"] for r in rows)),
            "countries": len({r["Country"] for r in rows}), "first_date": min(dates), "last_date": max(dates),
            "rows_per_event": dict(Counter(groups.values())), "duplicate_country_event_pairs": sum(v - 1 for v in pairs.values()),
            "target_countries": {c: dict(Counter(r["Voting"] for r in rows if r["Country"] == c)) for c in TARGETS}}


def empirical_baselines(train, test):
    # Non-Voting is neither N nor A. Keep the exclusions explicit in the output.
    legal_train = [r for r in train if r["Voting"] in VOTES]
    legal_test = [r for r in test if r["Voting"] in VOTES]
    global_counts = Counter(r["Voting"] for r in legal_train)
    country_counts = defaultdict(Counter)
    for row in legal_train:
        country_counts[row["Country"]][row["Voting"]] += 1
    truth = [r["Voting"] for r in legal_test]
    result = {"status": "empirical_baselines_not_model_results", "smoothing_alpha": 1,
              "fit_split": "official_train_only", "evaluation_split": "official_test",
              "excluded_train": [r for r in train if r["Voting"] not in VOTES],
              "excluded_test": [r for r in test if r["Voting"] not in VOTES],
              "unseen_test_countries": sorted({r["Country"] for r in legal_test} - set(country_counts)), "arms": {}}
    for name in ("always_yes", "global_train_prior", "country_train_prior"):
        probabilities = []
        for row in legal_test:
            counts = country_counts.get(row["Country"], global_counts) if name == "country_train_prior" else global_counts
            probabilities.append({label: (counts[label] + 1) / (sum(counts.values()) + len(VOTES)) for label in VOTES})
        predictions = ["Y"] * len(truth) if name == "always_yes" else [max(p, key=p.get) for p in probabilities]
        scored_probs = None if name == "always_yes" else probabilities
        overall = classification_metrics(truth, predictions, probabilities=scored_probs)
        by_country = {}
        for country in TARGETS:
            indexes = [i for i, r in enumerate(legal_test) if r["Country"] == country]
            if indexes:
                by_country[country] = classification_metrics([truth[i] for i in indexes], [predictions[i] for i in indexes],
                    probabilities=[probabilities[i] for i in indexes] if scored_probs else None)
        result["arms"][name] = {"overall": overall, "target_countries": by_country}
    return result


def audit(root):
    all_folders, all_texts = draft_index(root, "all_drafts")
    adopted_folders, _ = draft_index(root, "drafts_adopted")
    result = {"schema_version": 1, "scope": "locally_acquired_author_release",
              "source_files_sha256": {name: sha256(root / name) for name in CORE},
              "english_drafts": {"all_drafts": sum(map(len, all_folders.values())),
                                 "drafts_adopted": sum(map(len, adopted_folders.values()))},
              "limitations": ["Exact whitespace-normalized text and document-ID checks do not identify all related event families.",
                              "A document date is not proof of pre-vote public availability; timestamps require review.",
                              "Archive metadata and labels have not been independently verified against UN primary records.",
                              "Folder IDs are directory-local: all_drafts and drafts_adopted have different namespaces.",
                              "Examining label distributions does not establish a sealed final test or eliminate model pretraining contamination."]}
    task1, task2, task3, event_sets, text_sets, document_sets = {}, {}, {}, {}, {}, {}
    for split in ("train", "test"):
        rows = json.loads((root / f"task1_{split}.json").read_text())
        joined, texts, docs = joins(rows, all_folders, "folder_id", "date")
        task1[split] = {"rows": len(rows), "events": len({r["folder_id"] for r in rows}),
                        "first_date": min(r["date"] for r in rows), "last_date": max(r["date"] for r in rows), "join": joined}
        event_sets[f"task1_{split}"] = {str(r["folder_id"]) for r in rows}
        text_sets[f"task1_{split}"] = texts
        document_sets[f"task1_{split}"] = docs
        rows = read_csv(root / f"task2_{split}_author.csv")
        joined, texts, docs = joins(rows, adopted_folders, "Original_id", "Date")
        task2[split] = {**vote_summary(rows), "join": joined,
                        "nonstandard_labels": [r for r in rows if r["Voting"] not in VOTES]}
        event_sets[f"task2_{split}"] = {r["Original_id"] for r in rows}
        text_sets[f"task2_{split}"] = texts
        document_sets[f"task2_{split}"] = docs
        data = json.loads((root / f"task3_{split}.json").read_text())
        if len(data["drafts"]) != len(data["labels"]):
            raise ValueError("Task3 label/text alignment failure")
        hashes = [text_hash(x) for x in data["drafts"]]
        label_sets = defaultdict(set)
        for key, label in zip(hashes, data["labels"]):
            label_sets[key].add(str(label))
        nonunique = [i for i, h in enumerate(hashes) if len(all_texts.get(h, [])) != 1]
        matches = [all_texts[h][0] for h in hashes if len(all_texts.get(h, [])) == 1]
        dates = [date_iso(m["date"]) for m in matches]
        valid_dates = [d for d in dates if d is not None]
        task3[split] = {"rows": len(hashes), "labels": dict(Counter(str(x) for x in data["labels"])),
                        "unique_texts": len(set(hashes)), "nonunique_draft_match_row_indexes": nonunique,
                        "conflicting_labels_for_same_text": [h for h, labels in label_sets.items() if len(labels) > 1],
                        "matched_draft_date_range": [min(valid_dates), max(valid_dates)] if valid_dates else None,
                        "unparsed_matched_dates": len(dates) - len(valid_dates)}
        text_sets[f"task3_{split}"] = set(hashes)
        document_sets[f"task3_{split}"] = {m["document_id"] for m in matches}
    pairs = [(a, b) for i, a in enumerate(text_sets) for b in list(text_sets)[i + 1:]]
    result.update(task1=task1, task2=task2, task3=task3,
        within_task_event_overlap={t: len(event_sets[f"{t}_train"] & event_sets[f"{t}_test"]) for t in ("task1", "task2")},
        exact_overlap=[{"left": a, "right": b, "shared_texts": len(text_sets[a] & text_sets[b]),
                        "shared_document_ids": len(document_sets[a] & document_sets[b])} for a, b in pairs])
    train = read_csv(root / "task2_train_author.csv")
    test = read_csv(root / "task2_test_author.csv")
    result["task2_test_negative_rows"] = [r for r in test if r["Voting"] == "N"]
    result["notebook_reproduction_flags"] = {
        "task2": ["Invalid outputs replaced with random.choice(valid_votes).", "Prompt uses country and Content, omitting Date and Authors.",
                  "AUC/AP calculated from binarized hard labels; metric class set inferred from observed labels and predictions."],
        "task3": ["Invalid outputs replaced with random 0/1.", "Labels and predictions flipped before binary F1: non-adoption is positive.",
                  "ROC/PR AUC calculated from hard labels; ROC exception returns zero."],
        "status": "Manually inspected notebook source, never executed; paper table discrepancies remain unresolved."}
    baselines = empirical_baselines(train, test)
    tr3 = json.loads((root / "task3_train.json").read_text())
    te3 = json.loads((root / "task3_test.json").read_text())
    counts = Counter(str(y) for y in tr3["labels"])
    prior = {k: (counts[k] + 1) / (len(tr3["labels"]) + 2) for k in ("0", "1")}
    baselines["task3_train_prior"] = classification_metrics([str(y) for y in te3["labels"]],
        [max(prior, key=prior.get)] * len(te3["labels"]), labels=("0", "1"), probabilities=[prior] * len(te3["labels"]))
    return result, baselines


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    report, baselines = audit(args.root)
    write_json(args.output_dir / "unbench-audit.json", report)
    write_json(args.output_dir / "empirical-baselines.json", baselines)
    print(json.dumps({"task2_test": report["task2"]["test"], "always_yes_accuracy": baselines["arms"]["always_yes"]["overall"]["accuracy"]}, indent=2))
