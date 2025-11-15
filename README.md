# PC Screen Sync for MohuanLED / BJ_LED (Ambient Light)

This project is a Python script that provides ambient lighting (screen synchronization) for cheap, unbranded Bluetooth LE LED bulbs that use the **MohuanLED** or **BJ_LED** mobile app (commonly found on Temu, AliExpress, etc.).

It reads the average color of your PC screen in real-time and sends that color directly to the bulb, including all intermediate colors (orange, purple, etc.).



## The Protocol (The "EVLAT" Discovery)

These bulbs do not use a standard protocol and cannot be controlled by Windows out of the box. This script is the result of a long reverse-engineering process (dubbed the "EVLAT YAPIYORUZ" series) involving `btsnoop_hci.log` analysis with Wireshark.

After many tests, we discovered the specific algorithm this hardware revision uses:

* **Protocol Header:** `69960502`
* **Write Characteristic UUID:** `0000ee01-0000-1000-8000-00805f9b34fb`
* **Algorithm:** `69960502` + `[R_BYTE]` + `[G_BYTE]` + `[B_BYTE]` + `[MODE_BYTE]`
* **ON Mode (with Full Brightness):** `0x7f` (Confirmed by our "Red" and "Yellow" tests)
* **OFF Mode:** `0xff` (Confirmed by our "EVLAT 3" test)

This repository implements this algorithm to talk directly to the bulb.

---

## 🚀 Installation

### 1. Find Your Bulb's MAC Address

The script needs to know which device to connect to.

1.  Make sure your bulb is plugged in.
2.  **Crucially, turn OFF your phone's Bluetooth.** The bulb cannot be connected to your phone and the PC at the same time.
3.  Install the `bleak` library: `pip install bleak`
4.  Run the `find_my_led.py` script included in this repository:
    ```bash
    python find_my_led.py
    ```
5.  Look for a device named `BJ_LED` or `MohuanLED` and copy its MAC address (e.g., `FF:FF:11:3F:B4:44`).

### 2. Install All Dependencies

Install all the required Python libraries using the `requirements.txt` file:

```bash
pip install -r requirements.txt
