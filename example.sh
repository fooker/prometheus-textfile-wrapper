#!/usr/bin/env bash

set -euo pipefail

echo "FD: ${PROM_METRICS_FD}"

sleep 1

echo "# HELP test_count This is a test metric\ncontaining a newline" >&${PROM_METRICS_FD}
echo "# TYPE test_count gauge" >&${PROM_METRICS_FD}
echo "test_count {foo=\"bar\", testkey=\"$1\"} 42" >&${PROM_METRICS_FD}

sleep 2

exit 3