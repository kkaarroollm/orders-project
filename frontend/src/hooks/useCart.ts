import { useContext } from 'react';
import { CartContext, type CartContextValue } from '@/store/cart-context';

export const useCart = (): CartContextValue => {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error('useCart must be used inside a CartProvider');
  }
  return ctx;
};

export type { Cart, CartLine } from '@/store/cart-context';
