# Decision-case post-training format (candidate v1)

The first projection covers China and Germany on two shared UN General Assembly decisions (2 March and 12 October 2022). It yields four country–event views and eight **quarantined** conversational prompt/completion rows. It is a format and review artifact, not a new training set. No row is admitted to training or fresh evaluation. The same two events cannot support claims about a broad national persona.

Run `python scripts/build_decision_posttraining.py` after restoring the private source snapshot. This writes `data/prepared/decision-posttraining-20260916/candidates.jsonl` and a same-order metadata sidecar. The public, project-authored projection is `explorer/decision-showcase.json`; it omits original third-party document bodies and retains primary-source links. The builder fails if a case loses its verified roll call or quarantine flags.

Each case supplies two candidate tasks:

| Task | Supplied to model | Assistant target | Review check |
|---|---|---|---|
| Recorded vote reconstruction | Country, date, draft symbol and project-authored proposal summary | Exact final vote label | Match verified roll call; avoid treating this as causal reasoning or a counterfactual decision |
| Evidence-grounded decision report | Same draft context, observed vote, statement status and project-authored statement summary (if acquired) | Short report separating action, attributed statement and missing rationale | Correct vote and statement type; no invented motive or agreement condition |

Both use TRL's conversational `prompt`/`completion` shape, with `enable_thinking: false` for the selected Qwen3-8B non-thinking mode. Prompt and completion are separate so the existing trainer can mask prompt tokens and supervise only the assistant completion. The candidate files are not fed to a training job by this builder.

The March China text is labeled **explanation of vote**. The October China text is labeled **pre-vote statement** and never cast as an explanation of the abstention. Germany's explanation is **not acquired** in these records; the report teaches explicit uncertainty, not a guessed rationale. The statement summaries are project-authored paraphrases, not original transcripts. The vote task withholds the observed vote and all statements from its prompt. The report task supplies them because its objective is evidence-faithful reporting, not prediction.

Each task has a sidecar containing source URLs, source case ID, review status, event group and admission flags. Both countries' views of a UN decision share a group. A future train/evaluation split must keep the whole event—and its translations and derived formats—together. These exposed historical cases also risk pretraining contamination. Before actual training, acquire broader issues and time periods; independently review draft, roll call and attributed statement spans; evaluate a base-model baseline; and validate the exact Qwen3 chat-template boundary and token lengths. Do not use historical vote accuracy alone as a reward for diplomatic quality or future decisions.

Method references: [TRL conversational prompt/completion and completion-only loss](https://huggingface.co/docs/trl/sft_trainer#expected-dataset-type-and-format), [Qwen3 model card and thinking-mode controls](https://huggingface.co/Qwen/Qwen3-8B), [CheckList behavioral evaluation](https://aclanthology.org/2020.acl-main.442/). The format follows the library conventions; task validity and persona generalization remain empirical questions.
