import axios from 'axios';
import { MenuItem, Order, OrderResponse } from '../types';
import { API_ORDERS_URL } from '@/config/env';

export const fetchMenu = async (): Promise<MenuItem[]> => {
  const response = await axios.get<MenuItem[]>(
    `${API_ORDERS_URL}/api/v1/menu/items`,
  );
  return response.data;
};

export const createOrder = async (order: Order): Promise<OrderResponse> => {
  const response = await axios.post<OrderResponse>(
    `${API_ORDERS_URL}/api/v1/orders/`,
    order,
  );
  return response.data;
};
