import unittest
from unittest.mock import patch

from acenite_agent.constants import ACENITE_URL
from acenite_agent.host_metrics import build_host_metrics_payload, send_host_metrics


METRICS = {
    "cpu_percent": 10.0,
    "memory_used_percent": 20.0,
    "memory_used_bytes": 200,
    "memory_total_bytes": 1000,
    "disk_used_percent": 30.0,
    "disk_used_bytes": 300,
    "disk_total_bytes": 1000,
    "network_rx_bytes": 400,
    "network_tx_bytes": 500,
    "load_average_1m": 1.2,
    "host_uptime_seconds": 60,
}


class HostMetricsTests(unittest.TestCase):
    @patch("acenite_agent.host_metrics.collect_host_metrics", return_value=METRICS)
    def test_build_payload_defaults_instance_id_to_hostname(self, _collect):
        payload = build_host_metrics_payload(
            service_name="billing-api",
            hostname="prod-api-1",
        )

        self.assertEqual(payload["service_name"], "billing-api")
        self.assertEqual(payload["hostname"], "prod-api-1")
        self.assertEqual(payload["instance_id"], "prod-api-1")
        self.assertEqual(payload["metrics"]["network_rx_bytes"], 400)

    @patch("acenite_agent.host_metrics.time.sleep", return_value=None)
    @patch("acenite_agent.host_metrics.build_host_metrics_payload", return_value={"metrics": METRICS})
    @patch("acenite_agent.host_metrics.requests.post")
    def test_send_host_metrics_posts_to_host_endpoint(self, post, _payload, _sleep):
        send_host_metrics(
            api_key="test-key",
            service_name="billing-api",
            interval=60,
            instance_id="server-01",
            hostname="prod-api-1",
        )

        post.assert_called_once()
        args, kwargs = post.call_args
        self.assertEqual(args[0], f"{ACENITE_URL}/metrics/host")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")


if __name__ == "__main__":
    unittest.main()
