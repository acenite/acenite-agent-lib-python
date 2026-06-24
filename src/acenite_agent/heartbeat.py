import time, random, uuid, requests

from .constants import resolve_acenite_url

BOOT_ID = str(uuid.uuid4())

def send_heartbeat(
    *,
    api_key: str,
    interval: float,
    jitter: bool = True,
    acenite_environment: str = "production",
):
    # jitter each run (avoid thundering herd)
    if jitter:
        time.sleep(random.uniform(0.0, interval / 10))

    try:
        requests.post(
            f"{resolve_acenite_url()}/heartbeat/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "X-Acenite-Environment": acenite_environment,
            },
            json={
                "status": "up",
                "boot_id": BOOT_ID,
                "instance_id": "default",
            },
            timeout=(3, 5),  # connect, read
        )
    except Exception as e:
        # swallow; next run will try again
        print(e)
        pass
