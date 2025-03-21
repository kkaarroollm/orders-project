import { useQuery } from '@tanstack/react-query';
import { fetchMenu } from '@/api/ordersService';
import { MenuItem } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Link } from '@tanstack/react-router';
import { useCart } from '@/hooks/useCart.ts';

const MenuPage = () => {
  const {
    data: menu,
    isLoading,
    error,
  } = useQuery<MenuItem[]>({
    queryKey: ['menu'],
    queryFn: fetchMenu,
  });

  const { cart, updateCart } = useCart();

  if (isLoading) return <p>Loading menu...</p>;
  if (error) return <p className="text-red-500">Failed to load menu.</p>;

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">🍔 Menu</h1>
      <div className="grid gap-4">
        {menu?.map((item) => (
          <div
            key={item._id ?? ''}
            className="p-4 border rounded-lg shadow flex justify-between items-center"
          >
            <div>
              <h2 className="text-lg font-semibold">
                {item.name} - ${item.price.toFixed(2)}
              </h2>
              <p>Stock: {item.stock}</p>
            </div>
            <div className="flex items-center">
              <Input
                type="number"
                min="0"
                max={item.stock}
                value={cart[item._id ?? '']?.quantity || 0}
                onChange={(e) =>
                  updateCart(
                    item._id ?? '',
                    parseInt(e.target.value) || 0,
                    item.stock,
                    item.price,
                  )
                }
                className="w-20 text-center"
              />
              <Button
                variant="outline"
                className="ml-2"
                disabled={cart[item._id ?? '']?.quantity === 0}
              >
                Add to Cart
              </Button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 text-center">
        <Link to="/cart">
          <Button variant="default" size="lg" className="w-full">
            🛒 View Cart
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default MenuPage;
