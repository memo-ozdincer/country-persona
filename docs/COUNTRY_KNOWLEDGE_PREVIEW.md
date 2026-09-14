# Country knowledge: a substantive preview

The previous examples exposed a real weakness: authentic ministry Q&A can still contain almost no useful policy information. More languages and more transcripts do not fix that. The project needs country knowledge that helps answer a concrete proposal, explain an observed choice, or identify where the evidence is insufficient.

This small release provides **six country profiles, 18 statistics, eight policy records, six votes on one resolution, three public explanations of those votes, and three authored instruction examples**. It is a working demonstration of the revised data structure, not a comprehensive six-country dataset or a validated training set. The subsequent [France/UK/India/Brazil data release](COUNTRY_EXTENSION_20260914.md) adds broader country evidence and 12 further policy applications.

## What the data actually contains

### 1. Material country context

These are **2024 observations from the World Bank's database vintage retrieved in September 2026**. Trade means exports plus imports of goods and services as a share of GDP; it is not the share of trade with China, dependence on a particular supplier, or a political preference. GDP is nominal current US dollars. Display values below are rounded; the data retain the API values and indicator definitions.

| Country | Population, millions | GDP, US$ trillions | Trade / GDP |
|---|---:|---:|---:|
| China | 1,409.0 | 18.730 | 38.0% |
| Germany | 83.5 | 4.686 | 79.1% |
| France | 68.6 | 3.160 | 68.1% |
| UK | 69.3 | 3.696 | 62.8% |
| India | 1,450.9 | 3.761 | 45.9% |
| Brazil | 212.0 | 2.186 | 35.6% |

