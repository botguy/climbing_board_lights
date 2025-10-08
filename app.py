#!/home/admin/climbing_wall/.venv/bin/python

from flask import Flask, render_template, request, jsonify
import json
import os

import neopixel
import board

# Configuration constants
NUM_LEDS = 100
LED_PIN = board.D18
ROWS, COLS = 12, 7
STATE_NAMES = ["off", "hand", "foot", "start", "end"]

assert ROWS*COLS <= NUM_LEDS
led = neopixel.NeoPixel(LED_PIN, NUM_LEDS, pixel_order=neopixel.RGB)
app = Flask(__name__)

# Initialize grid
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

PATTERN_FILE = "patterns.json"
if os.path.exists(PATTERN_FILE):
    with open(PATTERN_FILE, "r") as f:
        patterns = json.load(f)
else:
    patterns = {}

@app.route("/")
def index():
    return render_template("index.html", grid=grid, states=STATE_NAMES, patterns=list(patterns.keys()))

@app.route("/set_cell", methods=["POST"])
def set_cell():
    data = request.json
    r, c = data["row"], data["col"]
    grid[r][c] = (grid[r][c] + 1) % len(STATE_NAMES)  # cycle state
    return jsonify({"state": grid[r][c], "name": STATE_NAMES[grid[r][c]]})

@app.route("/save", methods=["POST"])
def save_pattern():
    data = request.json
    name = data["name"]
    patterns[name] = grid
    with open(PATTERN_FILE, "w") as f:
        json.dump(patterns, f, indent=2)
    return jsonify({"status": "saved", "patterns": list(patterns.keys())})

@app.route("/load", methods=["POST"])
def load_pattern():
    data = request.json
    name = data["name"]
    if name in patterns:
        global grid
        grid = patterns[name]
        return jsonify({"grid": grid})
    return jsonify({"error": "not found"}), 404

if __name__ == "__main__":
    led[0] = (255, 255, 255)
    app.run(host="0.0.0.0", port=80, debug=True)
