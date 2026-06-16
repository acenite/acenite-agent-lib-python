from .otel import setup_otel
from .heartbeat import send_heartbeat
from .host_metrics import default_hostname, send_host_metrics
from apscheduler.schedulers.background import BackgroundScheduler
from opentelemetry import trace


class AceniteAgent:
    _started = False

    @classmethod
    def start(
        cls,
        *,
        app: object | None = None,
        framework: str,
        instrumentations: list[str] | None = None ,
        api_key: str,
        service_name: str = "unknown-service",
        enable_logging: bool = True,
        enable_heartbeat: bool = True,
        heartbeat_interval: float = 60.0,
        enable_host_metrics: bool = True,
        host_metrics_interval: float = 60.0,
        instance_id: str | None = None,
        hostname: str | None = None,
    ) -> None:

        if cls._started:
            return

        resolved_hostname = (hostname or default_hostname()).strip() or "unknown-host"
        resolved_instance_id = (instance_id or resolved_hostname).strip() or resolved_hostname

        if enable_logging:
            setup_otel(
                app=app,
                framework=framework,
                instrumentations=instrumentations,
                api_key=api_key,
                service_name=service_name
            )

        if enable_heartbeat:
            scheduler = BackgroundScheduler(daemon=True)
            scheduler.add_job(send_heartbeat, "interval", seconds=heartbeat_interval, max_instances=1, coalesce=True,
                kwargs={
                    "api_key": api_key,
                    "interval": heartbeat_interval,
                },
            )
            scheduler.start()

        if enable_host_metrics:
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

        cls._started = True

    @classmethod
    def get_tracer(cls):
        tracer = trace.get_tracer(__name__)
        return tracer
