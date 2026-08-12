import { motion } from 'framer-motion';
import {
  Check,
  ChefHat,
  PackageCheck,
  Truck,
  Bike,
  Warehouse,
  type LucideIcon,
} from 'lucide-react';
import { useOrderTracking } from '@/hooks/useOrderTracking';
import { OrderStatus } from '@/types';
import { cn } from '@/lib/utils';

const statuses: OrderStatus[] = [
  OrderStatus.CONFIRMED,
  OrderStatus.PREPARING,
  OrderStatus.OUT_FOR_DELIVERY,
  OrderStatus.WAITING_FOR_PICKUP,
  OrderStatus.ON_THE_WAY,
  OrderStatus.DELIVERED,
];

const statusIcons: Record<OrderStatus, LucideIcon> = {
  [OrderStatus.CONFIRMED]: Check,
  [OrderStatus.PREPARING]: ChefHat,
  [OrderStatus.OUT_FOR_DELIVERY]: Warehouse,
  [OrderStatus.WAITING_FOR_PICKUP]: Truck,
  [OrderStatus.ON_THE_WAY]: Bike,
  [OrderStatus.DELIVERED]: PackageCheck,
};

const timelineLabels: Record<OrderStatus, string> = {
  [OrderStatus.CONFIRMED]: 'Confirmed',
  [OrderStatus.PREPARING]: 'Preparing',
  [OrderStatus.OUT_FOR_DELIVERY]: 'Out for delivery',
  [OrderStatus.WAITING_FOR_PICKUP]: 'Pickup',
  [OrderStatus.ON_THE_WAY]: 'On the way',
  [OrderStatus.DELIVERED]: 'Delivered',
};

const statusMessages: Record<OrderStatus, string> = {
  [OrderStatus.CONFIRMED]: 'The order is confirmed and queued for the kitchen.',
  [OrderStatus.PREPARING]: 'It is being prepared. Shipment follows shortly.',
  [OrderStatus.OUT_FOR_DELIVERY]: 'It has left the kitchen for the depot.',
  [OrderStatus.WAITING_FOR_PICKUP]: 'Waiting for a courier to collect it.',
  [OrderStatus.ON_THE_WAY]: 'A courier is on the way to your address.',
  [OrderStatus.DELIVERED]: 'Delivered. Enjoy it.',
};

const ConnectionPill = ({ connected }: { connected: boolean }) => (
  <span className="flex items-center gap-1.5">
    <span className="relative flex h-1.5 w-1.5">
      {connected && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-success opacity-70" />
      )}
      <span
        className={cn(
          'relative inline-flex h-1.5 w-1.5 rounded-full',
          connected ? 'bg-success' : 'bg-muted-foreground',
        )}
      />
    </span>
    <span className="label">{connected ? 'SSE live' : 'Reconnecting'}</span>
  </span>
);

const clockTime = (ms: number) =>
  new Date(ms).toLocaleTimeString('en-GB', { hour12: false });

export default function OrderTracker({ orderId }: { orderId: string }) {
  const {
    status: currentStatus,
    events,
    isConnected,
  } = useOrderTracking(orderId);

  const currentIndex = currentStatus ? statuses.indexOf(currentStatus) : -1;
  const progress =
    currentIndex < 0 ? 0 : (currentIndex / (statuses.length - 1)) * 100;
  const CurrentIcon = currentStatus ? statusIcons[currentStatus] : null;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-2">
          <p className="label">Tracking</p>
          <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
            {currentStatus
              ? timelineLabels[currentStatus]
              : 'Waiting for the first event'}
          </h1>
          <p className="numeric text-sm text-muted-foreground">{orderId}</p>
        </div>
        <ConnectionPill connected={isConnected} />
      </header>

      <section className="surface-card p-6 sm:p-7">
        {/* progress rail */}
        <div className="relative mb-6 h-0.5 w-full bg-border">
          <motion.div
            className="absolute inset-y-0 left-0 bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          />
        </div>

        <ol className="grid grid-cols-3 gap-y-6 sm:grid-cols-6">
          {statuses.map((status, index) => {
            const Icon = statusIcons[status];
            const reached = index <= currentIndex;
            const isCurrent = index === currentIndex;

            return (
              <li
                key={status}
                className="flex flex-col items-center gap-2 text-center"
              >
                <span
                  className={cn(
                    'flex h-9 w-9 items-center justify-center rounded-full border transition-colors',
                    reached
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-muted text-muted-foreground',
                    isCurrent &&
                      'ring-2 ring-primary/30 ring-offset-2 ring-offset-card',
                  )}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span
                  className={cn(
                    'text-xs leading-tight',
                    reached ? 'text-foreground' : 'text-muted-foreground',
                  )}
                >
                  {timelineLabels[status]}
                </span>
              </li>
            );
          })}
        </ol>
      </section>

      {currentStatus && CurrentIcon ? (
        <motion.section
          key={currentStatus}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="surface-card flex items-center gap-4 p-6"
        >
          <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <CurrentIcon className="h-5 w-5" />
          </span>
          <p className="text-sm">{statusMessages[currentStatus]}</p>
        </motion.section>
      ) : (
        <section className="surface-card p-10 text-center">
          <p className="text-sm text-muted-foreground">
            {isConnected
              ? 'Connected. Waiting for the first status to be pushed.'
              : 'Opening the event stream…'}
          </p>
        </section>
      )}

      {events.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="label">Events received</h2>
          <ul className="surface-card overflow-hidden font-mono text-xs">
            {events.map((event) => (
              <li
                key={`${event.status}-${event.receivedAt}`}
                className="flex items-center gap-4 border-b border-border px-4 py-2.5 last:border-b-0"
              >
                <span className="numeric text-muted-foreground">
                  {clockTime(event.receivedAt)}
                </span>
                <span>{event.status}</span>
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground">
            Each line arrived as a server-sent push from the notifications
            service, not from polling.
          </p>
        </section>
      )}
    </div>
  );
}
