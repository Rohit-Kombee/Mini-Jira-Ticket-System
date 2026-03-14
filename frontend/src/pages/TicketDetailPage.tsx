import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getTicket, updateTicket, deleteTicket, getMessages, addMessage } from "../api/tickets";
import { getUsers } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, Message, User } from "../types";

function statusClass(s: string) {
  const k = s.toLowerCase().replace(/\s+/g, "-");
  if (k === "open") return "badge-open";
  if (k === "in_progress" || k === "in progress") return "badge-in-progress";
  if (k === "resolved" || k === "closed") return "badge-resolved";
  return "";
}

function priorityClass(p: string) {
  const k = p.toLowerCase();
  if (k === "low") return "badge-low";
  if (k === "medium") return "badge-medium";
  if (k === "high" || k === "critical") return "badge-high";
  return "";
}

export function TicketDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user: currentUser } = useAuth();
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [developers, setDevelopers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [editPriority, setEditPriority] = useState("");
  const [editAssigneeIds, setEditAssigneeIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);
  const [newMessage, setNewMessage] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);

  const ticketId = id ? parseInt(id, 10) : NaN;
  const isAdmin = currentUser?.role === "admin";
  const isDeveloper = currentUser?.role === "developer" || currentUser?.role === "agent";
  const isQA = currentUser?.role === "qa" || currentUser?.role === "viewer";
  const isClosed = ticket?.status === "closed" || ticket?.status === "resolved";
  const canEditFull = isAdmin;
  const canEditProgress = isDeveloper;
  const canEditStatus = isQA;
  const canAssign = isAdmin;
  const canDelete = isAdmin;
  const canClose = isAdmin || isQA;

  const loadTicket = async () => {
    if (!id || isNaN(ticketId)) return;
    setLoading(true);
    setError("");
    try {
      const t = await getTicket(ticketId);
      setTicket(t);
      setEditTitle(t.title);
      setEditDescription(t.description || "");
      setEditStatus(t.status);
      setEditPriority(t.priority);
      setEditAssigneeIds(t.assignees?.map((a) => a.user_id) ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ticket");
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async () => {
    if (!id || isNaN(ticketId)) return;
    try {
      const res = await getMessages(ticketId);
      setMessages(res.items);
    } catch {
      setMessages([]);
    }
  };

  useEffect(() => {
    loadTicket();
  }, [id]);

  useEffect(() => {
    if (ticket) {
      loadMessages();
      setEditAssigneeIds(ticket.assignees?.map((a) => a.user_id) ?? []);
    }
  }, [ticket?.id]);

  useEffect(() => {
    if (isAdmin) getUsers("developer,qa").then(setDevelopers).catch(() => setDevelopers([]));
  }, [isAdmin]);

  const handleSave = async () => {
    if (!ticket || isNaN(ticketId)) return;
    setSaving(true);
    try {
      let payload: Parameters<typeof updateTicket>[1];
      if (isAdmin) {
        payload = { title: editTitle, description: editDescription || undefined, status: editStatus, priority: editPriority, assignee_ids: editAssigneeIds };
      } else if (isDeveloper) {
        payload = { description: editDescription || undefined };
      } else if (isQA) {
        payload = { status: editStatus };
      } else {
        setSaving(false);
        return;
      }
      const updated = await updateTicket(ticketId, payload);
      setTicket(updated);
      setEditMode(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Update failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!ticket || isNaN(ticketId) || !canDelete) return;
    if (!window.confirm("Delete this ticket? This cannot be undone.")) return;
    setSaving(true);
    try {
      await deleteTicket(ticketId);
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setSaving(false);
    }
  };

  const handleClose = async () => {
    if (!ticket || isNaN(ticketId)) return;
    setSaving(true);
    try {
      const updated = await updateTicket(ticketId, { status: "closed" });
      setTicket(updated);
      setEditStatus("closed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to close");
    } finally {
      setSaving(false);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || isNaN(ticketId)) return;
    setSendingMessage(true);
    try {
      await addMessage(ticketId, newMessage.trim());
      setNewMessage("");
      loadMessages();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setSendingMessage(false);
    }
  };

  if (loading || !ticket) {
    return (
      <div className="card">
        {error ? <p className="error-msg">{error}</p> : <p style={{ color: "var(--muted)" }}>Loading…</p>}
      </div>
    );
  }

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/" style={{ color: "var(--muted)", fontSize: "0.875rem" }}>← Back to tickets</Link>
      </div>

      <div className="card">
        {!editMode ? (
          <>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "0.75rem" }}>
              <h1 style={{ margin: 0, fontSize: "1.5rem" }}>{ticket.title}</h1>
              <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                {!isClosed && canClose && (
                  <button type="button" className="btn btn-sm btn-danger" onClick={handleClose} disabled={saving}>
                    {saving ? "…" : "Close ticket"}
                  </button>
                )}
                {(canEditFull || canEditProgress || canEditStatus) && (
                  <button type="button" className="btn btn-sm" onClick={() => setEditMode(true)}>
                    {canEditFull ? "Edit" : canEditProgress ? "Update progress" : "Update status"}
                  </button>
                )}
                {canDelete && (
                  <button type="button" className="btn btn-sm" style={{ borderColor: "var(--danger)", color: "var(--danger)" }} onClick={handleDelete} disabled={saving}>
                    Delete
                  </button>
                )}
              </div>
            </div>
            {ticket.description && <p style={{ marginTop: "0.75rem", color: "var(--muted)" }}>{ticket.description}</p>}
            {ticket.assigned_to_you_by && (
              <p style={{ margin: 0, padding: "0.5rem 0.75rem", background: "var(--border)", borderRadius: "6px", fontSize: "0.9rem" }}>
                <strong>{ticket.assigned_to_you_by.name}</strong> assigned you this ticket.
              </p>
            )}
            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
              <span className={`badge ${statusClass(ticket.status)}`}>{ticket.status}</span>
              <span className={`badge ${priorityClass(ticket.priority)}`}>{ticket.priority}</span>
              <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                Created by {ticket.created_by_name ?? "—"}
              </span>
              {(ticket.assignees?.length ?? 0) > 0 && (
                <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>
                  · Assigned to: {ticket.assignees!.map((a) => a.user_name).join(", ")}
                </span>
              )}
            </div>
            {canAssign && (
              <div className="form-group" style={{ marginTop: "1rem", paddingTop: "1rem", borderTop: "1px solid var(--border)" }}>
                <label>Assign to (Developer or QA, multiple)</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                  {(ticket.assignees ?? []).map((a) => (
                    <span
                      key={a.user_id}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.25rem",
                        padding: "0.25rem 0.5rem",
                        background: "var(--border)",
                        borderRadius: "6px",
                        fontSize: "0.875rem",
                      }}
                    >
                      {a.user_name}
                      {a.assigned_by_name && <span style={{ color: "var(--muted)", fontSize: "0.75rem" }}>(by {a.assigned_by_name})</span>}
                      <button
                        type="button"
                        onClick={async () => {
                          const next = (ticket.assignees ?? []).filter((x) => x.user_id !== a.user_id).map((x) => x.user_id);
                          setSaving(true);
                          try {
                            const updated = await updateTicket(ticketId, { assignee_ids: next });
                            setTicket(updated);
                          } catch (err) {
                            setError(err instanceof Error ? err.message : "Failed to update");
                          } finally {
                            setSaving(false);
                          }
                        }}
                        disabled={saving}
                        style={{ marginLeft: "0.25rem", padding: "0 0.25rem", cursor: "pointer", background: "none", border: "none", color: "var(--muted)" }}
                        aria-label="Remove"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  <select
                    value=""
                    onChange={async (e) => {
                      const uid = Number(e.target.value);
                      if (!uid) return;
                      e.target.value = "";
                      const current = ticket.assignees?.map((a) => a.user_id) ?? [];
                      if (current.includes(uid)) return;
                      const next = [...current, uid];
                      setSaving(true);
                      try {
                        const updated = await updateTicket(ticketId, { assignee_ids: next });
                        setTicket(updated);
                      } catch (err) {
                        setError(err instanceof Error ? err.message : "Failed to add assignee");
                      } finally {
                        setSaving(false);
                      }
                    }}
                    disabled={saving}
                    style={{ minWidth: "140px" }}
                  >
                    <option value="">+ Add assignee</option>
                    {developers
                      .filter((d) => !(ticket.assignees ?? []).some((a) => a.user_id === d.id))
                      .map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.role === "developer" || d.role === "agent" ? "Developer" : d.role === "qa" || d.role === "viewer" ? "QA" : d.role})
                        </option>
                      ))}
                  </select>
                </div>
                {developers.length === 0 && (
                  <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>No Developer or QA accounts. Create them in the Users page.</p>
                )}
              </div>
            )}
          </>
        ) : (
          <>
            <h2 style={{ marginTop: 0 }}>{canEditFull ? "Edit ticket" : canEditProgress ? "Update progress" : "Update status"}</h2>
            {canEditFull && (
              <>
                <div className="form-group">
                  <label>Title</label>
                  <input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea value={editDescription} onChange={(e) => setEditDescription(e.target.value)} rows={3} />
                </div>
                <div className="form-group">
                  <label>Status</label>
                  <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                    <option value="open">Open</option>
                    <option value="in_progress">In progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Priority</label>
                  <select value={editPriority} onChange={(e) => setEditPriority(e.target.value)}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
              </>
            )}
            {canEditProgress && !canEditFull && (
              <div className="form-group">
                <label>Progress / Description</label>
                <textarea value={editDescription} onChange={(e) => setEditDescription(e.target.value)} rows={3} placeholder="Update progress or notes…" />
              </div>
            )}
            {canEditStatus && !canEditFull && (
              <div className="form-group">
                <label>Status (for testing)</label>
                <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
                  <option value="open">Open</option>
                  <option value="in_progress">In progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="closed">Closed</option>
                </select>
              </div>
            )}
            {canAssign && (
              <div className="form-group">
                <label>Assign to (Developer or QA, multiple)</label>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                  {editAssigneeIds.map((uid) => {
                    const u = developers.find((d) => d.id === uid) || ticket?.assignees?.find((a) => a.user_id === uid);
                    const name = u ? ("name" in u ? u.name : u.user_name) : `User #${uid}`;
                    return (
                      <span
                        key={uid}
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                          padding: "0.25rem 0.5rem",
                          background: "var(--border)",
                          borderRadius: "6px",
                          fontSize: "0.875rem",
                        }}
                      >
                        {name}
                        <button
                          type="button"
                          onClick={() => setEditAssigneeIds((prev) => prev.filter((id) => id !== uid))}
                          style={{ marginLeft: "0.25rem", padding: "0 0.25rem", cursor: "pointer", background: "none", border: "none", color: "var(--muted)" }}
                          aria-label="Remove"
                        >
                          ×
                        </button>
                      </span>
                    );
                  })}
                  <select
                    value=""
                    onChange={(e) => {
                      const uid = Number(e.target.value);
                      if (uid && !editAssigneeIds.includes(uid)) setEditAssigneeIds((prev) => [...prev, uid]);
                      e.target.value = "";
                    }}
                    style={{ minWidth: "140px" }}
                  >
                    <option value="">+ Add assignee</option>
                    {developers.filter((d) => !editAssigneeIds.includes(d.id)).map((d) => (
                      <option key={d.id} value={d.id}>{d.name} ({d.role === "developer" || d.role === "agent" ? "Developer" : d.role === "qa" || d.role === "viewer" ? "QA" : d.role})</option>
                    ))}
                  </select>
                </div>
              </div>
            )}
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button type="button" className="btn btn-primary" onClick={handleSave} disabled={saving}>
                {saving ? "Saving…" : "Save"}
              </button>
              <button type="button" className="btn" onClick={() => setEditMode(false)}>
                Cancel
              </button>
            </div>
          </>
        )}
      </div>

      {error && <p className="error-msg">{error}</p>}

      <h2 style={{ marginTop: "1.5rem", marginBottom: "0.75rem" }}>Messages</h2>
      <div className="card">
        {messages.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No messages yet.</p>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {messages.map((m) => (
              <li
                key={m.id}
                style={{
                  padding: "0.75rem 0",
                  borderBottom: "1px solid var(--border)",
                }
              }
              >
                <p style={{ margin: 0 }}>{m.message}</p>
                <p style={{ margin: "0.25rem 0 0", fontSize: "0.8rem", color: "var(--muted)" }}>
                  Message #{m.id} · {m.created_at ? new Date(m.created_at).toLocaleString() : ""}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <form onSubmit={handleSendMessage} className="card" style={{ marginTop: "0.5rem" }}>
        <div className="form-group" style={{ marginBottom: "0.75rem" }}>
          <label htmlFor="new-msg">Add message</label>
          <textarea
            id="new-msg"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message…"
            rows={2}
            required
          />
        </div>
        <button type="submit" className="btn btn-primary" disabled={sendingMessage || !newMessage.trim()}>
          {sendingMessage ? "Sending…" : "Send"}
        </button>
      </form>
    </>
  );
}
