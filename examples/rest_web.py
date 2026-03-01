import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask, request, jsonify, render_template_string
from HatchBaby import Rest, RestSongs

app = Flask(__name__)
device = None

SONGS = [
    {"id": s.value, "name": s.name.replace("_", " ").title()}
    for s in RestSongs
]


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, songs=SONGS)


@app.route("/connect", methods=["POST"])
def connect():
    global device
    data = request.get_json()
    mac = data.get("mac", "").strip()
    if not mac:
        return jsonify(error="MAC address required"), 400
    try:
        device = Rest(mac, connect=True)
        return _status_json()
    except Exception as e:
        device = None
        return jsonify(error=str(e)), 500


@app.route("/disconnect", methods=["POST"])
def disconnect():
    global device
    device = None
    return jsonify(ok=True)


@app.route("/status")
def status():
    if device is None:
        return jsonify(error="Not connected"), 400
    try:
        device.update_status()
        return _status_json()
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/power", methods=["POST"])
def power():
    if device is None:
        return jsonify(error="Not connected"), 400
    data = request.get_json()
    try:
        device.set_powered(data.get("on", True))
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/volume", methods=["POST"])
def volume():
    if device is None:
        return jsonify(error="Not connected"), 400
    data = request.get_json()
    try:
        device.set_volume(int(data["volume"]))
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/song", methods=["POST"])
def song():
    if device is None:
        return jsonify(error="Not connected"), 400
    data = request.get_json()
    try:
        device.set_song(int(data["song"]))
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/color", methods=["POST"])
def color():
    if device is None:
        return jsonify(error="Not connected"), 400
    data = request.get_json()
    try:
        device.set_color(
            int(data["r"]),
            int(data["g"]),
            int(data["b"]),
            int(data.get("brightness", 255)),
        )
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route("/color/rainbow", methods=["POST"])
def color_rainbow():
    if device is None:
        return jsonify(error="Not connected"), 400
    data = request.get_json() or {}
    try:
        device.set_color_rainbow(int(data.get("brightness", 255)))
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(error=str(e)), 500


