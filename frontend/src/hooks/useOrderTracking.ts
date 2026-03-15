import { useCallback, useEffect, useRef, useState } from 'react';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { OrderStatus } from '@/types.ts';
import { NOTIFICATION_WS_URL } from '@/config/env';

export function useOrderTracking(orderId: string) {
  const [status, setStatus] = useState<OrderStatus | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const socketUrl = orderId
    ? `${NOTIFICATION_WS_URL}/ws/v1/order-tracking/${orderId}`
    : null;

  const onMessage = useCallback((event: MessageEvent) => {
    const data = JSON.parse(event.data);
    if (data.type === 'ping') return;
    setStatus(data.status as OrderStatus);
  }, []);

  const { sendMessage, readyState } = useWebSocket(socketUrl, {
    onMessage,
    shouldReconnect: () => true,
    reconnectAttempts: Infinity,
    reconnectInterval: (attempt) => Math.min(1000 * 2 ** attempt, 30000),
  });

  useEffect(() => {
    if (readyState === ReadyState.OPEN) {
      heartbeatRef.current = setInterval(() => {
        sendMessage('ping');
      }, 25000);
    }

    return () => {
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
    };
  }, [readyState, sendMessage]);

  return { status, isConnected: readyState === ReadyState.OPEN };
}
