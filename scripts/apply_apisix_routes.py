import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def env_value(name: str) -> str:
    value = os.getenv(name)
    if value:
        return value
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1]
    raise RuntimeError(f"{name} is required")


def request(method: str, path: str, body: dict | None = None) -> int:
    arguments = [
        "curl.exe",
        "--max-time",
        "15",
        "--silent",
        "--show-error",
        "--request",
        method,
        "--url",
        f"http://localhost:9180/apisix/admin{path}",
        "--header",
        f"X-API-KEY: {env_value('APISIX_ADMIN_KEY')}",
        "--header",
        "Content-Type: application/json",
        "--output",
        os.devnull,
        "--write-out",
        "%{http_code}",
    ]
    temporary_path = None
    try:
        if body is not None:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", suffix=".json", delete=False
            ) as file:
                json.dump(body, file)
                temporary_path = file.name
            arguments.extend(["--data-binary", f"@{temporary_path}"])
        result = subprocess.run(arguments, capture_output=True, text=True, check=True)
        return int(result.stdout)
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)


def main() -> None:
    policy = (ROOT / "apisix" / "ai-policy.lua").read_text(encoding="utf-8")
    plugins = {
        "limit-count": {
            "count": 60,
            "time_window": 60,
            "rejected_code": 429,
            "key": "remote_addr",
            "policy": "local",
        },
        "serverless-pre-function": {
            "phase": "rewrite",
            "functions": [policy],
        },
        "proxy-rewrite": {
            "regex_uri": ["^/api/(.*)", "/$1"],
        },
    }
    routes = json.loads((ROOT / "route.json").read_text(encoding="utf-8"))
    for route_definition in routes:
        route_id = route_definition["id"]
        uri = route_definition["uri"]
        upstream_name = route_definition["upstream"]
        route = {
            "id": route_id,
            "uri": uri,
            "plugins": plugins,
            "upstream": {
                "nodes": {f"{upstream_name}:8000": 1},
                "type": "roundrobin",
            },
        }
        response_code = request("PUT", f"/routes/{route_id}", route)
        if response_code not in {200, 201}:
            raise RuntimeError(f"APISIX rejected {route_id} with HTTP {response_code}")
        print(f"Applied {route_id}")
    response_code = request("DELETE", "/routes/1")
    if response_code in {200, 204}:
        print("Removed legacy route 1")


if __name__ == "__main__":
    main()
