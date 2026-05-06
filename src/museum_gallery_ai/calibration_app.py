from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


class CalibrationServer:
    def __init__(
        self,
        source: str | Path,
        output_config: str | Path,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self.source = Path(source)
        self.output_config = Path(output_config)
        self.host = host
        self.port = port
        self._frame_jpeg = self._extract_first_frame()

    def serve(self, open_browser: bool = True) -> None:
        server_state = {
            "frame_jpeg": self._frame_jpeg,
            "output_config": self.output_config,
        }

        class Handler(CalibrationRequestHandler):
            state = server_state

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        url = f"http://{self.host}:{self.port}"
        if open_browser:
            threading.Timer(0.5, lambda: webbrowser.open(url)).start()
        print(f"Calibration UI: {url}")
        print(f"Output config: {self.output_config}")
        print("Press Ctrl+C to stop the calibration server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nCalibration server stopped.")
        finally:
            server.server_close()

    def _extract_first_frame(self) -> bytes:
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("opencv-python is required for calibration. Install requirements-dev.txt.") from exc

        capture = cv2.VideoCapture(str(self.source))
        if not capture.isOpened():
            raise RuntimeError(f"Could not open video source: {self.source}")
        ok, frame = capture.read()
        capture.release()
        if not ok:
            raise RuntimeError(f"Could not read first frame from: {self.source}")
        ok, encoded = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92])
        if not ok:
            raise RuntimeError("Could not encode calibration frame.")
        return encoded.tobytes()


