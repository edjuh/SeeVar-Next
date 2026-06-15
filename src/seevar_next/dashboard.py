"""Small human dashboard for SeeVar Next."""

from __future__ import annotations

import argparse
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from seevar_next.config import load_config


def _read_text(path: Path, default: str = "not available") -> str:
    """Read a text file if it exists."""
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def _read_json(path: Path) -> dict:
    """Read a JSON object if it exists."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _target_rows(plan: dict) -> str:
    """Render target rows."""
    rows = []
    for idx, target in enumerate(plan.get("targets", []), start=1):
        start = str(target.get("best_start_utc") or "")[11:16]
        end = str(target.get("best_end_utc") or "")[11:16]
        alt = target.get("max_alt_deg")
        alt_text = f"{alt:.0f} deg" if isinstance(alt, int | float) else "-"
        rows.append(
            "<tr>"
            f"<td>{idx}</td>"
            f"<td>{html.escape(str(target.get('name', '-')))}</td>"
            f"<td>{html.escape(str(target.get('target_type') or '-'))}</td>"
            f"<td>{start}-{end}</td>"
            f"<td>{alt_text}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='5'>No plan yet</td></tr>"


def _status_rows(status: dict) -> str:
    """Render target status rows."""
    rows = []
    for target, item in sorted((status.get("targets") or {}).items()):
        rows.append(
            "<tr>"
            f"<td>{html.escape(target)}</td>"
            f"<td>{html.escape(str(item.get('phase', '-')))}</td>"
            f"<td>{html.escape(str(item.get('step', '-')))}</td>"
            f"<td>{html.escape(str(item.get('status', '-')))}</td>"
            f"<td>{html.escape(str(item.get('reason') or ''))}</td>"
            "</tr>"
        )
    return "\n".join(rows) or "<tr><td colspan='5'>No proof status yet</td></tr>"


def render_dashboard(config_path: Path = Path("config/seevar-next.json"), data_dir: Path = Path("data")) -> str:
    """Render the dashboard HTML."""
    config = load_config(config_path)
    readiness = _read_text(data_dir / "readiness.txt")
    plan = _read_json(data_dir / "tonights_plan.json")
    status = _read_json(data_dir / "status.json")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="30">
<title>SeeVar Next</title>
<style>
body {{ margin: 0; font: 16px system-ui, sans-serif; background: #111827; color: #e5e7eb; }}
main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
h1, h2 {{ margin: 0 0 12px; }}
section {{ border-top: 1px solid #374151; padding: 18px 0; }}
pre {{ white-space: pre-wrap; background: #020617; padding: 16px; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; background: #020617; }}
th, td {{ padding: 8px 10px; border-bottom: 1px solid #1f2937; text-align: left; }}
th {{ color: #93c5fd; }}
a {{ color: #67e8f9; margin-right: 16px; }}
.muted {{ color: #9ca3af; }}
</style>
</head>
<body>
<main>
<h1>SeeVar Next</h1>
<p class="muted">{html.escape(config.timezone)} | {config.latitude_deg:.4f}, {config.longitude_deg:.4f}</p>
<p><a href="/readiness.txt">readiness.txt</a><a href="/readiness.json">readiness.json</a><a href="/tonights_plan.json">plan.json</a><a href="/status.json">status.json</a></p>
<section>
<h2>Readiness</h2>
<pre>{html.escape(readiness)}</pre>
</section>
<section>
<h2>Tonight</h2>
<table><thead><tr><th>#</th><th>Target</th><th>Type</th><th>Window UTC</th><th>Max Alt</th></tr></thead><tbody>
{_target_rows(plan)}
</tbody></table>
</section>
<section>
<h2>Proof Status</h2>
<table><thead><tr><th>Target</th><th>Phase</th><th>Step</th><th>Status</th><th>Reason</th></tr></thead><tbody>
{_status_rows(status)}
</tbody></table>
</section>
</main>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    """Serve dashboard files."""

    config_path = Path("config/seevar-next.json")
    data_dir = Path("data")

    def do_GET(self) -> None:
        """Serve one GET request."""
        path = urlparse(self.path).path
        files = {
            "/readiness.txt": (self.data_dir / "readiness.txt", "text/plain"),
            "/readiness.json": (self.data_dir / "readiness.json", "application/json"),
            "/tonights_plan.json": (self.data_dir / "tonights_plan.json", "application/json"),
            "/status.json": (self.data_dir / "status.json", "application/json"),
        }
        if path in files:
            self._send_file(*files[path])
            return
        if path in {"/", "/index.html"}:
            self._send(200, "text/html", render_dashboard(self.config_path, self.data_dir).encode())
            return
        self._send(404, "text/plain", b"not found")

    def log_message(self, format: str, *args) -> None:
        """Keep service logs quiet."""

    def _send_file(self, path: Path, content_type: str) -> None:
        """Send one file."""
        if not path.exists():
            self._send(404, "text/plain", b"not available")
            return
        self._send(200, content_type, path.read_bytes())

    def _send(self, status: int, content_type: str, body: bytes) -> None:
        """Send one response."""
        self.send_response(status)
        self.send_header("content-type", f"{content_type}; charset=utf-8")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Serve SeeVar Next human dashboard.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config", type=Path, default=Path("config/seevar-next.json"))
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    DashboardHandler.config_path = args.config
    DashboardHandler.data_dir = args.data_dir
    server = ThreadingHTTPServer((args.host, args.port), DashboardHandler)
    print(f"SeeVar Next dashboard: http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
