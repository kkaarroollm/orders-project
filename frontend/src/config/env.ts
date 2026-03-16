const normalizeOrdersApiUrl = (rawUrl: string | undefined): string => {
  const localDefault = '/api/v1';

  if (!rawUrl) {
    return localDefault;
  }

  if (rawUrl.startsWith('/')) {
    return rawUrl.replace(/\/$/, '');
  }

  try {
    const base =
      typeof window !== 'undefined'
        ? window.location.origin
        : 'http://localhost';
    const parsed = new URL(rawUrl, base);

    // Local compose/nginx setup is HTTP only unless TLS is explicitly configured.
    if (parsed.hostname === 'localhost' && parsed.protocol === 'https:') {
      parsed.protocol = 'http:';
    }

    return parsed.toString().replace(/\/$/, '');
  } catch {
    return rawUrl.replace(/\/$/, '');
  }
};

export const API_ORDERS_URL = normalizeOrdersApiUrl(
  import.meta.env.VITE_API_ORDERS,
);
export const NOTIFICATION_WS_URL = import.meta.env.VITE_API_NOTIFICATIONS_WS;
