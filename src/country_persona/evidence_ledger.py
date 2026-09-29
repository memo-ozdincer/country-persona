"""Mechanical checks for claim/evidence JSON. Deliberately not an entailment judge."""
import json

from .eval_evidence import normalize
from .io import digest

COUNTRIES = {"FRA", "GBR", "IND", "BRA"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Non-JSON numeric constant: " + value)


def check_ledger(output, evidence, *, capped=False):
    """Validate the delivered text without repair; normalize only quote whitespace.

    Valid quotations can support the opposite of a model's claim. Return semantic
    fields as None even if every structural/source-location check passes.
    """
    index = {}
    for e in evidence:
        if e["id"] in index or e["country"] not in COUNTRIES or digest(e["text"]) != e["text_digest"]:
            raise ValueError("Invalid or changed evidence inventory")
        index[e["id"]] = e
    if {e["country"] for e in index.values()} != COUNTRIES:
        raise ValueError("Supply the four countries' evidence for this context")
    errors, quotes = [], []

    def error(kind, path, message):
        errors.append({"kind": kind, "path": path, "message": message})

    def obj(value, keys, path):
        if not isinstance(value, dict) or set(value) != set(keys):
            error("schema", path, "Expected exactly these object keys: " + ", ".join(keys))
            return False
        return True

    def string(value, path):
        if not isinstance(value, str) or not value.strip():
            error("schema", path, "Expected nonempty text")
            return False
        return True

    def array(value, path, minimum=0):
        if not isinstance(value, list) or len(value) < minimum:
            error("schema", path, f"Expected a list with at least {minimum} entries")
            return False
        return True

    def quote(item, country, path):
        good = string(item["evidence_id"], path + ".evidence_id")
        good = string(item["quote"], path + ".quote") and good
        if not good:
            return
        source = index.get(item["evidence_id"])
        valid_country = source is not None and source["country"] == country
        found = source is not None and normalize(item["quote"]) in normalize(source["text"])
        quotes.append({"path": path, "country": country, "evidence_id": item["evidence_id"],
                       "source_country_matches": valid_country, "quote_found": found,
                       "quote": item["quote"], "semantic_support": None})
        if not valid_country:
            error("source", path, "Unknown evidence ID or evidence belongs to a different country")
        if not found:
            error("source", path, "Quote absent from the named source after whitespace-only normalization")

    if capped:
        error("delivery", "$", "Output hit the generation cap; retain as delivered")
    try:
        value = json.loads(output, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except (ValueError, TypeError) as exc:
        error("json", "$", str(exc))
        value = None
    else:
        if obj(value, ("countries", "common_ground", "differences", "proposals"), "$"):
            if array(value["countries"], "$.countries", 4):
                seen = []
                for i, row in enumerate(value["countries"]):
                    path = f"$.countries[{i}]"
                    if not obj(row, ("country", "answer", "evidence", "not_established"), path):
                        continue
                    country = row["country"]
                    if not isinstance(country, str) or country not in COUNTRIES:
                        error("schema", path + ".country", "Unknown country")
                        continue
                    seen.append(country)
                    string(row["answer"], path + ".answer")
                    if array(row["not_established"], path + ".not_established"):
                        for j, unknown in enumerate(row["not_established"]):
                            string(unknown, f"{path}.not_established[{j}]")
                    if array(row["evidence"], path + ".evidence", 1):
                        for j, citation in enumerate(row["evidence"]):
                            cp = f"{path}.evidence[{j}]"
                            if obj(citation, ("claim", "evidence_id", "quote"), cp):
                                string(citation["claim"], cp + ".claim")
                                quote(citation, country, cp)
                if len(seen) != 4 or set(seen) != COUNTRIES:
                    error("schema", "$.countries", "Expected each of FRA/GBR/IND/BRA exactly once")
            for section in ("common_ground", "differences"):
                if not array(value[section], "$." + section):
                    continue
                for i, row in enumerate(value[section]):
                    path = f"$.{section}[{i}]"
                    if not obj(row, ("claim", "countries", "evidence"), path):
                        continue
                    string(row["claim"], path + ".claim")
                    named = row["countries"]
                    if not array(named, path + ".countries", 2):
                        continue
                    if any(not isinstance(c, str) or c not in COUNTRIES for c in named) or len(set(named)) != len(named):
                        error("schema", path + ".countries", "Expected distinct legal country codes")
                        continue
                    seen = []
                    if array(row["evidence"], path + ".evidence", 2):
                        for j, citation in enumerate(row["evidence"]):
                            cp = f"{path}.evidence[{j}]"
                            if obj(citation, ("country", "evidence_id", "quote"), cp):
                                country = citation["country"]
                                if not isinstance(country, str) or country not in named:
                                    error("schema", cp + ".country", "Citation country not among the claim's named countries")
                                    continue
                                seen.append(country)
                                quote(citation, country, cp)
                    if set(seen) != set(named):
                        error("coverage", path, "Every named country requires its own source quotation")
            if array(value["proposals"], "$.proposals", 1):
                for i, row in enumerate(value["proposals"]):
                    path = f"$.proposals[{i}]"
                    if obj(row, ("text", "status"), path):
                        string(row["text"], path + ".text")
                        if row["status"] != "proposal_not_commitment":
                            error("schema", path + ".status", "Must label proposal_not_commitment")
    return {"mechanical_checks_passed": not errors, "json_valid": not any(e["kind"] == "json" for e in errors),
            "schema_valid": None if any(e["kind"] == "json" for e in errors) else not any(e["kind"] == "schema" for e in errors),
            "errors": errors, "quote_checks": quotes, "quotations_checked": len(quotes),
            "valid_source_quotations": sum(q["source_country_matches"] and q["quote_found"] for q in quotes),
            "output_capped": capped, "semantic_validity": None, "answer_completeness": None,
            "interpretation": "Source-location and schema checks only. Independent entailment and full-answer review required."}
