# Checked-decision writer comparison

This is a four-response follow-up to the Syria language baseline. Each certified final matches one earlier solo or peer final. The full dialogue submissions, public dossier, final instruction and system message are unchanged. The new input appends one `compatibility_check` field with a status, the options jointly compatible, and the options excluded by at least one delegate. It explicitly limits the status to the fictional workshop and distinguishes admissibility from unconditional assent. The state is compiled from the quote-validated disclosures in the original generated submissions. The known private reference is used only to audit the result.

Both runs use frozen local Qwen3.5-4B in BF16 with SDPA, CPU, left-padded batches of four, greedy native chat with thinking disabled, and the same 240-token cap per final. The benchmark still requires at most 130 words, correct historical ownership and a clear authority boundary. All upstream outputs are reused.

The launch metadata keyed files by basename so the two `run.py` entries collided. The retained entry identifies the parent script. A separate [lock receipt](runner-lock.json) records the certified runner hash and verified command identity while the process was live. The verifier checks both files.

## Results

| Case and arm | Exact decision before → after | Rubric /70 before → after | Final words before → after | Guard before → after |
|---|---|---:|---:|---|
| Overlap, solo submissions | UNRESOLVED → B | 14 → 56 | 120 → 140 | Clear → clear |
| Overlap, peer submissions | B → B | 56 → 70 | 139 → 151 | Uncertain → clear |
| Impasse, solo submissions | UNRESOLVED → UNRESOLVED | 42 → 28 | 128 → 157 | Clear → clear |
| Impasse, peer submissions | UNRESOLVED → IMPASSE | 28 → 42 | 151 → 137 | Failed → clear |

The exact decision line improves from 1/4 to 3/4. All four new memos exceed the 130-word limit, so the complete contract remains 0/4. All four end at EOS within the unchanged 240-token cap. The field adds 79 input tokens on overlap and 81 on impasse. The peer overlap memo retains the four historical vote labels and meets all five semantic criteria. It explicitly bounds the jointly compatible package to hypothetical workshop positions.

The solo impasse memo still says unresolved and incorrectly claims that the check found no verified incompatibility. The peer impasse memo uses the right heading and drops the earlier invented UK opposition. It then writes that neither role accepts any package, although each role accepts two and their sets are disjoint. That is a substantive workshop reasoning error under the open-issues and positions criteria. The critical guard clears because the memo asserts no invented official vote or binding act. The distinction between a correct label and an internally consistent explanation matters here.

The same assistant designed and reviewed the pilot. The new finals were presented in an opaque review deck before the arm map was opened. This is an intervention on four exposed writer inputs, with no fresh family, independent adjudication, or optimizer updates. [Mechanical replay](evidence/review/mechanical.json) · [Rubric transitions](evidence/review/comparison.json) · [Raw transcripts](evidence/transcript.jsonl)

For a MARL environment, use a structured decision computed from actual role disclosures as the outcome measure. Score the explainer against the source and compatibility facts separately. A future writer can receive an independently fixed decision field and a dedicated body budget. Rewarding overlap detection alone would miss the claim that neither actor could accept anything.
