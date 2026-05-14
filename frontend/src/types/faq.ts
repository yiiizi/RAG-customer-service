export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  frequency: number;
  category: string;
  status: 'draft' | 'rejected' | 'active' | 'inactive';
  priority: number;
  similar_questions: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface FAQListResponse {
  items: FAQItem[];
  total: number;
}

export interface FAQCreateRequest {
  question: string;
  answer: string;
  category: string;
  status?: 'draft' | 'rejected' | 'active' | 'inactive';
  priority?: number;
  similar_questions?: string[];
}

export interface FAQBatchImportRequest {
  items: FAQCreateRequest[];
}

export interface FAQBatchImportResponse {
  imported: number;
  skipped: number;
  errors: string[];
}
