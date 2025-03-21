import { useEffect, useState } from 'react';
import { OrderStatus } from '@/types.ts';
import { NOTIFICATION_WS_URL } from '@/config/env';

export function useOrderTracking(orderId: string) {
  const [status, setStatus] = useState<OrderStatus | null>(null);

  useEffect(() => {
    if (!orderId) return;

    const socket = new WebSocket(
      `${NOTIFICATION_WS_URL}/order-tracking/${orderId}/ws`,
    );

    socket.onopen = () => console.log('WebSocket connected');

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setStatus(data.status as OrderStatus);
    };

    socket.onclose = () => console.log('WebSocket disconnected');

    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close(1000, 'Client closed connection');
      }
    };
  }, [orderId]);

  return status;
}
