import request from './request';
import type { KBListResponse, KBStats, KBUploadResponse } from '@/types/knowledge';

export async function uploadFile(file: File): Promise<KBUploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const res = await request.post<KBUploadResponse>('/kb/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  const data = res.data;
  if (data.status === 'error') {
    throw new Error(data.error || '索引失败');
  }
  return data;
}

export async function uploadDirectory(directory: string): Promise<{ status: string }> {
  const res = await request.post('/kb/upload-dir', null, { params: { directory } });
  return res.data;
}

export async function getKBList(): Promise<KBListResponse> {
  const res = await request.get<KBListResponse>('/kb/list');
  return res.data;
}

export async function getKBStats(): Promise<KBStats> {
  const res = await request.get<KBStats>('/kb/stats');
  return res.data;
}

export async function deleteKBFile(fileName: string): Promise<void> {
  await request.delete(`/kb/${encodeURIComponent(fileName)}`);
}

export async function getFileChunks(fileName: string): Promise<{
  file_name: string;
  chunk_count: number;
  parent_count: number;
  parents: Array<{
    parent_id: string;
    parent_text: string;
    children: Array<{
      id: string;
      text: string;
      chunk_index: number;
      created_at: number | null;
    }>;
  }>;
}> {
  const res = await request.get(`/kb/chunks/${encodeURIComponent(fileName)}`);
  return res.data;
}

export async function reindexFile(fileName: string): Promise<{ status: string }> {
  const res = await request.post('/kb/reindex', null, { params: { file_name: fileName } });
  return res.data;
}
