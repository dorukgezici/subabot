import asyncio
import hashlib
import ipaddress
import logging
import re
import secrets
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager, suppress
from typing import Annotated

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from sqlalchemy import delete, func
from sqlmodel import Session, SQLModel, select
from starlette.middleware.body_limit import RequestBodyLimitMiddleware

from subabot.config import Settings
from subabot.crawler import scan_workspace
from subabot.db import make_engine
from subabot.models import Monitor, Signal, Workspace
from subabot.schemas import (
    MonitorInput,
    MonitorPatch,
    MonitorView,
    SignalPatch,
    SignalView,
    SlackInput,
    TemplateInput,
    WorkspaceInput,
)
from subabot.templates import TEMPLATES

logger = logging.getLogger(__name__)
bearer = HTTPBearer(auto_error=False)


def get_session(request: Request):
    with Session(request.app.state.engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_workspace(session: SessionDep, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if not credentials:
        raise HTTPException(401, "Open or restore your workspace to continue.", headers={"WWW-Authenticate": "Bearer"})
    digest = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    workspace = session.exec(select(Workspace).where(Workspace.token_hash == digest)).first()
    if not workspace:
        raise HTTPException(401, "This workspace key is not valid.", headers={"WWW-Authenticate": "Bearer"})
    return workspace


WorkspaceDep = Annotated[Workspace, Depends(get_workspace)]


def workspace_view(workspace):
    return {"id": workspace.id, "name": workspace.name, "created_at": workspace.created_at}


def get_monitor(session, workspace_id, monitor_id):
    monitor = session.get(Monitor, monitor_id)
    if not monitor or monitor.workspace_id != workspace_id:
        raise HTTPException(404, "Monitor not found.")
    return monitor


def apply_public_slug(monitor):
    if monitor.public and not monitor.share_slug:
        prefix = re.sub(r"[^a-z0-9]+", "-", monitor.name.lower()).strip("-")[:40] or "signal"
        monitor.share_slug = f"{prefix}-{secrets.token_urlsafe(8)}"
    if not monitor.public:
        # Republish creates a fresh link so a withdrawn URL cannot return unexpectedly.
        monitor.share_slug = None


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    engine = make_engine(settings.database_url)
    active_scans = set()
    last_scans = {}
    creation_limits = defaultdict(deque)
    scan_slots = asyncio.Semaphore(3)

    async def run_scan(workspace_id):
        if workspace_id in active_scans:
            raise HTTPException(409, "A scan is already running for this workspace.")
        active_scans.add(workspace_id)
        try:
            async with scan_slots:
                async with asyncio.timeout(120):
                    return await scan_workspace(engine, workspace_id, settings)
        except TimeoutError:
            raise HTTPException(504, "The scan took too long. Signals found so far have been saved.") from None
        finally:
            active_scans.discard(workspace_id)
            last_scans[workspace_id] = time.monotonic()

    async def scheduler():
        while True:
            await asyncio.sleep(settings.scan_interval_seconds)
            with Session(engine) as session:
                ids = list(session.exec(select(Monitor.workspace_id).where(Monitor.enabled).distinct()).all())
            for workspace_id in ids:
                if (
                    workspace_id in active_scans
                    or time.monotonic() - last_scans.get(workspace_id, 0) < settings.scan_cooldown_seconds
                ):
                    continue
                try:
                    await run_scan(workspace_id)
                except Exception:
                    logger.exception("Scheduled workspace scan failed")

    @asynccontextmanager
    async def lifespan(app):
        SQLModel.metadata.create_all(engine)
        task = asyncio.create_task(scheduler()) if settings.scheduler_enabled else None
        yield
        if task:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
        engine.dispose()

    app = FastAPI(title="Subabot API", version="1.0.0", lifespan=lifespan)
    app.state.engine = engine
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url.rstrip("/")],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.add_middleware(RequestBodyLimitMiddleware, max_body_size=32_768)

    @app.middleware("http")
    async def security_headers(request, call_next):
        proxy_secret = settings.proxy_shared_secret.get_secret_value()
        api_request = request.url.path == "/api" or request.url.path.startswith("/api/")
        if (
            proxy_secret
            and api_request
            and request.url.path != "/api/health"
            and not secrets.compare_digest(
                request.headers.get("x-subabot-proxy-secret", "").encode(), proxy_secret.encode()
            )
        ):
            # Authenticate before routing, parsing bodies or updating any rate-limit state.
            # Do not log either the expected secret or the supplied header.
            response = JSONResponse(status_code=401, content={"detail": "Use the trusted frontend to access this API."})
        else:
            response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(RequestValidationError)
    async def safe_validation_error(request, exc):
        # Pydantic's default errors echo input. Never echo a pasted webhook secret.
        errors = [{"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": "1.0.0", "scheduler_enabled": settings.scheduler_enabled}

    @app.post("/api/workspaces", status_code=201)
    def create_workspace(request: Request, session: SessionDep, payload: WorkspaceInput | None = None):
        key = request.client.host if request.client else "unknown"
        if settings.trust_proxy_client_ip:
            try:
                key = str(ipaddress.ip_address(request.headers.get("x-subabot-client-address", "")))
            except ValueError:
                pass
        tick = time.monotonic()
        queue = creation_limits[key]
        while queue and queue[0] < tick - 3600:
            queue.popleft()
        if len(queue) >= 20:
            raise HTTPException(429, "Too many workspaces created. Please try again in an hour.")
        queue.append(tick)
        token = secrets.token_urlsafe(32)
        workspace = Workspace(
            name=payload.name if payload else "My workspace", token_hash=hashlib.sha256(token.encode()).hexdigest()
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)
        return {"token": token, "workspace": workspace_view(workspace)}

    @app.get("/api/workspace")
    def read_workspace(workspace: WorkspaceDep, session: SessionDep):
        monitors = session.exec(
            select(func.count()).select_from(Monitor).where(Monitor.workspace_id == workspace.id)
        ).one()
        signals = session.exec(
            select(func.count()).select_from(Signal).where(Signal.workspace_id == workspace.id)
        ).one()
        unread = session.exec(
            select(func.count()).select_from(Signal).where(Signal.workspace_id == workspace.id, ~Signal.is_read)
        ).one()
        bookmarked = session.exec(
            select(func.count()).select_from(Signal).where(Signal.workspace_id == workspace.id, Signal.is_bookmarked)
        ).one()
        return {
            "workspace": workspace_view(workspace),
            "slack": {"connected": bool(workspace.webhook_url)},
            "stats": {"monitors": monitors, "signals": signals, "unread": unread, "bookmarked": bookmarked},
        }

    @app.patch("/api/workspace")
    def update_workspace(payload: WorkspaceInput, workspace: WorkspaceDep, session: SessionDep):
        workspace.name = payload.name
        session.add(workspace)
        session.commit()
        return workspace_view(workspace)

    @app.delete("/api/workspace", status_code=204)
    def delete_workspace(workspace: WorkspaceDep, session: SessionDep):
        if workspace.id in active_scans:
            raise HTTPException(409, "Wait for the current scan to finish, then delete your workspace.")
        session.exec(delete(Signal).where(Signal.workspace_id == workspace.id))
        session.exec(delete(Monitor).where(Monitor.workspace_id == workspace.id))
        session.delete(workspace)
        session.commit()
        last_scans.pop(workspace.id, None)
        return Response(status_code=204)

    @app.get("/api/monitors", response_model=list[MonitorView])
    def list_monitors(workspace: WorkspaceDep, session: SessionDep):
        return session.exec(
            select(Monitor).where(Monitor.workspace_id == workspace.id).order_by(Monitor.created_at)
        ).all()

    def add_monitor(payload, workspace, session):
        count = session.exec(
            select(func.count()).select_from(Monitor).where(Monitor.workspace_id == workspace.id)
        ).one()
        if count >= settings.max_monitors:
            raise HTTPException(409, f"A workspace can have up to {settings.max_monitors} monitors.")
        monitor = Monitor(**payload.model_dump(), workspace_id=workspace.id)
        apply_public_slug(monitor)
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        return monitor

    @app.post("/api/monitors", response_model=MonitorView, status_code=201)
    def create_monitor(payload: MonitorInput, workspace: WorkspaceDep, session: SessionDep):
        return add_monitor(payload, workspace, session)

    @app.patch("/api/monitors/{monitor_id}", response_model=MonitorView)
    def update_monitor(monitor_id: str, payload: MonitorPatch, workspace: WorkspaceDep, session: SessionDep):
        monitor = get_monitor(session, workspace.id, monitor_id)
        values = {key: getattr(monitor, key) for key in MonitorInput.model_fields}
        values.update(payload.model_dump(exclude_unset=True))
        try:
            validated = MonitorInput.model_validate(values)
        except ValidationError as exc:
            raise HTTPException(
                422, [{"loc": ["body", *error["loc"]], "msg": error["msg"]} for error in exc.errors()]
            ) from None
        monitor.sqlmodel_update(validated.model_dump())
        apply_public_slug(monitor)
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        return monitor

    @app.delete("/api/monitors/{monitor_id}", status_code=204)
    def delete_monitor(monitor_id: str, workspace: WorkspaceDep, session: SessionDep):
        if workspace.id in active_scans:
            raise HTTPException(409, "Wait for the current scan to finish, then delete this monitor.")
        monitor = get_monitor(session, workspace.id, monitor_id)
        session.exec(delete(Signal).where(Signal.monitor_id == monitor.id))
        session.delete(monitor)
        session.commit()
        return Response(status_code=204)

    @app.post("/api/monitors/{monitor_id}/publish", response_model=MonitorView)
    def publish_monitor(monitor_id: str, workspace: WorkspaceDep, session: SessionDep):
        return update_monitor(monitor_id, MonitorPatch(public=True), workspace, session)

    @app.get("/api/signals", response_model=list[SignalView])
    def list_signals(
        workspace: WorkspaceDep,
        session: SessionDep,
        monitor_id: str | None = None,
        bookmarked: bool | None = None,
        unread: bool | None = None,
        search: str = Query(default="", max_length=200),
        limit: int = Query(default=100, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ):
        query = select(Signal).where(Signal.workspace_id == workspace.id)
        if monitor_id:
            get_monitor(session, workspace.id, monitor_id)
            query = query.where(Signal.monitor_id == monitor_id)
        if bookmarked is not None:
            query = query.where(Signal.is_bookmarked == bookmarked)
        if unread is not None:
            query = query.where(Signal.is_read == (not unread))
        if search:
            escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            query = query.where(
                Signal.title.ilike(f"%{escaped}%", escape="\\") | Signal.summary.ilike(f"%{escaped}%", escape="\\")
            )
        return session.exec(query.order_by(Signal.published_at.desc(), Signal.id).offset(offset).limit(limit)).all()

    @app.patch("/api/signals/{signal_id}", response_model=SignalView)
    def update_signal(signal_id: str, payload: SignalPatch, workspace: WorkspaceDep, session: SessionDep):
        signal = session.get(Signal, signal_id)
        if not signal or signal.workspace_id != workspace.id:
            raise HTTPException(404, "Signal not found.")
        signal.sqlmodel_update(payload.model_dump(exclude_none=True))
        session.add(signal)
        session.commit()
        session.refresh(signal)
        return signal

    @app.post("/api/scan")
    async def scan(workspace: WorkspaceDep):
        if time.monotonic() - last_scans.get(workspace.id, 0) < settings.scan_cooldown_seconds:
            raise HTTPException(429, "Your last scan just finished. Try again in a few seconds.")
        return await run_scan(workspace.id)

    @app.get("/api/templates")
    def templates():
        return TEMPLATES

    @app.post("/api/monitors/from-template/{template_id}", response_model=MonitorView, status_code=201)
    def from_template(
        template_id: str,
        workspace: WorkspaceDep,
        session: SessionDep,
        payload: TemplateInput | None = None,
    ):
        template = next((item for item in TEMPLATES if item["id"] == template_id), None)
        if not template:
            raise HTTPException(404, "Template not found.")
        fields = {key: value for key, value in template.items() if key in MonitorInput.model_fields}
        if payload and payload.name:
            fields["name"] = payload.name
        return add_monitor(MonitorInput(**fields), workspace, session)

    @app.get("/api/public/{slug}")
    def public_monitor(slug: str, session: SessionDep):
        monitor = session.exec(select(Monitor).where(Monitor.share_slug == slug, Monitor.public)).first()
        if not monitor:
            raise HTTPException(404, "This board is private or no longer available.")
        signals = session.exec(
            select(Signal).where(Signal.monitor_id == monitor.id).order_by(Signal.published_at.desc()).limit(100)
        ).all()
        fields = {
            key: getattr(monitor, key)
            for key in (
                "id",
                "name",
                "description",
                "keywords",
                "exclude_keywords",
                "match_mode",
                "feed_urls",
                "color",
                "share_slug",
            )
        }
        return {
            "monitor": fields,
            "signals": [
                SignalView.model_validate(signal).model_dump(exclude={"is_read", "is_bookmarked"}) for signal in signals
            ],
        }

    @app.post("/api/integrations/slack")
    def connect_slack(payload: SlackInput, workspace: WorkspaceDep, session: SessionDep):
        workspace.webhook_url = payload.webhook_url
        session.add(workspace)
        session.commit()
        return {"connected": True}

    @app.delete("/api/integrations/slack", status_code=204)
    def disconnect_slack(workspace: WorkspaceDep, session: SessionDep):
        workspace.webhook_url = None
        for signal in session.exec(
            select(Signal).where(Signal.workspace_id == workspace.id, Signal.delivery_pending)
        ).all():
            signal.delivery_pending = False
            session.add(signal)
        session.add(workspace)
        session.commit()
        return Response(status_code=204)

    return app


app = create_app()


def start():
    uvicorn.run("subabot.api:app", host="0.0.0.0", port=8000)
