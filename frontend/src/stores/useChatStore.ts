import { create } from 'zustand';
import type { ChatMessage, Conversation } from '@/types/chat';
import * as conversationService from '@/services/conversationService';

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  streaming: boolean;
  historyVisible: boolean;
  sourceVisible: boolean;
  sidebarCollapsed: boolean;
  selectedModelConfigId: number | null;
  // actions
  setActive: (id: string) => void;
  newConversation: () => Promise<string>;
  addMessage: (convId: string, msg: ChatMessage) => void;
  appendToLast: (convId: string, chunk: string) => void;
  updateLastSources: (convId: string, sources: ChatMessage['sources']) => void;
  updateLastMeta: (convId: string, meta: { intent?: string; latency_ms?: number }) => void;
  updateLastMessageId: (convId: string, messageId: number) => void;
  setStreaming: (v: boolean) => void;
  setHistoryVisible: (v: boolean) => void;
  setSourceVisible: (v: boolean) => void;
  setSidebarCollapsed: (v: boolean) => void;
  setSelectedModelConfigId: (id: number | null) => void;
  deleteConversation: (id: string) => Promise<void>;
  deleteLastAssistant: (convId: string) => void;
  loadConversations: () => Promise<void>;
  loadMessages: (convId: string) => Promise<void>;
  reset: () => void;
}

function _smartTruncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  const truncated = text.slice(0, maxLen);
  // Try to break at punctuation or space
  const breakPoints = ['。', '？', '！', '，', '、', '；', '.', '?', '!', ',', ';', ' '];
  for (const bp of breakPoints) {
    const idx = truncated.lastIndexOf(bp);
    if (idx > maxLen * 0.5) return truncated.slice(0, idx + 1);
  }
  return truncated + '...';
}

function _parseSources(raw?: string | null): ChatMessage['sources'] {
  if (!raw) return [];
  try {
    const payload = JSON.parse(raw);
    const sources = payload.public_sources || payload.sources || [];
    return sources.map((s: any) => ({
      text: s.text || '',
      source: s.source || s.label || '',
      score: s.score || 0,
      chunk_index: s.chunk_index ?? -1,
    }));
  } catch {
    return [];
  }
}

function _mapMessage(item: any): ChatMessage {
  return {
    id: item.id?.toString?.() || `${Date.now()}`,
    message_id: item.id,
    role: item.role === 'assistant' ? 'assistant' : 'user',
    content: item.content || '',
    sources: _parseSources(item.sources),
    intent: item.intent || undefined,
    latency_ms: item.latency_ms ?? undefined,
    timestamp: item.created_at || new Date().toISOString(),
  };
}

function _mapConversation(item: any): Conversation {
  return {
    id: item.id.toString(),
    title: item.title,
    messages: [],
    createdAt: item.created_at,
    updatedAt: item.updated_at,
  };
}

export const useChatStore = create<ChatState>()(
  (set, get) => ({
  conversations: [],
  activeId: null,
  streaming: false,
  historyVisible: true,
  sourceVisible: true,
  sidebarCollapsed: false,
  selectedModelConfigId: null,

  setActive: (id) => {
    set({ activeId: id });
    void get().loadMessages(id);
  },

  newConversation: async () => {
    const created = await conversationService.createConversation('新对话');
    const conv = _mapConversation(created);
    set((s) => {
      const exists = s.conversations.some((c) => c.id === conv.id);
      return {
        conversations: exists ? s.conversations : [conv, ...s.conversations],
        activeId: conv.id,
      };
    });
    await get().loadMessages(conv.id);
    return conv.id;
  },

  addMessage: (convId, msg) =>
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === convId
          ? {
              ...c,
              messages: [...c.messages, msg],
              title: c.messages.length === 0 ? _smartTruncate(msg.content, 30) : c.title,
              updatedAt: new Date().toISOString(),
            }
          : c
      ),
    })),

  appendToLast: (convId, chunk) =>
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant') {
          msgs[msgs.length - 1] = { ...last, content: last.content + chunk };
          return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
        }
        // Fallback: find the last empty assistant message (streaming in progress)
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant' && !msgs[i].content.trim()) {
            msgs[i] = { ...msgs[i], content: msgs[i].content + chunk };
            return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
          }
        }
        return c;
      }),
    })),

  updateLastSources: (convId, sources) =>
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant') {
          msgs[msgs.length - 1] = { ...last, sources };
        }
        return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
      }),
    })),

  updateLastMeta: (convId, meta: { intent?: string; latency_ms?: number }) =>
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant') {
          if (meta.intent) msgs[msgs.length - 1] = { ...last, intent: meta.intent };
          if (meta.latency_ms != null) msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], latency_ms: meta.latency_ms };
        }
        return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
      }),
      })),

  updateLastMessageId: (convId, messageId) =>
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages];
        const last = msgs[msgs.length - 1];
        if (last && last.role === 'assistant') {
          msgs[msgs.length - 1] = { ...last, message_id: messageId, id: messageId.toString() };
        }
        return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
      }),
    })),

  setStreaming: (v) => set({ streaming: v }),
  setHistoryVisible: (v) => set({ historyVisible: v }),
  setSourceVisible: (v) => set({ sourceVisible: v }),
  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
  setSelectedModelConfigId: (id) => set({ selectedModelConfigId: id }),

  deleteConversation: async (id) => {
    await conversationService.deleteConversation(Number(id));
    set((s) => {
      const remaining = s.conversations.filter((c) => c.id !== id);
      return {
        conversations: remaining,
        activeId: s.activeId === id ? (remaining[0]?.id ?? null) : s.activeId,
      };
    });
  },

  deleteLastAssistant: (convId) =>
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== convId) return c;
        const msgs = [...c.messages];
        // Remove last assistant message
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant') {
            msgs.splice(i, 1);
            break;
          }
        }
        return { ...c, messages: msgs, updatedAt: new Date().toISOString() };
      }),
    })),

  loadConversations: async () => {
    try {
      const data = await conversationService.getConversations();
      const conversations = data.items.map(_mapConversation);
      const currentActiveId = get().activeId;
      const activeId = conversations.some((conv) => conv.id === currentActiveId)
        ? currentActiveId
        : (conversations.length > 0 ? conversations[0].id : null);
      set({ conversations, activeId });
      if (activeId) {
        await get().loadMessages(activeId);
      } else {
        await get().newConversation();
      }
    } catch (error) {
      console.error('Failed to load conversations:', error);
      set({ conversations: [], activeId: null, streaming: false });
    }
  },

  loadMessages: async (convId) => {
    try {
      const data = await conversationService.getMessages(Number(convId));
      const messages = data.items.map(_mapMessage);
      set((s) => ({
        conversations: s.conversations.map((c) =>
          c.id === convId
            ? { ...c, messages, updatedAt: messages[messages.length - 1]?.timestamp || c.updatedAt }
            : c
        ),
      }));
    } catch (error) {
      console.error('Failed to load messages:', error);
      const current = get().conversations;
      if (current.some((conv) => conv.id === convId)) {
        set((s) => ({
          activeId: null,
          conversations: s.conversations.filter((conv) => conv.id !== convId),
          streaming: false,
        }));
      }
    }
  },

  reset: () =>
    set({
      conversations: [],
      activeId: null,
      streaming: false,
      historyVisible: true,
      sourceVisible: true,
      sidebarCollapsed: false,
      selectedModelConfigId: null,
    }),
})
);
