# Iraq impasse model comparison across opening orders

This comparison holds the six fictional private mandates, four
packages, standard floor procedure, 16-speech cap and 55-call cap
fixed. The registered orders are France first and the UAE first.
The reference uses GPT-6.1-Sol in every seat. The mixed roster
uses GPT-6-Astra for the UAE and GPT-6.1-Sol elsewhere.

The new UAE-opening mixed attempt received eight responses
before Astra's floor poll at call nine returned HTTP 429. The
resume started at the same unanswered request and verified
the full input for each reused decision.

The resume received five more replies. Sol as the UK was
rate-limited on its floor poll at call 14, after three speeches.
The first 13 successful replies matched the all-Sol reference on
speaker, action, draft version and any package proposed or
excluded. The mixed team had three signatures on the opening
package and zero checked exclusions.

The follow-up reused all 13 replies and recovered two more.
The UK passed on the unanswered poll, and Brazil signed the
opening package on speech four. These choices also matched
the all-Sol reference. The UAE's next Astra floor poll returned
HTTP 429 at call 16.

The next continuation reused all 15 successful replies and
received seven more, including Japan's opening signature on
speech five. The UK floor poll on call 23 returned HTTP 429.
The first 22 structured choices matched the all-Sol reference.
The scorecard records the longest prefix as one interrupted cell
without a terminal reward.

| Opener | All Sol | Astra in the UAE seat |
| --- | --- | --- |
| France | Unresolved in 16 speeches, 55 calls | Certified in 14 speeches, 48 calls |
| UAE | Unresolved in 15 speeches, 55 calls | Provider interruption after 5 speeches and 23 attempted calls |

## Offline verification

```sh
set -o pipefail
out=reports/council-workshop-iraq-uae-opening-focus-20261124
kit=research/council_workshop
python3 -B "$out/verify-resume.py" | cmp "$out/resume.json" -
python3 -B "$out/verify-resume.py" --followup | cmp "$out/followup.json" -
python3 -B "$out/verify-resume.py" --continuation | cmp "$out/continuation.json" -
python3 -B "$kit/held_suite.py" score --trace \
  reports/council-workshop-iraq-pilot-20261123/all-sol \
  reports/council-workshop-iraq-focus-resume-20261124/mixed \
  reports/council-workshop-all-sol-matrix-20261123/iraq-uae-impasse \
  "$out/continuation" | cmp "$out/continuation-score.json" -
```

[Original attempt](mixed/calls.jsonl) · [Resumed decisions](resumed/calls.jsonl) ·
[Follow-up decisions](followup/calls.jsonl) · [Latest decisions](continuation/calls.jsonl) ·
[Paired scores](continuation-score.json) ·
[Completed France-opening pair](../council-workshop-iraq-focus-resume-20261124/README.md)
