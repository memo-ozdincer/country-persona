"""Build a small family-disjoint comparison training pack."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent


def read(path):
    return json.loads(path.read_text())


def sources():
    afghan = read(RUNS/"afghanistan-2721-source-contrast/case.json")
    h = {b["id"]:b["text"] for b in read(RUNS/"humanitarian-2664-admission/case.json")["evidence"]}
    return (afghan["early_statements"][0]["text"], afghan["early_statements"][1]["text"],
            afghan["late_clauses"][0]["text"], afghan["late_clauses"][1]["text"],h)


def build():
    ru, a3, consult, unama, h = sources()
    ru_target = ("Russia made agreement a condition for its own support. The adopted provision calls "
                 "for consultation with the Afghan authorities and leaves their agreement outside the appointment requirements.")
    a3_target = ("The African members saw a role for the envoy alongside UNAMA. That view is consistent "
                 "with the adopted clause preserving UNAMA's mandate and work.")
    ind_target = ("The Council assigned monitoring to the 1267 Committee, while India judged that its "
                  "call for proactive Monitoring Team involvement and stronger reporting was still not fully addressed.")
    raw = (
        ("2721/russia-match",ru,consult,ru_target),
        ("2721/africa-match",a3,unama,a3_target),
        ("2721/russia-cross",ru,unama,"NONE"),
        ("2721/africa-cross",a3,consult,"NONE"),
        ("2721/russia-paraphrase",
         "Russia said it could endorse the envoy's appointment only if Afghanistan's de facto authorities assented.",
         "The adopted provision requests that the Secretary-General hear from Afghan authorities before appointing an envoy. Their agreement is unnecessary.",
         ru_target),
        ("2721/africa-paraphrase",
         "The African members said a new envoy could add to the work of the UN Assistance Mission in Afghanistan.",
         "Paragraph 3 asks for an envoy and leaves the responsibilities and activities of the UN Assistance Mission in Afghanistan in place.",
         a3_target),
        ("2664/india-match",h["india"],h["safeguards"],ind_target),
        ("2664/india-cross",h["india"],h["scope"],"NONE"),
        ("2664/request-only",
         "India called for greater involvement of the 1267 Monitoring Team. This excerpt does not record India's assessment of the adopted safeguards.",
         h["safeguards"],"NONE"),
        ("2664/finance-cross","India abstained and spoke about the inability of existing procedures to address diversion risks.",
         "At adoption the humanitarian exemption applied for two years to the ISIL and Al-Qaida sanctions regime.", "NONE"),
        ("2664/india-paraphrase",
         "India said the adopted text failed to meet in full its requests for a more active role for the 1267 Monitoring Team and more extensive reporting.",
         "The adopted resolution gives the 1267 Committee a responsibility for monitoring how the exemption works.",
         ind_target),
        ("2664/india-paraphrase-reverse",
         "India said its additional proposals on active Monitoring Team involvement and reporting had been fully incorporated.",
         "The adopted resolution describes humanitarian eligibility while reaffirming asset freezes.", "NONE"),
    )
    return [{"id":key,"payload":{"delegate_statement":early,"adopted_document":late},"target":target}
            for key,early,late,target in raw]


if __name__ == "__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
