import logging
import asyncio
import numpy as np

from bleak import BleakClient
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from bleak import _logger as logger

from datetime import datetime
from math import floor
import time

address = 'F8:CB:DB:27:E5:C1'
# address = 'D0:32:5F:9E:9D:81'
char_uuid1 = "0000eef1-0000-1000-8000-00805f9b34fb"
char_uuid2 = "0000eef2-0000-1000-8000-00805f9b34fb"
char_uuid3 = "0000eef3-0000-1000-8000-00805f9b34fb"
char_uuid4 = "0000eef4-0000-1000-8000-00805f9b34fb"
char_uuid5 = "0000eef5-0000-1000-8000-00805f9b34fb"
char_uuid6 = "0000eef6-0000-1000-8000-00805f9b34fb"
char_uuid7 = "0000eef7-0000-1000-8000-00805f9b34fb"
char_uuid8 = "0000eef8-0000-1000-8000-00805f9b34fb"
char_uuid_config = "0000eeff-0000-1000-8000-00805f9b34fb"

fs = 2000.0
h = float(1.0 / fs)

# Start QtApp:
# app = QtGui.QApplication([])
# win = pg.GraphicsWindow(title="Real-time EEG Data")
# p1 = win.addPlot(title="EEG, Ch 1")
# p2 = win.addPlot(title="EEG, Ch 2")
# p3 = win.addPlot(title="EEG, Ch 3")
# p4 = win.addPlot(title="EEG, Ch 4")
# p5 = win.addPlot(title="EEG, Ch 5")
# p6 = win.addPlot(title="EEG, Ch 6")
# curve1 = p1.plot()
# curve2 = p2.plot()
# curve3 = p3.plot()
# curve4 = p4.plot()
# curve5 = p5.plot()
# curve6 = p6.plot()
windowLimit = 2000
num_channels = 8
Yd = np.zeros(shape=(windowLimit, num_channels))
Xd = np.zeros(shape=(windowLimit, num_channels))
x_current = np.zeros(shape=num_channels)
totalBytesReceived = 0
currentBytesReceived = 0

initial_time = 0


# elapsed_time = 0


def current_milli_time():
    return floor(time.time() * 1000)


def update_graph(data, ch_num):
    global Yd, Xd, x_current
    global curve1, curve2, curve3, curve4, curve5, curve6
    for i in range(len(data)):
        Yd[:-1, ch_num] = Yd[1:, ch_num]
        Yd[-1, ch_num] = data[i]
        Xd[:-1, ch_num] = Xd[1:, ch_num]
        Xd[-1, ch_num] = x_current[ch_num]
        x_current[ch_num] += h
        if ch_num == 0:
            curve1.setData(Xd[0:, ch_num], Yd[0:, ch_num])
        elif ch_num == 1:
            curve2.setData(Xd[0:, ch_num], Yd[0:, ch_num])
        elif ch_num == 2:
            curve3.setData(Xd[0:, ch_num], Yd[0:, ch_num])
        elif ch_num == 3:
            curve4.setData(Xd[0:, ch_num], Yd[0:, ch_num])
        elif ch_num == 4:
            curve5.setData(Xd[0:, ch_num], Yd[0:, ch_num])
        elif ch_num == 5:
            curve6.setData(Xd[0:, ch_num], Yd[0:, ch_num])
    QtGui.QApplication.processEvents()


def unsignedByteToInt(byte):
    return int(byte)


def unsignedBytesToInt(b0, b1, b2):
    return (unsignedByteToInt(b0) << 16) + (unsignedByteToInt(b1) << 8) + unsignedByteToInt(b2)


def unsignedToSigned24bit(unsigned):
    if unsigned & 0x800000 != 0:
        return -1 * (0x800000 - (unsigned & 0x800000 - 1))
    else:
        return unsigned


def bytesToDouble(b0, b1, b2):
    unsigned = unsignedBytesToInt(b0, b1, b2)
    return float(unsignedToSigned24bit(unsigned))


def convert_bytes_to_double_array(data, gain, ref_voltage):
    data_len = len(data)
    dat_pts = int(data_len / 3)
    npdata = np.zeros(shape=[dat_pts])  # allocate space in np array:
    for i in range(dat_pts):  # Cut into appropriate size (3Bytes)
        b0 = data[3 * i]
        b1 = data[3 * i + 1]
        b2 = data[3 * i + 2]
        dat_fl = bytesToDouble(b0, b1, b2) / 8388607.0 / gain * ref_voltage * 1000.0  # converted to mV
        npdata[i] = dat_fl
    return npdata, dat_pts
    # TODO: save data as .matlab files


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
    """
    dat_conv, dat_pts = convert_bytes_to_double_array(data, gain=24.0, ref_voltage=4.5)
    if sender == 18:  # Ch1
        update_graph(dat_conv, ch_num=0)
    elif sender == 21:  # Ch2
        update_graph(dat_conv, ch_num=1)
    elif sender == 24:  # Ch3
        update_graph(dat_conv, ch_num=2)
    elif sender == 27:  # Ch4
        update_graph(dat_conv, ch_num=3)
    elif sender == 30:  # Ch5
        update_graph(dat_conv, ch_num=4)
    elif sender == 33:  # Ch6
        update_graph(dat_conv, ch_num=5)
    # print("sender: ", sender, "len: ", len(data))
    # TODO: figure out how to sort the channels
    """


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

        await client.start_notify(char_uuid1, notification_handler)
        await client.start_notify(char_uuid2, notification_handler)
        await client.start_notify(char_uuid3, notification_handler)
        await client.start_notify(char_uuid4, notification_handler)
        # await client.start_notify(char_uuid5, notification_handler)
        # await client.start_notify(char_uuid6, notification_handler)
        # await client.start_notify(char_uuid7, notification_handler)
        # await client.start_notify(char_uuid8, notification_handler)
        await asyncio.sleep(250.0)  # record for x seconds
        await client.stop_notify(char_uuid1)
        await client.stop_notify(char_uuid2)
        await client.stop_notify(char_uuid3)
        await client.stop_notify(char_uuid4)
        # await client.stop_notify(char_uuid5)
        # await client.stop_notify(char_uuid6)
        # await client.stop_notify(char_uuid7)
        # await client.stop_notify(char_uuid8)


loop = asyncio.get_event_loop()
# loop.set_debug(True)
loop.run_until_complete(run(address, True))

# terminate QtApp:
# pg.QtGui.QApplication.exec_()
