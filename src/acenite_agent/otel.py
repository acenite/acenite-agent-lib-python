import importlib

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

from .constants import ALLOWED_FRAMEWORKS, ALLOWED_INSTRUMENTATIONS, resolve_acenite_url
from .integrations import FRAMEWORKS, INSTRUMENTATIONS


def _load_callable(path: str):
    module_path, func_name = path.split(":")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)

def setup_otel(
        *,
        app: object | None,
        framework: str,
        instrumentations: list[str] | None,
        api_key: str,
        service_name: str,
        acenite_environment: str = "production",
) -> TracerProvider:
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "deployment.environment.name": acenite_environment,
        })
    )
    trace.set_tracer_provider(provider)

    exporter = OTLPSpanExporter(
                endpoint=f"{resolve_acenite_url()}/monitor/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "X-Acenite-Environment": acenite_environment,
                }
                )

    provider.add_span_processor(BatchSpanProcessor(exporter))

    # -------- Apply framework instrumentation --------
    if framework:
        if framework not in ALLOWED_FRAMEWORKS:
            raise ValueError(f"Unsupported framework: {framework}")

        if framework in ("flask", "fastapi") and app is None:
            raise ValueError(f"{framework} framework requires app instance")

        fn = _load_callable(FRAMEWORKS[framework])

        if framework in ("flask", "fastapi"):
            fn(app)
        else:
            fn()

    # -------- Apply selected instrumentations --------
    if instrumentations:
        for name in instrumentations:
            if name not in ALLOWED_INSTRUMENTATIONS:
                raise ValueError(f"Unsupported instrumentation: {name}")

            fn = _load_callable(INSTRUMENTATIONS[name])
            fn()

    return provider
