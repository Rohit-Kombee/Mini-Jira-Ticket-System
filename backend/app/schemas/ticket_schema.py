"""Ticket and message schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: str = "medium"
    assignee_ids: Optional[List[int]] = None  # Admin only: assign to developers/viewers when creating


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[int] = None
    assignee_ids: Optional[List[int]] = None


class AssigneeInfo(BaseModel):
    user_id: int
    user_name: str
    assigned_by_id: Optional[int] = None
    assigned_by_name: Optional[str] = None


class AssignedToYouBy(BaseModel):
    id: int
    name: str


class TicketResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    created_by: int
    assigned_to: Optional[int] = None
    created_at: Optional[datetime] = None
    created_by_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assignees: List[AssigneeInfo] = Field(default_factory=list)
    assigned_to_you_by: Optional[AssignedToYouBy] = None

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    limit: int
    pages: int


class MessageCreate(BaseModel):
    message: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    id: int
    ticket_id: int
    sender_id: int
    message: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    items: List[MessageResponse]
    total: int
