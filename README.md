# Installation

Install required packages
```
sudo apt install git
sudo apt install python3-dev
```

Setup virtual environment
```
python -m venv .venv
./.venv/bin/pip install flask rpi_ws281x adafruit-circuitpython-neopixel adafruit-circuitpython-led-animation ruamel.yaml numpy
```

# Run

Start the board app
```
sudo ./app.py
```

To access the web interface, go to `climbingwall.local` in a web browser


# Hardware

- Raspberry Pi Zero 2W
- 3.3v to 5v level converter
- LED strings
- 12v power supply
- Misc wiring and connectors


# Development tips

Image the SD card using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) with headless mode using **Raspberry Pi OS Lite (64 bit)**.

Vscode can be used in remote connection mode. **DO NOT** enable the python extension. It crashes the PI.

To skip typing the password into vscode everytime when connecting to the raspberry pi, generate a SSH key in windows using `ssh-keygen`, then copy the public key in `C:\Users\YourUsername\.ssh\*.pub` into `~/.ssh/authorized_keys`.
