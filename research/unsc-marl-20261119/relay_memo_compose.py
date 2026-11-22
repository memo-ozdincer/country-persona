"""Render evidence-bound memo controls from the same checked relay inputs."""
import json

import relay_final_memo as pilot


def render(row):
    fields=json.loads(row["messages"][1]["content"])
    family,status=row["family"],fields["checked_status"]
    cards={card["owner"]:card["card"] for card in fields["evidence_at_chair"]}
    assert len(cards)==len(fields["evidence_at_chair"])
    if family=="mali":
        assert cards["first delegate"]=="review"
        if status=="IMPASSE":
            assert cards["second delegate"]=="closure"
            body=("The first delegate accepts only review. The second delegate accepts only closure. "
                  "These exclusive positions are incompatible. The chair should refer review and closure "
                  "back to the delegates for another workshop round.")
        else:
            assert status=="UNRESOLVED" and "second delegate" not in cards
            body=("The first delegate accepts only review. The second delegate's card is missing. "
                  "Compatibility remains open pending its preference. The chair should request that card "
                  "and leave the workshop decision pending.")
        cause1=fields["historical_evidence"]["status-638"]
        cause2=fields["historical_evidence"]["status-639"]
        assert "13 in favour, 1 against and 1 abstention" in cause1
        assert "negative vote of a permanent member" in cause1 and "Russia cast the sole negative vote" in cause1
        assert "1 vote in favour, 1 against and 13 abstentions" in cause2
        assert "It was not adopted" in cause2
        history=("S/2023/638 was not adopted after Russia's permanent-member veto (13–1–1). "
                 "Separate draft S/2023/639 fell short of affirmative votes (1–1–13). "
                 "The workshop cannot change either official vote.")
    else:
        assert family=="myanmar" and cards["UN office"]=="early only"
        if status=="EARLY":
            assert cards["liaison office"]=="both"
            body=("The UN office can attend only early. The liaison office can attend both slots. "
                  "Early is their sole overlap, so the chair should propose an early briefing.")
        else:
            assert status=="UNRESOLVED" and "liaison office" not in cards
            body=("The UN office can attend only early. The liaison office's availability is missing. "
                  "Overlap remains unknown. The chair should ask the liaison office for its availability "
                  "and leave the scheduling decision pending.")
        mandate=fields["historical_evidence"]["mandate"]
        for exact in ("Resolution 2669","in coordination with the ASEAN Special Envoy",
                      "to report orally to the Security Council by 15 March 2023 on UN support for the Five-Point Consensus"):
            assert exact in mandate
        history=("Resolution 2669 requests the Secretary-General or his Special Envoy, in coordination "
                 "with the ASEAN Special Envoy, to report orally to the Security Council by 15 March 2023 "
                 "on UN support for the Five-Point Consensus. The workshop has no authority to change that duty.")
    text=f"Workshop status: {status}\n{body}\n{history}"
    assert len(text.split())<=100
    assert next(iter(text.splitlines()))==f"Workshop status: {status}"
    return {"id":row["id"],"memo":text,"words":len(text.split()),"workshop_fields":fields["evidence_at_chair"],
            "historical_evidence":fields["historical_evidence"]}


if __name__=="__main__":
    print(json.dumps({"scope":"Case-specific authored reference renderer. Cards and status come from the same writer inputs. No language-model generations or generic prose-quality claim.",
                      "records":[render(row) for row in pilot.suite()]},indent=2,ensure_ascii=False))
