import asyncio
from bleak import BleakScanner

async def run():
    print("Scanning for Bluetooth devices for 10 seconds...")
    print("Ensure your bulb is plugged in and NOT connected to your phone.")
    
    devices = await BleakScanner.discover(timeout=10.0)
    
    found = False
    for device in devices:
        if device.name and ("LED" in device.name.upper() or "BJ" in device.name.upper()):
            print("-" * 40)
            print(f">>> POTENTIAL BULB FOUND! <<<")
            print(f"    Name: {device.name}")
            print(f"    MAC Address: {device.address}")
            print("Please copy this MAC Address into the sync script.")
            print("-" * 40)
            found = True
    
    if not found:
        print("\nNo 'LED' or 'BJ' devices found. Here is a list of all devices found:")
        for device in devices:
            print(f"    Name: {device.name} (Address: {device.address})")

if __name__ == "__main__":
    asyncio.run(run())
