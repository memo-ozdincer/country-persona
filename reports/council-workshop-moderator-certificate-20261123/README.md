# Moderator certification when the evidence is complete

The [all-Sol baseline](../council-workshop-all-sol-matrix-20261123/README.md)
includes an Iraq impasse with all four checked exclusions on the record
and a call cap that stopped the meeting before the declaration. This
comparison replays all eight registered all-Sol meetings with
`--auto-certify-impasse`. The moderator closes the finite case immediately
after the last verified exclusion, before a further floor poll. It
records `certificate_source: moderator` in the result. Only a delegate's
validated exclusion can contribute evidence to the certificate.

| Archived trace | Standard termination | Moderator termination |
| --- | --- | --- |
| Gulf impasse, Norway opening | Certified in 9 speeches, 22 calls | Certified in 8 speeches, 20 calls |
| Iraq impasse, UAE opening | Unresolved in 15 speeches, 55 calls | Certified in 15 speeches, 53 calls |
| Other six traces | Four agreements, two unresolved | Identical outcomes and calls |

The moderator rule certifies **2 of 4 impasses**, up from **1 of 4**
under delegate declaration. It changes no model prompt or reply before
the new stopping point. Every reused request is validated against the
original call record. This is an exact-prefix replay of a changed
institutional rule. It measures what happens if the moderator acts on
already public checked evidence. The registered model-assignment cells
continue to use delegate declaration, and the standard all-Sol score
remains 5 of 8. The comparison uses no new model calls.

[Replay results](results.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-moderator-certificate-20261123
python3 -B "$out/replay-stop.py" | cmp "$out/results.json" -
```

The runner accepts `--auto-certify-impasse` for finite-mandate meetings.
Resume and extension retain the original closing rule. Advisory ballots,
when requested, still take their reserved calls after the meeting closes.
