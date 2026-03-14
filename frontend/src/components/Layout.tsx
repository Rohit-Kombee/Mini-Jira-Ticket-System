import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

function roleLabel(role: string) {
  if (role === "admin") return "Admin";
  if (role === "developer" || role === "agent") return "Developer";
  if (role === "qa" || role === "viewer") return "QA";
  return role;
}

export function Layout() {
  const { logout, isAuthenticated, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="container">
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", paddingBottom: "1rem", borderBottom: "1px solid var(--border)" }}>
        <Link to="/" style={{ fontSize: "1.25rem", fontWeight: 700, color: "var(--text)" }}>
          Support Tickets
        </Link>
        {isAuthenticated && (
          <div style={{ display: "flex", gap: "1rem", alignItems: "center", flexWrap: "wrap" }}>
            {user && (
              <span style={{ fontSize: "0.8rem", color: "var(--muted)" }} title={user.email}>
                {user.name} ({roleLabel(user.role)})
              </span>
            )}
            <Link to="/">Tickets</Link>
            {user?.role === "admin" && <Link to="/tickets/new">New ticket</Link>}
            {user?.role === "admin" && <Link to="/users">Users</Link>}
            <button type="button" className="btn btn-sm" onClick={handleLogout}>
              Logout
            </button>
          </div>
        )}
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