def _status_json():
    return jsonify(
        power=device._power,
        volume=device._volume,
        song=device._song,
        red=device._red,
        green=device._green,
        blue=device._blue,
        brightness=device._brightness,
    )


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hatch Rest Control Panel</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1a1a2e; color: #e0e0e0; min-height: 100vh;
    display: flex; justify-content: center; padding: 20px;
  }
  .container { max-width: 480px; width: 100%; }
  h1 { text-align: center; margin-bottom: 24px; color: #a78bfa; font-size: 1.5rem; }
  .card {
    background: #16213e; border-radius: 12px; padding: 20px;
    margin-bottom: 16px; border: 1px solid #0f3460;
  }
  .card h2 { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #7c83ff; margin-bottom: 12px; }
  label { font-size: 0.85rem; color: #aaa; }
  input[type="text"] {
    width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #0f3460;
    background: #0a0a23; color: #e0e0e0; font-size: 1rem; margin-top: 4px;
  }
  button {
    padding: 10px 18px; border: none; border-radius: 8px; cursor: pointer;
    font-size: 0.9rem; font-weight: 600; transition: opacity 0.15s;
  }
  button:hover { opacity: 0.85; }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-primary { background: #7c83ff; color: #fff; }
  .btn-danger { background: #e74c6f; color: #fff; }
  .btn-success { background: #10b981; color: #fff; }
  .btn-muted { background: #2a2a4a; color: #ccc; border: 1px solid #3a3a5a; }
  .btn-rainbow {
    background: linear-gradient(90deg, #f00, #ff0, #0f0, #0ff, #00f, #f0f, #f00);
    color: #000; font-weight: 700;
  }
  .row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .power-row { display: flex; gap: 8px; }
  .power-row button { flex: 1; padding: 14px; font-size: 1rem; }

  .songs-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  .songs-grid button {
    padding: 12px 6px; font-size: 0.8rem; background: #2a2a4a;
    color: #ccc; border: 2px solid transparent; border-radius: 8px;
  }
  .songs-grid button.active { border-color: #7c83ff; color: #fff; background: #3a3a6a; }

  .slider-group { margin-top: 8px; }
  .slider-group input[type="range"] { width: 100%; accent-color: #7c83ff; }
  .slider-label { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px; }

  .color-row { display: flex; align-items: center; gap: 12px; margin-top: 8px; }
  .color-row input[type="color"] {
    width: 60px; height: 40px; border: none; border-radius: 8px;
    cursor: pointer; background: none;
  }

  .status-bar {
    text-align: center; font-size: 0.8rem; color: #666; padding: 8px;
  }
  .status-bar.connected { color: #10b981; }
  .status-bar.error { color: #e74c6f; }

  .overlay {
    display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5);
    justify-content: center; align-items: center; z-index: 10;
  }
  .overlay.show { display: flex; }
  .overlay .spinner {
    width: 40px; height: 40px; border: 4px solid #333;
    border-top-color: #7c83ff; border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
  <h1>Hatch Rest Control</h1>

  <!-- Connection -->
  <div class="card">
    <h2>Connection</h2>
    <label>MAC Address</label>
    <input type="text" id="mac" placeholder="AA:BB:CC:DD:EE:FF" value="">
    <div class="row">
      <button class="btn-primary" id="connectBtn" onclick="doConnect()">Connect</button>
      <button class="btn-danger" id="disconnectBtn" onclick="doDisconnect()" disabled>Disconnect</button>
    </div>
    <div id="statusBar" class="status-bar">Not connected</div>
  </div>

  <!-- Controls (hidden until connected) -->
  <div id="controls" style="display:none;">

    <!-- Power -->
    <div class="card">
      <h2>Power</h2>
      <div class="power-row">
        <button class="btn-success" onclick="setPower(true)">On</button>
        <button class="btn-danger" onclick="setPower(false)">Off</button>
      </div>
    </div>

    <!-- Sounds -->
    <div class="card">
      <h2>Sounds</h2>
      <div class="songs-grid" id="songsGrid">
        {% for s in songs %}
        <button data-song="{{ s.id }}" onclick="setSong({{ s.id }})">{{ s.name }}</button>
        {% endfor %}
      </div>
    </div>

    <!-- Volume -->
    <div class="card">
      <h2>Volume</h2>
      <div class="slider-group">
        <div class="slider-label"><span>Volume</span><span id="volLabel">128</span></div>
        <input type="range" id="volSlider" min="0" max="255" value="128"
               oninput="document.getElementById('volLabel').textContent=this.value"
               onchange="setVolume(this.value)">
      </div>
    </div>

    <!-- Color -->
    <div class="card">
      <h2>Light</h2>
      <div class="color-row">
        <input type="color" id="colorPicker" value="#6644ff" onchange="sendColor()">
        <button class="btn-rainbow" onclick="setRainbow()">Rainbow</button>
      </div>
      <div class="slider-group" style="margin-top:12px;">
        <div class="slider-label"><span>Brightness</span><span id="brightLabel">255</span></div>
        <input type="range" id="brightSlider" min="0" max="255" value="255"
               oninput="document.getElementById('brightLabel').textContent=this.value"
               onchange="sendColor()">
      </div>
    </div>

  </div>
</div>

<div class="overlay" id="overlay"><div class="spinner"></div></div>

<script>
const $ = id => document.getElementById(id);
let connected = false;

function showLoading(on) { $('overlay').classList.toggle('show', on); }

async function api(path, method='POST', body=null) {
  showLoading(true);
  try {
    const opts = { method, headers: {'Content-Type':'application/json'} };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  } catch(e) {
    $('statusBar').textContent = e.message;
    $('statusBar').className = 'status-bar error';
    throw e;
  } finally {
    showLoading(false);
  }
}

async function doConnect() {
  const mac = $('mac').value.trim();
  if (!mac) return alert('Enter a MAC address');
  const data = await api('/connect', 'POST', { mac });
  connected = true;
  $('connectBtn').disabled = true;
  $('disconnectBtn').disabled = false;
  $('controls').style.display = '';
  $('statusBar').textContent = 'Connected';
  $('statusBar').className = 'status-bar connected';
  applyStatus(data);
}

async function doDisconnect() {
  await api('/disconnect');
  connected = false;
  $('connectBtn').disabled = false;
  $('disconnectBtn').disabled = true;
  $('controls').style.display = 'none';
  $('statusBar').textContent = 'Disconnected';
  $('statusBar').className = 'status-bar';
}

function applyStatus(data) {
  if (data.volume != null) {
    $('volSlider').value = data.volume;
    $('volLabel').textContent = data.volume;
  }
  if (data.brightness != null) {
    $('brightSlider').value = data.brightness;
    $('brightLabel').textContent = data.brightness;
  }
  if (data.red != null) {
    const hex = '#' + [data.red, data.green, data.blue].map(v => v.toString(16).padStart(2,'0')).join('');
    $('colorPicker').value = hex;
  }
  if (data.song != null) {
    document.querySelectorAll('.songs-grid button').forEach(b => {
      b.classList.toggle('active', parseInt(b.dataset.song) === data.song);
    });
  }
}

async function setPower(on) { await api('/power', 'POST', { on }); }

async function setSong(id) {
  await api('/song', 'POST', { song: id });
  document.querySelectorAll('.songs-grid button').forEach(b => {
    b.classList.toggle('active', parseInt(b.dataset.song) === id);
  });
}

async function setVolume(v) { await api('/volume', 'POST', { volume: parseInt(v) }); }

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return { r: (n>>16)&255, g: (n>>8)&255, b: n&255 };
}

async function sendColor() {
  const rgb = hexToRgb($('colorPicker').value);
  const brightness = parseInt($('brightSlider').value);
  await api('/color', 'POST', { ...rgb, brightness });
}

async function setRainbow() {
  const brightness = parseInt($('brightSlider').value);
  await api('/color/rainbow', 'POST', { brightness });
}
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
