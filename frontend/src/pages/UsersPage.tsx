import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { getUsers, createUser, updateUser, deleteUser } from "../api/users";
import type { User } from "../types";

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formRole, setFormRole] = useState<"developer" | "qa">("developer");
  const [saving, setSaving] = useState(false);

  const isAdmin = currentUser?.role === "admin";

  const load = () => {
    setLoading(true);
    setError("");
    getUsers()
      .then(setUsers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load users"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (isAdmin) load();
  }, [isAdmin]);

  const resetForm = () => {
    setFormName("");
    setFormEmail("");
    setFormPassword("");
    setFormRole("developer");
    setShowCreate(false);
    setEditingId(null);
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await createUser({ name: formName, email: formEmail, password: formPassword, role: formRole });
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setSaving(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId == null) return;
    setError("");
    setSaving(true);
    try {
      const payload: { name?: string; email?: string; password?: string; role?: "developer" | "qa" } = {
        name: formName,
        email: formEmail,
        role: formRole,
      };
      if (formPassword) payload.password = formPassword;
      await updateUser(editingId, payload);
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update user");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Delete this user? This cannot be undone.")) return;
    setError("");
    try {
      await deleteUser(id);
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete user");
    }
  };

  const startEdit = (u: User) => {
    setEditingId(u.id);
    setFormName(u.name);
    setFormEmail(u.email);
    setFormPassword("");
    setFormRole((u.role === "developer" || u.role === "agent" ? "developer" : "qa") as "developer" | "qa");
    setShowCreate(false);
  };

  if (!currentUser) return null;
  if (!isAdmin) {
    return (
      <div className="card">
        <p className="error-msg">Only Admin can manage users.</p>
        <Link to="/">← Back to tickets</Link>
      </div>
    );
  }

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem", marginBottom: "1rem" }}>
        <h1 style={{ margin: 0 }}>User management</h1>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Link to="/" style={{ color: "var(--muted)", fontSize: "0.875rem", alignSelf: "center" }}>← Tickets</Link>
          {!showCreate && !editingId && (
            <button type="button" className="btn btn-primary" onClick={() => { setShowCreate(true); setEditingId(null); setFormName(""); setFormEmail(""); setFormPassword(""); setFormRole("developer"); }}>
              Create user
            </button>
          )}
        </div>
      </div>

      {error && <p className="error-msg">{error}</p>}

      {(showCreate || editingId !== null) && (
        <div className="card" style={{ marginBottom: "1rem" }}>
          <h2 style={{ marginTop: 0 }}>{editingId != null ? "Edit user" : "Create user"}</h2>
          <form onSubmit={editingId != null ? handleUpdate : handleCreate}>
            <div className="form-group">
              <label>Name</label>
              <input value={formName} onChange={(e) => setFormName(e.target.value)} required maxLength={255} />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={formEmail} onChange={(e) => setFormEmail(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Password {editingId != null && "(leave blank to keep current)"}</label>
              <input type="password" value={formPassword} onChange={(e) => setFormPassword(e.target.value)} required={editingId == null} minLength={1} />
            </div>
            <div className="form-group">
              <label>Role</label>
              <select value={formRole} onChange={(e) => setFormRole(e.target.value as "developer" | "qa")}>
                <option value="developer">Developer</option>
                <option value="qa">QA</option>
              </select>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <button type="submit" className="btn btn-primary" disabled={saving}>
                {saving ? "Saving…" : editingId != null ? "Update" : "Create"}
              </button>
              <button type="button" className="btn" onClick={resetForm}>Cancel</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {loading ? (
          <p style={{ color: "var(--muted)" }}>Loading users…</p>
        ) : users.length === 0 ? (
          <p style={{ margin: 0, color: "var(--muted)" }}>No users yet. Create a user (Developer or QA) above.</p>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", textAlign: "left" }}>
                <th style={{ padding: "0.5rem 0.75rem" }}>Name</th>
                <th style={{ padding: "0.5rem 0.75rem" }}>Email</th>
                <th style={{ padding: "0.5rem 0.75rem" }}>Role</th>
                <th style={{ padding: "0.5rem 0.75rem" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} style={{ borderBottom: "1px solid var(--border)" }}>
                  <td style={{ padding: "0.5rem 0.75rem" }}>{u.name}</td>
                  <td style={{ padding: "0.5rem 0.75rem" }}>{u.email}</td>
                  <td style={{ padding: "0.5rem 0.75rem" }}>{u.role === "admin" ? "Admin" : u.role === "developer" || u.role === "agent" ? "Developer" : "QA"}</td>
                  <td style={{ padding: "0.5rem 0.75rem" }}>
                    {u.role !== "admin" && (
                      <>
                        <button type="button" className="btn btn-sm" onClick={() => startEdit(u)}>Edit</button>
                        {" "}
                        <button type="button" className="btn btn-sm" style={{ borderColor: "var(--danger)", color: "var(--danger)" }} onClick={() => handleDelete(u.id)}>Delete</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
