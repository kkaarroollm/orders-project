import { useState } from 'react';
import { useNotifications } from '../api/notifications';

const Notifications = () => {
  const [notifications, setNotifications] = useState<string[]>([]);

  useNotifications((msg) => {
    setNotifications((prev) => [...prev, msg]);
  });

  return (
    <div className="p-4 bg-gray-100 rounded">
      <h2 className="text-lg font-semibold">Notifications</h2>
      <ul>
        {notifications.map((n, i) => (
          <li key={i} className="text-sm text-gray-700">
            {n}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Notifications;
