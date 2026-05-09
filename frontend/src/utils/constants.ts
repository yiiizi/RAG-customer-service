export const INTENT_LABELS: Record<string, string> = {
  chat: '闲聊',
  faq: '高频问答',
  knowledge_qa: '商品咨询',
  order_query: '订单查询',
  logistics_track: '物流追踪',
  联网搜索: '联网搜索',
};

export const INTENT_COLORS: Record<string, string> = {
  chat: '#52c41a',
  faq: '#1890ff',
  knowledge_qa: '#fa8c16',
  order_query: '#eb2f96',
  logistics_track: '#722ed1',
  联网搜索: '#ffa940',
};

export const FILE_TYPE_ICONS: Record<string, string> = {
  '.pdf': '📄',
  '.docx': '📝',
  '.txt': '📃',
  '.md': '📘',
  '.html': '🌐',
  '.csv': '📊',
  '.xlsx': '📈',
  '.pptx': '📽️',
  '.json': '📋',
  '.epub': '📚',
  '.png': '🖼️',
  '.jpg': '🖼️',
  '.jpeg': '🖼️',
};

export const SUPPORTED_FILE_TYPES = [
  '.pdf', '.docx', '.txt', '.md', '.html', '.htm',
  '.csv', '.xlsx', '.pptx', '.json', '.epub',
  '.png', '.jpg', '.jpeg',
  '.py', '.java', '.go', '.js', '.ts', '.cpp', '.c',
];
