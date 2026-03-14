import { api } from "./client";
import type { User } from "../types";

export interface CreateUserInput {
  name: string;
  email: string;
  password: string;
  role: "developer" | "qa";
}

export interface UpdateUserInput {
  name?: string;
  email?: string;
  password?: string;
  role?: "developer" | "qa";
}

export async function getUsers(role?: string): Promise<User[]> {
  const q = role ? `?role=${encodeURIComponent(role)}` : "";
  return api<User[]>(`/users${q}`);
}

export async function getUser(id: number): Promise<User> {
  return api<User>(`/users/${id}`);
}

export async function createUser(data: CreateUserInput): Promise<User> {
  return api<User>("/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateUser(id: number, data: UpdateUserInput): Promise<User> {
  return api<User>(`/users/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteUser(id: number): Promise<void> {
  return api<void>(`/users/${id}`, { method: "DELETE" });
}
