# Installation

Install required packages
```
sudo apt install git
sudo apt install python3-dev
```

Setup virtual environment
```
python -m venv .venv
./.venv/bin/pip install flask rpi_ws281x adafruit-circuitpython-neopixel
```

# Run

Start the board app
```
sudo ./app.py
```