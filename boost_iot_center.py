import asyncio
import datetime
from time import sleep

from influxdb_client import Point
from paho.mqtt import client as mqtt_client
from playsound import playsound
from pylgbst import logging, get_connection_bleak
from pylgbst.hub import MoveHub, VisionSensor
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


def send(data):
    p = Point("environment") \
        .tag("clientId", "lego_boost") \
        .time(datetime.datetime.utcnow())

    for key, value in data.items():
        p = p.field(key, float(value))

    logging.info("> " + p.to_line_protocol())
    client_mqtt.publish(topic, p.to_line_protocol())


def run(mhub):
    sensor_data = {}

    def a_callback(speed):
        sensor_data["speed_a"] = speed

    def b_callback(speed):
        sensor_data["speed_b"] = speed

    def axis_callback(x, y, z):
        sensor_data["x_axis"] = x
        sensor_data["y_axis"] = y
        sensor_data["z_axis"] = z
        send(sensor_data)

    def battery_callback(voltage):
        sensor_data["voltage"] = round(voltage, 2)

    def vision_callback(distance):
        sensor_data["distance"] = distance

    mhub.motor_A.subscribe(a_callback, mode=EncodedMotor.SENSOR_SPEED)
    mhub.motor_B.subscribe(b_callback, mode=EncodedMotor.SENSOR_SPEED)
    mhub.tilt_sensor.subscribe(axis_callback, mode=TiltSensor.MODE_3AXIS_ACCEL)
    mhub.vision_sensor.subscribe(vision_callback, mode=VisionSensor.DISTANCE_INCHES)
    mhub.voltage.subscribe(battery_callback)

    try:
        zorba_dance(hub)

    except KeyboardInterrupt:
        raise KeyboardInterrupt

    finally:
        mhub.led.unsubscribe(b_callback)
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
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)d\t%(levelname)s\t%(name)s\t%(message)s')
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
