import unittest
import os
from unittest.mock import MagicMock, patch

from acenite_agent.agent import AceniteAgent


class AgentPhaseTwoTests(unittest.TestCase):
    def tearDown(self):
        AceniteAgent.stop()

    def test_all_canonical_frameworks_are_accepted_when_application_is_disabled(self):
        for framework in ("flask", "fastapi", "django"):
            with self.subTest(framework=framework):
                AceniteAgent.start(
                    api_key="key", framework=framework,
                    enable_application_monitoring=False,
                    enable_heartbeat=False, enable_host_metrics=False,
                )
                AceniteAgent.stop()

    def test_invalid_framework_and_intervals_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported framework"):
            AceniteAgent.start(api_key="key", framework="tornado", enable_heartbeat=False, enable_host_metrics=False)
        for value in (14, 301):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "between 15 and 300"):
                AceniteAgent.start(api_key="key", heartbeat_interval=value, enable_heartbeat=False, enable_host_metrics=False)

    @patch("acenite_agent.agent.send_host_metrics")
    @patch("acenite_agent.agent.send_heartbeat")
    @patch("apscheduler.schedulers.background.BackgroundScheduler")
    def test_prompt_samples_idempotent_start_and_stop(self, scheduler_type, heartbeat, host):
        heartbeat_scheduler = MagicMock()
        host_scheduler = MagicMock()
        scheduler_type.side_effect = [heartbeat_scheduler, host_scheduler]
        with patch("acenite_agent.otel.setup_otel", return_value=MagicMock()) as otel:
            AceniteAgent.start(api_key="key", framework="flask", app=object())
            AceniteAgent.start(api_key="key", framework="flask", app=object())
        heartbeat.assert_called_once_with(
            api_key="key", interval=60.0, jitter=False,
            acenite_environment="production",
        )
        host.assert_called_once()
        otel.assert_called_once()
        AceniteAgent.stop()
        heartbeat_scheduler.shutdown.assert_called_once_with(wait=False)
        host_scheduler.shutdown.assert_called_once_with(wait=False)

    @patch("acenite_agent.agent.send_host_metrics")
    @patch("acenite_agent.agent.send_heartbeat")
    def test_disabled_capabilities_start_no_workers_or_instrumentation(self, heartbeat, host):
        with patch("acenite_agent.otel.setup_otel") as otel:
            AceniteAgent.start(
                api_key="key", framework="django",
                enable_application_monitoring=False,
                enable_heartbeat=False,
                enable_host_metrics=False,
            )
        heartbeat.assert_not_called()
        host.assert_not_called()
        otel.assert_not_called()

    def test_enable_logging_remains_application_monitoring_compatibility_alias(self):
        with patch("acenite_agent.otel.setup_otel") as otel:
            AceniteAgent.start(
                api_key="key", framework="django", enable_logging=False,
                enable_heartbeat=False, enable_host_metrics=False,
            )
        otel.assert_not_called()

    @patch.dict(os.environ, {"ACENITE_ENVIRONMENT": "development"}, clear=True)
    @patch("acenite_agent.agent.send_host_metrics")
    @patch("acenite_agent.agent.send_heartbeat")
    def test_development_runs_only_instrumentation(self, heartbeat, host):
        with patch("acenite_agent.otel.setup_otel", return_value=MagicMock()) as otel:
            AceniteAgent.start(api_key="key", framework="django")
        heartbeat.assert_not_called()
        host.assert_not_called()
        self.assertEqual(otel.call_args.kwargs["acenite_environment"], "development")

    @patch.dict(os.environ, {}, clear=True)
    @patch("builtins.print")
    def test_missing_environment_warns_once_and_defaults_production(self, printer):
        AceniteAgent.start(
            api_key="key", enable_application_monitoring=False,
            enable_heartbeat=False, enable_host_metrics=False,
        )
        AceniteAgent.start(api_key="key")
        warnings = [str(call.args[0]) for call in printer.call_args_list if call.args]
        self.assertEqual(len(warnings), 1)
        self.assertIn("https://acenite.com/docs/environments", warnings[0])

    def test_empty_and_invalid_environment_fail_before_startup(self):
        for value in ("", "Production", " development ", "staging"):
            with self.subTest(value=value), patch.dict(
                os.environ, {"ACENITE_ENVIRONMENT": value}, clear=True,
            ), self.assertRaisesRegex(ValueError, "ACENITE_ENVIRONMENT"):
                AceniteAgent.start(api_key="key")


if __name__ == "__main__":
    unittest.main()
