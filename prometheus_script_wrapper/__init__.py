import subprocess
import time
import tempfile
import sys
import os
import io

import click

from typing import Tuple, List

from prometheus_client import Metric, generate_latest
from prometheus_client.parser import text_fd_to_metric_families

from pathlib import Path

from prometheus_script_wrapper.registry import SimpleRegistry


@click.command(help="Wrap a script and export Prometheus metrics about its execution.")
@click.option("--prefix", help="Metric name prefix", required=True)
@click.option(
    "--output", help="Path to the .prom file", required=True, type=click.Path(file_okay=True, dir_okay=False, writable=True, path_type=Path)
)
@click.option("labels", "--label", help="Extra labels to add to the metrics", multiple=True, type=(str, str))
@click.argument("script", nargs=-1, required=True)
def main(prefix: str, output: Path, labels: List[Tuple[str, str]], script: List[str]):
    # Convert labels to dict
    labels = dict(labels)

    # Create a pipe to receive metrics from the script
    metrics_recv_fd, metrics_send_fd = os.pipe()

    registry = SimpleRegistry()

    start = time.time()

    process = subprocess.Popen(
        script,
        stdout=None,
        stderr=None,
        stdin=None,
        pass_fds=[metrics_send_fd],
        env={**os.environ, "PROM_METRICS_FD": str(metrics_send_fd)},
    )

    # Close our copy of the metric sender
    os.close(metrics_send_fd)

    try:
        # Receive, parse and prefix metrics
        script_metrics = text_fd_to_metric_families(io.TextIOWrapper(io.FileIO(metrics_recv_fd, "r")))
        for metric in script_metrics:
            metric_wrapped = Metric(
                name=f"{prefix}_script_{metric.name}", documentation=metric.documentation, typ=metric.type, unit=metric.unit
            )

            for sample in metric.samples:
                metric_wrapped.add_sample(
                    name=f"{prefix}_script_{sample.name}",
                    labels=sample.labels | labels,
                    value=sample.value,
                    timestamp=sample.timestamp,
                    exemplar=sample.exemplar,
                    native_histogram=sample.native_histogram,
                )

            registry.add(metric_wrapped)

        # Wait for the child to end
        exit_code = process.wait()

    except Exception as e:
        process.kill()

        print(f"Script raised exception: {e}", file=sys.stderr)
        sys.exit(255)

    end = time.time()
    runtime = end - start

    exit_code_metric = Metric(name=f"{prefix}_exit_code", documentation="Exit code of the wrapped script", typ="gauge")
    exit_code_metric.add_sample(exit_code_metric.name, value=exit_code, labels=labels)
    registry.add(exit_code_metric)

    runtime_metric = Metric(name=f"{prefix}_runtime_seconds", documentation="Runtime duration of the script in seconds", typ="gauge")
    runtime_metric.add_sample(runtime_metric.name, value=runtime, labels=labels)
    registry.add(runtime_metric)

    if exit_code == 0:
        success_timestamp_metric = Metric(
            name=f"{prefix}_success_timestamp_seconds", documentation="Timestamp of the last successful script execution", typ="gauge"
        )
        success_timestamp_metric.add_sample(success_timestamp_metric.name, value=end, labels=labels)
        registry.add(success_timestamp_metric)

    # Open a temporary file for writing metrics to
    output_tmp = tempfile.NamedTemporaryFile("wb", delete=False, dir=output.parent)
    output_tmp.write(generate_latest(registry))
    output_tmp.close()

    # Move the output file to its final destination and ensure temporary is deleted
    try:
        os.rename(output_tmp.name, output)
    except IOError:
        try:
            os.unlink(output_tmp.name)
        except FileNotFoundError:
            pass

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
