# Six-seat Iraq workshop pilot

France opens the registered Iraq impasse case with the UK, Brazil,
Japan, Ghana and the United Arab Emirates. Each seat receives its own
fictional mandate. France alone can rule out `closed`, the UK
`aggregate`, Ghana `public`, and the UAE `hybrid`. A certified impasse
requires all four checked exclusions. The case was registered in
`3f83cdb` before these runs. The mandates and consultation options are
fictional. [Registered cases](../../research/council_workshop/held-cases.json)

The matched arms use GPT-6.1-Sol for five seats and either GPT-6.1-Sol
or GPT-6-Astra for the UAE. Both allow 16 speeches and 55 calls. The
models manage their own floor requests. Advisory ballots are disabled.

The all-Sol meeting ran all 16 speeches and used all 55 calls. It
recorded three of four exclusions and remained unresolved. The UAE
ruled out `hybrid` on its first speech, Ghana ruled out `public` on
speech 11, and the UK ruled out `aggregate` on speech 14. All three
exclusions concerned the draft then on the floor. France had three
speaking turns on which it could have ruled out `closed` in advance.
Brazil proposed `closed` at speech 15, after France's last turn. No
delegate signed a package outside its own mandate. The scripted
comparison certified the impasse in seven speeches and 18 calls.

The [scripted suffix](suffix-check.json) reuses the first 45 all-Sol
decisions, including the floor poll before France's third speech.
France uses speech 13 to rule out `closed`, the UK rules out
`aggregate`, and Brazil certifies the impasse on speech 15 at 51 calls.
Starting the same script one speech later leaves Brazil and Japan ahead
of France and runs out of time. The replay establishes reachability from
the observed prefix and uses no new model calls.

The first mixed-roster attempt received five Sol replies, then received
a provider 429 on its first Astra call, a UAE floor poll. The scorer
records one completed speech and six attempted calls, with no reward
for the interrupted arm. The [initial trace score](initial-score.json)
preserves that observation separately. The bounded resume reused those
five replies and received the UAE floor decision. It reached five
speeches and 26 logical calls before the provider returned another 429
on the UAE's first speech. The [resumed score](resumed-score.json) also
records an unscored call error. The mixed arm’s meeting outcome remains
unmeasured. Counting the Gulf of Guinea pilot, five of 32 registered
live cells have completed meetings.

[All-Sol trace](all-sol/calls.jsonl) · [First mixed attempt](sol-with-astra-uae/calls.jsonl) ·
[Resumed mixed attempt](sol-with-astra-uae-resumed/calls.jsonl)

## Replay

```sh
set -o pipefail
kit=research/council_workshop
out=reports/council-workshop-iraq-pilot-20261123
python3 -B "$kit/held_suite.py" audit | cmp "$kit/held-control-audit.json" -
python3 -B "$kit/held_suite.py" score --trace "$out/all-sol" "$out/sol-with-astra-uae" | cmp "$out/initial-score.json" -
python3 -B "$kit/held_suite.py" score --trace "$out/all-sol" "$out/sol-with-astra-uae-resumed" | cmp "$out/resumed-score.json" -
python3 -B "$out/suffix-check.py" | cmp "$out/suffix-check.json" -
```

To generate a fresh all-Sol run:

```sh
kit=research/council_workshop
case_file=$(mktemp)
python3 -B "$kit/held_suite.py" case iraq impasse > "$case_file"
python3 -B "$kit/run.py" --case "$case_file" --countries FRA GBR BRA JPN GHA ARE \
  --model gpt-6.1-sol --turn-cap 16 --call-cap 55 --call-timeout 90 --out runs/iraq-all-sol
```

For the mixed roster, use a fresh output directory and add
`--seat-model ARE=gpt-6-astra`.
