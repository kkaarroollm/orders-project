import { ExternalLink } from 'lucide-react';
import SystemFlow from '@/components/SystemFlow';

interface Tool {
  title: string;
  description: string;
  url: string;
  note?: string;
}

const dashboards: Tool[] = [
  {
    title: 'HTTP metrics',
    description:
      'Request rate, latency percentiles and error rates per service',
    url: '/grafana/d/http-metrics/http-metrics',
  },
  {
    title: 'Application logs',
    description: 'Live log stream from Loki, keyed by correlation id',
    url: '/grafana/d/application-logs/application-logs',
  },
  {
    title: 'Event pipeline',
    description: 'Stream throughput, consumer lag and the dead-letter stream',
    url: '/grafana/d/event-pipeline/event-pipeline',
  },
  {
    title: 'Prometheus',
    description: 'Raw metrics, PromQL and scrape targets',
    url: '/prometheus/',
    note: 'GET only',
  },
];

/** Every stream the services bind to, with the event types each one carries. */
const streams: Array<{
  stream: string;
  producer: string;
  consumer: string;
  events: string[];
  note?: string;
}> = [
  {
    stream: 'orders-stream',
    producer: 'Orders',
    consumer: 'Delivery, Notifications',
    events: ['order.created.v1', 'order.status_updated.v1'],
  },
  {
    stream: 'deliveries-stream',
    producer: 'Delivery',
    consumer: 'Notifications',
    events: ['delivery.created.v1', 'delivery.status_updated.v1'],
  },
  {
    stream: 'simulate-order-stream',
    producer: 'Orders',
    consumer: 'Simulator',
    events: ['order.simulate.v1'],
  },
  {
    stream: 'simulate-delivery-stream',
    producer: 'Delivery',
    consumer: 'Simulator',
    events: ['delivery.simulate.v1'],
  },
  {
    stream: 'order-status-stream',
    producer: 'Simulator',
    consumer: 'Orders',
    events: ['order.status_simulated.v1'],
  },
  {
    stream: 'delivery-status-stream',
    producer: 'Simulator',
    consumer: 'Delivery',
    events: ['delivery.status_simulated.v1'],
  },
  {
    stream: 'ws-events',
    producer: 'Notifications',
    consumer: 'Notifications',
    events: ['order.status_push.v1'],
    note: 'one group per replica, NOACK',
  },
  {
    stream: 'dead-letters',
    producer: 'any consumer',
    consumer: '—',
    events: ['original payload + error'],
    note: 'after three failures',
  },
];

const ToolCard = ({ tool }: { tool: Tool }) => (
  <a
    href={tool.url}
    target="_blank"
    rel="noopener noreferrer"
    className="surface-card group flex flex-col gap-2 p-5 transition-transform duration-200 hover:-translate-y-0.5 active:scale-[0.99]"
  >
    <div className="flex items-start justify-between gap-3">
      <h3 className="font-semibold">{tool.title}</h3>
      <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
    </div>
    <p className="text-sm text-muted-foreground">{tool.description}</p>
    {tool.note && <span className="label">{tool.note}</span>}
  </a>
);

const DevTools = () => (
  <div className="flex flex-col gap-12">
    <header className="flex max-w-2xl flex-col gap-3">
      <p className="label">Dev tools</p>
      <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
        How an order actually moves
      </h1>
      <p className="text-lg leading-relaxed text-muted-foreground">
        Services never call each other. An order is written, an event is
        emitted, and whoever cares reacts — so the only way to see the shape of
        it is to follow one event across the hops.
      </p>
    </header>

    <SystemFlow />

    <section className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <h2 className="label">Streams and events</h2>
        <p className="max-w-prose text-sm text-muted-foreground">
          Consumers read as group members, so adding a replica adds a consumer
          and the group rebalances. A redelivery hits the inbox unique index and
          aborts rather than applying twice.
        </p>
      </div>

      <div className="surface-card overflow-x-auto">
        <table className="w-full min-w-[720px] text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="label px-5 py-3 text-left font-semibold">
                Stream
              </th>
              <th className="label px-5 py-3 text-left font-semibold">
                Produced by
              </th>
              <th className="label px-5 py-3 text-left font-semibold">
                Consumed by
              </th>
              <th className="label px-5 py-3 text-left font-semibold">
                Events
              </th>
            </tr>
          </thead>
          <tbody>
            {streams.map((row) => (
              <tr
                key={row.stream}
                className="border-b border-border last:border-b-0"
              >
                <td className="px-5 py-3 font-mono text-xs">
                  {row.stream}
                  {row.note && (
                    <span className="mt-1 block text-[0.7rem] text-muted-foreground">
                      {row.note}
                    </span>
                  )}
                </td>
                <td className="px-5 py-3 text-muted-foreground">
                  {row.producer}
                </td>
                <td className="px-5 py-3 text-muted-foreground">
                  {row.consumer}
                </td>
                <td className="px-5 py-3">
                  <div className="flex flex-col gap-0.5 font-mono text-xs text-muted-foreground">
                    {row.events.map((event) => (
                      <span key={event}>{event}</span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>

    <section className="flex flex-col gap-5">
      <div className="flex flex-col gap-1">
        <h2 className="label">Dashboards</h2>
        <p className="max-w-prose text-sm text-muted-foreground">
          Prometheus scrapes RED metrics and per-stream consumer lag; Loki holds
          the logs. Consumer lag is the number to watch — streams are trimmed by
          MAXLEN, so a stalled consumer loses events long before memory runs
          out.
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {dashboards.map((tool) => (
          <ToolCard key={tool.title} tool={tool} />
        ))}
      </div>
      <p className="text-sm text-muted-foreground">
        Grafana asks for the credentials set on the deployment. Anonymous
        viewing is off unless the stack was started with it enabled.
      </p>
    </section>
  </div>
);

export default DevTools;
