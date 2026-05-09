import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ChatMessage, Conversation } from '@/types/chat';

interface ChatState {
  conversations: Conversation[];
  activeId: string | null;
  streaming: boolean;
  historyVisible: boolean;
  sourceVisible: boolean;
  sidebarCollapsed: boolean;
  // actions
  setActive: (id: string) => void;
  newConversation: () => string;
  addMessage: (convId: string, msg: ChatMessage) => void;
  appendToLast: (convId: string, chunk: string) => void;
  updateLastSources: (convId: string, sources: ChatMessage['sources']) => void;
  updateLastMeta: (convId: string, meta: { intent?: string; latency_ms?: number }) => void;
  setStreaming: (v: boolean) => void;
  setHistoryVisible: (v: boolean) => void;
  setSourceVisible: (v: boolean) => void;
  setSidebarCollapsed: (v: boolean) => void;
  deleteConversation: (id: string) => void;
  deleteLastAssistant: (convId: string) => void;
}

let _counter = 0;

function genId(): string {
  return `conv_${Date.now()}_${++_counter}`;
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

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
  conversations: [],
  activeId: null,
  streaming: false,
  historyVisible: true,
  sourceVisible: true,
  sidebarCollapsed: false,

  setActive: (id) => set({ activeId: id }),

  newConversation: () => {
    const id = genId();
    const conv: Conversation = {
      id,
      title: '新对话',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    set((s) => ({ conversations: [conv, ...s.conversations], activeId: id }));
    return id;
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

  setStreaming: (v) => set({ streaming: v }),
  setHistoryVisible: (v) => set({ historyVisible: v }),
  setSourceVisible: (v) => set({ sourceVisible: v }),
  setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),

  deleteConversation: (id) =>
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeId: s.activeId === id
        ? (s.conversations.find((c) => c.id !== id)?.id ?? null)
        : s.activeId,
    })),

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
}),
    {
      name: 'rag-chat-store',
      partialize: (state) => ({
        conversations: state.conversations,
        activeId: state.activeId,
      }),
    }
  )
);
