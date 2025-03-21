import { z } from 'zod';

export const personSchema = z.object({
  first_name: z.string().min(2, 'First name is required'),
  last_name: z.string().min(2, 'Last name is required'),
  address: z.string().min(5, 'Address must be at least 5 characters'),
  phone_number: z.string().regex(/^\d{9}$/, 'Phone number must be 9 digits'),
});

export const cartItemSchema = z.object({
  item_id: z.string().nonempty('Item ID is required'),
  quantity: z.number().min(1, 'At least 1 quantity is required'),
});

export const orderSchema = z.object({
  person: personSchema,
  items: z.array(cartItemSchema).min(1, 'Cart must have at least one item'),
});
