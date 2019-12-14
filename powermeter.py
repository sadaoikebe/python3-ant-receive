"""
    Code based on:

https://github.com/mvillalba/python-ant/blob/develop/demos/ant.core/03-basicchannel.py

    in the python-ant repository and

https://github.com/tomwardill/developerhealth

    by Tom Wardill

Modified for Python 3 - Sadao Ikebe
reads bike power meter

"""
import sys
import time
from ant.core import driver, node, event, message, log
from ant.core.constants import CHANNEL_TYPE_TWOWAY_RECEIVE, TIMEOUT_NEVER
import socket
import struct

class PowerMeter(event.EventCallback):

    def __init__(self, serial, netkey, report):
        self.serial = serial
        self.netkey = netkey
        self.report = report
        self.antnode = None
        self.channel = None

    def start(self):
        print("starting node")
        self._start_antnode()
        self._setup_channel()
        self.channel.registerCallback(self)
        print("start listening for power events")

    def stop(self):
        if self.channel:
            self.channel.close()
            self.channel.unassign()
        if self.antnode:
            self.antnode.stop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.stop()

    def _start_antnode(self):
        stick = driver.USB1Driver(self.serial, log=None, debug=False)
        self.antnode = node.Node(stick)
        self.antnode.start()

    def _setup_channel(self):
        key = node.Network(name='N:ANT+', key=self.netkey)
        self.antnode.setNetworkKey(0, key)
        self.channel = self.antnode.getFreeChannel()
        self.channel.name = 'C:PowerMeter'
        self.channel.assign(key, CHANNEL_TYPE_TWOWAY_RECEIVE)
        self.channel.setID(11, 0, 0)
        self.channel.searchTimeout = TIMEOUT_NEVER
        self.channel.period = 8182 # might be 4091 or 8182
        self.channel.frequency = 57
        self.channel.open()

    def process(self, msg, node):
        if isinstance(msg, message.ChannelBroadcastDataMessage):
            if msg.payload[1] == 0x10: # Power Main Data Page
                pwr = msg.payload[8] * 256 + msg.payload[7]
                self.report(pwr)

def power_report(pwr):
    print(pwr)

with PowerMeter(serial='/dev/ttyUSB0', netkey=[0xb9, 0xa5, 0x21, 0xfb, 0xbd, 0x72, 0xc3, 0x45], report=power_report) as pwr:
    pwr.start()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            sys.exit(0)
