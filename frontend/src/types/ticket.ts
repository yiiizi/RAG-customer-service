import type { SourceItem } from '@/types/chat';

export type TicketStatus = 'open' | 'processing' | 'resolved' | 'closed';

export interface Ticket {
  id: number;
  ticket_no: string;
  user_id: number;
  username?: string | null;
  conversation_id?: number | null;
  message_id?: number | null;
  category: string;
  priority: string;
  status: TicketStatus;
  summary: string;
  user_question: string;
  ai_answer: string;
  public_sources: SourceItem[];
  debug_sources: SourceItem[];
  assigned_to?: number | null;
  assigned_username?: string | null;
  staff_note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketListResponse {
  items: Ticket[];
  total: number;
}

export interface TicketUpdateRequest {
  status?: TicketStatus;
  staff_note?: string;
  assigned_to?: number | null;
}
