import { useParams } from '@tanstack/react-router';
import OrderTracker from '@/components/OrderTracker';

export default function OrderTrackingPage() {
  const { order_id } = useParams({ from: '/tracking/$order_id' });

  return (
    <div className="flex justify-center items-center min-h-screen">
      <OrderTracker orderId={order_id} />
    </div>
  );
}
