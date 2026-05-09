import { useRef, useCallback, useState } from 'react';
import { getWebSocketUrl } from '@/services/chatService';

type MsgHandler = (data: Record<string, unknown>) => void;
export type ConnectionStatus = 'connected' | 'disconnected' | 'retrying';

const INITIAL_DELAY = 3000;
const MAX_DELAY = 30000;
const MAX_RETRIES = 10;

export function useWebSocket(onMessage: MsgHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const pendingRef = useRef<string[]>([]);
  const retryCountRef = useRef(0);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');

  const flushPending = useCallback(() => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    const pending = pendingRef.current;
    while (pending.length > 0) {
      const msg = pending.shift()!;
      ws.send(msg);
    }
  }, []);

  const send = useCallback((data: Record<string, unknown>) => {
    const msg = JSON.stringify(data);
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(msg);
    } else {
      pendingRef.current.push(msg);
      if (!ws || ws.readyState === WebSocket.CLOSED) {
        doConnect();
      }
    }
  }, []);

  const doConnect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const url = getWebSocketUrl();
    const ws = new WebSocket(url);
    wsRef.current = ws;
    setConnectionStatus('retrying');

    ws.onopen = () => {
      console.log('WebSocket connected');
      retryCountRef.current = 0;
      setConnectionStatus('connected');
      flushPending();
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessageRef.current(data);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      if (retryCountRef.current >= MAX_RETRIES) {
        console.warn('WebSocket: max retries reached');
        setConnectionStatus('disconnected');
        return;
      }
      const delay = Math.min(INITIAL_DELAY * Math.pow(2, retryCountRef.current), MAX_DELAY);
      retryCountRef.current++;
      setConnectionStatus('retrying');
      console.log(`WebSocket closed — reconnecting in ${delay / 1000}s (attempt ${retryCountRef.current})`);
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = setTimeout(() => doConnect(), delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [flushPending]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    retryCountRef.current = MAX_RETRIES;
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionStatus('disconnected');
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    retryCountRef.current = 0;
    setConnectionStatus('retrying');
    doConnect();
  }, [disconnect, doConnect]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    retryCountRef.current = 0;
    doConnect();
  }, [doConnect]);

  return { connect, send, disconnect, reconnect, connectionStatus };
}
