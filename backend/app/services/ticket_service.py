"""Ticket and message service with anomaly injection for observability demo."""
import random
import time
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.ticket import Ticket
from app.models.message import Message
from app.models.user import User
from app.schemas.ticket_schema import TicketCreate, TicketUpdate, MessageCreate
from app.repositories.ticket_repository import TicketRepository
from app.services.auth_service import get_users_by_ids
from app.observability.logging import get_logger
from app.observability.metrics import TICKETS_CREATED_TOTAL, TICKETS_BY_STATUS, DB_QUERY_DURATION_SECONDS, DB_ERRORS_TOTAL
from app.observability.tracing import get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)
settings = get_settings()


def _inject_anomalies():
    """Inject artificial delay and random errors for observability demo."""
    if settings.enable_anomaly_delay and settings.anomaly_delay_seconds:
        time.sleep(settings.anomaly_delay_seconds)
    if settings.anomaly_error_rate and random.random() < settings.anomaly_error_rate:
        logger.error("anomaly_injected_random_failure", extra={"detail": "Random failure"})
        raise Exception("Random failure (anomaly injection)")


def _slow_query_simulation(db: Session):
    """Simulate a slow query for observability (extra delay)."""
    if not settings.enable_slow_query_simulation:
        return
    with tracer.start_as_current_span("slow_query_simulation") as span:
        span.set_attribute("simulation", True)
        time.sleep(0.15)


def _normalize_role(role: str) -> str:
    """Normalize legacy role names to admin, developer, qa."""
    r = (role or "").lower().strip()
    if r in ("agent",):
        return "developer"
    if r in ("viewer",):
        return "qa"
    return r if r in ("admin", "developer", "qa") else "developer"


def create_ticket(db: Session, data: TicketCreate, user_id: int, role: str) -> Ticket:
    with tracer.start_as_current_span("ticket_service_create") as span:
        span.set_attribute("user_id", user_id)
        role = _normalize_role(role)
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can create tickets",
            )
        _inject_anomalies()
        repo = TicketRepository(db)
        ticket = repo.create(title=data.title, description=data.description, priority=data.priority, created_by=user_id)
        TICKETS_CREATED_TOTAL.inc()
        # Admin assigns to Developer or QA only
        assignee_ids = getattr(data, "assignee_ids", None)
        if assignee_ids:
            assignees = get_users_by_ids(db, assignee_ids)
            allowed_roles = {"developer", "qa"}
            if not all(_normalize_role(u.role) in allowed_roles for u in assignees) or len(assignees) != len(assignee_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignees must be Developers or QA only",
                )
            from app.schemas.ticket_schema import TicketUpdate
            repo.update(ticket, TicketUpdate(assignee_ids=assignee_ids), assigned_by_id=user_id)
            ticket = repo.get_by_id(ticket.id)
        logger.info("ticket_created", extra={"ticket_id": ticket.id, "user_id": user_id})
        return ticket


def _can_access_ticket(ticket: Ticket, user_id: int, role: str) -> bool:
    role = _normalize_role(role)
    if role == "admin":
        return True
    if ticket.created_by == user_id or ticket.assigned_to == user_id:
        return True
    if role in ("developer", "qa") and getattr(ticket, "assignments", None):
        if any(a.user_id == user_id for a in ticket.assignments):
            return True
    return False


def list_tickets(
    db: Session,
    user_id: int,
    role: str,
    status_filter: str | None = None,
    priority_filter: str | None = None,
    assigned_to_filter: int | None = None,
    created_by_filter: int | None = None,
    page: int = 1,
    limit: int = 10,
) -> tuple[list[Ticket], int]:
    with tracer.start_as_current_span("ticket_service_list") as span:
        span.set_attribute("page", page)
        span.set_attribute("limit", limit)
        role = _normalize_role(role)
        _inject_anomalies()
        _slow_query_simulation(db)
        repo = TicketRepository(db)
        tickets, total = repo.list(
            user_id=user_id,
            role=role,
            status_filter=status_filter,
            priority_filter=priority_filter,
            assigned_to_filter=assigned_to_filter,
            created_by_filter=created_by_filter,
            page=page,
            limit=limit,
        )
        return tickets, total


def get_ticket_by_id(db: Session, ticket_id: int, user_id: int, role: str) -> Ticket:
    with tracer.start_as_current_span("ticket_service_get") as span:
        span.set_attribute("ticket_id", ticket_id)
        role = _normalize_role(role)
        repo = TicketRepository(db)
        ticket = repo.get_by_id(ticket_id)
        if not ticket:
            logger.warning("ticket_not_found", extra={"ticket_id": ticket_id})
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        if not _can_access_ticket(ticket, user_id, role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this ticket")
        return ticket


def update_ticket(db: Session, ticket_id: int, data: TicketUpdate, user_id: int, role: str) -> Ticket:
    with tracer.start_as_current_span("ticket_service_update") as span:
        span.set_attribute("ticket_id", ticket_id)
        role = _normalize_role(role)
        ticket = get_ticket_by_id(db, ticket_id, user_id, role)
        repo = TicketRepository(db)
        # Admin: full update (assign only to Developer/QA)
        if role == "admin":
            assignee_ids = getattr(data, "assignee_ids", None)
            if assignee_ids is not None and getattr(data, "model_fields_set", None) and "assignee_ids" in data.model_fields_set:
                assignees = get_users_by_ids(db, assignee_ids)
                allowed_roles = {"developer", "qa"}
                if not all(_normalize_role(u.role) in allowed_roles for u in assignees) or len(assignees) != len(assignee_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Assignees must be Developers or QA only",
                    )
            return repo.update(ticket, data, assigned_by_id=user_id)
        # Developer: can only update description (progress)
        if role == "developer":
            if not (getattr(data, "model_fields_set", None) and "description" in data.model_fields_set):
                return ticket
            return repo.update(ticket, TicketUpdate(description=data.description), assigned_by_id=None)
        # QA: can only update status (for testing)
        if role == "qa":
            if not (getattr(data, "model_fields_set", None) and "status" in data.model_fields_set):
                return ticket
            return repo.update(ticket, TicketUpdate(status=data.status), assigned_by_id=None)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this ticket")


def add_message(db: Session, ticket_id: int, data: MessageCreate, user_id: int, role: str) -> Message:
    with tracer.start_as_current_span("ticket_service_add_message") as span:
        span.set_attribute("ticket_id", ticket_id)
        get_ticket_by_id(db, ticket_id, user_id, role)
        repo = TicketRepository(db)
        return repo.add_message(ticket_id=ticket_id, sender_id=user_id, message=data.message)


def get_messages(db: Session, ticket_id: int, user_id: int, role: str) -> list[Message]:
    with tracer.start_as_current_span("ticket_service_get_messages") as span:
        span.set_attribute("ticket_id", ticket_id)
        get_ticket_by_id(db, ticket_id, user_id, role)
        repo = TicketRepository(db)
        return repo.get_messages(ticket_id)


def delete_ticket(db: Session, ticket_id: int, user_id: int, role: str) -> None:
    with tracer.start_as_current_span("ticket_service_delete") as span:
        span.set_attribute("ticket_id", ticket_id)
        role = _normalize_role(role)
        if role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can delete tickets",
            )
        ticket = get_ticket_by_id(db, ticket_id, user_id, role)
        repo = TicketRepository(db)
        repo.delete(ticket)
        logger.info("ticket_deleted", extra={"ticket_id": ticket_id, "user_id": user_id})
