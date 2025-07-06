from prometheus_client import Counter, Histogram


# Custom Prometheus metrics for monitoring the LLM Gateway

REQUESTS_TOTAL = Counter(
    'gateway_requests_total',
    'Total number of HTTP requests processed by the gateway',
    ['owner', 'model', 'status_code']
)

REQUEST_LATENCY_SECONDS = Histogram(
    'gateway_request_duration_seconds',
    'Request duration in seconds',
    ['owner', 'model'],
    buckets=(0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 30.0, float('inf'))
)

TOKENS_USED_TOTAL = Counter(
    'gateway_tokens_used_total',
    'Total number of tokens processed by the gateway',
    ['owner', 'model', 'token_type']
)