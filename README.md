# Prometheus Script Wrapper

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A utility tool that wraps script execution and exports Prometheus metrics about its performance and status.

## Overview

Prometheus Script Wrapper allows you to run any script or command while automatically collecting execution metrics in Prometheus format. This is particularly useful for monitoring cron jobs, batch processes, or any scripts where you need to track execution time, success rate, and other performance indicators.

## Installation

```bash
uv add prometheus-script-wrapper
```

Or install directly from source:

```bash
git clone https://github.com/yourusername/prometheus-script-wrapper.git
cd prometheus-script-wrapper
uv add -e .
```

## Usage

### Basic Usage

```bash
python -m prometheus_script_wrapper --output /path/to/metrics.prom -- /bin/bash -c "echo 'Hello, Prometheus!'"
```

This will:
1. Run the specified command (`echo 'Hello, Prometheus!'`)
2. Track its execution time and exit code
3. Write the metrics to `/path/to/metrics.prom` in Prometheus format

### Command Line Options

```
Options:
  --prefix TEXT     Metric name prefix (default: "script")
  --output TEXT     Path to the .prom file  [required]
  --label KEY VALUE Add a label to all metrics (format: key=value). Can be specified multiple times.
  --help            Show this message and exit.
```

### Advanced Example

```bash
python -m prometheus_script_wrapper \
  --prefix database_backup \
  --output /var/lib/node_exporter/database_backup.prom \
  -- /usr/local/bin/backup_database.sh --full
```

## Metrics Documentation

The wrapper exports the following metrics in Prometheus format.
All metrics can include optional labels that are specified with the `--label` flag, allowing for better categorization and filtering in Prometheus queries.

### Core Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `{prefix}exit_code` | Gauge | Exit code of the script. 0 typically indicates success, non-zero values indicate errors |
| `{prefix}runtime_seconds` | Gauge | Total execution time of the script in seconds (with millisecond precision) |
| `{prefix}success_timestamp_seconds` | Gauge | Unix timestamp (in seconds) when the script completed successfully. Only exported when the exit code is 0. Useful for monitoring when a script last ran successfully. |

### Custom Metrics

Your script can export additional custom metrics by writing them to the file descriptor provided in the `PROM_METRICS_FD` environment variable. This allows you to track application-specific metrics like:

- Number of records processed
- Data transfer sizes
- Cache hit/miss rates
- Custom error counters

### Example of Custom Metrics

In your wrapped script (bash example):

```bash
#!/bin/bash

# Your script logic here...
RECORDS_PROCESSED=1250

# Export custom metric to Prometheus
if [ -n "$PROM_METRICS_FD" ]; then
  echo "script_records_processed ${RECORDS_PROCESSED}" >&$PROM_METRICS_FD
fi

exit 0
```

In your wrapped script (Python example):

```python
import os

# Your script logic here...
records_processed = 1250

# Export custom metric to Prometheus
if 'PROM_METRICS_FD' in os.environ:
    fd = int(os.environ['PROM_METRICS_FD'])
    with open(fd, 'w') as f:
        f.write(f"script_records_processed {records_processed}\n")
```

## Integration with Prometheus

To collect these metrics with Prometheus, configure the Node Exporter with textfile collection enabled:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
    params:
      collect[]:
        - textfile
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '(.*)'
        replacement: '$1'
```

Ensure the Node Exporter is configured with:

```
--collector.textfile.directory=/var/lib/node_exporter/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.