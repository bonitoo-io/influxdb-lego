from mindstorms import MSHub, Motor, MotorPair, ColorSensor, DistanceSensor, App
"""------------------"""
from hub import display, Image
import hub
import bluetooth
import random
import struct
import time
from time import sleep_ms
import time
from micropython import const
from machine import Timer

ble_msg = ""

class Lego_inventor():
    def __init__(self, name, motorA, motorB):
        #self.logo=Image(logo)
        #if ble==None:
        #    ble = bluetooth.BLE()
        #self.ble = ble
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.ble.irq(self.ble_irq)
        self.register()
        self.advertiser()
        self.conncetions = set()

    def ble_irq(self, event, data):
        global ble_msg

        if event == 1:# _IRQ_CENTRAL_CONNECT:
            # A central has connected to this peripheral
            print(213)
        elif event == 2:# _IRQ_CENTRAL_DISCONNECT:
            # A central has disconnected from this peripheral.
            self.advertiser()

        elif event == 3:# _IRQ_GATTS_WRITE:
            # A client has written to this characteristic or descriptor.
            buffer = self.ble.gatts_read(self.rx)
            ble_msg = buffer.decode('UTF-8').strip()

    def register(self):
        # Nordic UART Service (NUS)
        NUS_UUID = '257A156C-7B2F-4F6A-A3D8-5D30FD8CCE72'
        RX_UUID = "73091df7-67f1-4733-86b9-4591a02f2025"#'257A156C-7B2F-4F6A-A3D8-5D30FD8CCE72'
        TX_UUID = 'c3614996-4626-11ec-81d3-0242ac130003'

        BLE_NUS = bluetooth.UUID(NUS_UUID)
        BLE_RX = (bluetooth.UUID(RX_UUID), bluetooth.FLAG_WRITE)
        BLE_TX = (bluetooth.UUID(TX_UUID), bluetooth.FLAG_NOTIFY)

        BLE_UART = (BLE_NUS, (BLE_TX, BLE_RX,))
        SERVICES = (BLE_UART,)

        ((self.tx, self.rx,),) = self.ble.gatts_register_services(SERVICES)

    def send(self, data):
        self.ble.gatts_notify(0, self.tx, data + "\n")


    def advertiser(self):
        name = bytes(self.name, 'UTF-8')
        adv_data = bytearray('\x02\x01\x02') + bytearray((len(name) + 1, 0x09)) + name
        self.ble.gap_advertise(100, adv_data)
        print(adv_data)
        print("\r\n")
        # adv_data
        # raw: 0x02010209094553503332424C45
        # b'\x02\x01\x02\t\tESP32BLE'
        #
        # 0x02 - General discoverable mode
        # 0x01 - AD Type = 0x01
        # 0x02 - value = 0x02

        # https://jimmywongiot.com/2019/08/13/advertising-payload-format-on-ble/
        # https://docs.silabs.com/bluetooth/latest/general/adv-and-scanning/bluetooth-adv-data-basics
    def data_send(self):
        speed_A, encoderA, abs_encoder_A, power_A = hub.port.motorA.get()
        speed_B, encoderB, abs_encoder_B, power_B = hub.port.motorB.get()
        #speed_C, encoderC, abs_encoder_C, power_C = hub.port.motorC.get()
        hub_info = hub.info()
        return([hub_info])#, [speed_A, power_A], [Speed_B, power_B], [speed_C, power_C])

ble_name = Lego_inventor("Lego Hub", "A", "B")
gay = MSHub()
print(ble_name.rx)
print(ble_name.tx)
def data_extractor():
    message = []
    message.append(gay.motion_sensor.get_yaw_angle())
    message.append(Motor("B").get_speed())
    return "pyčo"

from time import sleep_ms

while True:

    if ble_msg == "w":
        ble_msg = ""
        Motor("B").run_for_seconds(0.5, 100)

    if ble_msg == "s":
        ble_msg = ""
        Motor("B").run_for_seconds(0.5, -100)

    if ble_msg == "d":
        ble_msg = ""
        Motor("A").run_for_seconds(0.5, 25)

    if ble_msg == "a":
        ble_msg = ""
        Motor("A").run_for_seconds(0.5, -25)

    if ble_msg == "image":
        ble_msg = ""
        H = hub.Image("05050:05050:05550:05050:05050")
        hub.display.show(H, delay=400, clear=False, wait=True, loop=True)

    sleep_ms(10)