import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  CartContext,
  CART_STORAGE_KEY,
  type Cart,
  type CartContextValue,
  type CartLine,
} from '@/store/cart-context';

const readStoredCart = (): Cart => {
  try {
    const saved = localStorage.getItem(CART_STORAGE_KEY);
    if (!saved) return {};
    const parsed: unknown = JSON.parse(saved);
    if (!parsed || typeof parsed !== 'object') return {};
    return parsed as Cart;
  } catch {
    // A corrupt entry should not take the whole app down with it.
    return {};
  }
};

export const CartProvider = ({ children }: { children: ReactNode }) => {
  // One instance for the whole tree, so the header badge and the menu page
  // are looking at the same cart.
  const [cart, setCart] = useState<Cart>(readStoredCart);

  useEffect(() => {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
  }, [cart]);

  const setQuantity = useCallback(
    (itemId: string, quantity: number, line: Omit<CartLine, 'quantity'>) => {
      if (!itemId) return;

      const safeQuantity = Math.max(0, Math.min(quantity, line.stock));

      setCart((prev) => {
        const next = { ...prev };
        if (safeQuantity > 0) {
          next[itemId] = { ...line, quantity: safeQuantity };
        } else {
          delete next[itemId];
        }
        return next;
      });
    },
    [],
  );

  const clearCart = useCallback(() => {
    setCart({});
    localStorage.removeItem(CART_STORAGE_KEY);
  }, []);

  const value = useMemo<CartContextValue>(() => {
    const lines = Object.entries(cart)
      .filter(([, line]) => line.quantity > 0)
      .map(([itemId, line]) => ({ itemId, ...line }));

    return {
      cart,
      lines,
      itemCount: lines.reduce((sum, line) => sum + line.quantity, 0),
      totalPrice: lines.reduce(
        (sum, line) => sum + line.quantity * line.price,
        0,
      ),
      setQuantity,
      clearCart,
    };
  }, [cart, setQuantity, clearCart]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
};
