export interface KBDocument {
  file_name: string;
  file_type: string;
  status: 'indexed' | 'indexing' | 'error';
  chunk_count: number;
  created_at: string | null;
}

export interface KBUploadResponse {
  status: string;
  file: string;
  parent_chunks: number;
  child_chunks: number;
  inserted: number;
  error?: string;
}

export interface KBListResponse {
  items: KBDocument[];
  total: number;
}

export interface KBStats {
  total_chunks: number;
  collection_name: string;
  dimension: number;
}

export interface ChunkNode {
  id: string;
  text: string;
  parent_id: string;
  children: ChunkNode[];
}
