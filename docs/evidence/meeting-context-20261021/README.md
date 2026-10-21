# SFT Trial 4: meeting context → authentic speech

[All experiments](../README.md)

The proposed task was **scenario + earlier meeting turns in chronological order + requested country/institution/role → authentic next speech**. This is separate from the assistant-written short-answer SFT experiment.

**[OPEN THE GENERATED MODEL ANSWERS — outputs only](model-outputs.md)** · [What our evaluations measured](../EVALUATION_GUIDE.md). The training page contains supplied supervision, not model-generated replies.

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
