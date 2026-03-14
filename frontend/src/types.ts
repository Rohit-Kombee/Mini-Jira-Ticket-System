export interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at?: string;
}

export interface AssigneeInfo {
  user_id: number;
  user_name: string;
  assigned_by_id?: number;
  assigned_by_name?: string;
}

export interface AssignedToYouBy {
  id: number;
  name: string;
}

export interface Ticket {
  id: number;
  title: string;
  description?: string;
  status: string;
  priority: string;
  created_by: number;
  assigned_to?: number;
  created_at?: string;
  created_by_name?: string;
  assigned_to_name?: string;
  assignees?: AssigneeInfo[];
  assigned_to_you_by?: AssignedToYouBy;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface Message {
  id: number;
  ticket_id: number;
  sender_id: number;
  message: string;
  created_at?: string;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
}
