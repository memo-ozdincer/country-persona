# Transfer to the 2017 Jerusalem docket

The test uses Egypt's draft S/2017/1060. The Council considered it at S/PV.8139 on 18 December 2017. The draft received 14 votes in favour and one against, with the United States casting the negative vote. The Council did not adopt it. The native UNBench draft and the UNSC-Bench roll call are pinned in `accession.json`. The source packets paraphrase operative paragraph 1 and the explanations from the United States, the United Kingdom and Sweden. [Draft](https://digitallibrary.un.org/record/1326934/files/S_2017_1060-EN.pdf) · [Council record](https://digitallibrary.un.org/record/1327435/files/S_PV.8139-EN.pdf)

This docket was absent from the Gaza receiver fit. It shares the Council agenda with that prior study and reuses the same four-topic, two-annex routing channel. The evidence distributions are simulated, using the ten archived Gaza index priors. Topic order is tested exhaustively across 24 mappings. These are sensitivity conditions within one new historical docket.

## Conditions

1. Give the responder one probe per topic. One language desk is instructed to request only for a draft provision. The other is instructed to request only for a national explanation. Calibration and mission prompts paraphrase the same underlying assignment. The request channel permits one fixed generic question or deliberate silence. A malformed completion is reported separately. The receiver sees a delivered bit, with the existing independent loss model. It receives no hidden assignment text.
2. Freeze the Gaza-trained receiver. Compare it with the original frozen receiver, a blind decoder and exact decoding that shares the Gaza development prior but sees the announced Jerusalem receipt values. The prior-informed oracle observes the partner and evaluation prior. Announced receipt values are 42 without a matching backup and 70 with one for every focus. The Gaza study had one 63-point focus. The transferred decoder is not refit to the new rubric.
3. The factored sender uses the model to identify the requested source category before applying the declared desk rule. This runs both protocols from one category decision per assignment. Each phase and topic retains its own model call. Nothing in the classifier states the reference category.
4. The extractive reference copies only the focal slip and the matched backup when available. The final-record trial also runs the identical Gaza writer prompt and token cap on the eight possible receipt conditions. This bank is reused for every policy. The writer has the supplied sources and rubric. A structurally unrelated backup is withheld before writing. Same-assistant exact-span annotations distinguish raw and release credit.

## Reproduction

Use the original Qwen CPU environment on this directory. The following replay commands need the locally pinned tokenizer for the recorded model traces and the existing data environment for the accession.

```bash
PYTHONPATH=../../../../src "$DATA_PY" check.py
"$MODEL_PY" transfer.py
"$MODEL_PY" language_partner.py score language-evidence
"$MODEL_PY" factored_partner.py score factored-evidence
"$MODEL_PY" transfer.py --language-actions factored-evidence/actions.json
"$MODEL_PY" record_writer.py score record-evidence
"$MODEL_PY" compare_transfer.py
```

Routing scores charge the declared signal and reply fees and amortize a four-probe setup over eight records. The language runs preserve actual token lengths separately from these benchmark-unit costs. Neither sender run updates model weights.

## Reward-aware receiver follow-up

The original receiver was trained for Gaza's receipt values. Treat the new docket's point values as public inputs. The learned policy adds the disclosed log marginal credit to its local evidence score. It trains on synthetic reward permutations with the Gaza shared reward and uses frozen Jerusalem messages and records only during evaluation. A separate model-based comparator estimates a probe likelihood and an inventory-conditioned distribution from finite simulated training traces. The component swap uses the declared development inventory prior, not the evaluation prior. The random weight audit reports expected lost credit and exact action agreement separately to expose near ties.

```bash
"$MODEL_PY" reward_receiver.py
"$MODEL_PY" reward_replay.py
"$MODEL_PY" estimate_receiver.py
"$MODEL_PY" probability_audit.py
"$MODEL_PY" reward_stress.py
```

## Fresh live episodes

The frozen plan selects four intact-delivery worlds. Each arm writes a new note from its selected source and produces a fresh chair supplement. Two worlds have the same responder inventory and silence with different focal slips. Two have a delivered request. The calibrated arm uses the declared development inventory distribution, learned signal likelihood and current rubric. The uncalibrated arm uses the archived receiver. Metadata verifies topic relevance at the chair's evidence gate. Notes and outputs remain unedited. The exact blind and known-sender controls reuse the observed branch for their chosen source. The both-inventories control is an upper bound on routing information.

The only writer intervention removes the public paragraph from the writer input. The protected paragraph is still attached unchanged in the final record. Source IDs, message budget and the actual generated note all stay fixed. The score artifact includes the common paragraph, focal slip, transmitted note and supplement with raw credit and strict release. The reviews use exact spans and were done by the same assistant. The blinded packet and separate analysis key provide a reproducible independent-review handoff.

```bash
"$MODEL_PY" live_protocol.py plan
"$MODEL_PY" live_protocol.py verify live-evidence
"$MODEL_PY" live_review.py score live-evidence
"$MODEL_PY" slip_writer.py score slip-evidence
```

## Extractive chair

`extractive_chair.py` compares an exact-copy chair with the two original free-form chair variants. It uses four actual matching notes and four single-sentence authored foils. No additional backup can enter the final record. The model sees the archived source to check the note, returns a list of note sentence IDs, and supplies no new prose. An invalid list falls back to the focal slip. Each extracted span remains traceable to the note after the declared placeholder removal. Records with no matching note use the slip directly. The copy-only design limits what the chair can add. The selector still has to reject unsupported material introduced by the responder.

`extractive_transfer.py` runs the same selector on eight actual Gaza writer outputs, including outputs with previously reviewed guard errors. It records retained errors, exact coverage witnesses, invalid selections and overlong assemblies. Its reference labels use same-assistant review. `verified_relay.py` gives a separate strongest copy control for the Jerusalem live choices. The responder sends the approved archived passage verbatim, under the same 65-word limit. The chair checks source membership, topic and exact bytes against the pinned registry before adding it to the protected slip. No new LLM calls enter this control.

```bash
"$MODEL_PY" extractive_chair.py score extractive-evidence
"$MODEL_PY" extractive_transfer.py score extractive-transfer-evidence
"$MODEL_PY" verified_relay.py
```

## Full-inventory relay and probe drift

The population replay authenticates every legal verified-relay receipt. It integrates declared packet losses and costs instead of restricting evaluation to the four intact live cases. The score panel compares the estimated calibrated receiver, exact decoding with and without probes, the older frozen receivers and an informed silent oracle. A one-probe script receives stronger information about the sender family. Fresh mission-style public probes test the statement desk that previously drifted between probe and mission. Their scores reuse the earlier observed mission actions and do not claim new live final records.

```bash
"$MODEL_PY" relay_population.py
"$MODEL_PY" two_family_probe.py
"$MODEL_PY" phase_probe.py score phase-probe-evidence
```
