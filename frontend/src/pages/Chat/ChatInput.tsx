import { useState, useRef, useCallback, useEffect } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined, DatabaseOutlined, GlobalOutlined, StopOutlined, ReloadOutlined } from '@ant-design/icons';
import { useChatStore } from '@/stores/useChatStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import type { SourceItem } from '@/types/chat';
import { v4 as uuidv4 } from './uuid';

interface ChatInputProps {
  sendRef?: React.MutableRefObject<((text: string) => void) | null>;
}

export default function ChatInput({ sendRef }: ChatInputProps) {
  const [value, setValue] = useState('');
  const [kbOnly, setKbOnly] = useState(false);
  const [webSearch, setWebSearch] = useState(false);
  const { activeId, streaming, setStreaming, addMessage, appendToLast, updateLastSources, updateLastMeta, newConversation } =
    useChatStore();
  const inputRef = useRef<any>(null);

  // FIFO queue: each send enqueues convId, each done/error dequeues
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

      const convId = activeConvId.current;
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
        activeConvId.current = null;
        if (convQueue.current.length === 0) {
          setStreaming(false);
        }
      } else if (type === 'error') {
        appendToLast(convId, `\n\n> ⚠️ 错误: ${data.data}`);
        activeConvId.current = null;
        if (convQueue.current.length === 0) {
          setStreaming(false);
        }
      }
    },
    [appendToLast, updateLastSources, updateLastMeta, setStreaming]
  );

  const { connect, send, disconnect, reconnect, connectionStatus } = useWebSocket(handleMessage);

  // Build and send a query (used by both direct send and sendRef)
  const doSend = useCallback((textOverride?: string) => {
    const text = (textOverride ?? value).trim();
    if (!text || streaming) return;

    // Get latest conversations from store (not stale closure)
    const state = useChatStore.getState();
    let convId = activeId ?? state.activeId;
    if (!convId) {
      convId = newConversation();
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
    const conv = state.conversations.find((c: any) => c.id === convId);
    const history = conv?.messages
      .filter((m: any) => m.content.trim())
      .slice(-10)
      .map((m: any) => ({ role: m.role, content: m.content })) || [];
    send({ query: text, kb_only: kbOnly, web_search: webSearch, history });
  }, [value, streaming, activeId, addMessage, setStreaming, newConversation, connect, send, kbOnly, webSearch]);

  // Expose doSend to parent via ref — simple reuse, no duplication
  useEffect(() => {
    if (sendRef) {
      sendRef.current = (text: string) => doSend(text);
    }
  }, [doSend, sendRef]);

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
          onPressEnter={(e) => { if (!e.shiftKey) { e.preventDefault(); doSend(); } }}
          disabled={streaming}
          style={{ borderRadius: 12, padding: '10px 52px 36px 14px', fontSize: 14, lineHeight: 1.8, resize: 'none' }}
        />
        {/* KB-only toggle */}
        <span
          onClick={(e) => { e.stopPropagation(); setKbOnly(!kbOnly); }}
          style={{
            position: 'absolute', left: 8, bottom: 8, zIndex: 5,
            height: 28, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 4,
            padding: '0 8px', cursor: 'pointer',
            color: kbOnly ? '#69b1ff' : 'var(--text-muted)',
            fontSize: 12, transition: 'color 0.2s', userSelect: 'none',
          }}
        >
          <DatabaseOutlined style={{ fontSize: 14 }} />
          <span>知识库</span>
        </span>
        {/* Web search toggle */}
        <span
          onClick={(e) => { e.stopPropagation(); setWebSearch(!webSearch); }}
          style={{
            position: 'absolute', left: 82, bottom: 8, zIndex: 5,
            height: 28, borderRadius: 6, display: 'flex', alignItems: 'center', gap: 4,
            padding: '0 8px', cursor: 'pointer',
            color: webSearch ? '#ffa940' : 'var(--text-muted)',
            fontSize: 12, transition: 'color 0.2s', userSelect: 'none',
          }}
        >
          <GlobalOutlined style={{ fontSize: 14 }} />
          <span>联网</span>
        </span>
        {/* Send / Stop button */}
        {streaming ? (
          <Button
            danger
            icon={<StopOutlined style={{ fontSize: 18 }} />}
            onClick={handleStop}
            style={{
              position: 'absolute', right: 8, bottom: 10,
              width: 36, height: 36, borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          />
        ) : (
          <Button
            type="primary"
            icon={<SendOutlined style={{ fontSize: 18 }} />}
            onClick={() => doSend()}
            style={{
              position: 'absolute', right: 8, bottom: 10,
              width: 36, height: 36, borderRadius: 8,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          />
        )}
      </div>
      {/* Connection status banner — below input */}
      {connectionStatus === 'disconnected' && (
        <div style={{
          marginTop: 8, padding: '6px 12px', borderRadius: 8, width: '56%', minWidth: 360, maxWidth: 680,
          background: 'rgba(255, 68, 114, 0.1)', border: '1px solid rgba(255, 68, 114, 0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
        }}>
          <span style={{ fontSize: 12, color: 'var(--red)' }}>连接已断开</span>
          <Button size="small" icon={<ReloadOutlined />} onClick={reconnect}
            style={{ fontSize: 11, height: 24 }}>重新连接</Button>
        </div>
      )}
    </div>
  );
}
