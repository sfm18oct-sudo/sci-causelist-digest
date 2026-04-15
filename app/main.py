from datetime import date
from contextlib import asynccontextmanager
import logging
from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.auth import hash_password, verify_password
from app.config import settings
from app.database import Base, engine, get_db
from app.models import Match, TrackedTerm, User
from app.services.digest import ist_today, run_digest
from app.services.matcher import DEFAULT_VARIANTS


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="SCI Cause List Digest", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    terms = db.execute(select(TrackedTerm).where(TrackedTerm.user_id == user.id).order_by(TrackedTerm.id.desc())).scalars().all()
    today = ist_today()
    matches = (
        db.query(Match)
        .join(Match.item)
        .filter(Match.user_id == user.id)
        .all()
    )
    today_matches = [m for m in matches if m.item.cause_list.list_date == today]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "terms": terms,
            "today": today,
            "today_matches": today_matches,
            "timezone": settings.timezone,
        },
    )


@app.get("/register", response_class=HTMLResponse)
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": ""})


@app.post("/register", response_class=HTMLResponse)
def register_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if existing:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already exists"})

    user = User(email=email.lower(), password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)

    for variant in DEFAULT_VARIANTS:
        db.add(TrackedTerm(user_id=user.id, term=variant))
    db.commit()

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    request.session["user_id"] = user.id
    return RedirectResponse("/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@app.post("/terms")
def add_term(request: Request, term: str = Form(...), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)
    if term.strip():
        db.add(TrackedTerm(user_id=user.id, term=term.strip()))
        db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/terms/{term_id}/delete")
def delete_term(term_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    term = db.get(TrackedTerm, term_id)
    if term and term.user_id == user.id:
        db.delete(term)
        db.commit()

    return RedirectResponse("/", status_code=303)


@app.post("/terms/{term_id}/edit")
def edit_term(term_id: int, request: Request, term: str = Form(...), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    target = db.get(TrackedTerm, term_id)
    if not target or target.user_id != user.id:
        raise HTTPException(status_code=404, detail="Term not found")
    target.term = term.strip()
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/matches/today", response_class=HTMLResponse)
def today_matches(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    today = ist_today()
    matches = db.query(Match).join(Match.item).filter(Match.user_id == user.id).all()
    items = [m.item for m in matches if m.item.cause_list.list_date == today]
    return templates.TemplateResponse(
        "matches.html",
        {"request": request, "items": items, "today": today, "user": user},
    )


@app.post("/admin/run-fetch")
def admin_run_fetch(request: Request, date_value: str = Form(""), db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    target = date.fromisoformat(date_value) if date_value else None
    run_digest(db, target)
    return RedirectResponse("/", status_code=303)
