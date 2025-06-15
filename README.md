# RS3 RuneMetrics Exporter for Loki/Prometheus
A simple RuneMetrics Exporter for exposing data to Loki & Prometheus.  
It exposes skill data to Prometheus, and sends activity logs to Loki

## Usage
Use Docker; change env variables as appropriate.

Example config:
```yaml
services:
  rs3runemetricsexporter:
    image: daku/rs3runemetricsexporter:v1.0

    environment:
      RUNESCAPE_USERNAME: ''
      # RSRME_ACTIVITIES: 20 # Activities to return from API, 20 is max.
      RSRME_LOG_TYPE:     'text' # text or details. API provides both; see below for differences
      RSRME_INTERVAL_MINUTES: 30

      PROMETHEUS_PORT: 9090
      LOKI_URL:        http://loki:3100

    ports: ["9090:9090"] # This should match PROMETHEUS_PORT
```

For more complicated configurations, please ask elsewhere 👍.

## Differences of log type:
RuneMetrics provides the activity log in two different forms:
- Text: `I killed 5 Gate of Elidinis.`
- Details: `I killed 5 Gates of Elidinis: sacred and powerful parts of the underworld, possessed by corruption.`


RUNESCAPE_USERNAME     = os.environ.get('RUNESCAPE_USERNAME', '')
RSRME_ACTIVITIES       = os.environ.get('RSRME_ACTIVITIES', 20) # 20 is max?
RSRME_LOG_TYPE         = os.environ.get('RSRME_LOG_TYPE', 'text') # text or details
RSRME_INTERVAL_MINUTES = int(os.environ.get('RSRME_INTERVAL_MINUTES', 30))

PROMETHEUS_PORT    = int(os.environ.get('PROMETHEUS_PORT', 8080))
LOKI_URL           = os.environ.get('LOKI_URL', 'http://loki:3100')
