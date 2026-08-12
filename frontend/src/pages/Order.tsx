import { useRef, useState } from 'react';
import { useNavigate, Link } from '@tanstack/react-router';
import { useMutation } from '@tanstack/react-query';
import { isAxiosError } from 'axios';
import { AlertCircle, Info, Loader2 } from 'lucide-react';
import { createOrder } from '@/api/ordersService';
import { Order, OrderingPerson, OrderResponse } from '@/types';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { useCart } from '@/hooks/useCart';
import { orderSchema } from '@/validation/orderSchema';
import { cn } from '@/lib/utils';

const currency = (value: number) =>
  value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });

const fields = [
  { key: 'first_name', label: 'First name', autoComplete: 'given-name' },
  { key: 'last_name', label: 'Last name', autoComplete: 'family-name' },
  { key: 'address', label: 'Delivery address', autoComplete: 'street-address' },
  { key: 'phone_number', label: 'Phone number', autoComplete: 'tel' },
] as const;

const OrderPage = () => {
  const navigate = useNavigate();
  const { lines, totalPrice, clearCart } = useCart();
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [person, setPerson] = useState<OrderingPerson>({
    first_name: '',
    last_name: '',
    address: '',
    phone_number: '',
  });

  const [simulationChecked, setSimulationChecked] = useState(true);

  // Held across retries of one checkout attempt, so a lost response or a
  // dropped connection cannot turn into a second order. Cleared once an order
  // is actually placed, so the next checkout gets a fresh key.
  const idempotencyKey = useRef<string | null>(null);

  const mutation = useMutation<OrderResponse, Error, Order>({
    mutationFn: (order) => {
      idempotencyKey.current ??= crypto.randomUUID();
      return createOrder(order, idempotencyKey.current);
    },
    onSuccess: async (data) => {
      idempotencyKey.current = null;
      const orderId = data.order._id;
      if (!orderId) {
        setSubmitError(
          'The order was placed, but the response carried no order id, so it cannot be tracked.',
        );
        return;
      }
      clearCart();
      await navigate({ to: '/tracking/' + orderId });
    },
    onError: (error: unknown) => {
      // 409 means the previous attempt with this key is still in flight, so
      // the key is kept and retrying resolves to that attempt's result.
      if (isAxiosError(error) && error.response?.status === 409) {
        setSubmitError(
          'That order is still being placed. Retry in a moment to pick up the original result.',
        );
        return;
      }
      setSubmitError(
        error instanceof Error
          ? error.message
          : 'The order could not be placed.',
      );
    },
  });

  const handleOrder = () => {
    setSubmitError(null);

    const validationResult = orderSchema.safeParse({
      person,
      items: lines.map((line) => ({
        item_id: line.itemId,
        quantity: line.quantity,
      })),
    });

    if (!validationResult.success) {
      const errorMessages: Record<string, string> = {};
      validationResult.error.issues.forEach((issue) => {
        errorMessages[issue.path.join('.')] = issue.message;
      });
      setErrors(errorMessages);
      return;
    }

    setErrors({});

    mutation.mutate({
      person,
      items: lines.map((line) => ({
        item_id: line.itemId,
        quantity: line.quantity,
      })),
      simulation: simulationChecked ? 1 : -1,
    });
  };

  if (lines.length === 0) {
    return (
      <div className="flex flex-col gap-8">
        <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
          There is nothing to order
        </h1>
        <div className="surface-card flex flex-col items-start gap-5 p-8">
          <p className="text-muted-foreground">
            Add something from the menu first.
          </p>
          <Link to="/">
            <Button variant="outline">Back to the menu</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
        Where is this going?
      </h1>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px] lg:items-start">
        <form
          className="surface-card flex flex-col gap-6 p-6 sm:p-7"
          onSubmit={(e) => {
            e.preventDefault();
            handleOrder();
          }}
          noValidate
        >
          <div className="grid gap-5 sm:grid-cols-2">
            {fields.map((field) => {
              const errorKey = `person.${field.key}`;
              const invalid = Boolean(errors[errorKey]);
              return (
                <div
                  key={field.key}
                  className={cn(
                    'flex flex-col gap-1.5',
                    field.key === 'address' && 'sm:col-span-2',
                  )}
                >
                  <Label htmlFor={field.key}>{field.label}</Label>
                  <Input
                    id={field.key}
                    autoComplete={field.autoComplete}
                    aria-invalid={invalid}
                    aria-describedby={
                      invalid ? `${field.key}-error` : undefined
                    }
                    value={person[field.key]}
                    onChange={(e) =>
                      setPerson({ ...person, [field.key]: e.target.value })
                    }
                    className={cn(invalid && 'border-destructive')}
                  />
                  {invalid && (
                    <p
                      id={`${field.key}-error`}
                      className="text-xs text-destructive"
                    >
                      {errors[errorKey]}
                    </p>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex items-start gap-3 rounded-lg bg-accent/50 p-4">
            <input
              type="checkbox"
              id="simulation-checkbox"
              checked={simulationChecked}
              onChange={(e) => setSimulationChecked(e.target.checked)}
              className="mt-0.5 h-4 w-4 accent-[var(--primary)]"
            />
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-1.5">
                <Label htmlFor="simulation-checkbox" className="cursor-pointer">
                  Simulate the delivery
                </Label>
                <Popover>
                  <PopoverTrigger
                    aria-label="What the simulation does"
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <Info className="h-3.5 w-3.5" />
                  </PopoverTrigger>
                  <PopoverContent className="text-sm">
                    The simulator advances the order through its lifecycle on
                    durable timers, so you can watch the status arrive over SSE
                    in real time.
                  </PopoverContent>
                </Popover>
              </div>
              <p className="text-xs text-muted-foreground">
                Drives the order through every status so you can watch tracking
                update live.
              </p>
            </div>
          </div>

          {submitError && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-lg bg-destructive/5 p-4 text-sm text-destructive"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <p>{submitError}</p>
            </div>
          )}

          <Button
            type="submit"
            size="lg"
            disabled={mutation.isPending}
            className="w-full"
          >
            {mutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            {mutation.isPending ? 'Placing order' : 'Place order'}
          </Button>

          <p className="label">
            Sent with an Idempotency-Key — retrying returns the original order
            rather than placing a second one.
          </p>
        </form>

        <aside className="surface-card flex flex-col gap-5 p-6 lg:sticky lg:top-24">
          <h2 className="label">Order summary</h2>

          <ul className="flex flex-col gap-2.5 text-sm">
            {lines.map((line) => (
              <li key={line.itemId} className="flex justify-between gap-3">
                <span className="min-w-0">
                  <span className="numeric text-muted-foreground">
                    {line.quantity}×
                  </span>{' '}
                  {line.name || 'Unnamed item'}
                </span>
                <span className="numeric shrink-0">
                  {currency(line.price * line.quantity)}
                </span>
              </li>
            ))}
          </ul>

          <div className="flex items-baseline justify-between border-t border-border pt-5">
            <span className="font-semibold">Total</span>
            <span className="numeric text-xl font-semibold">
              {currency(totalPrice)}
            </span>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default OrderPage;
