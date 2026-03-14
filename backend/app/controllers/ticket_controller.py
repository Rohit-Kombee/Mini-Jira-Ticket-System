"""Ticket API controller."""
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.ticket_schema import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketListResponse,
    AssigneeInfo,
    AssignedToYouBy,
    MessageCreate,
    MessageResponse,
    MessageListResponse,
)
from app.services.auth_service import get_current_user_from_token, get_users_by_ids
from app.services.ticket_service import (
    create_ticket,
    list_tickets,
    get_ticket_by_id,
    update_ticket,
    delete_ticket,
    add_message,
    get_messages,
)
from app.observability.tracing import get_tracer
from fastapi import Request

router = APIRouter(prefix="/tickets", tags=["tickets"])
tracer = get_tracer(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth.split(" ")[1]
    return get_current_user_from_token(db, token)


def _ticket_response(t, user_map: dict[int, str], current_user_id: int | None = None) -> TicketResponse:
    assignees: list[AssigneeInfo] = []
    assigned_to_you_by: AssignedToYouBy | None = None
    for a in getattr(t, "assignments", None) or []:
        assignees.append(
            AssigneeInfo(
                user_id=a.user_id,
                user_name=user_map.get(a.user_id, ""),
                assigned_by_id=a.assigned_by_id,
                assigned_by_name=user_map.get(a.assigned_by_id) if a.assigned_by_id else None,
            )
        )
        if current_user_id and a.user_id == current_user_id and a.assigned_by_id:
            assigned_to_you_by = AssignedToYouBy(id=a.assigned_by_id, name=user_map.get(a.assigned_by_id, ""))
    return TicketResponse(
        id=t.id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        created_by=t.created_by,
        assigned_to=t.assigned_to,
        created_at=t.created_at,
        created_by_name=user_map.get(t.created_by),
        assigned_to_name=user_map.get(t.assigned_to) if t.assigned_to else None,
        assignees=assignees,
        assigned_to_you_by=assigned_to_you_by,
    )


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create(data: TicketCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    with tracer.start_as_current_span("tickets_create_controller"):
        ticket = create_ticket(db, data, user.id, role=user.role)
        user_ids = {ticket.created_by}
        for a in getattr(ticket, "assignments", None) or []:
            user_ids.add(a.user_id)
            if a.assigned_by_id:
                user_ids.add(a.assigned_by_id)
        users = get_users_by_ids(db, list(user_ids))
        user_map = {u.id: u.name for u in users}
        return _ticket_response(ticket, user_map, user.id)


@router.get("", response_model=TicketListResponse)
def list_tickets_api(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    status_filter: str | None = Query(None, alias="status"),
    priority_filter: str | None = Query(None, alias="priority"),
    assigned_to: int | None = Query(None, description="Filter by assignee (admin)"),
    created_by: int | None = Query(None, description="Filter by creator (admin)"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    with tracer.start_as_current_span("tickets_list_controller"):
        tickets, total = list_tickets(
            db,
            user.id,
            role=user.role,
            status_filter=status_filter,
            priority_filter=priority_filter,
            assigned_to_filter=assigned_to,
            created_by_filter=created_by,
            page=page,
            limit=limit,
        )
        tickets = list(tickets)
        if tickets:
            from sqlalchemy.orm import joinedload
            from app.models.ticket import Ticket
            ticket_ids = [t.id for t in tickets]
            loaded = (
                db.query(Ticket)
                .options(joinedload(Ticket.assignments))
                .filter(Ticket.id.in_(ticket_ids))
                .all()
            )
            order_map = {tid: i for i, tid in enumerate(ticket_ids)}
            tickets = sorted(loaded, key=lambda t: order_map[t.id])
        pages = (total + limit - 1) // limit if limit else 0
        user_ids = set(t.created_by for t in tickets) | {t.assigned_to for t in tickets if t.assigned_to}
        for t in tickets:
            for a in getattr(t, "assignments", None) or []:
                user_ids.add(a.user_id)
                if a.assigned_by_id:
                    user_ids.add(a.assigned_by_id)
        users = get_users_by_ids(db, list(user_ids))
        user_map = {u.id: u.name for u in users}
        return TicketListResponse(
            items=[_ticket_response(t, user_map, user.id) for t in tickets],
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    with tracer.start_as_current_span("tickets_get_controller"):
        ticket = get_ticket_by_id(db, ticket_id, user.id, user.role)
        user_ids = [ticket.created_by] + ([ticket.assigned_to] if ticket.assigned_to else [])
        for a in getattr(ticket, "assignments", None) or []:
            user_ids.append(a.user_id)
            if a.assigned_by_id:
                user_ids.append(a.assigned_by_id)
        users = get_users_by_ids(db, list(set(user_ids)))
        user_map = {u.id: u.name for u in users}
        return _ticket_response(ticket, user_map, user.id)


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket_api(
    ticket_id: int,
    data: TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    with tracer.start_as_current_span("tickets_update_controller"):
        ticket = update_ticket(db, ticket_id, data, user.id, user.role)
        user_ids = [ticket.created_by] + ([ticket.assigned_to] if ticket.assigned_to else [])
        for a in getattr(ticket, "assignments", None) or []:
            user_ids.append(a.user_id)
            if a.assigned_by_id:
                user_ids.append(a.assigned_by_id)
        users = get_users_by_ids(db, list(set(user_ids)))
        user_map = {u.id: u.name for u in users}
        return _ticket_response(ticket, user_map, user.id)


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket_api(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    with tracer.start_as_current_span("tickets_delete_controller"):
        delete_ticket(db, ticket_id, user.id, user.role)


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    ticket_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    with tracer.start_as_current_span("tickets_message_create_controller"):
        msg = add_message(db, ticket_id, data, user.id, user.role)
        return MessageResponse(
            id=msg.id,
            ticket_id=msg.ticket_id,
            sender_id=msg.sender_id,
            message=msg.message,
            created_at=msg.created_at,
        )


@router.get("/{ticket_id}/messages", response_model=MessageListResponse)
def list_messages_api(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    with tracer.start_as_current_span("tickets_messages_list_controller"):
        messages = get_messages(db, ticket_id, user.id, user.role)
        return MessageListResponse(
            items=[
                MessageResponse(
                    id=m.id,
                    ticket_id=m.ticket_id,
                    sender_id=m.sender_id,
                    message=m.message,
                    created_at=m.created_at,
                )
                for m in messages
            ],
            total=len(messages),
        )
