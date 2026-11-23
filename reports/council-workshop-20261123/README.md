# Three delegations negotiate a climate-reporting clause

On 23 November 2026 we ran GPT-6.2-Astra and GPT-6.2-Sol through the desktop Codex CLI (0.171.0-alpha.13) with ChatGPT subscription login. Each model played all three delegations in its own session of the workshop. The UK opened, followed by a request-based speaking queue. The same fictional clause, dated source excerpts, low reasoning effort and four-speaking-turn cap applied to both models. [Simulator and commands](../../research/council_workshop/README.md) · [Case packet](../../research/council_workshop/climate.json)

## What to inspect

- **Sol.** The UK accepted the opening clause. India replaced it with reporting through existing climate institutions. France restored annual reporting to the Council for situations on its agenda while drawing on existing climate reports. The UK accepted that version. In private, the UK and France voted yes and India voted no. [Turns and ballots](sol/result.json)
- **Astra.** The UK proposed an annual report. India countered with reporting through the climate convention. France proposed using existing Council reports for case-specific security assessments alongside convention reporting. The UK accepted the wording. The UK and France voted yes. India voted no because even an existing Council report would retain the climate-security link it objected to. [Turns and ballots](astra-meeting/result.json)
- **Drafting comparisons.** The pooled analysts both suggested using existing reports. An analyst's proposed compromise does not establish that the delegations would accept it. The independent condition asks each delegation for one draft using only its own packet. The drafting comparisons use fewer calls than a meeting. [Astra solo](astra-solo/result.json) · [Sol solo](sol-solo/result.json) · [Astra independent](astra-drafts/result.json) · [Sol independent](sol-independent/result.json)

The four-turn cap gives the opener two speeches in this run and each other country one. Private final ballots give all three a decision on the same text. A cap records where observation stopped. It does not establish that further negotiation would fail. These are simulated workshop positions on one exposed case. Independent review of fidelity to the sources is still open.

## Operational record

The older CLI on PATH (0.156.1) rejected the requested model IDs. The desktop CLI accepted them under the same ChatGPT login. Some Astra calls timed out. The original requests and earlier replies remain in their partial folders. Recovery reuses a completed reply only when the full prompt, schema, speaker and run settings match. The recovery chain for the Astra meeting is `astra → astra-resumed → astra-final → astra-complete → astra-meeting`.

All six completed runs replayed offline with identical model inputs, speaking order and results. The full repository suite passed 253 tests and skipped 23 requiring optional research artifacts or fixtures.
