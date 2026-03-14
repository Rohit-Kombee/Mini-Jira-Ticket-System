import React, { createContext, useContext, useEffect, useState } from "react";
import { login as apiLogin, getMe, logout as apiLogout, TokenResponse } from "../api/auth";
import type { User } from "../types";

type AuthContextType = {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));
  const [user, setUser] = useState<User | null>(null);

  const fetchUser = async () => {
    try {
      const u = await getMe();
      setUser(u);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    if (token) fetchUser();
    else setUser(null);
  }, [token]);

  useEffect(() => {
    const onLogout = () => setToken(null);
    window.addEventListener("auth:logout", onLogout);
    return () => window.removeEventListener("auth:logout", onLogout);
  }, []);

  const login = async (email: string, password: string) => {
    const res: TokenResponse = await apiLogin({ email, password });
    localStorage.setItem("token", res.access_token);
    setToken(res.access_token);
  };

  const logout = () => {
    apiLogout().finally(() => {
      localStorage.removeItem("token");
      setToken(null);
      setUser(null);
    });
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        login,
        logout,
        refreshUser: fetchUser,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
