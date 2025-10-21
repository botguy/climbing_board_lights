#!/home/admin/climbing_wall/.venv/bin/python

from flask import Flask, render_template, request, jsonify
from ruamel.yaml import YAML
import os
from colorsys import hsv_to_rgb
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path

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
BOULDERS_FILE = "boulders.yml"
CONFIG_FILE = Path("config.yml")

yaml = YAML()
yaml.default_flow_style = None  # pretty prints 2d lists

# load config
if CONFIG_FILE.exists():
    with CONFIG_FILE.open('r') as f:
        config = yaml.load(f)
else:
    config = {
        'brightness': 0.8
    }

# setup LEDs
LED_ROWS = ROWS
LED_COLS = COLS + 1  # +1 since LEDS are on both sides of the holds
assert LED_ROWS*LED_COLS <= NUM_LEDS
led_strip = neopixel.NeoPixel(LED_PIN, NUM_LEDS, pixel_order=neopixel.RGB, auto_write=False, brightness=config['brightness'])
led_grid = PixelGrid(led_strip, LED_ROWS, LED_COLS, reverse_x=True, reverse_y=True, orientation='VERTICAL')

app = Flask(__name__)

# Initialize holds
holds = [[0 for _ in range(COLS)] for _ in range(ROWS)]

if os.path.exists(BOULDERS_FILE):
    with open(BOULDERS_FILE, "r") as f:
        boulders = yaml.load(f)
else:
    boulders = {}

@app.route("/")
def index():
    update_led_grid()
    return render_template("index.html.j2", holds=holds, states=list(STATE_COLORS.keys()), boulders=list(boulders.keys()), config=config)

@app.route("/set_cell", methods=["POST"])
def set_cell():
    data = request.json
    r, c = data["row"], data["col"]
    holds[r][c] = (holds[r][c] + 1) % len(STATE_COLORS)  # cycle state
    update_led_grid()
    return jsonify({"state": holds[r][c], "name": list(STATE_COLORS.keys())[holds[r][c]]})

@app.route("/save", methods=["POST"])
def save_boulder():
    data = request.json
    name = data["name"]
    difficulty = data["difficulty"]
    boulders[name] = {"difficulty": difficulty, "holds": deepcopy(holds)}
    with open(BOULDERS_FILE, "w") as f:
        yaml.dump(boulders, f)
    return jsonify({"status": "saved", "boulders": list(boulders.keys())})

@app.route("/load", methods=["POST"])
def load_boulder():
    data = request.json
    name = data["name"]
    if name in boulders:
        global holds
        holds = boulders[name]["holds"]
        update_led_grid()
        return jsonify({"holds": holds, "difficulty": boulders[name]["difficulty"]})
    return jsonify({"error": "not found"}), 404

@app.route("/clear", methods=["POST"])
def clear_boulder():
    global holds
    holds = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    update_led_grid()
    return jsonify({"holds": holds})

@app.route("/brightness", methods=["POST"])
def set_brightness():
    data = request.json
    led_strip.brightness = float(data["brightness"])
    led_strip.show()
    config['brightness'] = led_strip.brightness
    with CONFIG_FILE.open('w') as f:
        yaml.dump(config, f)
    return jsonify({'status': 'success'}), 200

def update_led_grid():
    led_strip.fill((0, 0, 0))
    state_color_indexed = list(STATE_COLORS.values())
    for r, state_row in enumerate(holds):
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
