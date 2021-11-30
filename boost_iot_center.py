import asyncio
import datetime
import random
from time import sleep

from influxdb_client import Point
from paho.mqtt import client as mqtt_client
from playsound import playsound
from pylgbst import logging, get_connection_bleak
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor

from lego_utils import auto_search

# MQTT settings
broker = "0.0.0.0"
port = 1883
topic = "iot_center"

def connect_mqtt():
    def on_connect(rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

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


def led_random(mhub):
    for x in range(20):
        mhub.led.set_color(random.randrange(0, 10))


def run(mhub):
    def a_callback(speed):
        data_send("TVOC", speed)

    def rgb_callback(values):
        data_send("rgb", values)

    def axis_callback(x, y, z):
        data_send("Pressure", x)
        data_send("Temperature", y)
        data_send("Humidity", z)

    def battery_callback(values):
        data_send("CO2", values)

    mhub.motor_A.subscribe(a_callback, mode=EncodedMotor.SENSOR_ANGLE)
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
        mhub.motor_A.unsubscribe(a_callback)


def zorba_dance(mhub):
    maxbl = 60 / 42  # 6O / bpm
    minbl = 60 / 160
    mins = 0.1
    p = 0.2

    s = mins  # speed  (0 - 0.5)
    bl = maxbl

    def spin():
        mhub.motor_A.start_speed(s)
        mhub.motor_B.start_speed(-s)
        sleep(bl / 2 - p)
        mhub.motor_AB.stop()
        sleep(p)
        mhub.motor_A.start_speed(-s * 2)
        mhub.motor_B.start_speed(+s * 2)
        sleep(bl / 2 - p)
        mhub.motor_AB.stop()
        sleep(p)
        mhub.motor_A.start_speed(s)
        mhub.motor_B.start_speed(-s)
        sleep(bl / 2 - p)
        mhub.motor_AB.stop()
        sleep(p)

    def basic(direction):  # Two bars
        mhub.motor_AB.start_speed(direction * s)
        sleep(bl / 2 - p)
        mhub.motor_AB.stop()
        sleep(p)
        spin()
        mhub.motor_AB.start_speed(-direction * s)
        sleep(bl / 2 - p)
        mhub.motor_AB.stop()
        sleep(p)
        spin()

    def spinning(direction):
        mhub.motor_A.start_speed(direction * minbl / bl / 1.5)
        mhub.motor_B.start_speed(-direction * minbl / bl / 1.5)
        sleep(2 * bl - p)
        mhub.motor_AB.stop()
        sleep(p)

    # Zorba Dance version (https://musescore.com/user/14008706/scores/4866772)
    playsound('Zorba_s_Dance_Sirrtaki.mp3', block=False)
    sleep(5)

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
    s = mins / (bl / maxbl)

    for x in range(5):
        basic(1)

    bl = 60 / 68
    s = mins / (bl / maxbl)

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


if __name__ == '__main__':
    parameters = {}
    hub = None
    try:
        client_mqtt = connect_mqtt()
        name, UUID = asyncio.run(auto_search())
        connection = get_connection_bleak(hub_mac=str(UUID), hub_name=str(name))
        parameters['connection'] = connection
        hub = MoveHub(**parameters)
        logging.info("Running Demo...")
        run(hub)
    except Exception as e:
        print(e)
    finally:
        if hub is not None:
            hub.disconnect()
