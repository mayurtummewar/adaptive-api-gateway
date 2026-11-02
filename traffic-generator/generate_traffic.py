
import csv
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from pathlib import Path

GATEWAY = "http://127.0.0.1:9081/hello"
OUTPUT = Path(__file__).parent / "traffic_dataset.csv"

random.seed(42)
recent_requests = deque()
previous_time = None
rows = []


def send_request(kind):
    global previous_time

    now = time.time()
    interarrival_ms = (
        0.0 if previous_time is None
        else (now - previous_time) * 1000
    )
    previous_time = now

    while recent_requests and now - recent_requests[0] > 10:
        recent_requests.popleft()

    recent_requests.append(now)

    params = {"user_id": str(random.randint(1, 1000))}
    headers = {"User-Agent": "GatewayDemo/1.0"}

    if kind == "unusual":
        params = {
            f"parameter_{i}": "x" * 100
            for i in range(40)
        }
        headers["User-Agent"] = "X" * 500

    elif kind == "burst":
        params["source"] = "burst_test"

    query = urllib.parse.urlencode(params)
    url = f"{GATEWAY}?{query}"

    request = urllib.request.Request(
        url,
        headers=headers,
        method="GET",
    )

    status_code = 0

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            status_code = response.status
    except urllib.error.HTTPError as exc:
        status_code = exc.code
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"Request failed: {exc}")

    rows.append({
        "path_length": len("/hello"),
        "query_length": len(query),
        "query_param_count": len(params),
        "header_count": len(headers) + 2,
        "user_agent_length": len(headers["User-Agent"]),
        "request_body_bytes": 0,
        "interarrival_ms": round(interarrival_ms, 2),
        "requests_last_10s": len(recent_requests),
        "label": "normal" if kind == "normal" else "suspicious",
        "scenario": kind,
        "status_code": status_code,
    })


def main():
    # Normal traffic
    for _ in range(80):
        send_request("normal")
        time.sleep(random.uniform(0.15, 0.5))

    # Unusually large requests
    for _ in range(10):
        send_request("unusual")
        time.sleep(random.uniform(0.1, 0.3))

    # Burst traffic
    for _ in range(10):
        send_request("burst")
        time.sleep(0.02)

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys(),
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} requests.")
    print(f"Dataset saved to: {OUTPUT.resolve()}")


if __name__ == "__main__":
    main()
