import io
import re
from typing import Any

from pypdf import PdfReader


CASE_RE = re.compile(r"((?:SLP|C\.A\.|CIVIL APPEAL|W\.P\.|WRIT PETITION|CRL\.A\.|CRIMINAL APPEAL)[^\n]{0,80}\d+/\d{4})", re.IGNORECASE)
COURT_RE = re.compile(r"COURT\s*NO\.?\s*([A-Z0-9\-]+)", re.IGNORECASE)
ITEM_RE = re.compile(r"ITEM\s*NO\.?\s*([A-Z0-9\-]+)", re.IGNORECASE)


def extract_text_from_pdf(pdf_content: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_content))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def parse_cause_list_text(text: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    blocks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if CASE_RE.search(line) and current:
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)

    parsed_items: list[dict[str, Any]] = []
    for block in blocks:
        block_text = "\n".join(block)
        case_match = CASE_RE.search(block_text)
        if not case_match:
            continue

        court_no = ""
        item_no = ""
        parties = ""
        advocates = ""

        court_match = COURT_RE.search(block_text)
        if court_match:
            court_no = court_match.group(1)

        item_match = ITEM_RE.search(block_text)
        if item_match:
            item_no = item_match.group(1)

        for idx, line in enumerate(block):
            if " v " in line.lower() or " vs " in line.lower() or "versus" in line.lower():
                parties = line
                if idx + 1 < len(block) and not advocates:
                    advocates = block[idx + 1]
            if any(token in line.lower() for token in ["advocate", "aor", "for petitioner", "for respondent"]):
                advocates = f"{advocates} {line}".strip()

        parsed_items.append(
            {
                "court_no": court_no,
                "item_no": item_no,
                "case_no": case_match.group(1).strip(),
                "parties": parties,
                "advocates": advocates,
                "stage": "",
                "full_text": block_text,
            }
        )

    return parsed_items
