import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, verify_password
from app.models.connection import Connection
from app.models.transfer import Transfer, TransferStatus
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


def _get_dashboard_user(request: Request, db: Session) -> User | None:
    """
    Variante non-bloquante de get_current_user pour les pages HTML :
    renvoie None plutôt que de lever une 401, pour permettre une redirection
    propre vers la page de connexion.
    """
    token = request.cookies.get("access_token")
    if not token:
        return None
    email = decode_access_token(token)
    if not email:
        return None
    return db.query(User).filter(User.email == email).first()


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, error: str | None = None):
    return templates.TemplateResponse(request=request, name="login.html", context={"request": request, "error": error})


@router.post("/login")
def login_submit(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url="/dashboard/login?error=1", status_code=303)

    token = create_access_token(subject=user.email)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="access_token", value=token, httponly=True, samesite="lax", max_age=60 * 60 * 24,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse(url="/dashboard/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@router.get("", response_class=HTMLResponse)
def dashboard_home(request: Request, db: Session = Depends(get_db)):
    current_user = _get_dashboard_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    connections = db.query(Connection).filter(Connection.owner_id == current_user.id).all()
    return templates.TemplateResponse(
    request=request, name="dashboard.html", context={"request": request, "user": current_user, "connections": connections}
)


@router.get("/transfers/{transfer_id}", response_class=HTMLResponse)
def transfer_detail_page(transfer_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    current_user = _get_dashboard_user(request, db)
    if not current_user:
        return RedirectResponse(url="/dashboard/login", status_code=303)

    transfer = (
        db.query(Transfer)
        .filter(Transfer.id == transfer_id, Transfer.owner_id == current_user.id)
        .first()
    )
    if not transfer:
        raise HTTPException(404, "Transfer not found")

    return templates.TemplateResponse(request=request, name="transfer_detail.html", context={"request": request, "transfer": transfer})


@router.get("/api/stats")
def dashboard_stats(request: Request, db: Session = Depends(get_db)):
    current_user = _get_dashboard_user(request, db)
    if not current_user:
        raise HTTPException(401, "Not authenticated")

    base_query = db.query(Transfer).filter(Transfer.owner_id == current_user.id)
    today = datetime.now(timezone.utc).date()

    transfers_today = base_query.filter(func.date(Transfer.created_at) == today).count()
    running = base_query.filter(Transfer.status == TransferStatus.RUNNING).count()
    completed = base_query.filter(Transfer.status == TransferStatus.COMPLETED).count()
    failed = base_query.filter(Transfer.status == TransferStatus.FAILED).count()

    completed_transfers = base_query.filter(Transfer.status == TransferStatus.COMPLETED).all()
    if completed_transfers:
        durations = [(t.updated_at - t.created_at).total_seconds() for t in completed_transfers]
        avg_duration = round(sum(durations) / len(durations), 1)
    else:
        avg_duration = None

    return {
        "transfers_today": transfers_today,
        "running": running,
        "completed": completed,
        "failed": failed,
        "avg_duration_seconds": avg_duration,
    }