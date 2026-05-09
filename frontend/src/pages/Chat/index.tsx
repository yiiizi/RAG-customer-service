import { useEffect, useRef, useCallback } from 'react';
import { useChatStore } from '@/stores/useChatStore';
import ChatWindow from './ChatWindow';
import ChatInput from './ChatInput';

export default function ChatPage() {
  const { activeId, newConversation, deleteLastAssistant, conversations } = useChatStore();
  const initRef = useRef(false);
  const sendRef = useRef<((text: string) => void) | null>(null);

  useEffect(() => {
    if (!initRef.current && !activeId) {
      initRef.current = true;
      newConversation();
    }
  }, [activeId, newConversation]);

  const handleQuickSend = useCallback((text: string) => {
    if (sendRef.current) sendRef.current(text);
  }, []);

  const handleRegenerate = useCallback(() => {
    if (!activeId) return;
    const state = useChatStore.getState();
    const conv = state.conversations.find((c) => c.id === activeId);
    if (!conv) return;
    const lastUserMsg = [...conv.messages].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;
    deleteLastAssistant(activeId);
    // doSend uses getState() internally, no need to wait for render
    if (sendRef.current) sendRef.current(lastUserMsg.content);
  }, [activeId, deleteLastAssistant]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <ChatWindow onQuickSend={handleQuickSend} onRegenerate={handleRegenerate} />
      <ChatInput sendRef={sendRef} />
    </div>
  );
}
