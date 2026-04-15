from datetime import date
import logging
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


LOGGER = logging.getLogger(__name__)
PUBLISHED_URL = "https://www.sci.gov.in/published-cause-list/"
API_PREFIX = "https://api.sci.gov.in"


def _date_tokens(target_date: date) -> list[str]:
    return [
        target_date.strftime("%Y-%m-%d"),
        target_date.strftime("%d-%m-%Y"),
        target_date.strftime("%Y%m%d"),
    ]


def discover_pdf_urls(target_date: date) -> list[str]:
    session = requests.Session()
    urls: set[str] = set()
    tokens = _date_tokens(target_date)

    try:
        response = session.get(PUBLISHED_URL, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup.find_all("a", href=True):
            href = tag["href"]
            if ".pdf" not in href.lower():
                continue
            full = urljoin(PUBLISHED_URL, href)
            if any(token in full for token in tokens):
                urls.add(full)

        discovered = set(re.findall(r"https?://[^\"'\s>]+\.pdf", response.text, re.IGNORECASE))
        for pdf_url in discovered:
            if any(token in pdf_url for token in tokens):
                urls.add(pdf_url)
    except Exception as exc:
        LOGGER.exception("Failed to parse published cause list page: %s", exc)

    api_index = f"{API_PREFIX}/jonew/cl/{target_date.strftime('%Y-%m-%d')}/"
    try:
        idx_resp = session.get(api_index, timeout=30)
        if idx_resp.ok:
            for match in re.findall(r"href=[\"']([^\"']+\.pdf)[\"']", idx_resp.text, re.IGNORECASE):
                urls.add(urljoin(api_index, match))
    except Exception as exc:
        LOGGER.warning("API index discovery failed: %s", exc)

    return sorted(urls)


def download_pdf(url: str) -> bytes:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content
