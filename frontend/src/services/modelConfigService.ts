/**
 * Model configuration API service.
 */

import request from './request';
import type { ModelConfig, ModelConfigListResponse } from '@/types/modelConfig';

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

/**
 * Get all model configs for current user.
 */
export const getModelConfigs = async (): Promise<ModelConfigListResponse> => {
  const response = await request.get('/model-configs');
  return response.data;
};

/**
 * Get a single model config by ID.
 */
export const getModelConfig = async (configId: number): Promise<ModelConfig> => {
  const response = await request.get(`/model-configs/${configId}`);
  return response.data;
};

/**
 * Create a new model config.
 */
export const createModelConfig = async (
  data: ModelConfigCreateRequest
): Promise<ModelConfig> => {
  const response = await request.post('/model-configs', data);
  return response.data;
};

/**
 * Update a model config.
 */
export const updateModelConfig = async (
  configId: number,
  data: ModelConfigUpdateRequest
): Promise<ModelConfig> => {
  const response = await request.put(`/model-configs/${configId}`, data);
  return response.data;
};

/**
 * Delete a model config.
 */
export const deleteModelConfig = async (configId: number): Promise<void> => {
  await request.delete(`/model-configs/${configId}`);
};

/**
 * Set a model config as default.
 */
export const setDefaultModelConfig = async (
  configId: number
): Promise<ModelConfig> => {
  const response = await request.post(`/model-configs/${configId}/set-default`);
  return response.data;
};

/**
 * Get the default model config for current user.
 */
export const getDefaultModelConfig = async (): Promise<ModelConfig> => {
  const response = await request.get('/model-configs/default');
  return response.data;
};
