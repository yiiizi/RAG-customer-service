import { useEffect } from 'react';
import { Input, List, Button } from 'antd';
import { PlusOutlined, DeleteOutlined, MessageOutlined } from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import dayjs from 'dayjs';

export default function ChatHistory() {
  const { conversations, activeId, setActive, newConversation, deleteConversation, loadConversations } = useChatStore();
  
  // Load conversations from backend on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const isEmpty = (conv: typeof conversations[0]) =>
    !conv.messages.some((m) => m.role === 'user' && m.content.trim());

  return (
    <div
      style={{
        width: 260,
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--sidebar-panel-bg)',
        backdropFilter: 'blur(8px)',
      }}
    >
      <div style={{ padding: '8px 12px' }}>
        <Button
          type="primary"
          block
          icon={<PlusOutlined />}
          onClick={() => { void newConversation(); }}
          style={{ borderRadius: 8, height: 34, fontWeight: 600, fontSize: 13 }}
        >
          新对话
        </Button>
      </div>

      <div style={{ padding: '0 12px 12px' }}>
        <Input prefix={<MessageOutlined style={{ color: 'var(--text-muted)' }} />} placeholder="搜索对话..." size="small" />
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        <List
          dataSource={conversations}
          renderItem={(conv) => {
            const empty = isEmpty(conv);
            return (
              <List.Item
                onClick={() => setActive(conv.id)}
                style={{
                  cursor: 'pointer',
                  padding: '10px 14px',
                  background: conv.id === activeId ? 'var(--bg-hover)' : 'transparent',
                  borderLeft: conv.id === activeId ? '3px solid var(--accent)' : '3px solid transparent',
                  borderBottom: '1px solid var(--border-subtle)',
                  transition: 'all 0.2s',
                }}
                actions={[
                  <Button
                    key="del"
                    type="text"
                    size="small"
                    icon={<DeleteOutlined />}
                    disabled={empty}
                    danger={!empty}
                    onClick={(e) => { e.stopPropagation(); if (!empty) void deleteConversation(conv.id); }}
                    title={empty ? '输入内容后可删除' : '删除对话'}
                    style={empty ? { color: 'var(--text-muted)', opacity: 0.4 } : {}}
                  />,
                ]}
              >
                <List.Item.Meta
                  title={
                    <div style={{
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      fontSize: 13, fontWeight: conv.id === activeId ? 600 : 400,
                      color: conv.id === activeId ? 'var(--accent)' : 'var(--text-secondary)',
                    }}>
                      {conv.title}
                    </div>
                  }
                  description={
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>
                      {dayjs(conv.updatedAt).format('MM-DD HH:mm')}
                    </span>
                  }
                />
              </List.Item>
            );
          }}
        />
      </div>
    </div>
  );
}
