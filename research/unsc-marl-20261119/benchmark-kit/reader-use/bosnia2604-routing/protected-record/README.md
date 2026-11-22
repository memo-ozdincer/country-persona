# Protect the Council decision and draft the delegates' statements separately

The previous Bosnia Resolution 2604 replay showed two failures. The original adaptive draft invented an asset seizure. Clarifying the Council's procedural language removed that assertion, while the next draft lost the qualification it had recovered. This experiment supplies a verified, 53-word decision and asks the frozen Qwen3.5-4B writer to draft only the delegates' section in at most 65 words. A deterministic join places the unchanged decision above the unedited model body. Every arm reuses its original opening and supplemental notes. [Locked public passage and generation contract](protocol.json) · [Prior paired replay](../plain-anchor/README.md) · [Official resolution](https://digitallibrary.un.org/record/3946754/files/S_RES_2604_%282021%29-EN.pdf)

The decision provides 40 rubric points per arm. The four delegation criteria total 30 points. Before seeing the outputs, the review identifies 30 available delegation points for the adaptive path, 23 each for the fixed UK and fixed Russia paths, and seven strict points for pooled solo. This counts a criterion in the input only when the relevant note states the required position and qualification. The strict solo assessment leaves the 5+2 closure link and the specific Russian procedural objection uncredited. [Available input evidence](input-spans.json)

| Drafting path | Original /70 and release | Clarified /70 and release | Protected /70 and release | Strict note points retained |
| --- | --- | --- | --- | --- |
| Adaptive follow-up | 62 · Fail | 48 · Pass | **70 · Pass** | 30/30 |
| Fixed UK follow-up | 36 · Pass | 36 · Fail | 63 · Pass | 23/23 |
| Fixed Russia follow-up | 63 · Pass | 56 · Pass | 55 · Fail | 15/23 |
| Pooled solo | 28 · Uncertain | 35 · Uncertain | 40 · Uncertain | 0/7 |

The adaptive section retains both the earlier 5+2 closure condition and the newly retrieved condition on executive powers. It also retains both Russian criteria. The fixed UK section retains every criterion supported by its own notes, including the closure condition, and omits the qualification its supplement failed to retrieve. The fixed Russia section changes the actor who urged completing the agenda from the UK delegate to Christian Schmidt, which fails release independently of coverage. The pooled section leaves the basis for closure and vacancy unclear and drops the internal scope of Russian dialogue. All four body generations end naturally within the requested 65 words. Only the fixed UK body explicitly names both delegations. The adaptive draft uses identifiable speaker names, which the original factual rubric accepts. Explicit delegation labeling therefore remains a format gap. [Exact-span marks](marks.json) · [Scores and format diagnostics](results.json) · [Unedited composited records](assembled-records.json)

## Change whether the follow-up contains the qualification

Remove “if needed” from the adaptive supplement and add it to the fixed UK supplement in a paired intervention. The original and edited contexts have the same openings, protected decision, writer instruction and generation budget. In the adaptive arm the executive-powers criterion changes from met to unmet and delegate coverage from 30 to 23. In the fixed UK arm the criterion changes from unmet to met and coverage from 23 to 30. The other three delegation criteria and release are retained in both. This isolates a seven-point effect of the qualification under this writing interface. The fixed UK addition is a diagnostic edit of its note, and is excluded from the policy comparison. [Locked edits](qualification-swap/protocol.json) · [Spans and outcomes](qualification-swap/marks.json) · [Replayed effects](qualification-swap/results.json)

The experiment verifies one instance in which a follow-up changed a final-record criterion after public facts were protected. The release advantage is specific to the replayed states and the writer contract. Four primary body generations and two edited-note generations use a single model and same-assistant assessment on an exposed case. The 40 public decision points are supplied, so between-arm gains under the protected condition should be read on the 30-point delegation scale. The design protects public wording and still needs source-attribution guards for the generated section.

## Replay

Use the local Qwen inference environment from this directory.

```bash
export PYTHONDONTWRITEBYTECODE=1
python score_protected.py score | cmp results.json
python score_protected.py records | cmp assembled-records.json
python qualification-swap/score_swap.py score | cmp qualification-swap/results.json
```

The audits check frozen input pins, the archived notes and paired edits, tokenization and exact output decoding, the deterministic join, and credited or adverse spans.
