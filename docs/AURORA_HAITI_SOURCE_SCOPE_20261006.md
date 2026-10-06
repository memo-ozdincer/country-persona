# Own-country context improves attribution; transfer remains incomplete

The 6 October Haiti source-scope diagnostic completed four new answers and zero optimizer updates. Removing only the other country's full speech improves the saved 288-step adapter from 11 met +4 unratable/28 content units to 14 met/28. Its universal source checks improve from 2 met +2 unratable/8 to 8 met/8. Both strict passes still fail. Base coverage falls from 13 met +1 unratable/28 to 10 met +1 unratable/28. All four new outputs were read completely; none hit the generation cap.

This supports using separate national context to reduce some attribution failures. It also exposes continuing omissions and a UK answer that imports themes from the WPS fitting task into Haiti. The next useful training question is whether diverse, source-complete single-country supervision generalizes across policy families, starting from fresh base weights to avoid inherited multi-country memo patterns. No next pack, fit, queue or sweep is prepared.

## What changed

Two frozen raw Haiti requests from the previous conditional India checkpoint are retained, including their system messages, hypothetical implementation note X, questions, 300-word limit and exact grading criteria. Only the other country's complete speech and one separator are deleted. Both base and saved conditional India adapter receive the same new inputs. Brazil's input is 1096 tokens rather than 1446; the UK's is 651 rather than 1448. Source scope and input length change together. No checked plan is added, and no weights are changed.

The scenario still includes a colleague's hypothetical claim about both countries' votes. It does not require the model to invent absent peer details; all fourteen own-country criteria remain assessable from the retained national source and scenario. Brazil's primary national-capacity boundary and original UK/Brazil speeches were checked in the previous checkpoint. This turn rereads both complete normalized speeches, both complete new requests, all source/application criteria and four old matching base/adapter outputs. Shared text is read once and its exact inclusion is verified. The original PDF/span audit and source bytes remain preserved; this turn does not claim another visual PDF audit.

The pack is frozen before calls. Two base answers are read and reviewed before the adapter launch; both adapter answers are then read and reviewed. One unblinded assistant performs the planning and annotation. Existing primitive grades remain unchanged. This is exposed development on one event, not independent review, sealed OOD, native vote prediction or persona/multi-agent improvement.

## Measured answers

Counts below require the frozen compound meanings; partial meanings are recorded in annotation reasons. Strict pass additionally requires every universal check, no cap and at most 300 words.

| Weights / context | Brazil met + unratable /14 | UK met + unratable /14 | Universal met + unratable /8 | Strict passes /2 |
|---|---:|---:|---:|---:|
| Base, both speeches |7 +1|6|0 +4|0|
| Base, own speech |3 +1|7|0 +4|0|
| Adapter288, both speeches |5 +2|6 +2|2 +2|0|
| Adapter288, own speech |7|7|8|0|

The new base Brazil answer preserves coordinated efforts, structural causes and political/socioeconomic work, but omits institutional detail within the compound criterion, urgent humanitarian access, arms measures and contribution willingness. Its 301 words exceed the limit by one. Solidarity conditionality and Council-mandate scope remain ambiguous. The new base UK answer removes the direct Brazilian aid quotation, but adds a "temporary" Mission characterization absent from the supplied speech and presents institutional prerequisites as an explicit UK position. These are bounded-source judgments; a claim might be supported elsewhere without being supported by this packet.

The new adapter Brazil answer no longer assigns X and the future vote to an unsupported country or chair. It gives immediate verified relief, parallel Haitian-owned reconstruction and a competing immediate-security cost. Contribution consideration, complete arms embargo/disarmament, law/sovereignty qualifications and other source details are still missing.

The new adapter UK answer preserves police support, the vote boundary and immediate relief. It introduces consent-based sexual/reproductive health, birth registration, investigative integrity, confidential victim reporting and withdrawal options. These echo its WPS fitting themes. They are labeled analytical proposals, so they are not automatically graded as invented official UK commitments. Its second operational step and competing cost do not adequately address the Haiti implementation question, and several source details remain omitted. The raw spelling "CARICOT" is preserved; the contextual CARICOM reference is treated as recognizable under the existing equivalent-meaning rule. No text is silently corrected.

## Runtime and decision

All four generations use the same pinned Qwen/Qwen3.5-4B revision, native thinking disabled, greedy 2048-token allowance, Torch2.8.0+cu128/Transformers5.17.0/TRL1.14.1/PEFT0.21.1 and the same generation helper as the matching historical controls. Exact hardware: NVIDIA RTX PRO 6000 Blackwell Server Edition. The saved adapter has 288 branch updates; cumulative Aurora Qwen3.5 remains 1246 and the separate Qwen2.5 reproduction remains 582.

The next candidate is one bounded fresh-base chosen-only fit with hand-audited complete single-country responses spanning several already audited policy families. Freeze a separate family and strong base-plus-plan controls before any optimization, preserve conditional authority distinctions, inspect one fit before expanding. This tests whether the pipeline can transfer a common national-source/application structure rather than only reproduce complete fitting texts. It changes data coverage, response scope and training history together; it would not isolate a single cause. Target count and budget are to be chosen after the data audit, not queued now.

Portable replay verifies primary source spans/normalization/hashes, exact source deletion, unchanged criteria, native prompt/output token rendering, matched protocol/hardware, adapter bytes, inspection continuity and stored review arithmetic. Both newly owned GPU identities exited naturally; unfamiliar processes were not changed. Replay establishes software and provenance consistency, not independent semantic validity. There are no new fitted targets or training results in this diagnostic.

Evidence: [preparation](../reports/haiti-source-scope-preparation-20261006.json), [measured ownership receipt](../reports/haiti-source-scope-checkpoint-20261006.json), [portable replay](../reports/haiti-source-scope-replay-20261006.json). Pack: `data/prepared/haiti-source-scope-20261006-v1`. Actual runs: `runs/aurora-haiti-source-scope-{base,adapter}-20261006-v1`. The previous [conditional India result](AURORA_CONDITIONAL_INDIA_20261006.md), all original sources and all earlier weights/annotations remain preserved.
