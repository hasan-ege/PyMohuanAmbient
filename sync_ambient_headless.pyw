# MohuanLED / BJ_LED PC Ambient Sync (Headless Version)
# This script runs COMPLETELY INVISIBLY in the background.
# To stop it, you MUST use the Task Manager (find pythonw.exe).

import asyncio
import numpy as np
import mss
from bleak import BleakClient
import sys

# --- SETTINGS (CHANGE THIS) ---
MAC_ADDRESS = "FF:FF:11:3F:B4:44" # <-- PASTE YOUR MAC ADDRESS HERE
# --- END OF SETTINGS ---

# --- Constants ---
WRITE_UUID = "0000ee01-0000-1000-8000-00805f9b34fb" 
REFRESH_RATE_SECONDS = 0.1 

# --- PROTOCOL (ALGORITHM CONFIRMED) ---
MODE_ON = 0x7f  
MODE_OFF = 0xff 

def create_color_command(r, g, b):
    hex_command = f"69960502{r:02x}{g:02x}{b:02x}{MODE_ON:02x}"
    return bytes.fromhex(hex_command)

COMMAND_OFF = bytes([0x69, 0x96, 0x05, 0x02, 0x00, 0x00, 0x00, MODE_OFF])
# --- END OF PROTOCOL ---


async def main_loop():
    sct = mss.mss()
    monitor = sct.monitors[1]
    last_color_sent = (0, 0, 0) 

    # This outer loop ensures the script tries to reconnect if it fails
    while True: 
        try:
            async with BleakClient(MAC_ADDRESS) as client:
                # Connection successful, start the inner sync loop
                while True: 
                    try:
                        img = sct.grab(monitor)
                        frame = np.frombuffer(img.rgb, dtype=np.uint8).reshape(img.height, img.width, 3)
                        avg_color = np.mean(frame, axis=(0, 1))
                        r, g, b = avg_color.astype(int)
                        
                        new_color = (r, g, b)
                        
                        if abs(r - last_color_sent[0]) < 10 and \
                           abs(g - last_color_sent[1]) < 10 and \
                           abs(b - last_color_sent[2]) < 10:
                            await asyncio.sleep(REFRESH_RATE_SECONDS)
                            continue 
                        
                        command = create_color_command(r, g, b)
                        await client.write_gatt_char(WRITE_UUID, command, response=False)
                        last_color_sent = new_color
                        
                        await asyncio.sleep(REFRESH_RATE_SECONDS)
                    
                    except Exception as e_inner:
                        # Connection dropped, break to outer loop to reconnect
                        break 
            
        except Exception as e_outer:
            # Device not found, wait 5 seconds and retry
            await asyncio.sleep(5) 

if __name__ == "__main__":
    try:
        asyncio.run(main_loop())
    except Exception:
        # Silently exit if any major error occurs
        sys.exit(1)
