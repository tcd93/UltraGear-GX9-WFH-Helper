# Monitor Control for LG UltraGear GX9

## What it does

- Lets you use keyboard and mouse inputs without having to connect them to the monitor directly
- Lets you quickly switch the monitor between DisplayPort and USB-C input

## Why I built it

My setup is:

- Laptop connected through USB-C
- Personal PC connected through DisplayPort, peripherals connected to this PC

As the LG UltraGear GX9 line do not have an usb-b port, peripherals connected to the monitor only work with the laptop. This makes it awkward when I want the PC to be the "main" while still using the same keyboard and mouse. (I should've read the manual carefully before spending 1000$ lol - but anyways, WebOS does come with a very convenient API).

This project helps with that by letting me switch inputs and control the monitor from the PC side instead.

Site note: To complete this WFH set up, I also have Mouse Without Borders installed on both devices, so I can seamlessly move the mouse and keyboard between them.

## Tested monitor

This was tested on an LG 34GX90SA-W.

> Note: if you have multiple Smart LG GX90 on home network with SSDP enabled, the automatic discovery step may pick the wrong one.

## Settings you need to set up

The monitor must have this settings turned on (settings > support)

- SSDP discovery (should be turned off later after setting a fixed IP)
- Network IP Control

## Setup

1. Install Python 3 on Windows (should be >= 3.11).

2. Open a terminal in the project folder.

3. Create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

4. Install the required Python packages.

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Pair the monitor and create a local `.env` file.

   Run the helper script:

   ```powershell
   python generate_client_key.py
   ```

   This will try to connect to the monitor, prompt you to approve the pairing request on the TV, and then save the received client key to `.env`.

   If you prefer to set it manually, the file should look like this:

   ```text
   LG_MONITOR_CLIENT_KEY=your_key_here
   ```

   This file is ignored by Git.

6. After a first time run, you should also see a `cache.json` file created. This file is also ignored by Git, and contains the monitor's IP address. For best possible experience and to prevent all sorts of bugs, **I strongly recommend you use 5Ghz WIFI or LAN cable and set a static IP for the monitor in Settings > Wifi Icon**. You can set it to the same IP as in `cache.json`.

7. Run the scripts.

   ```powershell
   python hub.py HOME
   python toggle_input.py
   ```

## How I use it

I use macro commands in Razer Synapse to run these scripts.

```powershell
C:\Scripts\Monitor\.venv\Scripts\pythonw.exe C:\Scripts\Monitor\hub.py HOME
C:\Scripts\Monitor\.venv\Scripts\pythonw.exe C:\Scripts\Monitor\toggle_input.py
```

If you do not use Razer, you can set up a keyboard button, shortcut, or macro in whatever tool (Autohotkey, PowerToys) you use to run the same commands.
