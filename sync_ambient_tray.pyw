# MohuanLED / BJ_LED PC Ambient Sync (System Tray Version)
# This script syncs the bulb to the PC screen's average color.
# It runs in the system tray with an exit button.

import asyncio
import numpy as np
import mss
from bleak import BleakClient
import threading
import pystray
from PIL import Image, ImageDraw
import sys

# --- SETTINGS (CHANGE THIS) ---
MAC_ADDRESS = "FF:FF:11:3F:B4:44" # <-- PASTE YOUR MAC ADDRESS HERE
# --- END OF SETTINGS ---

# --- Constants ---
WRITE_UUID = "0000ee01-0000-1000-8000-00805f9b34fb" 
REFRESH_RATE_SECONDS = 0.1 

# --- PROTOCOL (ALGORITHM CONFIRMED) ---
# Command: 69960502 + [R] + [G] + [B] + [MOD]
MODE_ON = 0x7f  # Confirmed "ON" mode (from Red/Yellow tests)
MODE_OFF = 0xff # Confirmed "OFF" mode (from "EVLAT 3" test)

def create_color_command(r, g, b):
    """Converts (R, G, B) values into the bulb's protocol."""
    hex_command = f"69960502{r:02x}{g:02x}{b:02x}{MODE_ON:02x}"
    return bytes.fromhex(hex_command)

# Static command to turn off the bulb
COMMAND_OFF = bytes([0x69, 0x96, 0x05, 0x02, 0x00, 0x00, 0x00, MODE_OFF])
# --- END OF PROTOCOL ---


# --- Main Async Sync Loop ---
async def sync_loop(stop_event):
    """The main function that connects and sends color data."""
    sct = mss.mss()
    monitor = sct.monitors[1]
    last_color_sent = (0, 0, 0) 

    while not stop_event.is_set(): # Loop until the "Exit" button is clicked
        try:
            # print(f"Async loop: Attempting connection to {MAC_ADDRESS}...")
            async with BleakClient(MAC_ADDRESS) as client:
                # print("Async loop: Connection successful! Starting sync (Real Average Mode)...")
                
                while not stop_event.is_set():
                    try:
                        # 1. Capture Screen
                        img = sct.grab(monitor)
                        
                        # 2. Calculate Average Color
                        frame = np.frombuffer(img.rgb, dtype=np.uint8).reshape(img.height, img.width, 3)
                        avg_color = np.mean(frame, axis=(0, 1))
                        r, g, b = avg_color.astype(int)
                        
                        new_color = (r, g, b)
                        
                        # 3. Check if color change is significant (prevents flickering)
                        if abs(r - last_color_sent[0]) < 10 and \
                           abs(g - last_color_sent[1]) < 10 and \
                           abs(b - last_color_sent[2]) < 10:
                            await asyncio.sleep(REFRESH_RATE_SECONDS)
                            continue 
                        
                        # 4. Send the new color command
                        command = create_color_command(r, g, b)
                        await client.write_gatt_char(WRITE_UUID, command, response=False)
                        last_color_sent = new_color
                        
                        await asyncio.sleep(REFRESH_RATE_SECONDS)
                    
                    except Exception as e_inner:
                        # Error inside the loop (e.g., connection dropped)
                        # print(f"Inner loop error: {e_inner}. Reconnecting...")
                        break # Break to the outer loop to reconnect
            
        except Exception as e_outer:
            # Error in the outer loop (e.g., device not found)
            # print(f"Connection error: {e_outer}. Retrying in 5 seconds...")
            if stop_event.is_set(): # If user clicked Exit during wait
                break
            await asyncio.sleep(5) 

    # --- Loop has been stopped ---
    # print("Async loop: Stop signal received. Turning bulb off...")
    try:
        # Try one last time to connect and send the OFF command
        async with BleakClient(MAC_ADDRESS, timeout=5.0) as client:
            await client.write_gatt_char(WRITE_UUID, COMMAND_OFF, response=False)
            # print("Bulb turned off.")
    except Exception as e:
        # print(f"Could not send OFF command (maybe already disconnected): {e}")
        pass # Silently fail
    finally:
        # print("Async loop: Terminated.")
        pass

# --- System Tray Icon Management ---

def create_tray_image():
    """Create a simple blue circle icon for the tray."""
    image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.ellipse([(4, 4), (60, 60)], fill=(0, 150, 255, 200), outline=(255, 255, 255, 255))
    return image

def on_exit_clicked(icon, item, stop_event, loop):
    """Callback function when 'Exit' is clicked."""
    # print("System Tray: Exit clicked.")
    
    # 1. Signal the async loop to stop
    stop_event.set()
    
    # 2. Stop the system tray icon
    icon.stop()
    
    # 3. Stop the asyncio event loop from its thread
    loop.call_soon_threadsafe(loop.stop)

def run_tray_icon(stop_event, loop):
    """Runs the system tray icon (this blocks the main thread)."""
    icon_image = create_tray_image()
    menu = (
        pystray.MenuItem(
            'Exit (MohuanLED Sync)',
            lambda icon, item: on_exit_clicked(icon, item, stop_event, loop)
        ),
    )
    icon = pystray.Icon("led_sync", icon_image, "MohuanLED PC Sync", menu)
    
    # print("System Tray: Running icon...")
    icon.run()

def start_asyncio_thread(loop, stop_event):
    """Starts the asyncio event loop in a separate thread."""
    asyncio.set_event_loop(loop)
    # Run our main sync_loop until it's stopped
    loop.run_until_complete(sync_loop(stop_event))


if __name__ == "__main__":
    # 1. Create a "stop" event to communicate between threads
    stop_event = threading.Event()
    
    # 2. Create a new asyncio loop for the background thread
    asyncio_loop = asyncio.new_event_loop()
    
    # 3. Start the background thread (runs the Bluetooth sync_loop)
    sync_thread = threading.Thread(
        target=start_asyncio_thread,
        args=(asyncio_loop, stop_event),
        daemon=True # Exit thread if main program crashes
    )
    sync_thread.start()
    
    # 4. Run the system tray icon in the main thread
    # This keeps the script alive until 'Exit' is clicked.
    run_tray_icon(stop_event, asyncio_loop)
    
    # 5. Clean up the thread
    sync_thread.join()
    sys.exit(0)
