import { ExternalLink } from 'lucide-react';

interface Tool {
  title: string;
  description: string;
  url: string;
  badge?: string;
  credentials?: string;
}

const groups: Array<{ heading: string; blurb: string; tools: Tool[] }> = [
  {
    heading: 'Dashboards',
    blurb:
      'Prometheus scrapes RED metrics and per-stream consumer lag; Loki holds the logs, keyed by correlation id.',
    tools: [
      {
        title: 'HTTP metrics',
        description: 'Request rate, latency percentiles and error rates',
        url: '/grafana/d/http-metrics/http-metrics',
        badge: 'read-only',
      },
      {
        title: 'Application logs',
        description: 'Live log stream, volume and error tracking (Loki)',
        url: '/grafana/d/application-logs/application-logs',
        badge: 'read-only',
      },
      {
        title: 'Event pipeline',
        description: 'Stream throughput, processing latency and dead letters',
        url: '/grafana/d/event-pipeline/event-pipeline',
        badge: 'read-only',
      },
      {
        title: 'Grafana',
        description: 'All dashboards, explore and admin',
        url: '/grafana/',
        credentials: 'admin / admin',
      },
      {
        title: 'Prometheus',
        description: 'Metrics collection, PromQL queries and targets',
        url: '/prometheus/',
        badge: 'read-only',
      },
    ],
  },
  {
    heading: 'Service APIs',
    blurb:
      'OpenAPI for each service. These are direct ports, so they only resolve when the stack runs locally.',
    tools: [
      {
        title: 'Orders',
        description: 'Orders and menu endpoints',
        url: 'http://localhost:8003/docs',
        badge: ':8003',
      },
      {
        title: 'Delivery',
        description: 'Delivery endpoints',
        url: 'http://localhost:8001/docs',
        badge: ':8001',
      },
      {
        title: 'Notifications',
        description: 'Notifications and SSE endpoints',
        url: 'http://localhost:8002/docs',
        badge: ':8002',
      },
    ],
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
      <h3 className="font-medium">{tool.title}</h3>
      <ExternalLink className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
    </div>
    <p className="text-sm text-muted-foreground">{tool.description}</p>
    {(tool.badge || tool.credentials) && (
      <div className="mt-1 flex flex-wrap gap-2">
        {tool.badge && <span className="label">{tool.badge}</span>}
        {tool.credentials && (
          <code className="rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[0.7rem]">
            {tool.credentials}
          </code>
        )}
      </div>
    )}
  </a>
);

const DevTools = () => (
  <div className="flex flex-col gap-10">
    <header className="flex flex-col gap-3">
      <p className="label">Dev tools</p>
      <h1 className="text-[2.8rem] font-semibold leading-[1.2] text-brand">
        Look inside the running system
      </h1>
    </header>

    {groups.map((group) => (
      <section key={group.heading} className="flex flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h2 className="label">{group.heading}</h2>
          <p className="max-w-prose text-sm text-muted-foreground">
            {group.blurb}
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {group.tools.map((tool) => (
            <ToolCard key={tool.title} tool={tool} />
          ))}
        </div>
      </section>
    ))}
  </div>
);

export default DevTools;
