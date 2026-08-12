import { useEffect, useState } from 'react';
import { OrderStatus } from '@/types.ts';
import { NOTIFICATION_SSE_URL } from '@/config/env';

export interface TrackingEvent {
  status: OrderStatus;
  receivedAt: number;
}

export function useOrderTracking(orderId: string) {
  const [status, setStatus] = useState<OrderStatus | null>(null);
  const [events, setEvents] = useState<TrackingEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!orderId) return;

    setStatus(null);
    setEvents([]);

    const source = new EventSource(
      `${NOTIFICATION_SSE_URL}/api/v1/order-tracking/${orderId}`,
    );

    source.onopen = () => setIsConnected(true);
    source.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data);
      const next = data.status as OrderStatus;
      setStatus(next);
      // Kept so the page can show that each status arrived as its own push,
      // rather than as the result of polling.
      setEvents((prev) =>
        prev.length > 0 && prev[prev.length - 1].status === next
          ? prev
          : [...prev, { status: next, receivedAt: Date.now() }],
      );
    };
    // EventSource reconnects on its own, using the server's `retry` interval.
    source.onerror = () => setIsConnected(false);

    return () => source.close();
  }, [orderId]);

  return { status, events, isConnected };
}
