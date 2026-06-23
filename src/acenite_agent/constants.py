import ipaddress
import os
from collections.abc import Mapping
from urllib.parse import urlsplit


ACENITE_URL = "https://ingest.acenite.com"
ALLOW_ENDPOINT_OVERRIDE_ENV = "ACENITE_AGENT_ALLOW_ENDPOINT_OVERRIDE"
INGEST_URL_ENV = "ACENITE_AGENT_INGEST_URL"


def resolve_acenite_url(environment: Mapping[str, str] | None = None) -> str:
    environment = os.environ if environment is None else environment
    if environment.get(ALLOW_ENDPOINT_OVERRIDE_ENV, "").lower() != "true":
        return ACENITE_URL

    candidate = environment.get(INGEST_URL_ENV)
    if not candidate or candidate != candidate.strip():
        return ACENITE_URL

    try:
        parsed = urlsplit(candidate)
        # Accessing port validates it (for example, rejects values above 65535).
        parsed.port
    except ValueError:
        return ACENITE_URL

    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return ACENITE_URL

    hostname = parsed.hostname.lower()
    if hostname == "localhost":
        return candidate

    try:
        if ipaddress.ip_address(hostname).is_loopback:
            return candidate
    except ValueError:
        pass

    return ACENITE_URL

ALLOWED_FRAMEWORKS = {
    "flask",
    "fastapi",
    "django",
}

ALLOWED_INSTRUMENTATIONS = {
    "requests",
    "httpx",
    "psycopg2",
    "sqlalchemy",
}
