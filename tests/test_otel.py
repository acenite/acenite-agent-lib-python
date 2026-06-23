import os
import unittest
from unittest.mock import patch

from acenite_agent.otel import setup_otel


class OpenTelemetryEndpointTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "ACENITE_AGENT_ALLOW_ENDPOINT_OVERRIDE": "true",
            "ACENITE_AGENT_INGEST_URL": "http://[::1]:5001",
        },
        clear=True,
    )
    @patch("acenite_agent.otel.BatchSpanProcessor")
    @patch("acenite_agent.otel.OTLPSpanExporter")
    @patch("acenite_agent.otel.trace.set_tracer_provider")
    def test_local_override_is_used_for_otlp(self, _set_provider, exporter, _processor):
        setup_otel(
            app=None,
            framework="",
            instrumentations=None,
            api_key="test-key",
            service_name="orders",
        )

        exporter.assert_called_once_with(
            endpoint="http://[::1]:5001/monitor/",
            headers={"Authorization": "Bearer test-key"},
        )


if __name__ == "__main__":
    unittest.main()