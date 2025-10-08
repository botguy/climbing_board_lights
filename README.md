# Installation

Install required packages
```
sudo apt install git
sudo apt install python3-dev
```

Setup virtual environment
```
python -m venv .venv
./.venv/bin/pip install flask rpi_ws281x adafruit-circuitpython-neopixel adafruit-circuitpython-led-animation
```

# Run

Start the board app
```
sudo ./app.py
```

To access the web interface, go to `climbingwall.local` in a web browser