class CalibrationRequestHandler(BaseHTTPRequestHandler):
    state: dict

    def log_message(self, format: str, *args) -> None:
        return

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_bytes(CALIBRATION_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/frame.jpg":
            self._send_bytes(self.state["frame_jpeg"], "image/jpeg")
            return
        self.send_error(404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/save_config":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        config = build_pipeline_config(payload)
        output_config: Path = self.state["output_config"]
        output_config.parent.mkdir(parents=True, exist_ok=True)
        output_config.write_text(json.dumps(config, indent=2), encoding="utf-8")
        response = {"status": "ok", "path": str(output_config)}
        self._send_bytes(json.dumps(response).encode("utf-8"), "application/json")

    def _send_bytes(self, body: bytes, content_type: str) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def build_pipeline_config(payload: dict) -> dict:
    zones = []
    for index, zone in enumerate(payload.get("zones", []), start=1):
        points = zone.get("points", [])
        if len(points) < 3:
            continue
        zones.append(
            {
                "zone_id": zone.get("zone_id") or f"exhibit_{index}",
                "zone_type": zone.get("zone_type") or "exhibit",
                "name": zone.get("name") or f"Exhibit {index}",
                "points": [[int(x), int(y)] for x, y in points],
            }
        )

    lines = []
    for index, line in enumerate(payload.get("lines", []), start=1):
        start = line.get("start")
        end = line.get("end")
        if not start or not end:
            continue
        lines.append(
            {
                "line_id": line.get("line_id") or f"line_{index}",
                "line_type": line.get("line_type") or "entry",
                "name": line.get("name") or f"Line {index}",
                "start": [int(start[0]), int(start[1])],
                "end": [int(end[0]), int(end[1])],
                "direction": line.get("direction") or "any",
            }
        )

    return {
        "camera": {
            "camera_id": payload.get("camera_id") or "camera_1",
            "gallery_id": payload.get("gallery_id") or "gallery_1",
            "name": payload.get("camera_name") or "Calibrated Camera",
        },
        "detector": {
            "provider": "ultralytics",
            "model_name": "yolo11n.pt",
            "confidence_threshold": 0.18,
            "image_size": 1280,
            "tracker": "bytetrack.yaml",
            "device": "cpu",
        },
        "processing": {
            "max_frames": None,
            "frame_stride": 1,
            "dwell_confirm_seconds": 3.0,
            "lost_track_grace_seconds": 5.0,
            "congestion_threshold": 5,
            "congestion_min_seconds": 10.0,
        },
        "zones": zones,
        "lines": lines,
    }


CALIBRATION_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Museum Gallery AI Calibration</title>
  <style>
    body { margin: 0; font-family: Segoe UI, Arial, sans-serif; background: #10141d; color: #eef2ff; }
    header { padding: 14px 18px; background: #161d2b; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    button, input, select { border: 1px solid #3c4864; background: #202a3d; color: #eef2ff; padding: 8px 10px; border-radius: 6px; }
    button { cursor: pointer; }
    button.active { background: #2563eb; border-color: #60a5fa; }
    button.danger { background: #7f1d1d; }
    main { display: grid; grid-template-columns: minmax(0, 1fr) 320px; height: calc(100vh - 62px); }
    #stage { overflow: auto; padding: 12px; }
    #wrap { position: relative; display: inline-block; line-height: 0; }
    #frame { max-width: none; display: block; }
    #canvas { position: absolute; left: 0; top: 0; cursor: crosshair; }
    aside { border-left: 1px solid #2f3a55; padding: 14px; overflow: auto; background: #111827; }
    h1 { font-size: 18px; margin: 0 8px 0 0; }
    h2 { font-size: 15px; margin: 16px 0 8px; color: #facc15; }
    .hint { color: #aab6d3; font-size: 13px; }
    .item { padding: 8px; border: 1px solid #2f3a55; border-radius: 6px; margin: 8px 0; }
    .row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  </style>
</head>
<body>
<header>
  <h1>Calibration</h1>
  <button id="zoneBtn" class="active">Draw Exhibit Zone</button>
  <button id="lineBtn">Draw Entry Line</button>
  <button id="undoBtn">Undo Point</button>
  <button id="finishBtn">Finish Shape</button>
  <button id="clearBtn" class="danger">Clear All</button>
  <button id="saveBtn">Save Config</button>
  <span class="hint">Zone: click 3+ points, Finish Shape. Line: click 2 points.</span>
</header>
<main>
  <section id="stage">
    <div id="wrap">
      <img id="frame" src="/frame.jpg" alt="Calibration frame">
      <canvas id="canvas"></canvas>
    </div>
  </section>
  <aside>
    <div class="row">
      <label>Camera</label><input id="cameraId" value="camera_1">
      <label>Gallery</label><input id="galleryId" value="gallery_1">
    </div>
    <h2>Current Points</h2>
    <div id="pointList" class="hint">No points yet.</div>
    <h2>Zones</h2>
    <div id="zoneList"></div>
    <h2>Lines</h2>
    <div id="lineList"></div>
    <h2>Status</h2>
    <div id="status" class="hint">Ready.</div>
  </aside>
</main>
<script>
const img = document.getElementById("frame");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");
const state = { mode: "zone", current: [], zones: [], lines: [] };

img.addEventListener("load", () => {
  canvas.width = img.naturalWidth;
  canvas.height = img.naturalHeight;
  draw();
});

document.getElementById("zoneBtn").onclick = () => setMode("zone");
document.getElementById("lineBtn").onclick = () => setMode("line");
document.getElementById("undoBtn").onclick = () => { state.current.pop(); draw(); };
document.getElementById("clearBtn").onclick = () => {
  if (!confirm("Clear all zones and lines?")) return;
  state.current = []; state.zones = []; state.lines = []; draw();
};
document.getElementById("finishBtn").onclick = finishShape;
document.getElementById("saveBtn").onclick = saveConfig;

canvas.addEventListener("click", event => {
  const rect = canvas.getBoundingClientRect();
  const x = Math.round((event.clientX - rect.left) * (canvas.width / rect.width));
  const y = Math.round((event.clientY - rect.top) * (canvas.height / rect.height));
  state.current.push([x, y]);
  if (state.mode === "line" && state.current.length === 2) finishShape();
  draw();
});

function setMode(mode) {
  state.mode = mode;
  state.current = [];
  document.getElementById("zoneBtn").classList.toggle("active", mode === "zone");
  document.getElementById("lineBtn").classList.toggle("active", mode === "line");
  setStatus(mode === "zone" ? "Click 3+ points around an exhibit zone." : "Click 2 points for the entry line.");
  draw();
}

function finishShape() {
  if (state.mode === "zone") {
    if (state.current.length < 3) return alert("A zone needs at least 3 points.");
    const index = state.zones.length + 1;
    state.zones.push({ zone_id: `exhibit_${index}`, zone_type: "exhibit", name: `Exhibit ${index}`, points: state.current });
  } else {
    if (state.current.length !== 2) return alert("A line needs exactly 2 points.");
    const index = state.lines.length + 1;
    state.lines.push({ line_id: `entry_line_${index}`, line_type: "entry", name: `Entry Line ${index}`, start: state.current[0], end: state.current[1], direction: "any" });
  }
  state.current = [];
  draw();
}

async function saveConfig() {
  const payload = {
    camera_id: document.getElementById("cameraId").value || "camera_1",
    gallery_id: document.getElementById("galleryId").value || "gallery_1",
    zones: state.zones,
    lines: state.lines
  };
  const response = await fetch("/save_config", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload) });
  const result = await response.json();
  setStatus(result.status === "ok" ? `Saved: ${result.path}` : "Save failed.");
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const zone of state.zones) drawPolygon(zone.points, "#fb923c", true, zone.name);
  for (const line of state.lines) drawLine(line.start, line.end, "#38bdf8", line.name);
  if (state.mode === "zone" && state.current.length) drawPolygon(state.current, "#facc15", false, "current");
  if (state.mode === "line" && state.current.length) {
    drawPoints(state.current, "#facc15");
    if (state.current.length === 2) drawLine(state.current[0], state.current[1], "#facc15", "current");
  }
  renderLists();
}

function drawPolygon(points, color, closed, label) {
  ctx.strokeStyle = color; ctx.fillStyle = color + "22"; ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach(([x, y], i) => i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y));
  if (closed) { ctx.closePath(); ctx.fill(); }
  ctx.stroke();
  drawPoints(points, color);
  if (points[0]) drawText(label, points[0][0] + 6, points[0][1] - 8, color);
}

function drawLine(start, end, color, label) {
  ctx.strokeStyle = color; ctx.lineWidth = 4;
  ctx.beginPath(); ctx.moveTo(start[0], start[1]); ctx.lineTo(end[0], end[1]); ctx.stroke();
  drawPoints([start, end], color);
  drawText(label, start[0] + 6, start[1] - 8, color);
}

function drawPoints(points, color) {
  ctx.fillStyle = color;
  points.forEach(([x, y]) => ctx.fillRect(x - 4, y - 4, 8, 8));
}

function drawText(text, x, y, color) {
  ctx.font = "18px Segoe UI"; ctx.fillStyle = "#000"; ctx.fillText(text, x + 1, y + 1); ctx.fillStyle = color; ctx.fillText(text, x, y);
}

function renderLists() {
  document.getElementById("pointList").textContent = state.current.length ? JSON.stringify(state.current) : "No points yet.";
  document.getElementById("zoneList").innerHTML = state.zones.map(z => `<div class="item">${z.name}: ${z.points.length} points</div>`).join("") || "<div class='hint'>No zones yet.</div>";
  document.getElementById("lineList").innerHTML = state.lines.map(l => `<div class="item">${l.name}: ${JSON.stringify(l.start)} -> ${JSON.stringify(l.end)}</div>`).join("") || "<div class='hint'>No lines yet.</div>";
}

function setStatus(text) { document.getElementById("status").textContent = text; }
</script>
</body>
</html>
"""
