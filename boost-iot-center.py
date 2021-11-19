import asyncio
import datetime
from time import sleep

import pygame
from bleak import BleakScanner
from influxdb_client import Point
from paho.mqtt import client as mqtt_client
from pylgbst import logging, get_connection_bleak
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor

# MQTT settings
broker = "0.0.0.0"
port = 1883
topic = "iot_center"


def connect_mqtt():
    def on_connect(rc):
        if rc == 0:
            logging.info("Connected to MQTT Broker!")
        else:
            logging.error("Failed to connect, return code %d\n", rc)

    logging.info("Connecti     ng to MQTT Broker...")
    client2 = mqtt_client.Client()
    client2.on_connect = on_connect
    client2.connect(broker, port)
    return client2


def data_send(metric_name, data):
    p = Point("environment") \
        .tag("CO2Sensor", "virtual_CO2Sensor") \
        .tag("PressureSensor", "virtual_PressureSensor") \
        .tag("HumiditySensor", "virtual_HumiditySensor") \
        .tag("TVOCSensor", "virtual_TVOCSensor") \
        .tag("clientId", "lego_boost") \
        .field(metric_name, float(data)) \
        .time(datetime.datetime.utcnow())
    logging.info("> " + p.to_line_protocol())
    client_mqtt.publish(topic, p.to_line_protocol())


async def auto_search():
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)d\t%(levelname)s\t%(name)s\t%(message)s')
    logging.info("Press the green button on the Lego Hub ...")

    devices = await BleakScanner.discover(timeout=10)
    possible_devices = []
    for d in devices:
        if d.name == "Move Hub":
            possible_devices.append(d)

    if len(possible_devices) == 0:
        raise Exception("Move Hub was not found.")

    if len(str(possible_devices[1].metadata)) > len(str(possible_devices[0].metadata)):
        return possible_devices[1].name, possible_devices[1].address
    else:
        return possible_devices[0].name, possible_devices[0].address


name, UUID = asyncio.run(auto_search())


def run(mhub):
    def callback_a(speed):
        data_send("Pressure", speed)

    def callback_b(speed):
        data_send("Humidity", speed)

    def rgb_callback(values):
        data_send("rgb", values)

    def axis_callback(x, y, z):
        data_send("Temperature", x)
        data_send("TVOC", z)

    def battery_callback(values):
        data_send("CO2", values)

    mhub.motor_A.subscribe(callback_a, mode=EncodedMotor.SENSOR_SPEED)
    mhub.motor_B.subscribe(callback_b, mode=EncodedMotor.SENSOR_SPEED)
    mhub.led.subscribe(rgb_callback)
    mhub.tilt_sensor.subscribe(axis_callback, mode=TiltSensor.MODE_3AXIS_ACCEL)
    mhub.voltage.subscribe(battery_callback)

    try:
        zorba_dance(hub)

    except KeyboardInterrupt:
        raise KeyboardInterrupt
    finally:
        mhub.led.unsubscribe(rgb_callback)
        mhub.tilt_sensor.unsubscribe(axis_callback)
        mhub.voltage.unsubscribe(battery_callback)
        mhub.motor_B.unsubscribe(callback_b)
        mhub.motor_A.unsubscribe(callback_a)


def zorba_dance(mhub):
    play_music("zorba-dance.midi")

    sleep(5)

    bl = 60 / 42  # 6O / bpm
    minbl = 120 / 160
    s = 0.1  # speed  (0 - 0.5)

    def spin():
        if not pygame.mixer.music.get_busy():
            raise KeyboardInterrupt

        mhub.motor_B.start_speed(-s)
        mhub.motor_A.start_speed(-s)
        sleep(bl / 2)
        mhub.motor_A.start_speed(-s * 2)
        mhub.motor_B.start_speed(+s * 2)
        sleep(bl / 2)
        mhub.motor_A.start_speed(s)
        mhub.motor_B.start_speed(-s)
        sleep(bl / 2)
        mhub.motor_AB.stop()

    def basic(dir):  # Two bars
        mhub.motor_AB.start_speed(dir * s)
        sleep(bl / 2)
        spin()
        mhub.motor_AB.start_speed(-dir * s)
        sleep(bl / 2)
        spin()
        mhub.motor_AB.stop()

    def spinning(dir):  # Divide speed argument to slow down spinning, one bar
        mhub.motor_A.start_speed(dir * minbl / bl)
        mhub.motor_B.start_speed(-dir * minbl / bl)
        sleep(2 * bl)

    for x in range(3):
        basic(1)
    for x in range(1):
        basic(-1)
    for x in range(4):
        basic(1)
    for x in range(2):
        basic(-1)
    for x in range(5):
        basic(1)

    bl = 60 / 48
    for x in range(5):
        basic(1)

    bl = 60 / 68
    for x in range(2):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(4):
        spinning(1)
    for x in range(6):
        spinning(-1)
    for x in range(10):
        spinning(1)
    for x in range(2):
        spinning(-1)

    bl = 60 / 90
    for x in range(10):
        basic(1)
    for x in range(2):
        basic(-1)
    for x in range(2):
        basic(1)

    bl = minbl
    for x in range(10):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(4):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(8):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(4):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(6):
        spinning(1)
    for x in range(4):
        spinning(-1)
    for x in range(4):
        spinning(1)

    pygame.mixer.music.fadeout(1000)
    pygame.mixer.music.stop()


def play_music(midi_file):
    logging.info(f"Playing {midi_file}...")
    pygame.mixer.init(44100, -16, 2, 1024)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.load(midi_file)
    pygame.mixer.music.play()


if __name__ == '__main__':
    hub = None
    try:
        client_mqtt = connect_mqtt()
        logging.info("Connecting to Lego Hub...")
        parameters = {'connection': get_connection_bleak(hub_mac=str(UUID), hub_name=str(name))}
        hub = MoveHub(**parameters)
        logging.info("Running Demo...")
        run(hub)
    except KeyboardInterrupt as e:
        logging.info("Demo ended.")
    except Exception as e:
        logging.error("There was an error", e)
    finally:
        pygame.mixer.music.fadeout(1000)
        pygame.mixer.music.stop()

        if hub is not None:
            hub.disconnect()
