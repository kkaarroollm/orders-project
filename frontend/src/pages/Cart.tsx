import { useCart } from '../hooks/useCart.ts';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Link } from '@tanstack/react-router';

const CartPage = () => {
  const { cart } = useCart();

  const validCart = Object.entries(cart).filter(
    ([, item]) => item.quantity > 0,
  );

  const totalPrice = validCart.reduce(
    (acc, [, item]) => acc + item.quantity * item.price,
    0,
  );

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">🛍 Your Cart</h1>

      {validCart.length > 0 ? (
        <Card className="p-4 mt-4">
          {validCart.map(([itemId, item]) => (
            <p key={itemId}>
              Item {itemId}: {item.quantity} pcs - ${item.price.toFixed(2)} each
            </p>
          ))}
          <Separator className="my-2" />
          <h3 className="text-lg font-bold">Total: ${totalPrice.toFixed(2)}</h3>
        </Card>
      ) : (
        <p className="text-gray-500 mt-4">No items in cart.</p>
      )}

      <div className="mt-4">
        {validCart.length > 0 ? (
          <Link to="/order">
            <Button variant="default" size="lg" className="w-full">
              Proceed to Checkout
            </Button>
          </Link>
        ) : (
          <Button variant="default" size="lg" className="w-full" disabled>
            ❌ Cart is Empty
          </Button>
        )}
      </div>
    </div>
  );
};

export default CartPage;
