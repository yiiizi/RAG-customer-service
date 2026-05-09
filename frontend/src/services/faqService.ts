import request from './request';
import type {
  FAQItem,
  FAQListResponse,
  FAQCreateRequest,
  FAQBatchImportRequest,
  FAQBatchImportResponse,
} from '@/types/faq';

export async function getFAQList(params: {
  keyword?: string;
  category?: string;
  offset?: number;
  limit?: number;
}): Promise<FAQListResponse> {
  const res = await request.get<FAQListResponse>('/faq', { params });
  return res.data;
}

export async function createFAQ(data: FAQCreateRequest): Promise<FAQItem> {
  const res = await request.post<FAQItem>('/faq', data);
  return res.data;
}

export async function updateFAQ(id: string, data: Partial<FAQCreateRequest>): Promise<FAQItem> {
  const res = await request.put<FAQItem>(`/faq/${id}`, data);
  return res.data;
}

export async function deleteFAQ(id: string): Promise<void> {
  await request.delete(`/faq/${id}`);
}

export async function batchImportFAQ(
  data: FAQBatchImportRequest
): Promise<FAQBatchImportResponse> {
  const res = await request.post<FAQBatchImportResponse>('/faq/batch-import', data);
  return res.data;
}
