# Installation

1. Image the SD card using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/) with headless mode using **Raspberry Pi OS Lite (64 bit)**. Name the device `climbingwall.local` and note the username and password.

2. Install required packages
```
sudo apt install git
sudo apt install python3-dev
```

3. Checkout this project `git clone https://github.com/botguy/climbing_board_lights.git`

4. Setup virtual environment in the checkout directory
```
python -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

5. Automatically start the board app by calling `sudo crontab -e` and adding this line:
```
@reboot cd <checkout directory>; sudo ./app.py >> log.txt 2>&1
```

# Usage

To access the web interface, go to `climbingwall.local` in a web browser.


# Hardware

- Raspberry Pi Zero 2W
- 3.3v to 5v level converter
- LED strings
- 12v power supply
- Misc wiring and connectors


# Development tips

VsCode can be used in remote connection mode. **DO NOT** enable the python extension. It crashes the Pi.

To skip typing the password into vscode everytime when connecting to the raspberry pi, generate a SSH key in windows using `ssh-keygen`, then copy the public key in `C:\Users\YourUsername\.ssh\*.pub` into `~/.ssh/authorized_keys`.
