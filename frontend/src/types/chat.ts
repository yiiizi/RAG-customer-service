export interface SourceItem {
  text: string;
  source: string;
  score: number;
  chunk_index: number;
}

export interface ChatMessage {
  id: string;
  message_id?: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceItem[];
  intent?: string;
  latency_ms?: number;
  timestamp: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  sources?: string | null;
  intent?: string | null;
  latency_ms?: number | null;
  created_at: string;
}

export interface ChatRequest {
  query: string;
  conversation_id?: number;
  kb_only?: boolean;
  web_search?: boolean;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: SourceItem[];
  latency_ms: number;
  conversation_id?: number;
  message_id?: number;
}
