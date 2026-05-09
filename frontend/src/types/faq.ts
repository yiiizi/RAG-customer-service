export interface FAQItem {
  id: string;
  question: string;
  answer: string;
  frequency: number;
  category: string;
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
}

export interface FAQBatchImportRequest {
  items: FAQCreateRequest[];
}

export interface FAQBatchImportResponse {
  imported: number;
  skipped: number;
  errors: string[];
}
