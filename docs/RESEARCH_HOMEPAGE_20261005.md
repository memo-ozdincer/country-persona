# Illustrated research homepage

Presentation checkpoint, 5 October 2026 UTC. No new model calls, optimizer steps, GPU inspections or experiment queues. The underlying country and character findings are unchanged.

The existing public Hugging Face Space now opens on [Teaching models to take a position](https://memo-ozdincer-country-persona-explorer.static.hf.space/index.html). The user requested a paper-blog-style homepage, using the two Anthropic examples as visual references, emphasizing goals, data, evaluations, preliminary results and future methods rather than operational run details.

The page uses self-hosted Newsreader and DM Sans, warm paper surfaces, a consistent green/gold/blue/violet figure palette, narrow prose and wider illustrations. It contains an opening evidence-to-response diagram, ten numbered figures and two real browser captures. Interactive controls change corpus record types and humor conditions; source-matrix cells show their contributing collections. Small screens use a stacked opening diagram and scrollable matrices/charts. Reading navigation, descriptive chart labels, keyboard controls, reduced-motion styles and print styles are present.

The original source visualizer is preserved at [data.html](../explorer/data.html), including all six countries and the Germany/China decision-case views. Both initial legacy `index.html#country=...` loads and subsequent country hash changes redirect. The full catalog, policy workshop and Reddit pages remain in the same public Space. The private Space and datasets were not modified.

## Evidence and claims

- Corpus figures derive from `explorer/overview.json` and `explorer/sources.json`: six countries, 26 distinct source collections and eleven recorded languages. Translations, spans and shared institutional records can overlap. No sum is presented as a global number of independent training examples.
- UNSC-Bench counts are the acquired audit's 469 event records, 258 adopted and 211 vetoed, with 6,619 country-vote rows. UNBench's acquired vote-task test split has 6,420 country-event rows across 428 events: 6,210 Yes, 209 Abstain, one No. The 96.7% always-Yes observation is dataset arithmetic, not an evaluated model score. Availability/conflict/grouping limits remain explicit.
- Humor figures show all six arms and all nine conditions from the measured Open Character reproduction. The two-condition chart defaults to ordinary instructions and can switch to strongest neutrality. The default 58.6% and neutrality 35.2% fresh-full scores are classifier recognition, with same-question classifier dependence disclosed. The page retains the authors' released-weight controls and acknowledges six improvements/three regressions after SFT, output caps and surviving content errors. It does not imply country-policy or multi-agent gain.
- The country design lesson shows all matched base/adapter values in the source/checked-plan/explicit-boundary comparison: 18/18, 18/22 and 24/22 met units out of 24. Values are summed directly from stored ratings. The event is exposed development, and the same unblinded assistant authored plans and reviewed answers; independent review is pending.
- Source-linked SFT, clause weighting and pure DPO are labeled tested at small scope. Anchored DPO followed by introspective SFT is the published-model positive control. Country anchoring, pressure/update tests, interaction and interactive reinforcement learning remain prospective. No scheduled pipeline or government private beliefs are claimed.

[Figure data and input SHA-256 provenance](../explorer/homepage-data.json) are public and downloadable. Rebuild with `python3 scripts/build_research_homepage.py`. This command performs no inference. The existing overview/static staging paths now include the homepage, assets and sample walkthrough and refresh figure provenance after rebuilding inventories.

## Publication and verification

[Publication receipt](../reports/research-homepage-publication-20261005.json) records commit `01dcdb5881312ed6a98d4dc9b33a2299bd6042dc`, its parent, and fourteen authored assets. All ten existing explorer dependencies matched local bytes before publishing. A parent-commit constraint prevented overwriting concurrent updates. The uploader made additive/targeted file changes, retained a copy of the prior live homepage/catalog, and verified live bytes after removing only the known HF-injected configuration script. It preserved the existing static catalog adapter.

[Verification receipt](../reports/research-homepage-verification-20261005.json) records local asset/navigation checks, Python compilation, provenance and chart arithmetic, all-six-country browser checks, desktop/mobile checks, real screenshot/image/font loading, live condition switching, and legacy routing. Browser screenshots, font origins, prepared site copies and the prior live files are retained under `runs/research-homepage-20261005-v1/` for the next private snapshot. These are software/presentation checks, not independent semantic review or new model-quality results.

The build initially found the old preview port occupied and used a different port without touching its occupant. Chromium required the existing isolated browser's no-sandbox launch flag. A same-document legacy hash navigation missed the initial redirect; an explicit hash-change handler repaired it and both paths were checked. No unfamiliar process was changed.

The fresh private handoff destination for this checkpoint is `/mfs1/u/memo/country-persona-research/handoffs/persona-20261005-homepage-v11`. Its manifest captures working changes and ignored presentation artifacts, separately from the public UI commit; base weights and credentials remain excluded.
