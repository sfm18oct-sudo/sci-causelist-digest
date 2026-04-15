import re
from typing import Iterable


DEFAULT_VARIANTS = [
    "KrishnaMurthy",
    "Krishna Murthy",
    "Krishnamurthy",
    "K. Krishna Murthy",
    "K Krishna Murthy",
]


def normalize_for_match(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def match_counsel(advocates_text: str, terms: Iterable[str]) -> str | None:
    normalized_text = normalize_for_match(advocates_text)
    for term in terms:
        if not term:
            continue
        if normalize_for_match(term) in normalized_text:
            return term
    return None
