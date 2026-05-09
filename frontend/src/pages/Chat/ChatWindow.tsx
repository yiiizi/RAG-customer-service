import { useEffect, useRef } from 'react';
import { Tag, Typography, message as antMsg } from 'antd';
import { RobotOutlined, UserOutlined, ShoppingOutlined, CarOutlined, SafetyCertificateOutlined, GiftOutlined, CustomerServiceOutlined, CopyOutlined, ReloadOutlined } from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import MarkdownViewer from '@/components/MarkdownViewer';
import { INTENT_LABELS, INTENT_COLORS } from '@/utils/constants';
import { formatLatency } from '@/utils/format';
import type { ChatMessage } from '@/types/chat';

const SUGGESTED_QUESTIONS = [
  { icon: <ShoppingOutlined />, text: '最近有什么优惠活动？' },
  { icon: <CarOutlined />, text: '我的订单什么时候能到？' },
  { icon: <SafetyCertificateOutlined />, text: '退换货政策是什么？' },
  { icon: <GiftOutlined />, text: '怎么使用优惠券？' },
  { icon: <CustomerServiceOutlined />, text: '如何联系人工客服？' },
];

function formatTime(ts: string) {
  const d = new Date(ts);
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function AssistantBubble({ msg, showThinking, onRegenerate }: { msg: ChatMessage; showThinking?: boolean; onRegenerate?: () => void }) {
  const isEmpty = !msg.content || !msg.content.trim();

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    antMsg.success('已复制');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'row', gap: 10, marginBottom: 20, padding: '0 8px' }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10, flexShrink: 0,
        background: 'linear-gradient(135deg, #7c3aed, #5b21b6)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 12px rgba(124,58,237,0.3)',
      }}>
        <RobotOutlined style={{ color: '#fff' }} />
      </div>
      <div style={{ maxWidth: '75%' }}>
        <div style={{
          padding: '14px 18px', borderRadius: 12,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          lineHeight: 1.8, wordBreak: 'break-word',
          backdropFilter: 'blur(6px)',
          display: 'flex', alignItems: 'center',
        }}>
          {showThinking && isEmpty ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="thinking-dot" style={{ animationDelay: '0s' }} />
              <span className="thinking-dot" style={{ animationDelay: '0.2s' }} />
              <span className="thinking-dot" style={{ animationDelay: '0.4s' }} />
            </div>
          ) : (
            <MarkdownViewer content={msg.content} />
          )}
        </div>
        {/* Meta row: intent + latency + timestamp */}
        <div style={{ marginTop: 4, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {!isEmpty && msg.intent && (
            <Tag color={INTENT_COLORS[msg.intent] || 'cyan'} style={{ fontSize: 10, borderRadius: 4 }}>
              {INTENT_LABELS[msg.intent] || msg.intent}
            </Tag>
          )}
          {msg.latency_ms != null && (
            <Typography.Text style={{ fontSize: 10, color: 'var(--text-muted)' }}>
              {formatLatency(msg.latency_ms)}
            </Typography.Text>
          )}
          <Typography.Text style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            {formatTime(msg.timestamp)}
          </Typography.Text>
        </div>
        {/* Action buttons */}
        {!isEmpty && !showThinking && (
          <div style={{ marginTop: 4, display: 'flex', gap: 4 }}>
            <button
              className="msg-action-btn"
              onClick={handleCopy}
              title="复制"
            >
              <CopyOutlined /> 复制
            </button>
            {onRegenerate && (
              <button
                className="msg-action-btn"
                onClick={onRegenerate}
                title="重新生成"
              >
                <ReloadOutlined /> 重新生成
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function MessageBubble({ msg, onRegenerate }: { msg: ChatMessage; onRegenerate?: () => void }) {
  const isUser = msg.role === 'user';
  if (!isUser) return <AssistantBubble msg={msg} onRegenerate={onRegenerate} />;
  return (
    <div style={{ display: 'flex', flexDirection: 'row-reverse', gap: 10, marginBottom: 20, padding: '0 8px' }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10, flexShrink: 0,
        background: 'linear-gradient(135deg, #00d4ff, #0098b3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 12px rgba(0,212,255,0.3)',
      }}>
        <UserOutlined style={{ color: '#fff' }} />
      </div>
      <div style={{ maxWidth: '75%' }}>
        <div style={{
          padding: '14px 18px', borderRadius: 12,
          background: 'var(--bg-hover)',
          border: '1px solid var(--border-subtle)',
          lineHeight: 1.8, wordBreak: 'break-word',
          backdropFilter: 'blur(6px)',
        }}>
          <Typography.Text style={{ color: 'var(--text-primary)' }}>{msg.content}</Typography.Text>
        </div>
        <div style={{ marginTop: 4, textAlign: 'right' }}>
          <Typography.Text style={{ fontSize: 10, color: 'var(--text-muted)' }}>
            {formatTime(msg.timestamp)}
          </Typography.Text>
        </div>
      </div>
    </div>
  );
}

function WelcomeScreen({ onQuickSend }: { onQuickSend: (text: string) => void }) {
  const handleEnter = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.borderColor = 'var(--accent)';
    e.currentTarget.style.background = 'var(--bg-hover)';
  };
  const handleLeave = (e: React.MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.borderColor = 'var(--border-subtle)';
    e.currentTarget.style.background = 'var(--bg-card)';
  };

  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 20,
      padding: '0 20px',
    }}>
      <div style={{ textAlign: 'center' }}>
        <Typography.Title level={3} style={{ margin: 0, color: 'var(--text-primary)', fontWeight: 700 }}>
          智能客服助手
        </Typography.Title>
        <Typography.Text style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4, display: 'block' }}>
          商品咨询 · 订单查询 · 物流追踪 · 售后服务
        </Typography.Text>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 600 }}>
        {SUGGESTED_QUESTIONS.map((q, idx) => (
          <div
            key={idx}
            onClick={() => onQuickSend(q.text)}
            onMouseEnter={handleEnter}
            onMouseLeave={handleLeave}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-card)',
              cursor: 'pointer', transition: 'all 0.2s',
              fontSize: 13, color: 'var(--text-primary)',
              whiteSpace: 'nowrap',
            }}
          >
            <span style={{ color: 'var(--accent)', fontSize: 14 }}>{q.icon}</span>
            <span>{q.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface ChatWindowProps {
  onQuickSend?: (text: string) => void;
  onRegenerate?: () => void;
}

export default function ChatWindow({ onQuickSend, onRegenerate }: ChatWindowProps) {
  const { conversations, activeId, streaming } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);
  const conv = conversations.find((c) => c.id === activeId);
  const messages = conv?.messages ?? [];

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, streaming]);

  if (!activeId || messages.length === 0) {
    return <WelcomeScreen onQuickSend={onQuickSend || (() => {})} />;
  }

  const lastMsg = messages[messages.length - 1];
  const isLastStreaming = streaming && lastMsg?.role === 'assistant';

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '16px 0' }}>
      {messages.map((msg, idx) => {
        const isLastAssistant = idx === messages.length - 1 && msg.role === 'assistant' && !isLastStreaming;
        if (idx === messages.length - 1 && isLastStreaming) {
          return <AssistantBubble key={msg.id} msg={msg} showThinking />;
        }
        return (
          <MessageBubble
            key={msg.id}
            msg={msg}
            onRegenerate={isLastAssistant ? onRegenerate : undefined}
          />
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
