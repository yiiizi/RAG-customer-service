import request from './request';
import type { ChatRequest, ChatResponse } from '@/types/chat';
import { getAccessToken } from '@/utils/token';

export async function sendChat(query: string): Promise<ChatResponse> {
  const res = await request.post<ChatResponse>('/chat', { query } as ChatRequest);
  return res.data;
}

export function getWebSocketUrl(): string {
  // Use current hostname so other computers on the network can connect
  const host = window.location.hostname;
  const port = import.meta.env.VITE_API_PORT || '8000';
  const token = getAccessToken();
  const query = token ? `?token=${encodeURIComponent(token)}` : '';
  return `ws://${host}:${port}/api/ws/chat${query}`;
}
