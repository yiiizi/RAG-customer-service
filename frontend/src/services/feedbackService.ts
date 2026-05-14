import request from './request';

export type FeedbackRating = 'helpful' | 'unhelpful';

export interface FeedbackRequest {
  rating: FeedbackRating;
  reason?: string;
  comment?: string;
}

export interface FeedbackResponse {
  id: number;
  message_id: number;
  rating: FeedbackRating;
  reason?: string | null;
  comment?: string | null;
  created_at?: string | null;
}

export async function submitMessageFeedback(
  messageId: number,
  data: FeedbackRequest
): Promise<FeedbackResponse> {
  const res = await request.post<FeedbackResponse>(`/messages/${messageId}/feedback`, data);
  return res.data;
}
