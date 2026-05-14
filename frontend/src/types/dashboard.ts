export interface DailyTrendItem {
  date: string;
  count: number;
}

export interface DashboardStats {
  total_queries: number;
  avg_latency_ms: number;
  hit_rate: number;
  range: 'today' | '7d' | '30d';
  intent_distribution: Record<string, number>;
  daily_trend: DailyTrendItem[];
  top_faqs: Array<{
    id: string;
    question: string;
    answer: string;
    frequency: number;
    category: string;
  }>;
  milvus_stats: {
    total_chunks: number;
    collection_name: string;
    dimension: number;
  };
  helpful_rate: number;
  unhelpful_rate: number;
  unresolved_count: number;
  handoff_rate: number;
  ticket_resolution_rate: number;
  faq_conversion_count: number;
  top_unresolved: Array<{
    id: number;
    question: string;
    frequency: number;
    status: string;
  }>;
}

export interface SettingsData {
  llm: {
    api_base: string;
    model: string;
    temperature: number;
    max_tokens: number;
  };
  retrieval: {
    dense_top_k: number;
    sparse_top_k: number;
    reranker_top_n: number;
    bm25_threshold: number;
  };
  cache: {
    redis_faq_ttl_hours: number;
    redis_hot_threshold: number;
    redis_hot_ttl_days: number;
  };
}
