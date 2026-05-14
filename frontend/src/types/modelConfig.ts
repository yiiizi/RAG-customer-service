/**
 * Model configuration types.
 */

export interface ModelConfig {
  id: number;
  user_id: number;
  provider: string;
  model_name: string;
  api_key_masked: string;
  base_url?: string;
  temperature: number;
  max_tokens: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface ModelConfigListResponse {
  items: ModelConfig[];
  total: number;
}

export interface ModelConfigCreateRequest {
  provider: string;
  model_name: string;
  api_key: string;
  base_url?: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
}

export interface ModelConfigUpdateRequest {
  provider?: string;
  model_name?: string;
  api_key?: string;
  base_url?: string;
  temperature?: number;
  max_tokens?: number;
  is_default?: boolean;
}
