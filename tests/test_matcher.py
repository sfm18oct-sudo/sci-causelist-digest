from app.services.matcher import match_counsel


def test_match_counsel_variants_case_insensitive():
    advocates = "For Petitioner: Mr. K. Krishna Murthy, AOR"
    terms = ["KrishnaMurthy", "Other Name"]
    assert match_counsel(advocates, terms) == "KrishnaMurthy"


def test_match_counsel_no_match():
    advocates = "For Respondent: Ms. Someone Else"
    terms = ["KrishnaMurthy"]
    assert match_counsel(advocates, terms) is None
