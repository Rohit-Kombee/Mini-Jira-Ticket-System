import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getTickets } from "../api/tickets";
import { getUsers } from "../api/users";
import { useAuth } from "../auth/AuthContext";
import type { Ticket, User } from "../types";

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
  if (k === "high") return "badge-high";
  if (k === "critical") return "badge-high";
  return "";
}

export function TicketListPage() {
  const { user } = useAuth();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [assigneeFilter, setAssigneeFilter] = useState<number | "">("");
  const [assignableUsers, setAssignableUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const isAdmin = user?.role === "admin";

  useEffect(() => {
    if (isAdmin) getUsers("developer,qa").then(setAssignableUsers).catch(() => setAssignableUsers([]));
  }, [isAdmin]);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await getTickets({
        page,
        limit: 10,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        assigned_to: assigneeFilter === "" ? undefined : (assigneeFilter as number),
      });
      setTickets(res.items);
      setTotal(res.total);
      setPages(res.pages);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tickets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [page, statusFilter, priorityFilter, assigneeFilter]);

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0 }}>Tickets</h1>
        {isAdmin && (
          <Link to="/tickets/new" className="btn btn-primary">
            New ticket
          </Link>
        )}
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", alignItems: "center" }}>
          <div className="form-group" style={{ marginBottom: 0, minWidth: "120px" }}>
            <label htmlFor="status">Status</label>
            <select
              id="status"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            >
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="in_progress">In progress</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div className="form-group" style={{ marginBottom: 0, minWidth: "120px" }}>
            <label htmlFor="priority">Priority</label>
            <select
              id="priority"
              value={priorityFilter}
              onChange={(e) => { setPriorityFilter(e.target.value); setPage(1); }}
            >
              <option value="">All</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
          {isAdmin && (
            <div className="form-group" style={{ marginBottom: 0, minWidth: "160px" }}>
              <label htmlFor="assignee">Assigned to</label>
              <select
                id="assignee"
                value={assigneeFilter}
                onChange={(e) => { setAssigneeFilter(e.target.value === "" ? "" : Number(e.target.value)); setPage(1); }}
              >
                <option value="">All</option>
                {assignableUsers.map((u) => (
                  <option key={u.id} value={u.id}>{u.name} ({u.role === "developer" || u.role === "agent" ? "Developer" : u.role === "qa" || u.role === "viewer" ? "QA" : u.role})</option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>

      {error && <p className="error-msg">{error}</p>}
      {loading ? (
        <p style={{ color: "var(--muted)" }}>Loading tickets…</p>
      ) : tickets.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0, color: "var(--muted)" }}>No tickets yet. Create one to get started.</p>
        </div>
      ) : (
        <>
          {tickets.map((t) => (
            <div key={t.id} className="card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.75rem" }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <Link to={`/tickets/${t.id}`} style={{ fontWeight: 600, fontSize: "1.05rem" }}>
                  {t.title}
                </Link>
                {t.description && (
                  <p style={{ margin: "0.35rem 0 0", color: "var(--muted)", fontSize: "0.9rem" }}>
                    {t.description.slice(0, 120)}{t.description.length > 120 ? "…" : ""}
                  </p>
                )}
                <div style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap", alignItems: "center" }}>
                  <span className={`badge ${statusClass(t.status)}`}>{t.status}</span>
                  <span className={`badge ${priorityClass(t.priority)}`}>{t.priority}</span>
                  {(t.created_by_name || (t.assignees?.length ?? 0) > 0) && (
                    <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {t.created_by_name && `By ${t.created_by_name}`}
                      {(t.assignees?.length ?? 0) > 0 && (
                        <>
                          {t.created_by_name && " · "}
                          Assigned to: {(t.assignees ?? []).map((a) => a.user_name).join(", ")}
                        </>
                      )}
                    </span>
                  )}
                </div>
              </div>
              <Link to={`/tickets/${t.id}`} className="btn btn-sm">
                View
              </Link>
            </div>
          ))}
          {pages > 1 && (
            <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "1rem" }}>
              <button
                type="button"
                className="btn btn-sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </button>
              <span style={{ color: "var(--muted)", fontSize: "0.875rem" }}>
                Page {page} of {pages} ({total} total)
              </span>
              <button
                type="button"
                className="btn btn-sm"
                disabled={page >= pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </>
  );
}
