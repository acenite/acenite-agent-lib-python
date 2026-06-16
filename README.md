# Acenite Agent (Python)

**Acenite Agent** is the official Python agent library for the Acenite server monitoring platform.

The agent is designed to connect Python services to the Acenite monitoring backend and enable observability features such as service telemetry, heartbeat monitoring, and runtime instrumentation.

This project is currently under active development.

---

## Development Status

Current version: `0.x.x`

The library is in an **early development stage**.  
Versions in the `0.x.x` range indicate that the public API is **not yet stable**.

The following should be expected:

- Breaking changes may occur in future releases
- APIs and internal structures may change without prior notice
- Features may be added, modified, or removed as the platform evolves

The package is published primarily to reserve the package name and support early development of the Acenite ecosystem.

---

## About Acenite

Acenite is a server monitoring platform currently under development.  
The platform aims to provide visibility into service health, runtime behavior, and system telemetry for distributed applications.

The Python agent will serve as the integration layer between Python services and the Acenite monitoring infrastructure.

---

## Package Information

- Package name: `acenite-agent`
- Package registry: PyPI
- Development stage: Active development
- Stability: Experimental

PyPI page:  
https://pypi.org/project/acenite-agent/

---

## Project Status

This repository is part of the broader Acenite platform which is still being built.  
Documentation, features, and integrations will evolve over time as the platform progresses.

More information will be published as the system approaches a stable release.

## Host resource metrics

The agent can report lightweight host metrics to Acenite:

```python
AceniteAgent.start(
    framework="flask",
    api_key="your-api-key",
    service_name="orders-service",
    enable_host_metrics=True,
    host_metrics_interval=60,
    instance_id="server-01",
)
```

Host metrics are sent to `/server/metrics/host` separately from heartbeat requests.
`network_rx_bytes` and `network_tx_bytes` are cumulative host counters; the Acenite backend calculates deltas and chart rates.
