# SCI Cause List Digest

Web app that sends a daily email digest of Supreme Court of India cause list items matching tracked counsel names.

## MVP implemented

- Supreme Court of India source discovery from published cause list and API date directory attempts.
- Mode A matching (counsel name only), case-insensitive.
- Initial counsel variants seeded on registration:
  - KrishnaMurthy
  - Krishna Murthy
  - Krishnamurthy
  - K. Krishna Murthy
  - K Krishna Murthy
- Basic email/password auth.
- Web UI to add/edit/delete tracked counsel terms and view today's matched items.
- Daily scheduler at **08:00 Asia/Kolkata** in worker service.
- Postgres persistence.
- Raw extracted PDF text stored in `cause_lists.raw_text` for debugging.
- Email digest via SendGrid API or SMTP.
- Basic logging.

## Local development (Docker Compose)

```bash
docker compose up --build
```

App UI: `http://localhost:8000`

Services:
- `web`: FastAPI app/UI
- `worker`: APScheduler background job runner
- `db`: Postgres

## Required environment variables

Set in shell or `.env` (Docker Compose will read them):

- `DATABASE_URL` (default in compose)
- `APP_SECRET_KEY`
- `APP_TIMEZONE` (default `Asia/Kolkata`)
- `APP_MODE` (default `A`)

Email options:

### SendGrid API mode
- `SENDGRID_API_KEY`
- `SENDGRID_FROM`

### SMTP mode (SendGrid SMTP defaulted)
- `SMTP_HOST` (default `smtp.sendgrid.net`)
- `SMTP_PORT` (default `587`)
- `SMTP_USERNAME` (default `apikey`)
- `SMTP_PASSWORD`
- `SMTP_FROM`

## Scheduling behavior

`worker` runs APScheduler cron:
- `hour=8, minute=0`
- timezone: `Asia/Kolkata`

At trigger time it:
1. Discovers PDFs for current IST day.
2. Downloads and extracts text.
3. Heuristically parses case number/parties/advocates.
4. Matches advocates against each user's tracked counsel terms (Mode A).
5. Stores matches and sends digest email.

## Manual run

After login, dashboard includes a **Fetch + Match + Email** button (optional date input) to trigger a manual run.

## Tests

```bash
docker compose run --rm web pytest -q
```
