import unittest

from acenite_agent.constants import ACENITE_URL, resolve_acenite_url


class EndpointResolutionTests(unittest.TestCase):
    def test_no_variables_uses_production(self):
        self.assertEqual(resolve_acenite_url({}), ACENITE_URL)

    def test_url_alone_uses_production(self):
        self.assertEqual(
            resolve_acenite_url({"ACENITE_AGENT_INGEST_URL": "http://127.0.0.1:5001"}),
            ACENITE_URL,
        )

    def test_allow_flag_alone_uses_production(self):
        self.assertEqual(
            resolve_acenite_url({"ACENITE_AGENT_ALLOW_ENDPOINT_OVERRIDE": "TrUe"}),
            ACENITE_URL,
        )

    def test_loopback_ipv4_override(self):
        self.assertEqual(self._resolve("http://127.0.0.1:5001"), "http://127.0.0.1:5001")

    def test_localhost_override(self):
        self.assertEqual(self._resolve("http://localhost:5001"), "http://localhost:5001")

    def test_loopback_ipv6_override(self):
        self.assertEqual(self._resolve("http://[::1]:5001"), "http://[::1]:5001")

    def test_remote_http_and_https_urls_use_production(self):
        for url in ("http://example.com:5001", "https://example.com"):
            with self.subTest(url=url):
                self.assertEqual(self._resolve(url), ACENITE_URL)

    @staticmethod
    def _resolve(url: str) -> str:
        return resolve_acenite_url(
            {
                "ACENITE_AGENT_ALLOW_ENDPOINT_OVERRIDE": "true",
                "ACENITE_AGENT_INGEST_URL": url,
            }
        )


if __name__ == "__main__":
    unittest.main()
