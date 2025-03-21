export interface MenuItem {
  _id?: string;
  name: string;
  description?: string;
  price: number;
  category: string;
  stock: number;
}

export enum OrderStatus {
  CONFIRMED = 'confirmed',
  PREPARING = 'preparing',
  OUT_FOR_DELIVERY = 'out_for_delivery',
  WAITING_FOR_PICKUP = 'waiting_for_pickup',
  ON_THE_WAY = 'on_the_way',
  DELIVERED = 'delivered',
}

export interface OrderedItem {
  item_id: string;
  quantity: number;
}

export interface OrderingPerson {
  first_name: string;
  last_name: string;
  address: string;
  phone_number: string;
}

export interface Order {
  _id?: string;
  person: OrderingPerson;
  items: OrderedItem[];
  simulation: number;
  total_price?: number;
  status?: OrderStatus;
  created_at?: string;
}

export interface OrderResponse {
  order: Order;
  success: boolean;
}
