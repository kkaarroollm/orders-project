import { ReactNode } from 'react';
import { Link, useRouterState } from '@tanstack/react-router';
import { ShoppingBag, Wrench } from 'lucide-react';
import { ModeToggle } from './mode-toggle';
import { useCart } from '@/hooks/useCart';
import { cn } from '@/lib/utils';

const BrandMark = () => (
  <svg
    width="26"
    height="26"
    viewBox="0 0 26 26"
    role="img"
    aria-label="Orders"
    className="shrink-0"
  >
    <circle cx="13" cy="13" r="12" fill="var(--primary)" />
    <path
      d="M7 16.5 L7 11 L13 7.5 L19 11 L19 16.5"
      fill="none"
      stroke="var(--primary-foreground)"
      strokeWidth="1.6"
      strokeLinejoin="round"
      strokeLinecap="round"
    />
    <circle cx="13" cy="14" r="2.2" fill="var(--primary-foreground)" />
  </svg>
);

const NavLink = ({
  to,
  active,
  children,
}: {
  to: string;
  active: boolean;
  children: ReactNode;
}) => (
  <Link
    to={to}
    className={cn(
      'rounded-full px-3 py-1.5 text-sm transition-colors',
      active
        ? 'font-semibold text-brand'
        : 'text-foreground/80 hover:text-brand',
    )}
  >
    {children}
  </Link>
);

/**
 * The floating circular order button. DESIGN.md treats this as the product's
 * signature elevation element: it persists over every shopping surface and
 * loses its ambient shadow on press.
 */
const FloatingCartButton = ({ count }: { count: number }) => (
  <Link
    to="/cart"
    aria-label={`Review cart, ${count} item${count === 1 ? '' : 's'}`}
    className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-float transition-all duration-200 active:scale-95 active:shadow-[var(--shadow-float-active)]"
  >
    <ShoppingBag className="h-5 w-5" />
    <span className="numeric absolute -right-0.5 -top-0.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-foreground px-1 text-[0.7rem] font-semibold text-background">
      {count}
    </span>
  </Link>
);

const Layout = ({ children }: { children?: ReactNode }) => {
  const { itemCount } = useCart();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const onShoppingSurface = pathname !== '/cart' && pathname !== '/order';

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="sticky top-0 z-40 bg-card shadow-nav">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-4 px-4 sm:h-[72px] sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <BrandMark />
            <span className="text-base font-semibold text-brand">Orders</span>
          </Link>

          <nav className="ml-3 hidden items-center gap-1 sm:flex">
            <NavLink to="/" active={pathname === '/'}>
              Menu
            </NavLink>
            <NavLink to="/cart" active={pathname === '/cart'}>
              Cart
            </NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <ModeToggle />

            <Link
              to="/dev"
              aria-label="Dev tools"
              className={cn(
                'rounded-full p-2 transition-colors',
                pathname === '/dev'
                  ? 'text-brand'
                  : 'text-muted-foreground hover:text-brand',
              )}
            >
              <Wrench className="h-4 w-4" />
            </Link>

            <Link
              to="/cart"
              aria-label={`Cart, ${itemCount} item${itemCount === 1 ? '' : 's'}`}
              className="relative rounded-full border border-foreground/80 px-4 py-[7px] text-sm font-semibold transition-all duration-200 active:scale-95"
            >
              Cart
              {itemCount > 0 && (
                <span className="numeric ml-1.5">({itemCount})</span>
              )}
            </Link>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
        {children}
      </main>

      {itemCount > 0 && onShoppingSurface && (
        <FloatingCartButton count={itemCount} />
      )}

      {/* Deep-tier bookend, the way the system closes every page */}
      <footer className="bg-deep text-white">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-end gap-3 px-4 py-8 sm:px-6">
          <a
            href="https://github.com/kkaarroollm/orders-project"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-semibold text-white underline-offset-4 hover:underline"
          >
            Source
          </a>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
