import useWebSocket from 'react-use-websocket';

const NOTIFICATION_WS_URL = import.meta.env.VITE_WS_NOTIFICATIONS;

export const useNotifications = (onMessage: (msg: string) => void) => {
  useWebSocket(NOTIFICATION_WS_URL, {
    onMessage: (event) => onMessage(event.data),
    shouldReconnect: () => true,
  });
};
