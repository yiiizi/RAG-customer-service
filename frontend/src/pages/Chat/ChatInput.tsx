import { useState, useRef, useCallback, useEffect } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined, GlobalOutlined, StopOutlined } from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SourceItem } from '@/types/chat';
import { v4 as uuidv4 } from './uuid';

interface ChatInputProps {
  sendRef?: React.MutableRefObject<((text: string) => void) | null>;
}

export default function ChatInput({ sendRef }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [webSearch, setWebSearch] = useState(false);
  const { activeId, streaming, setStreaming, addMessage, appendToLast, updateLastSources, updateLastMeta, updateLastMessageId, newConversation } =
    useChatStore();
  const inputRef = useRef<any>(null);

  const convQueue = useRef<string[]>([]);
  const activeConvId = useRef<string | null>(null);

  const handleMessage = useCallback(
    (data: Record<string, unknown>) => {
      const type = data.type as string;

      if (type === 'sources' || type === 'token' || type === 'error') {
        if (!activeConvId.current && convQueue.current.length > 0) {
          activeConvId.current = convQueue.current.shift()!;
        }
      }

      const savedPayload = type === 'message_saved' ? data.data as Record<string, unknown> | undefined : undefined;
      const convId = activeConvId.current || (savedPayload?.conversation_id ? String(savedPayload.conversation_id) : null);
      if (!convId) return;

      if (type === 'sources') {
        const sources = (data.data as any[]) || [];
        updateLastSources(convId, sources.map((s: any) => ({
          text: s.text || '',
          source: s.source || '',
          score: s.score || 0,
          chunk_index: s.chunk_index ?? -1,
        })));
      } else if (type === 'token') {
        appendToLast(convId, data.data as string);
      } else if (type === 'done') {
        const meta = data.data as Record<string, unknown> | undefined;
        updateLastMeta(convId, {
          intent: meta?.intent as string,
          latency_ms: meta?.latency_ms as number,
        });
        if (convQueue.current.length === 0) {
          setStreaming(false);
        }
      } else if (type === 'message_saved') {
        const messageId = Number(savedPayload?.message_id);
        if (Number.isFinite(messageId)) {
          updateLastMessageId(convId, messageId);
        }
        activeConvId.current = null;
      } else if (type === 'error') {
        appendToLast(convId, `\n\n> ⚠️ 错误: ${data.data}`);
        activeConvId.current = null;
        if (convQueue.current.length === 0) {
          setStreaming(false);
        }
      }
    },
    [appendToLast, updateLastSources, updateLastMeta, updateLastMessageId, setStreaming]
  );

  const { connect, send, disconnect, connectionStatus } = useWebSocket(handleMessage);

  // Auto-connect on mount (once only)
  const hasAutoConnected = useRef(false);
  useEffect(() => {
    if (!hasAutoConnected.current) {
      hasAutoConnected.current = true;
      connect();
    }
  }, [connect]);

  const doSend = useCallback(async (textOverride?: string) => {
    const text = (textOverride ?? value).trim();
    if (!text || streaming) return;

    const state = useChatStore.getState();
    let convId = activeId ?? state.activeId;
    if (!convId || !state.conversations.some((conv) => conv.id === convId)) {
      convId = await newConversation();
    }

    convQueue.current.push(convId);

    const userMsg = { id: uuidv4(), role: 'user' as const, content: text, timestamp: new Date().toISOString() };
    addMessage(convId, userMsg);
    const assistantMsg = { id: uuidv4(), role: 'assistant' as const, content: '', sources: [] as SourceItem[], timestamp: new Date().toISOString() };
    addMessage(convId, assistantMsg);
    setStreaming(true);

    setValue('');
    inputRef.current?.focus();

    connect();
    send({ query: text, conversation_id: Number(convId), kb_only: false, web_search: webSearch });
  }, [value, streaming, activeId, addMessage, setStreaming, newConversation, connect, send, webSearch]);

  useEffect(() => {
    if (sendRef) {
      sendRef.current = (text: string) => { void doSend(text); };
    }
  }, [doSend, sendRef]);

  useEffect(() => {
    const handler = (event: Event) => {
      const text = (event as CustomEvent<string>).detail;
      if (typeof text === 'string' && text.trim()) {
        void doSend(text);
      }
    };
    window.addEventListener('rag:quick-send', handler);
    return () => window.removeEventListener('rag:quick-send', handler);
  }, [doSend]);

  const handleStop = () => {
    disconnect();
    setStreaming(false);
    activeConvId.current = null;
    convQueue.current = [];
  };

  return (
    <div style={{ padding: '0 0 16px', display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
      <div style={{ position: 'relative', width: '56%', minWidth: 360, maxWidth: 680 }}>

        <Input.TextArea
          ref={inputRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="输入你的问题... (Shift+Enter 换行，Enter 发送)"
          autoSize={{ minRows: 2, maxRows: 4 }}
          onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); void doSend(); } }}
          disabled={streaming}
          style={{
            borderRadius: 12,
            padding: '12px 52px 40px 16px',
            fontSize: 14,
            lineHeight: 1.8,
            resize: 'none',
            background: 'var(--input-bg)',
            boxShadow: 'inset 0 1px 4px rgba(0,0,0,0.1)',
          }}
        />

        {/* Capsule toggles */}
        <div style={{ position: 'absolute', left: 8, bottom: 8, zIndex: 5, display: 'flex', gap: 6 }}>
          <span
            className={`capsule-toggle${webSearch ? ' active' : ''}`}
            onClick={(e) => { e.stopPropagation(); setWebSearch(!webSearch); }}
          >
            <GlobalOutlined style={{ fontSize: 12 }} />
            <span>联网</span>
          </span>
        </div>

        {/* Send / Stop button */}
        {streaming ? (
          <Button
            danger
            icon={<StopOutlined style={{ fontSize: 16 }} />}
            onClick={handleStop}
            style={{
              position: 'absolute', right: 8, bottom: 10,
              width: 40, height: 40, borderRadius: 12,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          />
        ) : (
          <button
            onClick={() => { void doSend(); }}
            style={{
              position: 'absolute', right: 8, bottom: 10,
              width: 40, height: 40, borderRadius: 12,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'linear-gradient(135deg, #6C63FF, #FF6584)',
              border: 'none',
              cursor: 'pointer',
              boxShadow: '0 4px 16px rgba(108, 99, 255, 0.3)',
              transition: 'transform 0.2s, box-shadow 0.2s',
              color: '#fff',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.transform = 'scale(1.08)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(108, 99, 255, 0.4)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(108, 99, 255, 0.3)'; }}
          >
            <SendOutlined style={{ fontSize: 18 }} />
          </button>
        )}
      </div>
    </div>
  );
}
