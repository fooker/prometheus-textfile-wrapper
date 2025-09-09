from typing import Iterable

from prometheus_client import Metric
from prometheus_client.registry import Collector


class SimpleRegistry(Collector):
    """A simple registry that just collects pre-existing metrics."""

    def __init__(self):
        self.__metrics = []

    def add(self, metric: Metric):
        self.__metrics.append(metric)

    def collect(self) -> Iterable[Metric]:
        return self.__metrics
