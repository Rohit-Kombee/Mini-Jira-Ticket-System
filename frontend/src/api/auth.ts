import { api } from "./client";
import type { User } from "../types";

export interface LoginInput {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(data: LoginInput): Promise<TokenResponse> {
  return api<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function logout(): Promise<void> {
  try {
    await api("/auth/logout", { method: "POST" });
  } catch {
    // Ignore (e.g. network or 401); still clear local token
  }
}

export async function getMe(): Promise<User> {
  return api<User>("/auth/me");
}
