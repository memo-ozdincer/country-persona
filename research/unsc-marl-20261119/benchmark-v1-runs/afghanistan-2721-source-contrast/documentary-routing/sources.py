"""Extract documented speaker-bounded 2721 views from S/PV.9521."""

from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import fitz

URL = "https://documents.un.org/doc/undoc/pro/n23/432/19/pdf/n2343219.pdf"


def extract(path):
    doc = fitz.open(path)
    assert len(doc) == 6

    def page(index):
        text = " ".join(doc[index - 1].get_text(sort=False).replace("\b", " ").split())
        text = re.sub(r"^S/PV\.9521 The situation in Afghanistan 29/12/2023 \d/6 23-43219 ", "", text)
        return re.sub(r"^29/12/2023 The situation in Afghanistan S/PV\.9521 23-43219 \d/6 ", "", text)

    fourth, fifth = page(4), page(5)
    ghana_start = fourth.index("Mr. Agyeman (Ghana):")
    china_start = fourth.index("Mr. Geng Shuang (China)")
    russia_start = fifth.index("Ms. Evstigneeva (Russian Federation)")
    france_heading = fifth.index("Mr. De Rivière (France)", russia_start)
    ghana = fourth[ghana_start:china_start].strip()
    china = " ".join([fourth[china_start:], fifth[:russia_start]]).strip()
    russia = fifth[russia_start:france_heading].strip()
    russia_consultation = russia[russia.index("We still believe") : russia.index("We would like to be absolutely clear")].strip()
    ghana_short = ghana[:ghana.index("Today, as we reaffirm")].strip()
    assert "without agreement from the de facto authorities" in russia
    assert "consult with the de facto authorities when appointing" in russia_consultation
    assert "we will not support" not in russia_consultation
    assert "complementing the work of the United Nations Assistance Mission" in ghana_short
    assert "A forcible appointment" in china
    return {
        "url": URL, "sha256": sha256(path.read_bytes()).hexdigest(),
        "views": {
            "russia-full": {"pages": [5], "text": russia, "registered": "ru-condition", "support_condition": True},
            "russia-consultation-only": {"pages": [5], "text": russia_consultation, "registered": None,
                                         "support_condition": False},
            "ghana-full": {"pages": [4], "text": ghana, "registered": "a3-complement", "support_condition": False},
            "ghana-complement-excerpt": {"pages": [4], "text": ghana_short, "registered": "a3-complement",
                                         "support_condition": False},
            "china-full": {"pages": [4, 5], "text": china, "registered": None, "support_condition": False},
            "no-message": {"pages": [], "text": "", "registered": None, "support_condition": False},
        },
    }


if __name__ == "__main__":
    print(json.dumps(extract(Path(sys.argv[1])), indent=2, ensure_ascii=False))
