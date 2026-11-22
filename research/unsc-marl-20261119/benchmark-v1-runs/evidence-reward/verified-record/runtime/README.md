# Run the learned UN workshop team

The runner connects the saved chair and delegate policies, addressed
Qwen replies, typed evidence admission and the source-checked record
compiler. It supports the existing Mali and Cyprus packets and the
Cyprus vote-withheld control. Select a fitted pair explicitly or use
automatic selection, which forecasts net over the public world prior
and chooses between the two learned pairs and silence. Fixed order and
compulsory replies under the former chair are available as controls.

```bash
python3 workshop.py mali --private 010 --profile access-weak --policy former --adapter archive
python3 workshop.py cyprus --private 001 --adapter archive
python3 workshop.py cyprus --private 001 --drop 1
```

Use the project Python with NumPy. The three input digits are fictional
cards supplied by the test harness, in desk order. The archive adapter
requires an exact addressed request from the saved traces. The default
fixture emits the declared bit for other worlds and controlled transport
faults. The Python entry point accepts a callable in place of the adapter
name. It receives the role-scoped request and returns a mapping with
`text` and `termination`. The compiled record and public dialogue trace
are separate from the simulator's message-cost diagnostics.

A desk adapter sees its own card and the public state. The chair receives
only a receipt tied to its addressed question, or the absence of one.
Dropped replies, deliberate withholding and rejected text all leave the
chair's evidence state unchanged. The admitted bit is checked by the
addressed trusted adapter against its fictional card. This is an
in-process protocol. It relies on trusted adapters and does not establish
the authenticity or truth of claims from external participants.

## Verified replay

[The Mali trace](mali-archive.json) and [the Cyprus trace](cyprus-archive.json)
reproduce the exact previously scored records, with 56/70 and 70/70
released points respectively. Removing or invalidating either decisive
reply forces a warranted deferral in all eight injection tests. An empty
callback response or a timeout also forces deferral. The check
rejects nine mismatched receipts or invalid payloads, exercises 12 local
role-card combinations and verifies all 81 renderer states across the
three packets. The matched Mali optional reply exercise preserves the
viable set with one attempt in the learned arm and two under the same
chair with compulsory sending. All native replies are archival.
[Verification](verification.json)

## Transfer to a new menu size

Both learned pairs were fit only on four-option menus. The holdout
audit tests all 56 three-option menus at three rates and two query caps.
It uses the same three roles, shared reward, truthful reply assumption
and modeled costs. The selector's net is the expected documentary
credit after query and reply costs.

| Profile and cap | Selected learned team or silence | Fixed order | Exact planner |
| --- | ---: | ---: | ---: |
| Even, 2 | 0.1546 | 0.0317 | 0.1845 |
| Even, 3 | 0.5080 | 0.4850 | 0.5278 |
| Third role weak, 2 | 0.0915 | 0.0111 | 0.1122 |
| Third role weak, 3 | 0.2001 | 0.1360 | 0.2147 |
| First role weak, 2 | 0.0893 | −0.1026 | 0.1043 |
| First role weak, 3 | 0.1859 | 0.0218 | 0.1995 |

The selector has higher mean net than fixed order under every rate and
cap. It loses to fixed order on eight individual menus, all with even
rates and a three-question cap. The maximum regret to the exact planner
is 0.0697. The source-aware pair has no negative-net menus in this matrix.
The selector uses modeled candidate outcomes and known rates. This
checks transfer to a different menu size under the same proof rules and
does not add a documentary family or language-model test.
[Transfer protocol](transfer-protocol.md) · [All 336 conditions](size-transfer.json)

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 verify_runtime.py | cmp - verification.json
python3 size_transfer.py | cmp - size-transfer.json
```
