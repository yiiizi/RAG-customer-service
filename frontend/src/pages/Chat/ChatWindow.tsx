import { useEffect, useRef, useState, type MouseEvent } from 'react';
import { App, Input, Modal, Select, Tag, Typography } from 'antd';
import {
  CarOutlined,
  CopyOutlined,
  CustomerServiceOutlined,
  DislikeOutlined,
  GiftOutlined,
  LikeOutlined,
  ReloadOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  ShoppingOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import MarkdownViewer from '@/components/MarkdownViewer';
import { INTENT_COLORS, INTENT_LABELS } from '@/utils/constants';
import { formatLatency } from '@/utils/format';
import type { ChatMessage } from '@/types/chat';
import { submitMessageFeedback } from '@/services/feedbackService';

const SUGGESTED_QUESTIONS = [
  { icon: <ShoppingOutlined />, text: '查询我的订单状态' },
  { icon: <CarOutlined />, text: '我的快递到哪里了' },
  { icon: <SafetyCertificateOutlined />, text: '退换货规则是什么' },
  { icon: <GiftOutlined />, text: '有哪些优惠活动' },
  { icon: <CustomerServiceOutlined />, text: '转人工客服' },
];

function formatTime(ts: string) {
  const d = new Date(ts);
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}

function AssistantBubble({
  msg,
  showThinking,
  onRegenerate,
}: {
  msg: ChatMessage;
  showThinking?: boolean;
  onRegenerate?: () => void;
}) {
  const isEmpty = !msg.content || !msg.content.trim();
  const { message } = App.useApp();
  const [feedbackSent, setFeedbackSent] = useState<'helpful' | 'unhelpful' | null>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackReason, setFeedbackReason] = useState('not_solved');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackSubmitting, setFeedbackSubmitting] = useState(false);
  const parsedMessageId = Number(msg.message_id ?? msg.id);
  const messageId = Number.isFinite(parsedMessageId) ? parsedMessageId : undefined;

  const handleCopy = () => {
    void navigator.clipboard.writeText(msg.content);
    message.success('已复制');
  };

  const handleHelpful = async () => {
    if (!messageId) {
      message.warning('当前消息还未保存，稍后再反馈');
      return;
    }
    setFeedbackSubmitting(true);
    try {
      await submitMessageFeedback(messageId, { rating: 'helpful' });
      setFeedbackSent('helpful');
      message.success('已记录反馈');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  const handleUnhelpful = async () => {
    if (!messageId) {
      message.warning('当前消息还未保存，稍后再反馈');
      return;
    }
    setFeedbackSubmitting(true);
    try {
      await submitMessageFeedback(messageId, {
        rating: 'unhelpful',
        reason: feedbackReason,
        comment: feedbackComment.trim() || undefined,
      });
      setFeedbackSent('unhelpful');
      setFeedbackOpen(false);
      message.success('已记录反馈');
    } finally {
      setFeedbackSubmitting(false);
    }
  };

  return (
    <div className="msg-bubble-enter" style={{ display: 'flex', flexDirection: 'row', gap: 10, marginBottom: 12, padding: '0 8px' }}>
      <div style={{
        width: 36, height: 36, borderRadius: 12, flexShrink: 0,
        background: 'linear-gradient(135deg, #6C63FF, #8B7FFF)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 12px rgba(108, 99, 255, 0.3)',
      }}>
        <RobotOutlined style={{ color: '#fff', fontSize: 16 }} />
      </div>
      <div style={{ maxWidth: '75%' }}>
        <div style={{
          padding: '14px 18px', borderRadius: '18px 12px 12px 18px',
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          lineHeight: 1.8, wordBreak: 'break-word',
          backdropFilter: 'blur(6px)',
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
        <div style={{ marginTop: 4, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          {!isEmpty && msg.intent && (
            <Tag color={INTENT_COLORS[msg.intent] || 'cyan'} style={{ fontSize: 10, borderRadius: 6 }}>
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
        {!isEmpty && !showThinking && (
          <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
            <button className="msg-action-btn" onClick={handleCopy} title="复制">
              <CopyOutlined /> 复制
            </button>
            {onRegenerate && (
              <button className="msg-action-btn" onClick={onRegenerate} title="重新生成">
                <ReloadOutlined /> 重新生成
              </button>
            )}
            <button className="msg-action-btn" onClick={handleHelpful} disabled={feedbackSubmitting || feedbackSent === 'helpful'} title="有帮助">
              <LikeOutlined /> 有帮助
            </button>
            <button className="msg-action-btn" onClick={() => setFeedbackOpen(true)} disabled={feedbackSubmitting || feedbackSent === 'unhelpful'} title="没帮助">
              <DislikeOutlined /> 没帮助
            </button>
          </div>
        )}
        <Modal
          title="反馈原因"
          open={feedbackOpen}
          confirmLoading={feedbackSubmitting}
          onOk={handleUnhelpful}
          onCancel={() => setFeedbackOpen(false)}
          okText="提交"
          cancelText="取消"
        >
          <Select
            value={feedbackReason}
            onChange={setFeedbackReason}
            style={{ width: '100%', marginBottom: 12 }}
            options={[
              { value: 'wrong_answer', label: '答非所问' },
              { value: 'incomplete', label: '信息不完整' },
              { value: 'outdated', label: '信息可能过期' },
              { value: 'not_solved', label: '没解决问题' },
              { value: 'need_human', label: '需要人工客服' },
              { value: 'other', label: '其他' },
            ]}
          />
          <Input.TextArea
            value={feedbackComment}
            onChange={(e) => setFeedbackComment(e.target.value)}
            placeholder="可以补充具体问题，便于客服后续优化"
            rows={4}
            maxLength={1000}
            showCount
          />
        </Modal>
      </div>
    </div>
  );
}

function MessageBubble({ msg, onRegenerate }: { msg: ChatMessage; onRegenerate?: () => void }) {
  const isUser = msg.role === 'user';
  if (!isUser) return <AssistantBubble msg={msg} onRegenerate={onRegenerate} />;
  return (
    <div className="msg-bubble-enter" style={{ display: 'flex', flexDirection: 'row-reverse', gap: 10, marginBottom: 12, padding: '0 8px' }}>
      <div style={{
        width: 36, height: 36, borderRadius: 12, flexShrink: 0,
        background: 'linear-gradient(135deg, #FF6584, #FF8FA3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 12px rgba(255, 101, 132, 0.3)',
      }}>
        <UserOutlined style={{ color: '#fff', fontSize: 16 }} />
      </div>
      <div style={{ maxWidth: '75%' }}>
        <div style={{
          padding: '14px 18px', borderRadius: '12px 18px 18px 12px',
          background: 'linear-gradient(135deg, #6C63FF, #7B73FF)',
          border: 'none',
          lineHeight: 1.8, wordBreak: 'break-word',
          color: '#fff',
        }}>
          <Typography.Text style={{ color: '#fff' }}>{msg.content}</Typography.Text>
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
  const handleEnter = (e: MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.borderColor = 'var(--accent)';
    e.currentTarget.style.background = 'var(--bg-hover)';
  };
  const handleLeave = (e: MouseEvent<HTMLDivElement>) => {
    e.currentTarget.style.borderColor = 'var(--border-subtle)';
    e.currentTarget.style.background = 'var(--bg-card)';
  };

  return (
    <div className="fade-in" style={{
      flex: 1, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: 20,
      padding: '0 20px',
    }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{
          width: 64, height: 64, borderRadius: 18,
          background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 16,
          boxShadow: '0 8px 32px rgba(108, 99, 255, 0.3)',
        }}>
          <RobotOutlined style={{ color: '#fff', fontSize: 28 }} />
        </div>
        <Typography.Title level={3} style={{ margin: 0, color: 'var(--text-primary)', fontWeight: 700 }}>
          智能客服问答
        </Typography.Title>
        <Typography.Text style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 4, display: 'block' }}>
          可以咨询订单、物流、售后、优惠活动，也可以直接转人工客服
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
              padding: '8px 16px', borderRadius: 8,
              border: '1px solid var(--border-subtle)',
              background: 'var(--bg-card)',
              cursor: 'pointer', transition: 'all 0.25s',
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

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
