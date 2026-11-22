# Iraq certificate transfer under the v1.1 release gate

The earlier Iraq experiment tested independent notes, typed disclosure,
a computed certificate, and a follow-up clarification of the final line
format. This replay scores all 16 archived records on the frozen v1.1
final rubric and confirms that raw coverage, guard labels and exact
decisions match the earlier annotations.

| Writer condition | Exact decision /4 | Released records /4 | Raw lower coverage /280 | v1.0 released /280 | v1.1 released /280 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Independent notes | 0 | 0 | 112 | 112 | 0 |
| Typed notes | 0 | 0 | 154 | 84 | 0 |
| Typed notes plus a certificate | 2 | 1 | 210 | 168 | 56 |
| Same certificates with literal format instruction | 4 | 4 | 210 | 210 | 210 |

All four public certificates in the writer arms were correct. Both
agreement finals with the certificate used `PACKAGE-A` as the decision,
which the parser rejects. Only one of the two correctly formatted
impasses cleared the source-authority guard. The format intervention
kept the typed notes and certificates fixed and made four fresh final
calls in the original study. With a literal label instruction all four
finals release, while one earns the full 70 points. Three omit the
historical unanimity and two omit the documentation choice. The next
writer intervention can target those criteria while holding certified
decisions and actor disclosures fixed.

These are archived same-assistant marks on an exposed family. The typed
protocol and format prompt are interventions outside the frozen model
comparison. This replay adds no model calls or updates. It uses the
v1.1 final-record scorer and preserves original marks.
[Original transfer](../README.md) · [Replay results and input hashes](replay.json)

```bash
PYTHONDONTWRITEBYTECODE=1 python3 replay.py | cmp - replay.json
```
