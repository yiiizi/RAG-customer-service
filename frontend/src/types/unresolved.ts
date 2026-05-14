import type { SourceItem } from '@/types/chat';
import type { FAQItem } from '@/types/faq';

export type UnresolvedStatus = 'pending' | 'converted_to_faq' | 'ignored' | 'resolved';

export interface UnresolvedQuestion {
  id: number;
  normalized_question: string;
  question: string;
  user_id?: number | null;
  conversation_id?: number | null;
  message_id?: number | null;
  ai_answer: string;
  reason: string;
  intent?: string | null;
  confidence: number;
  sources: SourceItem[];
  status: UnresolvedStatus;
  frequency: number;
  last_seen_at: string;
  created_at: string;
  updated_at: string;
}

export interface UnresolvedQuestionListResponse {
  items: UnresolvedQuestion[];
  total: number;
}

export interface UnresolvedToFAQRequest {
  question?: string;
  answer?: string;
  category: string;
  similar_questions: string[];
}

export type { FAQItem };
