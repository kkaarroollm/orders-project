import { ReactNode } from 'react';
import { Link } from '@tanstack/react-router';
import { ShoppingCart } from 'lucide-react';
import { ModeToggle } from './mode-toggle';

const Layout = ({ children }: { children?: ReactNode }) => {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="p-4 border-b bg-gray-100 dark:bg-gray-800 flex justify-between items-center">
        <h1 className="text-xl font-bold">
          <Link to="/">🛒 Order what you want</Link>
        </h1>
        <div className="flex items-center gap-4">
          <ModeToggle />
          <Link to="/cart">
            <ShoppingCart className="h-6 w-6 hover:text-blue-500 transition" />
          </Link>
        </div>
      </header>
      <main className="p-4">{children}</main>
    </div>
  );
};

export default Layout;
