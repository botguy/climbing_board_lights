#!/home/admin/climbing_wall/.venv/bin/python

from flask import Flask, render_template, request, jsonify
from ruamel.yaml import YAML
import os
from colorsys import hsv_to_rgb
from collections import OrderedDict
from copy import deepcopy

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
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Initialize grid
grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]

BOULDERS_FILE = "boulders.yml"
yaml = YAML()
yaml.default_flow_style = None  # pretty prints 2d lists
if os.path.exists(BOULDERS_FILE):
    with open(BOULDERS_FILE, "r") as f:
        boulders = yaml.load(f)
else:
    boulders = {}

@app.route("/")
def index():
    update_led_grid()
    return render_template("index.html.j2", grid=grid, states=list(STATE_COLORS.keys()), boulders=list(boulders.keys()))

@app.route("/set_cell", methods=["POST"])
def set_cell():
    data = request.json
    r, c = data["row"], data["col"]
    grid[r][c] = (grid[r][c] + 1) % len(STATE_COLORS)  # cycle state
    update_led_grid()
    return jsonify({"state": grid[r][c], "name": list(STATE_COLORS.keys())[grid[r][c]]})

@app.route("/save", methods=["POST"])
def save_boulder():
    data = request.json
    name = data["name"]
    difficulty = data["difficulty"]
    boulders[name] = {"difficulty": difficulty, "holds": deepcopy(grid)}
    with open(BOULDERS_FILE, "w") as f:
        yaml.dump(boulders, f)
    return jsonify({"status": "saved", "boulders": list(boulders.keys())})

@app.route("/load", methods=["POST"])
def load_boulder():
    data = request.json
    name = data["name"]
    if name in boulders:
        global grid
        grid = boulders[name]["holds"]
        update_led_grid()
        return jsonify({"grid": grid, "difficulty": boulders[name]["difficulty"]})
    return jsonify({"error": "not found"}), 404

@app.route("/clear", methods=["POST"])
def clear_boulder():
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
