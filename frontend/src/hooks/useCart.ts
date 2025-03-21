import { useState, useEffect } from 'react';

type Cart = { [itemId: string]: { quantity: number; price: number } };

export const useCart = () => {
  const [cart, setCart] = useState<Cart>(() => {
    const savedCart = localStorage.getItem('cart');
    return savedCart ? JSON.parse(savedCart) : {};
  });

  useEffect(() => {
    localStorage.setItem('cart', JSON.stringify(cart));
  }, [cart]);

  const updateCart = (
    itemId: string,
    quantity: number,
    stock: number,
    price: number,
  ) => {
    if (!itemId) return;

    const safeQuantity = Math.min(quantity, stock);

    setCart((prevCart) => {
      const newCart = { ...prevCart };

      if (safeQuantity > 0) {
        newCart[itemId] = { quantity: safeQuantity, price };
      } else {
        delete newCart[itemId];
      }

      return newCart;
    });
  };

  const clearCart = () => {
    setCart({});
    localStorage.removeItem('cart');
  };

  return { cart, updateCart, clearCart };
};
