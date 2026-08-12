import { createContext } from 'react';

export interface CartLine {
  quantity: number;
  price: number;
  name: string;
  stock: number;
}

export type Cart = Record<string, CartLine>;

export interface CartContextValue {
  cart: Cart;
  lines: Array<CartLine & { itemId: string }>;
  itemCount: number;
  totalPrice: number;
  setQuantity: (
    itemId: string,
    quantity: number,
    line: Omit<CartLine, 'quantity'>,
  ) => void;
  clearCart: () => void;
}

export const CART_STORAGE_KEY = 'cart';

export const CartContext = createContext<CartContextValue | null>(null);
