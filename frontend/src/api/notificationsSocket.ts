import useWebSocket from 'react-use-websocket';
import { NOTIFICATION_WS_URL } from '@/config/env';

export const useNotifications = (onMessage: (msg: string) => void) => {
  useWebSocket(NOTIFICATION_WS_URL, {
    onMessage: (event) => onMessage(event.data),
    shouldReconnect: () => true,
  });
};
