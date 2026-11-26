import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic.alias_generators import to_camel
from sqlalchemy import func
from sqlmodel import Session, select

from .config import settings
from .database import get_session, init_db
from .models import BgvRequest, BgvRequestHistory, BgvRequestIn, LoginRequest, User
from .security import ApiError, create_token, require_auth, verify_password


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="BGV Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ok(data=None, message: Optional[str] = None, **extra):
    body: dict = {"success": True}
    if message is not None:
        body["message"] = message
    if data is not None:
        body["data"] = data
    body.update(extra)
    return body


def _apply(data: BgvRequestIn, target: BgvRequest) -> None:
    # Create and update share the same field mapping; optional identifiers are stored as null, not empty strings.
    target.ps_number = data.ps_number
    target.requested_by_name = data.requested_by_name
    target.rr_number = data.rr_number
    target.employee_type = data.employee_type
    target.candidate_id = data.candidate_id or None
    target.resource_name = data.resource_name
    target.resource_ps_no = data.resource_ps_no or None
    target.resource_type = data.resource_type
    target.geo_region = data.geo_region
    target.country = data.country
    target.status = data.status
    target.bgv_initiated_by = data.bgv_initiated_by
    target.comments_from_pmo = data.comments_from_pmo
    target.bgv_stopped_reason = data.bgv_stopped_reason
    target.onboarding_type = data.onboarding_type
    target.priority = data.priority or "NORMAL"
    target.request_submitted_on = data.request_submitted_on.isoformat()
    target.user_role = data.user_role
    target.interim_date = data.interim_date or None
    target.interim_status = data.interim_status or None
    target.final_bgv_date = data.final_bgv_date or None
    target.final_bgv_status = data.final_bgv_status or None


# History has its own ID and a smaller schema than the current request record.
_HISTORY_EXCLUDE = {"id", "interim_date", "interim_status", "final_bgv_date", "final_bgv_status", "updated_at"}


def _snapshot(session: Session, request: BgvRequest, action: str) -> None:
    try:
        fields = request.model_dump(exclude=_HISTORY_EXCLUDE)
        history = BgvRequestHistory(
            **fields, bgv_request_id=request.id, action=action, snapshot_at=int(time.time())
        )
        session.add(history)
        session.commit()
    except Exception as exc:  # history is best-effort and must never block the main operation
        print(f"Failed to save history snapshot: {exc}")


# --- Auth ---
@app.post("/api/auth/login")
def login(body: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(func.lower(User.email) == body.email.lower())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise ApiError(401, "Invalid email or password")
    return ok(
        data={
            "token": create_token(user),
            "userId": user.id,
            "email": user.email,
            "fullName": user.full_name,
            "role": user.role,
            "organizationId": user.organization_id,
            "candidateId": user.candidate_id,
        }
    )


# --- BGV requests ---
@app.post("/api/bgv-requests", status_code=status.HTTP_201_CREATED)
def create_request(data: BgvRequestIn, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    try:
        if data.candidate_id and session.exec(
            select(BgvRequest).where(BgvRequest.candidate_id == data.candidate_id)
        ).first():
            raise ValueError(f"Candidate ID already exists: {data.candidate_id}")
        if data.resource_ps_no and session.exec(
            select(BgvRequest).where(BgvRequest.resource_ps_no == data.resource_ps_no)
        ).first():
            raise ValueError(f"Resource PS No already exists: {data.resource_ps_no}")
        request = BgvRequest()
        _apply(data, request)
        now = int(time.time())
        request.created_at = now
        request.updated_at = now
        session.add(request)
        session.commit()
        session.refresh(request)
        _snapshot(session, request, "CREATE")
        return ok(request, "BGV Request created successfully")
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(400, f"Error creating BGV Request: {exc}")


@app.put("/api/bgv-requests/{request_id}")
def update_request(
    request_id: str, data: BgvRequestIn, session: Session = Depends(get_session), _: User = Depends(require_auth)
):
    try:
        request = session.get(BgvRequest, request_id)
        if request is None:
            raise ApiError(404, "BGV Request not found")
        _apply(data, request)
        request.updated_at = int(time.time())
        session.add(request)
        session.commit()
        session.refresh(request)
        _snapshot(session, request, "UPDATE")
        return ok(request, "BGV Request updated successfully")
    except ApiError:
        raise
    except Exception as exc:
        raise ApiError(400, f"Error updating BGV Request: {exc}")


@app.get("/api/bgv-requests")
def get_all(session: Session = Depends(get_session), _: User = Depends(require_auth)):
    items = session.exec(select(BgvRequest)).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/ps/{ps_number}")
def get_by_ps(ps_number: str, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    items = session.exec(select(BgvRequest).where(BgvRequest.ps_number == ps_number)).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/history/ps/{ps_number}")
def history_by_ps(ps_number: str, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    items = session.exec(
        select(BgvRequestHistory)
        .where(BgvRequestHistory.ps_number == ps_number)
        .order_by(BgvRequestHistory.snapshot_at.desc())
    ).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/history/resource-ps/{resource_ps_no}")
def history_by_resource_ps(
    resource_ps_no: str, session: Session = Depends(get_session), _: User = Depends(require_auth)
):
    items = session.exec(
        select(BgvRequestHistory)
        .where(BgvRequestHistory.resource_ps_no == resource_ps_no)
        .order_by(BgvRequestHistory.snapshot_at.desc())
    ).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/history/candidate/{candidate_id}")
def history_by_candidate(candidate_id: str, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    items = session.exec(
        select(BgvRequestHistory)
        .where(BgvRequestHistory.candidate_id == candidate_id)
        .order_by(BgvRequestHistory.snapshot_at.desc())
    ).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/history/search/{term}")
def search_history(term: str, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    like = f"%{term.lower()}%"
    statement = (
        select(BgvRequestHistory)
        .where(
            func.lower(BgvRequestHistory.ps_number).like(like)
            | func.lower(BgvRequestHistory.resource_name).like(like)
            | func.lower(BgvRequestHistory.candidate_id).like(like)
            | func.lower(BgvRequestHistory.status).like(like)
        )
        .order_by(func.coalesce(BgvRequestHistory.snapshot_at, BgvRequestHistory.created_at).desc())
    )
    items = session.exec(statement).all()
    return ok(items, total=len(items))


@app.get("/api/bgv-requests/config/country-georegion-mapping")
def country_georegion_mapping(_: User = Depends(require_auth)):
    return ok(settings.country_map)


# Register this catch-all ID route after named routes such as config and history.
@app.get("/api/bgv-requests/{request_id}")
def get_one(request_id: str, session: Session = Depends(get_session), _: User = Depends(require_auth)):
    request = session.get(BgvRequest, request_id)
    if request is None:
        raise ApiError(404, "BGV Request not found")
    return ok(request)


# --- Exception handlers (envelope shapes mirror the Java GlobalExceptionHandler) ---
@app.exception_handler(ApiError)
async def _handle_api_error(request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "timestamp": _now_iso()},
    )


@app.exception_handler(RequestValidationError)
async def _handle_validation(request, exc: RequestValidationError):
    # Match the frontend's camelCase field names and existing 400 validation-error contract.
    errors: dict[str, str] = {}
    for err in exc.errors():
        location = [p for p in err["loc"] if p != "body"]
        field = str(location[-1]) if location else "request"
        errors[to_camel(field)] = err["msg"]
    return JSONResponse(
        status_code=400,
        content={"success": False, "message": "Validation failed", "errors": errors, "timestamp": _now_iso()},
    )


@app.exception_handler(Exception)
async def _handle_generic(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "An unexpected error occurred", "timestamp": _now_iso()},
    )
