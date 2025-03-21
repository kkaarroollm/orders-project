import React, { JSX } from 'react';
import { useOrderTracking } from '@/hooks/useOrderTracking';
import { Card } from '@/components/ui/card';
import { motion } from 'framer-motion';
import { CheckCircle, Truck, Timer, Package } from 'lucide-react';
import { OrderStatus } from '@/types';

const statuses: OrderStatus[] = [
  OrderStatus.CONFIRMED,
  OrderStatus.PREPARING,
  OrderStatus.OUT_FOR_DELIVERY,
  OrderStatus.WAITING_FOR_PICKUP,
  OrderStatus.ON_THE_WAY,
  OrderStatus.DELIVERED,
];

const statusIcons: Record<OrderStatus, JSX.Element> = {
  [OrderStatus.CONFIRMED]: <CheckCircle className="h-6 w-6" />,
  [OrderStatus.PREPARING]: <Timer className="h-6 w-6" />,
  [OrderStatus.OUT_FOR_DELIVERY]: <Truck className="h-6 w-6" />,
  [OrderStatus.WAITING_FOR_PICKUP]: <Timer className="h-6 w-6" />,
  [OrderStatus.ON_THE_WAY]: <Truck className="h-6 w-6" />,
  [OrderStatus.DELIVERED]: <Package className="h-6 w-6" />,
};

const timelineLabels: Record<OrderStatus, string> = {
  [OrderStatus.CONFIRMED]: 'Confirmed',
  [OrderStatus.PREPARING]: 'Preparing',
  [OrderStatus.OUT_FOR_DELIVERY]: 'Out for Delivery',
  [OrderStatus.WAITING_FOR_PICKUP]: 'Pickup',
  [OrderStatus.ON_THE_WAY]: 'On The Way',
  [OrderStatus.DELIVERED]: 'Delivered',
};

const statusMessages: Record<OrderStatus, string> = {
  [OrderStatus.CONFIRMED]:
    'Your order has been confirmed and is now being processed.',
  [OrderStatus.PREPARING]:
    'We are preparing your order. It will be ready for shipment shortly.',
  [OrderStatus.OUT_FOR_DELIVERY]:
    'Your order is out for delivery. Get ready to receive it!',
  [OrderStatus.WAITING_FOR_PICKUP]:
    'Your order is waiting for pickup. The courier will collect it soon.',
  [OrderStatus.ON_THE_WAY]: 'Your order is on the way to your location.',
  [OrderStatus.DELIVERED]:
    'Your order has been delivered. Enjoy your purchase!',
};

const statusVariants = {
  hidden: { opacity: 0, scale: 0.9 },
  visible: { opacity: 1, scale: 1, transition: { duration: 0.5 } },
};

export default function OrderTracker({ orderId }: { orderId: string }) {
  const currentStatus = useOrderTracking(orderId);

  if (!currentStatus) {
    return (
      <Card className="p-6 space-y-4 dark:bg-gray-800">
        <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">
          📦 Order Tracking
        </h1>
        <p className="text-gray-500 text-center">Loading order status...</p>
      </Card>
    );
  }

  const currentIndex = statuses.indexOf(currentStatus);

  return (
    <Card className="p-6 space-y-8 dark:bg-gray-800">
      <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-gray-100">
        📦 Order Tracking
      </h1>

      <div className="flex items-center justify-center space-x-6">
        {statuses.map((status, index) => {
          const isActive = index <= currentIndex;
          return (
            <div key={status} className="flex flex-col items-center">
              <div
                className={`rounded-full p-2 
                  ${
                    isActive
                      ? 'bg-blue-500 dark:bg-blue-600'
                      : 'bg-gray-300 dark:bg-gray-700'
                  }
                `}
              >
                {React.cloneElement(statusIcons[status], {
                  className: isActive
                    ? 'h-6 w-6 text-white'
                    : 'h-6 w-6 text-gray-600 dark:text-gray-300',
                })}
              </div>

              <span
                className={`mt-1 text-xs 
                  ${
                    isActive
                      ? 'text-blue-500 dark:text-blue-400 font-semibold'
                      : 'text-gray-500 dark:text-gray-400'
                  }
                `}
              >
                {timelineLabels[status]}
              </span>
            </div>
          );
        })}
      </div>

      <motion.div
        key={currentStatus}
        initial="hidden"
        animate="visible"
        variants={statusVariants}
        className="flex flex-col items-center space-y-3"
      >
        <div className="rounded-full p-4 bg-blue-500 dark:bg-blue-600">
          {React.cloneElement(statusIcons[currentStatus], {
            className: 'h-10 w-10 text-white',
          })}
        </div>
        <p className="text-base text-center text-gray-700 dark:text-gray-200">
          {statusMessages[currentStatus]}
        </p>
      </motion.div>
    </Card>
  );
}
