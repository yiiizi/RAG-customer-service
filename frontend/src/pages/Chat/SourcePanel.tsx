import { List, Tag, Typography } from 'antd';
import { GlobalOutlined, DatabaseOutlined, FileTextOutlined } from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import { formatPercent } from '@/utils/format';

const BOX_MAX_HEIGHT = 200;

export default function SourcePanel() {
  const { conversations, activeId } = useChatStore();
  const conv = conversations.find((c) => c.id === activeId);

  const lastAssistant = conv?.messages.filter((m) => m.role === 'assistant').at(-1);
  const sources = lastAssistant?.sources ?? [];
  const hasAnswer = !!(lastAssistant?.content && lastAssistant.content.trim());
  const intent = lastAssistant?.intent;

  // Separate web sources from KB sources
  const webSources = sources.filter((s) => s.source && (s.source.startsWith('http') || s.source === '互联网' || s.source === 'Tavily'));
  const kbSources = sources.filter((s) => !webSources.includes(s));

  // Determine the empty state message
  let emptyHint = '检索来源将在这里显示';
  let emptyIcon = <FileTextOutlined style={{ fontSize: 32, color: 'var(--text-muted)', marginBottom: 8 }} />;
  if (hasAnswer) {
    if (intent === 'faq') {
      emptyHint = '回答来自高频问答缓存';
    } else if (intent === 'chat') {
      emptyHint = '回答来自 AI 对话';
    } else if (intent === 'order_query' || intent === 'logistics_track') {
      emptyHint = '回答来自订单/物流查询';
    } else if (intent === '联网搜索') {
      emptyHint = '网络搜索结果已整合在回答中';
    } else {
      emptyHint = '知识库中未找到相关信息';
    }
  }

  if (sources.length === 0) {
    return (
      <div style={{
        width: 310, flexShrink: 0,
        borderLeft: '1px solid var(--border-subtle)',
        background: 'var(--sidebar-panel-bg)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: 24, gap: 8,
      }}>
        {emptyIcon}
        <Typography.Text style={{ fontSize: 13, color: 'var(--text-muted)', textAlign: 'center' }}>
          {emptyHint}
        </Typography.Text>
      </div>
    );
  }

  return (
    <div style={{
      width: 310, flexShrink: 0,
      borderLeft: '1px solid var(--border-subtle)',
      background: 'var(--sidebar-panel-bg)',
      overflow: 'auto', padding: 16,
    }}>
      {/* Web search sources */}
      {webSources.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <GlobalOutlined style={{ fontSize: 13, color: '#ffa940' }} />
            <Typography.Text strong style={{ fontSize: 12, color: '#ffa940' }}>
              网络搜索结果
            </Typography.Text>
            <Tag color="orange" style={{ fontSize: 10, marginLeft: 'auto' }}>
              {webSources.length} 条
            </Tag>
          </div>
          {webSources.map((item, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <div style={{
                fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7,
                whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                border: '1px solid rgba(255, 169, 64, 0.2)', borderRadius: 6,
                padding: '6px 10px', background: 'rgba(255, 169, 64, 0.04)',
                maxHeight: BOX_MAX_HEIGHT, overflow: 'auto',
              }}>
                {item.text}
              </div>
              {item.source && item.source !== '互联网' && (
                <Typography.Text style={{ fontSize: 10, display: 'block', marginTop: 2, color: 'var(--text-muted)' }}>
                  来源: {item.source}
                </Typography.Text>
              )}
            </div>
          ))}
        </div>
      )}

      {/* KB sources */}
      {kbSources.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <DatabaseOutlined style={{ fontSize: 13, color: 'var(--accent)' }} />
            <Typography.Text strong style={{ fontSize: 12, color: 'var(--accent)' }}>
              知识库检索结果
            </Typography.Text>
            <Tag color="cyan" style={{ fontSize: 10, marginLeft: 'auto' }}>
              {kbSources.length} 条
            </Tag>
          </div>
          {kbSources.map((item, idx) => (
            <div key={idx} style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
                <Typography.Text strong style={{ fontSize: 11, color: 'var(--text-primary)' }}>
                  来源 {idx + 1}
                </Typography.Text>
                <Tag color="cyan" style={{ fontSize: 10, marginLeft: 'auto' }}>
                  {formatPercent(item.score)}
                </Tag>
              </div>
              <div style={{
                maxHeight: BOX_MAX_HEIGHT, overflow: 'auto',
                fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.7,
                whiteSpace: 'pre-wrap', wordBreak: 'break-all',
                border: '1px solid var(--border-subtle)', borderRadius: 6,
                padding: '6px 10px', background: 'var(--surface-raised)',
              }}>
                {item.text}
              </div>
              {item.source && (
                <Typography.Text style={{ fontSize: 10, display: 'block', marginTop: 2, color: 'var(--text-muted)' }}>
                  来自: {item.source}
                </Typography.Text>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
