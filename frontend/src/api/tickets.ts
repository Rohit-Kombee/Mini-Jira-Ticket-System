import { api } from "./client";
import type { Ticket, TicketListResponse, Message, MessageListResponse } from "../types";

export interface TicketCreateInput {
  title: string;
  description?: string;
  priority?: string;
  assignee_ids?: number[];  // Admin only: assign to developers/viewers when creating
}

export interface TicketUpdateInput {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  assigned_to?: number | null;
  assignee_ids?: number[];
}

export async function getTickets(params?: {
  status?: string;
  priority?: string;
  assigned_to?: number;
  created_by?: number;
  page?: number;
  limit?: number;
}): Promise<TicketListResponse> {
  const sp = new URLSearchParams();
  if (params?.status) sp.set("status", params.status);
  if (params?.priority) sp.set("priority", params.priority);
  if (params?.assigned_to != null) sp.set("assigned_to", String(params.assigned_to));
  if (params?.created_by != null) sp.set("created_by", String(params.created_by));
  if (params?.page != null) sp.set("page", String(params.page));
  if (params?.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return api<TicketListResponse>(`/tickets${q ? `?${q}` : ""}`);
}

export async function getTicket(id: number): Promise<Ticket> {
  return api<Ticket>(`/tickets/${id}`);
}

export async function createTicket(data: TicketCreateInput): Promise<Ticket> {
  return api<Ticket>("/tickets", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTicket(id: number, data: TicketUpdateInput): Promise<Ticket> {
  return api<Ticket>(`/tickets/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteTicket(id: number): Promise<void> {
  return api<void>(`/tickets/${id}`, { method: "DELETE" });
}

export async function getMessages(ticketId: number): Promise<MessageListResponse> {
  return api<MessageListResponse>(`/tickets/${ticketId}/messages`);
}

export async function addMessage(ticketId: number, message: string): Promise<Message> {
  return api<Message>(`/tickets/${ticketId}/messages`, {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}
