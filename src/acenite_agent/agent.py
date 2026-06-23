from .heartbeat import send_heartbeat
from .host_metrics import default_hostname, send_host_metrics
from .constants import ACENITE_URL, resolve_acenite_url
from opentelemetry import trace


class AceniteAgent:
    _started = False
    _heartbeat_scheduler = None
    _host_metrics_scheduler = None
    _otel_runtime = None

    @classmethod
    def start(
        cls,
        *,
        app: object | None = None,
        framework: str | None = None,
        instrumentations: list[str] | None = None ,
        api_key: str,
        service_name: str = "unknown-service",
        enable_logging: bool = True,
        enable_application_monitoring: bool | None = None,
        enable_heartbeat: bool = True,
        heartbeat_interval: float = 60.0,
        enable_host_metrics: bool = True,
        host_metrics_interval: float = 60.0,
        instance_id: str | None = None,
        hostname: str | None = None,
    ) -> None:
        if cls._started:
            return

        cls._validate_interval("heartbeat_interval", heartbeat_interval)
        cls._validate_interval("host_metrics_interval", host_metrics_interval)
        if framework is not None and framework not in {"flask", "fastapi", "django"}:
            raise ValueError(f"Unsupported framework: {framework}")

        # Before this option existed, enable_logging controlled OpenTelemetry.
        # Preserve that behavior for callers that do not pass the canonical flag.
        application_monitoring = (
            enable_logging
            if enable_application_monitoring is None
            else enable_application_monitoring
        )

        resolved_acenite_url = resolve_acenite_url()
        if enable_logging and resolved_acenite_url != ACENITE_URL:
            print(
                "Acenite development endpoint override active: "
                f"telemetry is being sent to {resolved_acenite_url} instead of production."
            )

        resolved_hostname = (hostname or default_hostname()).strip() or "unknown-host"
        resolved_instance_id = (instance_id or resolved_hostname).strip() or resolved_hostname

        if application_monitoring:
            from .otel import setup_otel

            cls._otel_runtime = setup_otel(
                app=app,
                framework=framework,
                instrumentations=instrumentations,
                api_key=api_key,
                service_name=service_name
            )

        if enable_heartbeat:
            from apscheduler.schedulers.background import BackgroundScheduler

            send_heartbeat(api_key=api_key, interval=heartbeat_interval, jitter=False)
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(send_heartbeat, "interval", seconds=heartbeat_interval, max_instances=1, coalesce=True,
                kwargs={
                    "api_key": api_key,
                    "interval": heartbeat_interval,
                },
            )
            scheduler.start()
            cls._heartbeat_scheduler = scheduler

        if enable_host_metrics:
            from apscheduler.schedulers.background import BackgroundScheduler

            send_host_metrics(
                api_key=api_key,
                service_name=service_name,
                interval=host_metrics_interval,
                instance_id=resolved_instance_id,
                hostname=resolved_hostname,
                jitter=False,
            )
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(send_host_metrics, "interval", seconds=host_metrics_interval, max_instances=1, coalesce=True,
                kwargs={
                    "api_key": api_key,
                    "service_name": service_name,
                    "interval": host_metrics_interval,
                    "instance_id": resolved_instance_id,
                    "hostname": resolved_hostname,
                },
            )
            scheduler.start()
            cls._host_metrics_scheduler = scheduler

        cls._started = True

    @classmethod
    def get_tracer(cls):
        return trace.get_tracer("acenite-agent")

    @classmethod
    def stop(cls) -> None:
        if cls._heartbeat_scheduler is not None:
            cls._heartbeat_scheduler.shutdown(wait=False)
            cls._heartbeat_scheduler = None
        if cls._host_metrics_scheduler is not None:
            cls._host_metrics_scheduler.shutdown(wait=False)
            cls._host_metrics_scheduler = None
        if cls._otel_runtime is not None:
            cls._otel_runtime.shutdown()
            cls._otel_runtime = None
        cls._started = False

    @staticmethod
    def _validate_interval(name: str, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")
        if value < 15 or value > 300:
            raise ValueError(f"{name} must be between 15 and 300 seconds")
