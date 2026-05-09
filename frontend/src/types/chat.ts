export interface SourceItem {
  text: string;
  source: string;
  score: number;
  chunk_index: number;
}

export interface ChatMessage {
  id: string;
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

export interface ChatRequest {
  query: string;
}

export interface ChatResponse {
  answer: string;
  intent: string;
  sources: SourceItem[];
  latency_ms: number;
}
