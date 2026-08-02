import { useEffect, useState } from 'react';
import { OrderStatus } from '@/types.ts';
import { NOTIFICATION_SSE_URL } from '@/config/env';

export function useOrderTracking(orderId: string) {
  const [status, setStatus] = useState<OrderStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;

    const source = new EventSource(
      `${NOTIFICATION_SSE_URL}/api/v1/order-tracking/${orderId}`,
    );

    source.onopen = () => setIsConnected(true);
    source.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      setStatus(data.status as OrderStatus);
    };
    // EventSource reconnects on its own, using the server's `retry` interval.
    source.onerror = () => setIsConnected(false);

    return () => source.close();
  }, [orderId]);

  return { status, isConnected };
}
