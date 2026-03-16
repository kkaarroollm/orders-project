from prometheus_client import Counter, Histogram

STREAM_MESSAGES_TOTAL = Counter(
    "stream_messages_processed_total",
    "Total stream messages processed",
    ["stream", "group", "status"],
)

STREAM_MESSAGE_DURATION = Histogram(
    "stream_message_duration_seconds",
    "Time to process a stream message",
    ["stream", "group"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

STREAM_DLQ_TOTAL = Counter(
    "stream_dlq_messages_total",
    "Messages sent to dead-letter queue",
    ["stream", "group"],
)
