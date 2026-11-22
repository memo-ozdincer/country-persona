"""Extract fixed documentary views from the official 2553 vote explanations."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import fitz

URL = "https://documents.un.org/doc/undoc/gen/n20/342/63/pdf/n2034263.pdf"


def extract(path):
    document = fitz.open(path)
    assert len(document) == 28

    def annex(page, number):
        text = " ".join(document[page - 1].get_text(sort=True).split())
        text = text.replace("\u0002", "").replace("\u00ad", "")
        text = text.removeprefix("S/2020/1167 ").removesuffix(f" {page}/28 20-16404")
        assert f"Annex {number}" in text[:35]
        return text

    uk = annex(28, "XIX")
    vote = annex(23, "XIV")
    belgium = annex(26, "XVII")
    germany = annex(27, "XVIII")
    start_vote = uk.index("While we are sufficiently content")
    start_inclusion = uk.index("Secondly, we know")
    end_inclusion = uk.index("The United Nations system should")
    assert uk.index("The compressed timeline") > start_vote
    assert "inadequate time for proper negotiations" in uk
    assert "external monitoring" in uk[start_inclusion:end_inclusion]
    assert "the United Kingdom votes in favour" in vote
    assert "within an appropriate time frame" in belgium
    assert "little time was given" in germany
    assert "prerogative and authority in the management of the Fund" in germany
    return {
        "url": URL, "pdf_sha256": sha256(path.read_bytes()).hexdigest(),
        "views": {
            "uk-explanation": {"page": 28, "text": uk, "verified_cards": ["gb-process", "gb-inclusion"]},
            "uk-negotiations": {"page": 28, "text": uk[start_vote:start_inclusion].strip(),
                                "verified_cards": ["gb-process"]},
            "uk-inclusion": {"page": 28, "text": uk[start_inclusion:end_inclusion].strip(),
                             "verified_cards": ["gb-inclusion"]},
            "uk-vote-letter": {"page": 23, "text": vote, "verified_cards": []},
            "belgium-explanation": {"page": 26, "text": belgium, "verified_cards": ["be-inclusion", "be-funding"]},
            "no-message": {"page": None, "text": "", "verified_cards": []},
        },
        "reply_source": {"page": 27, "sha256": sha256(germany.encode()).hexdigest()},
    }


if __name__ == "__main__":
    print(json.dumps(extract(Path(sys.argv[1])), indent=2, ensure_ascii=False))
