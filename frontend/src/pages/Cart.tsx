import { Link } from '@tanstack/react-router';
import { Minus, Plus, Trash2, ShoppingBag } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useCart } from '@/hooks/useCart';

const currency = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

const CartPage = () => {
  const { lines, totalPrice, itemCount, setQuantity, clearCart } = useCart();

  if (lines.length === 0) {
    return (
      <div className="flex flex-col gap-8">
        <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
          Nothing here yet
        </h1>

        <div className="surface-card flex flex-col items-center gap-5 px-6 py-16">
          <ShoppingBag className="h-7 w-7 text-primary" />
          <p className="text-muted-foreground">Your cart is empty.</p>
          <Link to="/">
            <Button variant="outline">Browse the menu</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
        {itemCount} item{itemCount === 1 ? '' : 's'} ready to order
      </h1>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px] lg:items-start">
        <ul className="flex flex-col gap-4">
          {lines.map((line) => (
            <li
              key={line.itemId}
              className="surface-card flex items-center gap-4 p-5"
            >
              <div className="min-w-0 flex-1">
                <h2 className="font-semibold">{line.name || 'Unnamed item'}</h2>
                <p className="numeric mt-0.5 text-sm text-muted-foreground">
                  {currency(line.price)} each
                </p>
              </div>

              <div className="flex items-center gap-1 rounded-full border border-primary p-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-primary"
                  aria-label={`Remove one ${line.name}`}
                  onClick={() =>
                    setQuantity(line.itemId, line.quantity - 1, line)
                  }
                >
                  <Minus className="h-3.5 w-3.5" />
                </Button>
                <span className="numeric w-7 text-center text-sm font-semibold">
                  {line.quantity}
                </span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-primary"
                  aria-label={`Add one ${line.name}`}
                  disabled={line.quantity >= line.stock}
                  onClick={() =>
                    setQuantity(line.itemId, line.quantity + 1, line)
                  }
                >
                  <Plus className="h-3.5 w-3.5" />
                </Button>
              </div>

              <span className="numeric w-20 shrink-0 text-right font-semibold">
                {currency(line.price * line.quantity)}
              </span>

              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive"
                aria-label={`Remove ${line.name} from cart`}
                onClick={() => setQuantity(line.itemId, 0, line)}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </li>
          ))}
        </ul>

        <aside className="surface-card flex flex-col gap-5 p-6 lg:sticky lg:top-24">
          <h2 className="label">Summary</h2>

          <dl className="flex flex-col gap-2.5 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Items</dt>
              <dd className="numeric">{itemCount}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Delivery</dt>
              <dd>Free</dd>
            </div>
          </dl>

          <div className="flex items-baseline justify-between border-t border-border pt-5">
            <span className="font-semibold">Total</span>
            <span className="numeric text-xl font-semibold">
              {currency(totalPrice)}
            </span>
          </div>

          <Link to="/order" className="w-full">
            <Button size="lg" className="w-full">
              Checkout
            </Button>
          </Link>

          <Button
            variant="ghost"
            size="sm"
            onClick={clearCart}
            className="text-muted-foreground"
          >
            Clear cart
          </Button>
        </aside>
      </div>
    </div>
  );
};

export default CartPage;
