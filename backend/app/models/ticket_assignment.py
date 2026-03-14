"""Ticket assignment model - many-to-many: ticket can have multiple assignees, with who assigned them."""
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class TicketAssignment(Base):
    __tablename__ = "ticket_assignments"
    __table_args__ = (UniqueConstraint("ticket_id", "user_id", name="uq_ticket_assignee"),)

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="assignments")
    assignee = relationship("User", foreign_keys=[user_id], back_populates="ticket_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])
