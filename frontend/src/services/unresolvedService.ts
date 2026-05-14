import request from './request';
import type {
  FAQItem,
  UnresolvedQuestion,
  UnresolvedQuestionListResponse,
  UnresolvedStatus,
  UnresolvedToFAQRequest,
} from '@/types/unresolved';

export async function getUnresolvedQuestions(params: {
  status?: UnresolvedStatus | '';
  page?: number;
  page_size?: number;
}): Promise<UnresolvedQuestionListResponse> {
  const res = await request.get<UnresolvedQuestionListResponse>('/unresolved', { params });
  return res.data;
}

export async function updateUnresolvedStatus(
  id: number,
  status: UnresolvedStatus
): Promise<UnresolvedQuestion> {
  const res = await request.put<UnresolvedQuestion>(`/unresolved/${id}`, { status });
  return res.data;
}

export async function convertToFAQ(
  id: number,
  payload: UnresolvedToFAQRequest
): Promise<FAQItem> {
  const res = await request.post<FAQItem>(`/unresolved/${id}/to-faq`, payload);
  return res.data;
}
