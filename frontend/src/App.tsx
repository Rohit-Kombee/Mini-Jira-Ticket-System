import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Login } from "./pages/Login";
import { TicketListPage } from "./pages/TicketListPage";
import { UsersPage } from "./pages/UsersPage";
import { TicketDetailPage } from "./pages/TicketDetailPage";
import { NewTicketPage } from "./pages/NewTicketPage";

function HomeRedirect() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) return <TicketListPage />;
  return <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomeRedirect />} />
            <Route path="login" element={<Login />} />
            <Route path="users" element={<ProtectedRoute><UsersPage /></ProtectedRoute>} />
            <Route path="tickets" element={<ProtectedRoute><TicketListPage /></ProtectedRoute>} />
            <Route path="tickets/new" element={<ProtectedRoute><NewTicketPage /></ProtectedRoute>} />
            <Route path="tickets/:id" element={<ProtectedRoute><TicketDetailPage /></ProtectedRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
