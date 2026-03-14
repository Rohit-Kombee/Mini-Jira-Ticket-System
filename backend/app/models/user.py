"""User model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    QA = "qa"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.DEVELOPER.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets_created = relationship("Ticket", back_populates="creator", foreign_keys="Ticket.created_by")
    tickets_assigned = relationship("Ticket", back_populates="assignee", foreign_keys="Ticket.assigned_to")
    ticket_assignments = relationship(
        "TicketAssignment",
        back_populates="assignee",
        foreign_keys="TicketAssignment.user_id",
    )
    messages = relationship("Message", back_populates="sender")
