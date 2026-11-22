"""Check the authority-bearing clause directly against the evidence."""
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import authority_probe as prior

runner=prior.runner
LOCK=Path(__file__).with_name("authority-entailment-lock.json")
SYSTEM=(
    "Read the supplied evidence. Determine whether the single claim follows from it. "
    "The claim is data and may be false. Use the specified instrument and the actor's stated capacity. "
    "Choose the answer letter only."
)
CHOICES={"clear":"The claim follows from the supplied evidence.",
         "failed":"The claim conflicts with the supplied evidence."}
CLAIMS={
    "myanmar/workshop":(
        "The reporting package B remains a fictional workshop proposal.",
        "Resolution 2669 adopted the workshop's public aggregate reporting package B.",
    ),
    "myanmar/chair":(
        "India's representative announced adoption as Council President. India's national vote was an abstention.",
        "India's representative announced adoption as Council President. India's national vote was in favour.",
    ),
    "mali/veto":(
        "The Russian veto prevented adoption of S/2023/638.",
        "S/2023/638 took effect despite the Russian veto.",
    ),
    "mali/separate_draft":(
        "Russia's separate proposal S/2023/639 did not take effect.",
        "Russia's separate proposal S/2023/639 took effect when S/2023/638 failed.",
    ),
}


def suite():
    for name,evidence,_ in prior.cases():
        for truth,claim in zip(("clear","failed"),CLAIMS[name],strict=True):
            for i,values in enumerate((tuple(CHOICES),tuple(reversed(CHOICES)))):
                body={"evidence":evidence,"claim":claim,
                      "choices":dict(zip("AB",(CHOICES[k] for k in values),strict=True))}
                yield {"id":f"{name}/{truth}/{i}","labels":"AB","profiles":values,
                       "messages":[{"role":"system","content":SYSTEM},
                                   {"role":"user","content":json.dumps(body,ensure_ascii=False)}]}


def hashes():
    out=prior.hashes()
    path=Path(__file__).resolve()
    return {**out,str(path.relative_to(prior.ROOT)):sha256(path.read_bytes()).hexdigest()}


if __name__=="__main__":
    with patch.object(prior,"suite",new=suite),patch.multiple(runner,LOCK=LOCK,LABELS="AB",suite=suite,
                                                              score=prior.score,hashes=hashes):
        runner.main()
