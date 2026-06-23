import os
import random
import socket
import time
from datetime import datetime, timezone

import requests

from .constants import resolve_acenite_url


def default_hostname() -> str:
    return socket.gethostname() or "unknown-host"


def collect_host_metrics() -> dict:
    import psutil

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(_disk_path())
    net = psutil.net_io_counters()

    load_average = 0.0
    try:
        load_average = float(os.getloadavg()[0])
    except (AttributeError, OSError):
        try:
            load_average = float(psutil.getloadavg()[0])
        except (AttributeError, OSError):
            load_average = 0.0

    return {
        "cpu_percent": float(psutil.cpu_percent(interval=None)),
        "memory_used_percent": float(memory.percent),
        "memory_used_bytes": int(memory.used),
        "memory_total_bytes": int(memory.total),
        "disk_used_percent": float(disk.percent),
        "disk_used_bytes": int(disk.used),
        "disk_total_bytes": int(disk.total),
        # Cumulative counters. The Acenite backend calculates deltas/rates.
        "network_rx_bytes": int(net.bytes_recv),
        "network_tx_bytes": int(net.bytes_sent),
        "load_average_1m": max(0.0, load_average),
        "host_uptime_seconds": int(time.time() - psutil.boot_time()),
    }


def build_host_metrics_payload(
    *,
    service_name: str,
    instance_id: str | None = None,
    hostname: str | None = None,
) -> dict:
    resolved_hostname = (hostname or default_hostname()).strip() or "unknown-host"
    resolved_instance_id = (instance_id or resolved_hostname).strip() or resolved_hostname

    return {
        "service_name": service_name,
        "instance_id": resolved_instance_id,
        "hostname": resolved_hostname,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "metrics": collect_host_metrics(),
    }


def send_host_metrics(
    *,
    api_key: str,
    service_name: str,
    interval: float,
    instance_id: str | None = None,
    hostname: str | None = None,
    jitter: bool = True,
):
    if jitter:
        time.sleep(random.uniform(0.0, interval / 10))

    try:
        requests.post(
            f"{resolve_acenite_url()}/metrics/host",
            headers={"Authorization": f"Bearer {api_key}"},
            json=build_host_metrics_payload(
                service_name=service_name,
                instance_id=instance_id,
                hostname=hostname,
            ),
            timeout=(3, 5),
        )
    except Exception as e:
        print(e)
        pass


def _disk_path() -> str:
    if os.name == "nt":
        return os.path.abspath(os.sep)
    return "/"