Source: [World Bank WDI snapshot query](https://api.worldbank.org/v2/country/bra;chn;deu;fra;gbr;ind/indicator/SP.POP.TOTL;NY.GDP.MKTP.CD;NE.TRD.GNFS.ZS?source=2&date=2024&format=json&per_page=1000). Observation year, database update date, retrieval date, units and original source organizations remain separate. These revised statistics must not be supplied as information known to a decision-maker in 2024 or earlier without a contemporaneous data vintage.

### 2. Explicit policy, including conditions and limits

| Country / source date | Concrete content retained | What the evidence does not establish |
|---|---|---|
| Germany, 13 July 2023 | Reduce critical dependencies on China, including medicines, rare earths and energy-transition inputs; preserve economic ties and climate cooperation. | A numerical supplier-concentration threshold or approval of a specific contract. |
| China, 10 January 2021 | Development cooperation should avoid political strings and interference; projects should be recipient-led. | That every real project complies with the white paper. |
| France, undated page retrieved September 2026 | Expand both Council membership categories; support G4 permanent seats and greater African representation, including permanent membership. | Historical availability of this page version or acceptance of a final reform package. |
| UK, 11 November 2024 | Expand Council membership into the mid-twenties, with permanent African representation and permanent seats for Brazil, Germany, India and Japan. | Which African states would receive seats. |
| India and Brazil jointly, 8 July 2025 | Mutual support for permanent Council membership; defend food-security stockholding and oppose protectionist pretexts for agricultural restrictions. | Independent evidence for each country's position, or disagreement between them on these jointly endorsed points. |

Sources: [Germany's China Strategy](https://www.auswaertiges-amt.de/resource/blob/2608580/49d50fecc479304c3da2e2079c55e106/china-strategie-en-data.pdf), [China's development white paper](https://english.mee.gov.cn/Resources/publications/Whitep/202101/P020210122374486901993.pdf), [French policy page](https://www.diplomatie.gouv.fr/en/the-ministry-in-action/action-for-peace-and-respect-for-human-rights/france-and-the-united-nations/france-and-the-united-nations-security-council), [UK statement](https://www.gov.uk/government/speeches/the-uk-remains-a-strong-supporter-of-un-security-council-reform-uk-statement-in-the-un-general-assembly), [India–Brazil joint statement](https://www.eoibrasilia.gov.in/pr-10-07-25.php).

Each policy record has country attribution, speaking capacity, issue, date, supported and opposed proposals, unknown details, a source URL, and an exact evidence span with a file hash. A joint statement is one shared record. A public position is not independent verification of government conduct or a recovered private preference. An empty `opposes` list means nothing opposing was extracted, not that the country accepts everything.

### 3. Observed decisions with the actual proposal and reservations

On **2 March 2022**, for **A/RES/ES-11/1, “Aggression against Ukraine”**:

| China | Germany | France | UK | India | Brazil |
|---|---|---|---|---|---|
| Abstained | In favour | In favour | In favour | Abstained | In favour |

All six labels were checked against the [official meeting record](https://documents.un.org/api/symbol/access?l=en&s=A%2FES-11%2FPV.5&t=pdf), pp. 14–15, as well as the existing UNGA-DM table. The [adopted resolution](https://documents.un.org/api/symbol/access?l=en&s=A%2FRES%2FES-11%2F1&t=pdf) is retained separately. Its issuance on 18 March is later than the vote; it is retrospective evidence here, not a pre-vote input.

Brazil's explanation, on p. 17, supports the resolution while retaining reservations about interpreting it as permission for indiscriminate sanctions or arms deployments. China's explanation on p. 16 and India's on p. 18 are also linked to their votes. Explanations for Germany, France and the UK were not acquired in this preview; those fields are null rather than invented. An abstention does not by itself establish a country's motive.

This is one historical event with six country views, not six independent test events. It is not a blind forecasting benchmark; it may already be in Qwen's pretraining data.

## Three actual authored examples

These are saved in `data/prepared/country-knowledge-20260914/examples.jsonl`. Each includes the source passages in the user message, the target answer, and an inspection rubric. They are explicitly labeled assistant-authored interpretations, not authentic historical Q&A or model outputs. The abbreviated display below omits the supplied evidence passages and machine metadata.

**Germany — apply a policy to a concrete proposal**

**Question:** Assess a proposal to source all critical energy-transition inputs from a single Chinese supplier. Would the stated strategy instead require ending all economic and climate cooperation with China?

**Target:** The proposal would raise a critical-dependency concern under our 2023 China Strategy: energy-transition inputs are among the areas it identifies for reducing dependence. Diversification would be consistent with that policy, but the source does not determine approval of this particular contract. The strategy seeks to preserve economic ties and cooperate on climate; it does not call for ending all cooperation with China.

**Inspect:** Can the model apply the dependency concern without inventing a contract decision or turning it into blanket decoupling?

**China — distinguish a stated principle from verified conduct**

**Question:** A proposed development agreement requires the recipient to change its domestic political system. How does that compare with the white paper's stated approach, and can we infer that every Chinese project complies?

**Target:** That requirement conflicts with the white paper's stated opposition to political strings and interference in a recipient's chosen development path. It also emphasizes recipient leadership of projects. These are published principles; they do not establish the terms or conduct of every Chinese-financed project.

**Inspect:** Does the model identify the substantive objection while preserving the distinction between policy and implementation?

**Brazil — retain reservations within a supporting vote**

**Question:** Did supporting ES-11/1 mean Brazil endorsed indiscriminate sanctions and arms deployments? Explain the recorded vote and the representative's reservation.

**Target:** Brazil voted in favour. Its representative nevertheless warned against interpreting the resolution as permission for indiscriminate sanctions or arms deployments and stressed a negotiated settlement. The recorded support and the stated reservation must both be retained.

**Inspect:** Does the answer preserve both the vote and the reservation, without turning this into a timeless stance on every sanction?

## How this changes the training strategy

1. Build dated country dossiers from statistics, commitments, positions and behavior. Next additions should prioritize bilateral trade and energy exposure, treaty and institutional memberships, climate commitments, sanctions positions, security guarantees and explanations of vote. These are coverage targets, not claims of data already acquired.
2. Use retrieval to supply the relevant dossier evidence. Compare Qwen3-8B with country prompting against the same model with evidence before spending on another training run. [RAFT](https://arxiv.org/abs/2403.10131) motivates evidence-conditioned domain adaptation; this prototype does not reproduce its complete training procedure.
3. Train a small, balanced LoRA only on reviewed tasks that apply those facts and policies to concrete questions. Genuine Q&A is useful when it contains substantive answers; authenticity alone is insufficient. A [study of fine-tuning on new knowledge](https://arxiv.org/abs/2405.05904) motivates testing factual errors carefully, rather than assuming ordinary SFT reliably installs a new knowledge base.
4. Inspect country-specific policy correctness, supported agreement, unsupported details, date sensitivity, and the distinction between public claims and observed behavior. Use matched issue cases and language changes, following the behavioral-testing principle of [CheckList](https://aclanthology.org/2020.acl-main.442/). Do not reward artificial country differences or names and rhetorical style alone.

This release uses **zero four-H100 node-hours**. It launches no training. The exact curriculum mix and useful scale remain empirical choices; these eight policy records and three examples are far too small to establish that a persona model works.

## Reproduce and inspect

```bash
.venv/bin/python scripts/prepare_country_knowledge.py --fetch
```

This replays the [frozen source manifest](../data/manifests/country-knowledge-20260914.json) and verifies raw hashes before preparation; changed publisher bytes fail. It requires the existing Python environment and Poppler's `pdftotext`. The failed combined World Bank metadata query is recorded as excluded and replaced with three validated individual queries.

The [curation seed](../data/curation/country_knowledge_seed.json) holds the claims, source anchors and authored examples. The [verification report](../reports/country-knowledge-20260914.json) records counts and artifact hashes. Private source text and prepared data remain outside Git. Every row is quarantined, not automatically admitted to training; independent subject-matter review, full translation/event-family leakage checks and source-use review remain outstanding. The three displayed examples are development demonstrations and must not later become a hidden test set.
