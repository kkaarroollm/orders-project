import { useEffect, useState } from 'react';
import { Pause, Play } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Walks one order through the system, one hop at a time. Every stream and
 * event name here is the one the services actually use.
 */

interface Step {
  id: string;
  title: string;
  caption: string;
  /** Edge ids lit for this step. */
  edges: string[];
  /** Node ids lit for this step. */
  nodes: string[];
}

const steps: Step[] = [
  {
    id: 'place',
    title: 'The order arrives',
    caption:
      'POST /orders carries an Idempotency-Key. The key is reserved inside the order transaction, so a client that times out and retries gets its original order back instead of a second one.',
    edges: ['browser-nginx', 'nginx-orders'],
    nodes: ['browser', 'nginx', 'orders'],
  },
  {
    id: 'commit',
    title: 'One transaction, two writes',
    caption:
      'The order and its outbox row commit together. After the commit the event cannot be missing — which is what makes publishing afterwards safe.',
    edges: ['orders-mongo'],
    nodes: ['orders', 'mongo'],
  },
  {
    id: 'publish',
    title: 'The relay publishes',
    caption:
      'A relay tails the outbox by change stream, with a 30-second sweep behind it for correctness, and publishes order.created.v1 to orders-stream.',
    edges: ['orders-stream'],
    nodes: ['orders', 'orders-stream'],
  },
  {
    id: 'react',
    title: 'Whoever cares, reacts',
    caption:
      'Delivery and Notifications each consume orders-stream as a group member. Delivery writes its own record and publishes delivery.created.v1 to deliveries-stream.',
    edges: ['stream-delivery', 'delivery-deliveries', 'stream-notifications'],
    nodes: ['orders-stream', 'delivery', 'deliveries-stream', 'notifications'],
  },
  {
    id: 'simulate',
    title: 'Durable timers move it along',
    caption:
      'The simulator advances the order through its lifecycle. Steps are rows in a Redis sorted set claimed atomically by Lua, so a restart resumes rather than stranding the order.',
    edges: ['simulator-redis'],
    nodes: ['simulator', 'deliveries-stream'],
  },
  {
    id: 'push',
    title: 'Every replica gets the push',
    caption:
      'A domain event reaches exactly one Notifications replica, so it republishes to ws-events, which is consumed by a group per replica. Each replica then pushes over SSE to the clients it actually holds.',
    edges: ['notif-ws', 'notif-browser'],
    nodes: ['notifications', 'ws-events', 'browser'],
  },
];

