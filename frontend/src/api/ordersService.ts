import axios from 'axios';
import { MenuItem, Order, OrderResponse } from '../types';
import { API_ORDERS_URL } from '@/config/env';

const ORDERS_API_BASE = (API_ORDERS_URL ?? '').replace(/\/$/, '');

export const fetchMenu = async (): Promise<MenuItem[]> => {
  const response = await axios.get<unknown>(`${ORDERS_API_BASE}/menu/items`);

  if (!Array.isArray(response.data)) {
    throw new Error('Invalid menu response format');
  }

  return response.data as MenuItem[];
};

export const createOrder = async (order: Order): Promise<OrderResponse> => {
  const response = await axios.post<OrderResponse>(`${ORDERS_API_BASE}/orders`, order);
  return response.data;
};
