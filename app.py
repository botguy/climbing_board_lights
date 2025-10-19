#!/home/admin/climbing_wall/.venv/bin/python

from flask import Flask, render_template, request, jsonify
import json
import os
from colorsys import hsv_to_rgb
from collections import OrderedDict

import neopixel
import board
from adafruit_led_animation.grid import PixelGrid

# Configuration constants
NUM_LEDS = 100
LED_PIN = board.D18
ROWS, COLS = 12, 7
STATE_COLORS = OrderedDict([
    ("off", (0, 0, 0)),
    ("hand", (0, 0, 255)),
    ("foot", (0, 255, 0)),
    ("start", (255, 0, 0)),
    ("end", (255, 215, 0)),
])

# setup LEDs
LED_ROWS = ROWS
LED_COLS = COLS + 1  # +1 since LEDS are on both sides of the holds
assert LED_ROWS*LED_COLS <= NUM_LEDS
led_strip = neopixel.NeoPixel(LED_PIN, NUM_LEDS, pixel_order=neopixel.RGB, auto_write=False)
led_grid = PixelGrid(led_strip, LED_ROWS, LED_COLS, reverse_x=True, reverse_y=True, orientation='VERTICAL')

app = Flask(__name__)

# Initialize grid
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

PROBLEM_FILE = "problems.json"
if os.path.exists(PROBLEM_FILE):
    with open(PROBLEM_FILE, "r") as f:
        problems = json.load(f)
else:
    problems = {}

@app.route("/")
def index():
    update_led_grid()
    return render_template("index.html.j2", grid=grid, states=list(STATE_COLORS.keys()), problems=list(problems.keys()))

@app.route("/set_cell", methods=["POST"])
def set_cell():
    data = request.json
    r, c = data["row"], data["col"]
    grid[r][c] = (grid[r][c] + 1) % len(STATE_COLORS)  # cycle state
    update_led_grid()
    return jsonify({"state": grid[r][c], "name": list(STATE_COLORS.keys())[grid[r][c]]})

@app.route("/save", methods=["POST"])
def save_problem():
    data = request.json
    name = data["name"]
    problems[name] = grid
    with open(PROBLEM_FILE, "w") as f:
        json.dump(problems, f, indent=2)
    return jsonify({"status": "saved", "problems": list(problems.keys())})

@app.route("/load", methods=["POST"])
def load_problem():
    data = request.json
    name = data["name"]
    if name in problems:
        global grid
        grid = problems[name]
        update_led_grid()
        return jsonify({"grid": grid})
    return jsonify({"error": "not found"}), 404

@app.route("/clear", methods=["POST"])
def clear_problem():
    global grid
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    update_led_grid()
    return jsonify({"grid": grid})

def update_led_grid():
    led_strip.fill((0, 0, 0))
    state_color_indexed = list(STATE_COLORS.values())
    for r, state_row in enumerate(grid):
        for c, state_idx in enumerate(state_row):
            led_grid[r][c] = state_color_indexed[state_idx]
    led_strip.show()

def diag_rainbow():
    ''' configures LEDs with a diagonal rainbow '''
    for r in range(LED_ROWS):
        for c in range(LED_COLS):
            hue = (r*LED_ROWS + c*LED_COLS) / (LED_ROWS**2 + LED_COLS**2)  # inner product with diag vector
            rgb = hsv_to_rgb(hue, 1, 1)
            led_grid[r][c] = [int(255*rgb_i) for rgb_i in rgb]
    led_strip.show()

if __name__ == "__main__":
    diag_rainbow()
    app.run(host="0.0.0.0", port=80, debug=True)
