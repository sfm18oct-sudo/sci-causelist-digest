from app.services.pdf_parser import parse_cause_list_text


def test_parse_cause_list_text_extracts_case_and_advocate():
    sample = """
COURT NO. 7
ITEM NO. 12
SLP(C) 12345/2026
State of Tamil Nadu versus Some Party
For Petitioner: Mr. K. Krishna Murthy, AOR
"""
    items = parse_cause_list_text(sample)
    assert len(items) == 1
    assert items[0]["case_no"].lower().startswith("slp")
    assert "Tamil Nadu" in items[0]["parties"]
    assert "Krishna Murthy" in items[0]["advocates"]
