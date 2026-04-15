from collections import defaultdict
from datetime import date, datetime
import logging
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CauseList, CauseListItem, Match, TrackedTerm, User
from app.services.emailer import send_digest_email
from app.services.matcher import DEFAULT_VARIANTS, match_counsel
from app.services.pdf_parser import extract_text_from_pdf, parse_cause_list_text
from app.services.sci_fetcher import discover_pdf_urls, download_pdf


LOGGER = logging.getLogger(__name__)


def ist_today() -> date:
    return datetime.now(ZoneInfo(settings.timezone)).date()


def build_digest_content(items: list[CauseListItem]) -> tuple[str, str]:
    grouped: dict[str, list[CauseListItem]] = defaultdict(list)
    for item in items:
        grouped[item.court_no or "Unknown"].append(item)

    html_parts = ["<h2>Supreme Court Cause List Digest</h2>"]
    text_parts = ["Supreme Court Cause List Digest"]

    for court, court_items in sorted(grouped.items(), key=lambda pair: pair[0]):
        html_parts.append(f"<h3>Court {court}</h3><ul>")
        text_parts.append(f"\nCourt {court}")
        for item in court_items:
            html_parts.append(
                f"<li><strong>{item.case_no}</strong> | Item {item.item_no or '-'}<br>{item.parties}<br>{item.advocates}</li>"
            )
            text_parts.append(f"- {item.case_no} | Item {item.item_no or '-'} | {item.parties} | {item.advocates}")
        html_parts.append("</ul>")

    return "".join(html_parts), "\n".join(text_parts)


def run_digest(db: Session, target_date: date | None = None) -> int:
    list_date = target_date or ist_today()
    LOGGER.info("Starting digest run for %s", list_date)

    pdf_urls = discover_pdf_urls(list_date)
    LOGGER.info("Discovered %d pdf urls", len(pdf_urls))

    if not pdf_urls:
        return 0

    stored_items: list[CauseListItem] = []
    for pdf_url in pdf_urls:
        existing = db.execute(
            select(CauseList).where(CauseList.list_date == list_date, CauseList.source_url == pdf_url)
        ).scalar_one_or_none()
        if existing:
            stored_items.extend(existing.items)
            continue

        pdf_content = download_pdf(pdf_url)
        text = extract_text_from_pdf(pdf_content)
        cause_list = CauseList(list_date=list_date, source_url=pdf_url, raw_text=text)
        db.add(cause_list)
        db.flush()

        for parsed in parse_cause_list_text(text):
            item = CauseListItem(cause_list_id=cause_list.id, **parsed)
            db.add(item)
            stored_items.append(item)

    db.commit()

    users = db.execute(select(User)).scalars().all()
    if not users:
        return 0

    for user in users:
        terms = [t.term for t in user.tracked_terms]
        if not terms:
            terms = DEFAULT_VARIANTS

        user_matches: list[CauseListItem] = []
        today_item_ids = (
            select(CauseListItem.id).join(CauseList).where(CauseList.list_date == list_date)
        )
        db.query(Match).filter(Match.user_id == user.id, Match.item_id.in_(today_item_ids)).delete(
            synchronize_session="fetch"
        )

        for item in stored_items:
            matched_term = match_counsel(item.advocates or "", terms)
            if matched_term:
                user_matches.append(item)
                db.add(Match(user_id=user.id, item_id=item.id, matched_term=matched_term, matched_on="COUNSEL"))

        db.commit()

        subject = f"SCI Cause List Digest - {list_date.isoformat()} ({len(user_matches)} matches)"
        html_body, text_body = build_digest_content(user_matches)
        if user_matches:
            send_digest_email(user.email, subject, html_body, text_body)
        LOGGER.info("User %s matched %d entries", user.email, len(user_matches))

    return len(stored_items)
