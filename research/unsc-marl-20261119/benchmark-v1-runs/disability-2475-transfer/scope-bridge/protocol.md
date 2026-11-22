# Cross evidence restoration with a scope-check prompt

Use the existing three receipt masks 3, 6 and 7. Cross the original
Qwen notes and compact authored notes with the original bridge prompt
and a new prompt that asks the writer to identify each actor's claim
and the instrument or provision it concerns. Both prompts return
only one comparison sentence and use the same 60-token ceiling.
The input payload for each prompt pair is byte-identical. The
original-note original-prompt cell reuses three archived calls.
Generate the nine other cells once each on frozen Qwen3.5-4B.

The authored notes and the public control come verbatim from the
existing oracle bank's separate paragraphs. Do not include any
authored bridge, rubric, score or answer key in model prompts.
Use the existing public lead with native notes, and the authored
lead with authored notes. Compare absolute scores within each
source bank and report incremental rubric credit above its
no-bridge record. The main endpoint is the distinction between
France's call for ratification and implementation of the treaty
and Russia's reading of the resolution's operative paragraph.
Maintain the original source guard and word cap. Evaluate any change
in UK–Russia credit separately because the UK note can establish it
on its own. Record raw coverage, guard, released points and 27-word
bridge compliance. Use opaque answer IDs and a single source reader.

After scoring, replay the strongest fixed and adaptive baselines
on each complete score bank with the same routing assumptions.
Do not tune or select a forecast variant on the held rows. The
authored materials are an interventional control on a known case.