const STEP_MS = 4200;

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const SystemFlow = () => {
  const reduced = prefersReducedMotion();
  const [active, setActive] = useState(0);
  const [playing, setPlaying] = useState(!reduced);

  useEffect(() => {
    if (!playing) return;
    const timer = setInterval(
      () => setActive((i) => (i + 1) % steps.length),
      STEP_MS,
    );
    return () => clearInterval(timer);
  }, [playing]);

  const step = steps[active];
  const edgeOn = (id: string) => step.edges.includes(id);
  const nodeOn = (id: string) => step.nodes.includes(id);

  const edge = (id: string) =>
    cn(
      'flow-edge',
      edgeOn(id) && 'flow-edge-on',
      !reduced && edgeOn(id) && 'flow-edge-live',
    );
  const node = (id: string) => cn('flow-node', nodeOn(id) && 'flow-node-on');
  const nodeText = (id: string) =>
    cn('flow-node-label', nodeOn(id) && 'flow-node-label-on');

  return (
    <section className="flex flex-col gap-5">
      <div className="surface-card overflow-x-auto p-4 sm:p-6">
        <svg
          viewBox="0 0 1000 600"
          role="img"
          aria-label="An order enters through NGINX to the orders service, commits with its outbox row to MongoDB, is published to orders-stream in Redis, consumed by delivery and notifications, advanced by the simulator on durable timers, and pushed back to the browser over SSE."
          className="w-full min-w-[760px]"
        >
          <defs>
            <marker
              id="fa"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M0 0 L10 5 L0 10 z" className="flow-arrow" />
            </marker>
          </defs>

          {/* Redis enclosure */}
          <rect
            x="530"
            y="30"
            width="222"
            height="310"
            rx="8"
            className="flow-enclosure"
          />
          <text x="538" y="22" className="flow-caption">
            REDIS
          </text>

          {/* ---------- edges ---------- */}
          <path
            d="M150 248 H184"
            className={edge('browser-nginx')}
            markerEnd="url(#fa)"
          />
          <path
            d="M240 220 V78 H334"
            className={edge('nginx-orders')}
            markerEnd="url(#fa)"
          />
          <text x="250" y="150" className="flow-caption">
            POST /orders
          </text>

          <path
            d="M405 106 V350 H855 V338"
            className={edge('orders-mongo')}
            markerEnd="url(#fa)"
          />
          <text x="600" y="366" className="flow-caption">
            order + outbox, one transaction
          </text>

          <path
            d="M470 78 H539"
            className={edge('orders-stream')}
            markerEnd="url(#fa)"
          />

          <path
            d="M735 99 H794"
            className={edge('stream-delivery')}
            markerEnd="url(#fa)"
          />
          <text x="742" y="90" className="flow-caption">
            group
          </text>

          <path
            d="M830 106 V184 H739"
            className={edge('delivery-deliveries')}
            markerEnd="url(#fa)"
          />

          <path
            d="M545 99 H505 V392 H424"
            className={edge('stream-notifications')}
            markerEnd="url(#fa)"
          />
          <text x="452" y="384" className="flow-caption">
            group
          </text>

          <path
            d="M800 420 H770 V336"
            className={cn(edge('simulator-redis'), 'flow-edge-dashed')}
            markerEnd="url(#fa)"
          />
          <text x="700" y="440" className="flow-caption">
            durable timers
          </text>

          <path
            d="M490 428 H640 V292"
            className={edge('notif-ws')}
            markerEnd="url(#fa)"
            markerStart="url(#fa)"
          />
          <text x="556" y="420" className="flow-caption">
            fan-out, one group per replica
          </text>

          <path
            d="M340 428 H90 V284"
            className={cn(edge('notif-browser'), 'flow-edge-dashed')}
            markerEnd="url(#fa)"
          />
          <text x="150" y="450" className="flow-caption">
            SSE push
          </text>

          {/* ---------- nodes ---------- */}
          <g>
            <rect
              x="30"
              y="220"
              width="120"
              height="56"
              rx="6"
              className={node('browser')}
            />
            <text
              x="90"
              y="245"
              textAnchor="middle"
              className={nodeText('browser')}
            >
              Browser
            </text>
            <text x="90" y="262" textAnchor="middle" className="flow-caption">
              React
            </text>
          </g>

          <g>
            <rect
              x="190"
              y="220"
              width="100"
              height="56"
              rx="6"
              className={node('nginx')}
            />
            <text
              x="240"
              y="245"
              textAnchor="middle"
              className={nodeText('nginx')}
            >
              NGINX
            </text>
            <text x="240" y="262" textAnchor="middle" className="flow-caption">
              :80
            </text>
          </g>

          <g>
            <rect
              x="340"
              y="50"
              width="130"
              height="56"
              rx="6"
              className={node('orders')}
            />
            <text
              x="405"
              y="75"
              textAnchor="middle"
              className={nodeText('orders')}
            >
              Orders
            </text>
            <text x="405" y="92" textAnchor="middle" className="flow-caption">
              :8003
            </text>
          </g>

          <g>
            <rect
              x="800"
              y="50"
              width="130"
              height="56"
              rx="6"
              className={node('delivery')}
            />
            <text
              x="865"
              y="75"
              textAnchor="middle"
              className={nodeText('delivery')}
            >
              Delivery
            </text>
            <text x="865" y="92" textAnchor="middle" className="flow-caption">
              :8001
            </text>
          </g>

          <g>
            <rect
              x="340"
              y="400"
              width="150"
              height="56"
              rx="6"
              className={node('notifications')}
            />
            <text
              x="415"
              y="425"
              textAnchor="middle"
              className={nodeText('notifications')}
            >
              Notifications
            </text>
            <text x="415" y="442" textAnchor="middle" className="flow-caption">
              :8002
            </text>
          </g>

          <g>
            <rect
              x="800"
              y="400"
              width="130"
              height="56"
              rx="6"
              className={node('simulator')}
            />
            <text
              x="865"
              y="425"
              textAnchor="middle"
              className={nodeText('simulator')}
            >
              Simulator
            </text>
            <text x="865" y="442" textAnchor="middle" className="flow-caption">
              Lua + ZSET
            </text>
          </g>

          <g>
            <rect
              x="780"
              y="274"
              width="160"
              height="64"
              rx="6"
              className={node('mongo')}
            />
            <text
              x="860"
              y="300"
              textAnchor="middle"
              className={nodeText('mongo')}
            >
              MongoDB rs0
            </text>
            <circle cx="836" cy="318" r="4.5" className="flow-primary-dot" />
            <circle cx="854" cy="318" r="4.5" className="flow-member-dot" />
            <circle cx="872" cy="318" r="4.5" className="flow-member-dot" />
          </g>

          <g>
            <rect
              x="545"
              y="80"
              width="190"
              height="38"
              rx="19"
              className={node('orders-stream')}
            />
            <text
              x="640"
              y="104"
              textAnchor="middle"
              className={nodeText('orders-stream')}
            >
              orders-stream
            </text>
          </g>

          <g>
            <rect
              x="545"
              y="165"
              width="190"
              height="38"
              rx="19"
              className={node('deliveries-stream')}
            />
            <text
              x="640"
              y="189"
              textAnchor="middle"
              className={nodeText('deliveries-stream')}
            >
              deliveries-stream
            </text>
          </g>

          <g>
            <rect
              x="545"
              y="254"
              width="190"
              height="38"
              rx="19"
              className={node('ws-events')}
            />
            <text
              x="640"
              y="278"
              textAnchor="middle"
              className={nodeText('ws-events')}
            >
              ws-events
            </text>
          </g>

          <g>
            <rect
              x="545"
              y="302"
              width="190"
              height="30"
              rx="15"
              className="flow-node flow-node-muted"
            />
            <text x="640" y="322" textAnchor="middle" className="flow-caption">
              dead-letters
            </text>
          </g>
        </svg>
      </div>

      {/* ---------- narration ---------- */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {steps.map((s, i) => (
            <button
              key={s.id}
              type="button"
              onClick={() => {
                setActive(i);
                setPlaying(false);
              }}
              aria-current={i === active}
              className={cn(
                'rounded-full px-3 py-1.5 text-xs font-semibold transition-colors',
                i === active
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:text-foreground',
              )}
            >
              {i + 1}. {s.title}
            </button>
          ))}

          <button
            type="button"
            onClick={() => setPlaying((p) => !p)}
            aria-label={
              playing ? 'Pause the walkthrough' : 'Play the walkthrough'
            }
            className="ml-auto flex items-center gap-1.5 rounded-full border border-foreground/30 px-3 py-1.5 text-xs font-semibold transition-all active:scale-95"
          >
            {playing ? (
              <>
                <Pause className="h-3 w-3" /> Pause
              </>
            ) : (
              <>
                <Play className="h-3 w-3" /> Play
              </>
            )}
          </button>
        </div>

        <p className="max-w-prose text-sm leading-relaxed text-muted-foreground">
          <span className="font-semibold text-foreground">{step.title}.</span>{' '}
          {step.caption}
        </p>
      </div>
    </section>
  );
};

export default SystemFlow;
