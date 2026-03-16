import { ExternalLink } from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from '@/components/ui/card';

const tools = [
  {
    title: 'Grafana — HTTP Metrics',
    description: 'Request rate, latency percentiles & error rates',
    url: '/grafana/d/http-metrics/http-metrics',
    badge: 'read-only',
  },
  {
    title: 'Grafana — Application Logs',
    description: 'Live log stream, volume & error tracking (Loki)',
    url: '/grafana/d/application-logs/application-logs',
    badge: 'read-only',
  },
  {
    title: 'Grafana',
    description: 'All dashboards, explore & admin',
    url: '/grafana/',
    credentials: 'admin / admin',
  },
  {
    title: 'Prometheus',
    description: 'Metrics collection, PromQL queries & targets',
    url: '/prometheus/',
    badge: 'read-only',
  },
  {
    title: 'Order Service — API Docs',
    description: 'OpenAPI / Swagger UI for orders & menu endpoints',
    url: 'http://localhost:8003/docs',
  },
  {
    title: 'Delivery Service — API Docs',
    description: 'OpenAPI / Swagger UI for delivery endpoints',
    url: 'http://localhost:8001/docs',
  },
  {
    title: 'Notifications Service — API Docs',
    description: 'OpenAPI / Swagger UI for notifications endpoints',
    url: 'http://localhost:8002/docs',
  },
];

const DevTools = () => {
  return (
    <div className="max-w-5xl mx-auto">
      <h2 className="text-2xl font-bold mb-6">Dev Tools</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <a
            key={tool.title}
            href={tool.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block hover:ring-2 hover:ring-blue-500 rounded-xl transition"
          >
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  {tool.title}
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                </CardTitle>
                <CardDescription>{tool.description}</CardDescription>
              </CardHeader>
              {(tool.credentials || tool.badge) && (
                <CardContent className="flex gap-2">
                  {tool.credentials && (
                    <code className="text-xs bg-muted px-2 py-1 rounded">
                      {tool.credentials}
                    </code>
                  )}
                  {tool.badge && (
                    <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded">
                      {tool.badge}
                    </span>
                  )}
                </CardContent>
              )}
            </Card>
          </a>
        ))}
      </div>
    </div>
  );
};

export default DevTools;
