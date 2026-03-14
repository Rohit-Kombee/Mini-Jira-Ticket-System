import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createTicket } from "../api/tickets";
import { getUsers } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import type { User } from "../types";

export function NewTicketPage() {
  const { user: currentUser } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [assigneeIds, setAssigneeIds] = useState<number[]>([]);
  const [developers, setDevelopers] = useState<User[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const isAdmin = currentUser?.role === "admin";

  useEffect(() => {
    if (isAdmin) getUsers("developer,qa").then(setDevelopers).catch(() => setDevelopers([]));
  }, [isAdmin]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const ticket = await createTicket({
        title,
        description: description || undefined,
        priority,
        ...(assigneeIds.length > 0 && { assignee_ids: assigneeIds }),
      });
      navigate(`/tickets/${ticket.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create ticket");
    } finally {
      setLoading(false);
    }
  };

  // Only Admin can create tickets
  if (currentUser && !isAdmin) {
    return (
      <>
        <div style={{ marginBottom: "1rem" }}>
          <Link to="/" style={{ color: "var(--muted)", fontSize: "0.875rem" }}>← Back to tickets</Link>
        </div>
        <div className="card">
          <p className="error-msg">Only Admin can create tickets. You can view tickets assigned to you and add messages.</p>
        </div>
      </>
    );
  }

  const addAssignee = (userId: number) => {
    if (!assigneeIds.includes(userId)) setAssigneeIds([...assigneeIds, userId]);
  };
  const removeAssignee = (userId: number) => {
    setAssigneeIds(assigneeIds.filter((id) => id !== userId));
  };

  return (
    <>
      <div style={{ marginBottom: "1rem" }}>
        <Link to="/" style={{ color: "var(--muted)", fontSize: "0.875rem" }}>← Back to tickets</Link>
      </div>
      <div className="card">
        <h1 style={{ marginTop: 0, marginBottom: "1rem" }}>New ticket</h1>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="title">Title</label>
            <input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={500}
              placeholder="Short summary"
            />
          </div>
          <div className="form-group">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              placeholder="Optional details"
            />
          </div>
          <div className="form-group">
            <label htmlFor="priority">Priority</label>
            <select id="priority" value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>
          {isAdmin && (
            <div className="form-group">
              <label>Assign to (Developer or QA)</label>
              <p style={{ margin: "0.25rem 0 0.5rem", color: "var(--muted)", fontSize: "0.875rem" }}>
                Select one or more Developers or QA. They will see this ticket and who assigned it.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", alignItems: "center" }}>
                {assigneeIds.map((uid) => {
                  const u = developers.find((d) => d.id === uid);
                  return (
                    <span key={uid} className="badge badge-medium" style={{ display: "inline-flex", alignItems: "center", gap: "0.25rem" }}>
                      {u?.name ?? `User #${uid}`}
                      <button type="button" onClick={() => removeAssignee(uid)} aria-label="Remove" style={{ background: "none", border: "none", cursor: "pointer", padding: "0 0.2rem", lineHeight: 1 }}>×</button>
                    </span>
                  );
                })}
                <select
                  value=""
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v) addAssignee(Number(v));
                    e.target.value = "";
                  }}
                  style={{ minWidth: "14rem" }}
                  aria-label="Add Developer or QA to assign"
                >
                  <option value="">+ Add assignee (multiple allowed)</option>
                  {developers.filter((d) => !assigneeIds.includes(d.id)).map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} — {d.role === "developer" || d.role === "agent" ? "Developer" : d.role === "qa" || d.role === "viewer" ? "QA" : d.role}
                    </option>
                  ))}
                </select>
              </div>
              {developers.length === 0 && (
                <p style={{ margin: "0.25rem 0 0", color: "var(--muted)", fontSize: "0.8rem" }}>
                  No Developer or QA accounts found. Create accounts first.
                </p>
              )}
            </div>
          )}
          {error && <p className="error-msg">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Creating…" : "Create ticket"}
          </button>
        </form>
      </div>
    </>
  );
}
