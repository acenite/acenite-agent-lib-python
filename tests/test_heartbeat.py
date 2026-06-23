import os
import unittest
from unittest.mock import patch

from acenite_agent.heartbeat import send_heartbeat


class HeartbeatTests(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "ACENITE_AGENT_ALLOW_ENDPOINT_OVERRIDE": "true",
            "ACENITE_AGENT_INGEST_URL": "http://127.0.0.1:5001",
        },
        clear=True,
    )
    @patch("acenite_agent.heartbeat.time.sleep", return_value=None)
    @patch("acenite_agent.heartbeat.requests.post")
    def test_local_override_is_used_for_heartbeat(self, post, _sleep):
        send_heartbeat(api_key="test-key", interval=60)

        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:5001/heartbeat/")


if __name__ == "__main__":
    unittest.main()