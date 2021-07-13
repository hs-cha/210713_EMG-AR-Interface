import logging
import asyncio

from bleak import BleakClient
from bleak import _logger as logger

from math import floor
import time

# address = "F0:51:A2:3B:C0:BB"
# address = "E6:49:2D:51:BC:52"
# address = "DC:F9:AE:A1:D5:44"
# address = "E5:E4:D5:41:85:AB"
# address = "F8:03:50:45:B0:9D"
# address = "D5:3D:65:28:D0:BC"
address = "CF:79:7B:31:60:BB"

char_uuid_mpu = '0000a3a5-0000-1000-8000-00805f9b34fb'

initial_time = 0
totalBytesReceived = 0
currentBytesReceived = 0


def current_milli_time():
    return floor(time.time() * 1000)


def notification_handler(sender, data):
    global totalBytesReceived, initial_time, currentBytesReceived
    totalBytesReceived += len(data)
    currentBytesReceived += len(data)
    elapsed_time = current_milli_time() - initial_time
    if elapsed_time > 4999:
        # calculate throughput and reset
        throughput = float(currentBytesReceived) / 5.0
        print("Throughput: %s bytes/s" % throughput)
        initial_time = current_milli_time()
        currentBytesReceived = 0


async def run(_address, debug=False):
    global initial_time
    if debug:
        import sys
        l = logging.getLogger("asyncio")
        l.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        l.addHandler(h)
        logger.addHandler(h)

    async with BleakClient(_address) as client:
        x = await client.is_connected()
        logger.info("Connected: {0}".format(x))

        # Read 0xEEFF:
        # Start timer:
        if initial_time == 0:
            initial_time = current_milli_time()

        await client.start_notify(char_uuid_mpu, notification_handler)
        await asyncio.sleep(30.0)  # record for x seconds
        await client.stop_notify(char_uuid_mpu)


loop = asyncio.get_event_loop()
# loop.set_debug(True)
loop.run_until_complete(run(address, False))
