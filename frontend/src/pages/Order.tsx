import { useNavigate } from '@tanstack/react-router';
import { useMutation } from '@tanstack/react-query';
import { createOrder } from '@/api/ordersService';
import { Order, OrderingPerson, OrderResponse } from '@/types';
import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useCart } from '@/hooks/useCart';
import { orderSchema } from '@/validation/orderSchema';
import { Info } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';

const OrderPage = () => {
  const navigate = useNavigate();
  const { cart, clearCart } = useCart();
  const [errors, setErrors] = useState<Record<string, string>>({});

  const [person, setPerson] = useState<OrderingPerson>({
    first_name: '',
    last_name: '',
    address: '',
    phone_number: '',
  });

  const [simulationChecked, setSimulationChecked] = useState(false);

  const mutation = useMutation<OrderResponse, Error, Order>({
    mutationFn: createOrder,
    onSuccess: async (data) => {
      const orderId = data.order._id;
      if (!orderId) {
        alert('Order placed, but order ID is missing in the response.');
        return;
      }
      alert(`✅ Order placed successfully! Order ID: ${orderId}`);
      clearCart();
      await navigate({ to: '/tracking/' + orderId });
    },
    onError: (error: unknown) => {
      if (error instanceof Error) {
        alert(`Failed to place order: ${error.message}`);
      } else {
        alert('An unknown error occurred.');
      }
    },
  });

  const validCart = Object.entries(cart).filter(
    ([, item]) => item.quantity > 0,
  );
  const totalPrice = validCart.reduce(
    (acc, [, item]) => acc + item.quantity * item.price,
    0,
  );

  const handleOrder = () => {
    const validationResult = orderSchema.safeParse({
      person,
      items: validCart.map(([itemId, item]) => ({
        item_id: itemId,
        quantity: item.quantity,
      })),
    });

    if (!validationResult.success) {
      const errorMessages: Record<string, string> = {};
      validationResult.error.issues.forEach((issue) => {
        errorMessages[issue.path.join('.')] = issue.message;
      });
      setErrors(errorMessages);
      return;
    }

    if (validCart.length === 0) {
      alert('Cannot place an order with an empty cart!');
      return;
    }

    const newOrder: Order = {
      person,
      items: validCart.map(([itemId, item]) => ({
        item_id: itemId,
        quantity: item.quantity,
      })),
      simulation: simulationChecked ? 1 : -1,
    };

    mutation.mutate(newOrder);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">🛒 Confirm Order</h1>

      {validCart.length === 0 ? (
        <p className="text-red-500 mt-4">
          ❌ Your cart is empty. Add items before placing an order.
        </p>
      ) : (
        <Card className="p-4 mt-4">
          <h2 className="text-lg font-semibold">Order Summary</h2>
          {validCart.map(([itemId, item]) => (
            <p key={itemId}>
              Item {itemId}: {item.quantity} pcs - ${item.price.toFixed(2)} each
            </p>
          ))}
          <Separator className="my-2" />
          <h3 className="text-lg font-bold">Total: ${totalPrice.toFixed(2)}</h3>
        </Card>
      )}

      <div className="mt-4 space-y-2">
        <Input
          placeholder="First Name"
          value={person.first_name}
          onChange={(e) => setPerson({ ...person, first_name: e.target.value })}
        />
        {errors['person.first_name'] && (
          <p className="text-red-500">{errors['person.first_name']}</p>
        )}

        <Input
          placeholder="Last Name"
          value={person.last_name}
          onChange={(e) => setPerson({ ...person, last_name: e.target.value })}
        />
        {errors['person.last_name'] && (
          <p className="text-red-500">{errors['person.last_name']}</p>
        )}

        <Input
          placeholder="Address"
          value={person.address}
          onChange={(e) => setPerson({ ...person, address: e.target.value })}
        />
        {errors['person.address'] && (
          <p className="text-red-500">{errors['person.address']}</p>
        )}

        <Input
          placeholder="Phone Number"
          value={person.phone_number}
          onChange={(e) =>
            setPerson({ ...person, phone_number: e.target.value })
          }
        />
        {errors['person.phone_number'] && (
          <p className="text-red-500">{errors['person.phone_number']}</p>
        )}

        <div className="flex items-center space-x-2 mt-2">
          <input
            type="checkbox"
            id="simulation-checkbox"
            checked={simulationChecked}
            onChange={(e) => setSimulationChecked(e.target.checked)}
          />
          <label htmlFor="simulation-checkbox" className="text-sm">
            Enable Simulation
          </label>
          <Popover>
            <PopoverTrigger asChild>
              <Info className="h-4 w-4 text-gray-500 cursor-pointer" />
            </PopoverTrigger>
            <PopoverContent className="p-2">
              <p className="text-sm">
                During the simulation you'll see real-time updates of your
                order's journey.
              </p>
            </PopoverContent>
          </Popover>
        </div>
      </div>

      <Button
        className="w-full mt-4 bg-green-600 hover:bg-green-700 text-white"
        onClick={handleOrder}
        disabled={mutation.isPending || validCart.length === 0}
      >
        {mutation.isPending ? 'Placing Order...' : '✅ Confirm Order'}
      </Button>
    </div>
  );
};

export default OrderPage;
