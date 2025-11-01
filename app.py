#!/home/admin/climbing_wall/.venv/bin/python

from flask import Flask, render_template, request, jsonify
from ruamel.yaml import YAML
import os
from colorsys import hsv_to_rgb
from collections import OrderedDict
from copy import deepcopy
from pathlib import Path
import numpy as np

import neopixel
import board
from adafruit_led_animation.grid import PixelGrid

def hsv(h, s, v) -> np.array:
    ''' converts floats h,s,v [0, 1] to ints r,g,b [0, 255] '''
    rgb_floats = np.array(hsv_to_rgb(h, s, v))
    return np.minimum(256*rgb_floats, 255).astype(int)

# Configuration constants
NUM_LEDS = 100
LED_PIN = board.D18
ROWS, COLS = 12, 7
OFFSET_BRIGHTNESS = 0.25
HOLD_BRIGHTNESS = 0.5
HOLD_COLORS = OrderedDict([
    ("off", hsv(0, 0, 0)),
    ("hand", hsv(3/6, 1, HOLD_BRIGHTNESS)),
    ("start_end", hsv(0/6, 1, HOLD_BRIGHTNESS)),
])
ROW_OFFSET_COLORS = (
    (0, hsv(1/6, 1, OFFSET_BRIGHTNESS)),
    (-1, hsv(4/6, 1, OFFSET_BRIGHTNESS)),
)
COL_OFFSET_COLORS = (
    (0, hsv(2/6, 1, OFFSET_BRIGHTNESS)),
    (-1, hsv(5/6, 1, OFFSET_BRIGHTNESS)),
)
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
hold_idxs = [[0 for _ in range(COLS)] for _ in range(ROWS)]

if os.path.exists(BOULDERS_FILE):
    with open(BOULDERS_FILE, "r") as f:
        boulders = yaml.load(f)
else:
    boulders = {}

@app.route("/")
def index():
    update_led_grid()
    return render_template("index.html.j2", initial_hold_idxs=hold_idxs, hold_colors=HOLD_COLORS, initial_boulders=boulders, config=config)

@app.route("/set_hold", methods=["POST"])
def set_hold():
    data = request.json
    r, c = data["row"], data["col"]
    hold_idxs[r][c] = (hold_idxs[r][c] + 1) % len(HOLD_COLORS)  # cycle hold_idx
    update_led_grid()
    return jsonify({"hold_idx": hold_idxs[r][c], "hold_type": list(HOLD_COLORS.keys())[hold_idxs[r][c]]})

@app.route("/save", methods=["POST"])
def save_boulder():
    data = request.json
    name = data["name"]
    difficulty = data["difficulty"]
    boulders[name] = {"difficulty": difficulty, "hold_idxs": deepcopy(hold_idxs)}
    with open(BOULDERS_FILE, "w") as f:
        yaml.dump(boulders, f)
    return jsonify({"status": "saved", "boulders": {name: data["difficulty"] for name, data in boulders.items()} })

@app.route("/load", methods=["POST"])
def load_boulder():
    data = request.json
    name = data["name"]
    if name in boulders:
        global hold_idxs
        hold_idxs = boulders[name]["hold_idxs"]
        update_led_grid()
        return jsonify({"hold_idxs": hold_idxs, "difficulty": boulders[name]["difficulty"]})
    return jsonify({"error": "not found"}), 404

@app.route("/clear", methods=["POST"])
def clear_boulder():
    global hold_idxs
    hold_idxs = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    update_led_grid()
    return jsonify({"hold_idxs": hold_idxs})

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
    hold_type_color_indexed = tuple(HOLD_COLORS.items())
    for led_r in range(LED_ROWS):
        for led_c in range(LED_COLS):
            # Set LED to the average of the adjacent holds
            adjacent_hold_colors = []
            for r_offset, r_color in ROW_OFFSET_COLORS:
                for c_offset, c_color in COL_OFFSET_COLORS:
                    hold_r = led_r + r_offset
                    hold_c = led_c + c_offset
                    if 0 <= hold_r < ROWS and 0 <= hold_c < COLS:
                        hold_type, hold_color = hold_type_color_indexed[hold_idxs[hold_r][hold_c]]
                        if hold_type != 'off':
                            adjacent_hold_colors.append(hold_color + r_color + c_color)
            if adjacent_hold_colors:
                # average and limit to allowable range
                led_grid[led_r][led_c] = np.clip(np.average(adjacent_hold_colors, axis=0).astype(int) , 0, 255)
                # app.logger.debug(f'led[{led_r}, {led_c}] = {led_grid[led_r][led_c]} . adjacent_hold_colors = {adjacent_hold_colors}')
            else:
                led_grid[led_r][led_c] = HOLD_COLORS['off']
    led_strip.show()


def diag_rainbow():
    ''' configures LEDs with a diagonal rainbow '''
    for r in range(LED_ROWS):
        for c in range(LED_COLS):
            hue = (r*LED_ROWS + c*LED_COLS) / (LED_ROWS**2 + LED_COLS**2)  # inner product with diag vector
            led_grid[r][c] = hsv(hue, 1, 1)
    led_strip.show()


if __name__ == "__main__":
    diag_rainbow()
    app.run(host="0.0.0.0", port=80, debug=True)
