import request from './request';
import type { Ticket, TicketListResponse, TicketStatus, TicketUpdateRequest } from '@/types/ticket';

export async function getMyTickets(): Promise<TicketListResponse> {
  const res = await request.get<TicketListResponse>('/tickets/mine');
  return res.data;
}

export async function getQueueTickets(status?: TicketStatus | ''): Promise<TicketListResponse> {
  const res = await request.get<TicketListResponse>('/tickets/queue', {
    params: status ? { status } : undefined,
  });
  return res.data;
}

export async function claimTicket(ticketId: number): Promise<Ticket> {
  const res = await request.post<Ticket>(`/tickets/${ticketId}/claim`);
  return res.data;
}

export async function updateTicket(ticketId: number, payload: TicketUpdateRequest): Promise<Ticket> {
  const res = await request.put<Ticket>(`/tickets/${ticketId}`, payload);
  return res.data;
}
