/**
 * Conversation history API service.
 */

import request from './request';
import type { Conversation, Message } from '@/types/chat';

export interface ConversationListResponse {
  items: Conversation[];
  total: number;
}

export interface MessageListResponse {
  items: Message[];
  total: number;
}

/**
 * Get paginated conversations for current user.
 */
export const getConversations = async (
  page: number = 1,
  pageSize: number = 20
): Promise<ConversationListResponse> => {
  const response = await request.get('/conversations', {
    params: { page, page_size: pageSize },
  });
  return response.data;
};

/**
 * Get a single conversation by ID.
 */
export const getConversation = async (
  conversationId: number
): Promise<Conversation> => {
  const response = await request.get(`/conversations/${conversationId}`);
  return response.data;
};

/**
 * Create a new conversation.
 */
export const createConversation = async (
  title?: string
): Promise<Conversation> => {
  const response = await request.post('/conversations', {
    title: title || 'New Conversation',
  });
  return response.data;
};

/**
 * Update conversation title.
 */
export const updateConversation = async (
  conversationId: number,
  title: string
): Promise<Conversation> => {
  const response = await request.put(`/conversations/${conversationId}`, {
    title,
  });
  return response.data;
};

/**
 * Delete a conversation.
 */
export const deleteConversation = async (
  conversationId: number
): Promise<void> => {
  await request.delete(`/conversations/${conversationId}`);
};

/**
 * Get paginated messages for a conversation.
 */
export const getMessages = async (
  conversationId: number,
  page: number = 1,
  pageSize: number = 50
): Promise<MessageListResponse> => {
  const response = await request.get(
    `/conversations/${conversationId}/messages`,
    {
      params: { page, page_size: pageSize },
    }
  );
  return response.data;
};

/**
 * Create a message in a conversation.
 */
export const createMessage = async (
  conversationId: number,
  role: string,
  content: string,
  sources?: any,
  intent?: string,
  latencyMs?: number
): Promise<Message> => {
  // Note: This endpoint might not be needed for normal chat flow
  // Messages are usually created via the chat API
  const response = await request.post(
    `/conversations/${conversationId}/messages`,
    {
      role,
      content,
      sources,
      intent,
      latency_ms: latencyMs,
    }
  );
  return response.data;
};

/**
 * Delete a message.
 */
export const deleteMessage = async (
  messageId: number
): Promise<void> => {
  await request.delete(`/messages/${messageId}`);
};
