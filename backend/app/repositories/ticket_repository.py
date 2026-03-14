"""Ticket repository - database access with optional slow-query simulation."""
import time
from typing import List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, select

from app.models.ticket import Ticket
from app.models.ticket_assignment import TicketAssignment
from app.models.message import Message
from app.schemas.ticket_schema import TicketUpdate
from app.observability.metrics import DB_QUERY_DURATION_SECONDS, DB_ERRORS_TOTAL
from app.observability.tracing import get_tracer
from app.config import get_settings

tracer = get_tracer(__name__)
settings = get_settings()


class TicketRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, title: str, description: str | None, priority: str, created_by: int) -> Ticket:
        with tracer.start_as_current_span("db_ticket_create"):
            start = time.perf_counter()
            try:
                ticket = Ticket(
                    title=title,
                    description=description,
                    priority=priority or "medium",
                    status="open",
                    created_by=created_by,
                )
                self.db.add(ticket)
                self.db.commit()
                self.db.refresh(ticket)
                DB_QUERY_DURATION_SECONDS.labels(operation="create").observe(time.perf_counter() - start)
                return ticket
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="create").inc()
                raise

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        with tracer.start_as_current_span("db_ticket_get_by_id"):
            start = time.perf_counter()
            try:
                ticket = (
                    self.db.query(Ticket)
                    .filter(Ticket.id == ticket_id)
                    .options(joinedload(Ticket.assignments))
                    .first()
                )
                DB_QUERY_DURATION_SECONDS.labels(operation="get_by_id").observe(time.perf_counter() - start)
                return ticket
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="get_by_id").inc()
                raise

    def list(
        self,
        user_id: int,
        role: str,
        status_filter: str | None = None,
        priority_filter: str | None = None,
        assigned_to_filter: int | None = None,
        created_by_filter: int | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> Tuple[List[Ticket], int]:
        with tracer.start_as_current_span("db_ticket_list"):
            start = time.perf_counter()
            try:
                if role == "admin":
                    q = self.db.query(Ticket)
                elif role in ("developer", "qa", "agent", "viewer"):
                    sub = self.db.query(TicketAssignment.ticket_id).filter(TicketAssignment.user_id == user_id)
                    q = self.db.query(Ticket).filter(
                        (Ticket.created_by == user_id)
                        | (Ticket.assigned_to == user_id)
                        | Ticket.id.in_(sub)
                    )
                else:
                    q = self.db.query(Ticket).filter(Ticket.created_by == user_id)
                if assigned_to_filter is not None:
                    sub = self.db.query(TicketAssignment.ticket_id).filter(
                        TicketAssignment.user_id == assigned_to_filter
                    )
                    q = q.filter((Ticket.assigned_to == assigned_to_filter) | Ticket.id.in_(sub))
                if created_by_filter is not None:
                    q = q.filter(Ticket.created_by == created_by_filter)
                if status_filter:
                    q = q.filter(Ticket.status == status_filter)
                if priority_filter:
                    q = q.filter(Ticket.priority == priority_filter)
                total = q.count()
                offset = (page - 1) * limit
                items = q.order_by(Ticket.created_at.desc()).offset(offset).limit(limit).all()
                DB_QUERY_DURATION_SECONDS.labels(operation="list").observe(time.perf_counter() - start)
                return items, total
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="list").inc()
                raise

    def update(self, ticket: Ticket, data: TicketUpdate, assigned_by_id: int | None = None) -> Ticket:
        with tracer.start_as_current_span("db_ticket_update"):
            start = time.perf_counter()
            try:
                if data.title is not None:
                    ticket.title = data.title
                if data.description is not None:
                    ticket.description = data.description
                if data.status is not None:
                    ticket.status = data.status
                if data.priority is not None:
                    ticket.priority = data.priority
                if getattr(data, "model_fields_set", None) and "assigned_to" in data.model_fields_set:
                    ticket.assigned_to = data.assigned_to
                if getattr(data, "model_fields_set", None) and "assignee_ids" in data.model_fields_set:
                    ids = data.assignee_ids or []
                    self.db.query(TicketAssignment).filter(TicketAssignment.ticket_id == ticket.id).delete()
                    for uid in ids:
                        self.db.add(
                            TicketAssignment(
                                ticket_id=ticket.id,
                                user_id=uid,
                                assigned_by_id=assigned_by_id,
                            )
                        )
                    ticket.assigned_to = ids[0] if ids else None
                self.db.commit()
                self.db.refresh(ticket)
                ticket = (
                    self.db.query(Ticket)
                    .options(joinedload(Ticket.assignments))
                    .filter(Ticket.id == ticket.id)
                    .first()
                )
                DB_QUERY_DURATION_SECONDS.labels(operation="update").observe(time.perf_counter() - start)
                return ticket
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="update").inc()
                raise

    def add_message(self, ticket_id: int, sender_id: int, message: str) -> Message:
        with tracer.start_as_current_span("db_message_create"):
            start = time.perf_counter()
            try:
                msg = Message(ticket_id=ticket_id, sender_id=sender_id, message=message)
                self.db.add(msg)
                self.db.commit()
                self.db.refresh(msg)
                DB_QUERY_DURATION_SECONDS.labels(operation="add_message").observe(time.perf_counter() - start)
                return msg
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="add_message").inc()
                raise

    def get_messages(self, ticket_id: int) -> List[Message]:
        with tracer.start_as_current_span("db_messages_list"):
            start = time.perf_counter()
            try:
                items = self.db.query(Message).filter(Message.ticket_id == ticket_id).order_by(Message.created_at).all()
                DB_QUERY_DURATION_SECONDS.labels(operation="get_messages").observe(time.perf_counter() - start)
                return items
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="get_messages").inc()
                raise

    def delete(self, ticket: Ticket) -> None:
        with tracer.start_as_current_span("db_ticket_delete"):
            start = time.perf_counter()
            try:
                self.db.query(TicketAssignment).filter(TicketAssignment.ticket_id == ticket.id).delete()
                self.db.query(Message).filter(Message.ticket_id == ticket.id).delete()
                self.db.delete(ticket)
                self.db.commit()
                DB_QUERY_DURATION_SECONDS.labels(operation="delete").observe(time.perf_counter() - start)
            except Exception as e:
                DB_ERRORS_TOTAL.labels(operation="delete").inc()
                raise
