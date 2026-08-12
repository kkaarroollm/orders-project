import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Minus, Plus, AlertCircle } from 'lucide-react';
import { fetchMenu } from '@/api/ordersService';
import { MenuItem } from '@/types';
import { Button } from '@/components/ui/button';
import { useCart } from '@/hooks/useCart';
import { cn } from '@/lib/utils';

const currency = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

const StockState = ({ stock }: { stock: number }) => {
  if (stock === 0) {
    return <span className="text-sm text-destructive">Out of stock</span>;
  }
  if (stock <= 3) {
    return (
      <span className="numeric text-sm text-muted-foreground">
        Only {stock} left
      </span>
    );
  }
  return null;
};

const QuantityStepper = ({ item }: { item: MenuItem }) => {
  const { cart, setQuantity } = useCart();
  const itemId = item._id ?? '';
  const quantity = cart[itemId]?.quantity ?? 0;
  const soldOut = item.stock === 0;

  const apply = (next: number) =>
    setQuantity(itemId, next, {
      price: item.price,
      name: item.name,
      stock: item.stock,
    });

  if (quantity === 0) {
    return (
      <Button
        variant="outline"
        disabled={soldOut}
        onClick={() => apply(1)}
        className="min-w-24"
      >
        {soldOut ? 'Unavailable' : 'Add'}
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-1 rounded-full border border-primary p-1">
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-primary"
        aria-label={`Remove one ${item.name}`}
        onClick={() => apply(quantity - 1)}
      >
        <Minus className="h-3.5 w-3.5" />
      </Button>
      <span className="numeric w-7 text-center text-sm font-semibold">
        {quantity}
      </span>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-primary"
        aria-label={`Add one ${item.name}`}
        disabled={quantity >= item.stock}
        onClick={() => apply(quantity + 1)}
      >
        <Plus className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
};

const ItemCard = ({ item }: { item: MenuItem }) => {
  const { cart } = useCart();
  const inCart = (cart[item._id ?? '']?.quantity ?? 0) > 0;

  return (
    <li
      className={cn(
        'surface-card flex flex-col gap-4 p-5 transition-shadow',
        item.stock === 0 && 'opacity-60',
      )}
    >
      <div className="flex flex-col gap-1.5">
        <h3 className="text-lg font-semibold leading-snug">{item.name}</h3>
        {item.description && (
          <p className="text-sm text-muted-foreground">{item.description}</p>
        )}
        <StockState stock={item.stock} />
      </div>

      <div className="mt-auto flex items-center justify-between gap-3 pt-1">
        <span className="numeric text-base font-semibold">
          {currency(item.price)}
        </span>
        <QuantityStepper item={item} />
      </div>

      {inCart && (
        <span className="text-sm font-semibold text-primary">In your cart</span>
      )}
    </li>
  );
};

const MenuSkeleton = () => (
  <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-hidden="true">
    {Array.from({ length: 6 }).map((_, i) => (
      <div key={i} className="surface-card h-44 animate-pulse" />
    ))}
  </div>
);

const MenuPage = () => {
  const {
    data: menu,
    isLoading,
    error,
    refetch,
  } = useQuery<MenuItem[]>({
    queryKey: ['menu'],
    queryFn: fetchMenu,
  });

  const grouped = useMemo(() => {
    const items = Array.isArray(menu) ? menu : [];
    const byCategory = new Map<string, MenuItem[]>();
    for (const item of items) {
      const key = item.category || 'Other';
      byCategory.set(key, [...(byCategory.get(key) ?? []), item]);
    }
    return [...byCategory.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [menu]);

  return (
    <div className="flex flex-col gap-12">
      <header className="flex max-w-2xl flex-col gap-3">
        <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
          What are you having?
        </h1>
        <p className="text-lg leading-relaxed text-muted-foreground">
          Stock is read from a MongoDB secondary and cached in Redis, so it
          settles within thirty seconds of a refill.
        </p>
      </header>

      {isLoading && <MenuSkeleton />}

      {error && (
        <div className="surface-card flex flex-col items-start gap-3 p-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-4 w-4" />
            <p className="font-semibold">The menu could not be loaded</p>
          </div>
          <p className="text-sm text-muted-foreground">
            The orders service did not answer. It may still be starting up.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            Try again
          </Button>
        </div>
      )}

      {!isLoading && !error && grouped.length === 0 && (
        <div className="surface-card p-10 text-center">
          <p className="font-semibold">The menu is empty</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Nothing has been seeded into the database yet.
          </p>
        </div>
      )}

      {grouped.map(([category, items]) => (
        <section key={category} className="flex flex-col gap-5">
          <h2 className="label">{category}</h2>
          <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <ItemCard key={item._id ?? item.name} item={item} />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
};

export default MenuPage;
