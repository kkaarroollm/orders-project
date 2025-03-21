import axios from 'axios';
import { MenuItem, Order, OrderResponse } from '../types';

// const API_BASE_URL = import.meta.env.VITE_API_ORDERS;
const API_BASE_URL = 'http://localhost:8003';

export const fetchMenu = async (): Promise<MenuItem[]> => {
  const response = await axios.get<MenuItem[]>(
    `${API_BASE_URL}/api/v1/menu/items`,
  );
  console.log(response.data);
  return response.data;
};

export const createOrder = async (order: Order): Promise<OrderResponse> => {
  const response = await axios.post<OrderResponse>(
    `${API_BASE_URL}/api/v1/orders/`,
    order,
  );
  return response.data;
};
