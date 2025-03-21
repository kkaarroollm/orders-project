import { createRoute, createRootRoute, Outlet } from '@tanstack/react-router';
import Layout from '@/components/Layout';
import MenuPage from '@/pages/Menu';
import OrderPage from '@/pages/Order';
import CartPage from '@/pages/Cart.tsx';
import OrderTracking from '@/pages/OrderTracking.tsx';

const rootRoute = createRootRoute({
  component: () => (
    <Layout>
      <Outlet />
    </Layout>
  ),
});

const menuRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: MenuPage,
});

const cartRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/cart',
  component: CartPage,
});

const orderRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/order',
  component: OrderPage,
});

const trackerRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/tracking/$order_id',
  component: OrderTracking,
});

rootRoute.addChildren([menuRoute, cartRoute, orderRoute, trackerRoute]);

export const routeTree = rootRoute;
