"""Consistency checks for the data request spec. Run: python -m pytest test_spec.py -q (from this folder)."""
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
SPEC = HERE / "spec"


def read(name):
    with open(SPEC / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


FIELDS = read("fields.csv")
FILES = {r["file"] for r in read("files.csv")}


def build(program):
    out = Path(tempfile.mkdtemp())
    subprocess.run([sys.executable, str(HERE / "build_request.py"), "--program", program, "--institution", "Test College", "--out", str(out)], check=True, capture_output=True)
    return out


def test_every_field_belongs_to_a_listed_file():
    assert {f["file"] for f in FIELDS} <= FILES


def test_requirement_codes_and_tiers_are_valid():
    for f in FIELDS:
        assert f["law"] in {"Y", "N", "C", "-"}, f
        assert f["ug"] in {"Y", "N", "C", "-"}, f
        assert f["tier"] in {"1", "2", "A"}, f
        assert f["type"] in {"text", "int", "decimal", "date", "bool", "json"}, f


def test_zip5_only_in_zip_key():
    assert [f["file"] for f in FIELDS if f["field"] == "zip5"] == ["zip_key"]
    for f in FIELDS:
        if f["file"] != "zip_key" and "zip5" in f["description"].lower():
            assert "zip_key" in f["description"], f


def test_protected_attributes_are_audit_only():
    for f in FIELDS:
        if f["field"] in {"race_ethnicity", "gender"}:
            assert "audit" in f["description"].lower(), f


def test_no_forbidden_direct_identifiers_requested():
    banned = {"name", "email", "phone", "street_address", "ssn", "dob", "date_of_birth", "lsac_number"}
    assert not banned & {f["field"] for f in FIELDS}


def test_no_credit_data_statement_or_request():
    # methodology section 9 and Appendix E.3: the statement is not repeated in the data request; none is requested
    text = (SPEC / "request_spec.yaml").read_text(encoding="utf-8").lower()
    assert "consumer credit" not in text
    assert not any(re.search(r"credit (score|bureau|tradeline)", f["description"].lower()) for f in FIELDS)


def test_program_documents_do_not_leak_the_other_program():
    law = build("law")
    ug = build("undergraduate")
    law_md = next(law.glob("*.md")).read_text(encoding="utf-8")
    ug_md = next(ug.glob("*.md")).read_text(encoding="utf-8")
    for term in (r"\bJD\b", r"LSAT", r"UGPA", r"\bABA\b", r"LSAC", r"matriculant"):
        assert not re.search(term, ug_md), term
    for term in (r"\bSAT\b", r"\bACT\b", r"Pell", r"Parent PLUS", r"high school", r"athlet", r"hs_gpa"):
        assert not re.search(term, law_md), term


def test_both_programs_build_all_outputs():
    for p in ("law", "undergraduate"):
        out = build(p)
        names = {x.suffix for x in out.iterdir()}
        assert {".docx", ".md", ".xlsx", ".csv"} <= names
