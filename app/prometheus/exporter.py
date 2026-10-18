from prometheus_client import CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector
from prometheus_client import REGISTRY as DEFAULT_REGISTRY

from app.prometheus import metrics # noqa: F401


def build_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    for collector in list(DEFAULT_REGISTRY._collector_to_names):
        try:
            registry.register(collector)
        except ValueError:
            pass

    MultiProcessCollector(registry)

    return registry