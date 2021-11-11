from bleak import BleakScanner
import asyncio
import random

from influxdb_client import Point
from pylgbst import logging, get_connection_bleak
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor
from paho.mqtt import client as mqtt_client
import influxdb_client
from influxdb_client.client.write_api import ASYNCHRONOUS, SYNCHRONOUS

# MQTT settings
broker = "0.0.0.0"
port = 1883
topic = "/lego/mqtt"
client_id = f"python-mqtt-{random.randint(0, 1000)}"
username = "Lukash"
password = "bumbumbum"

# InfluxDB settings
bucket = "iot_center"
org = "my-org"
token = "my-token"
url = "http://localhost:8086"


def connect_mqtt():
    def on_connect(rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client2 = mqtt_client.Client(client_id)
    client2.username_pw_set(username, password)
    client2.on_connect = on_connect
    client2.connect(broker, port)
    return client2


def data_send(metric_name, data, mode="influx"):
    p = Point("Lego").tag("device_ID", UUID).field(metric_name, float(data))
    logging.info("> " + p.to_line_protocol())
    if mode == "influx":
        write_api.write(bucket=bucket, org=org, record=p)
    else:
        client_mqtt.publish(topic, p.to_line_protocol())


async def auto_search():
    logging.basicConfig(level=logging.INFO, format='%(relativeCreated)d\t%(levelname)s\t%(name)s\t%(message)s')
    logging.info("Searching for Lego Hub...")
    devices = await BleakScanner.discover(timeout=10)
    possible_devices = []
    for d in devices:
        if d.name == "Move Hub":
            possible_devices.append(d)

    if len(str(possible_devices[1].metadata)) > len(str(possible_devices[0].metadata)):
        return possible_devices[1].name, possible_devices[1].address
    else:
        return possible_devices[0].name, possible_devices[0].address


def led_random(mhub):
    for x in range(20):
        mhub.led.set_color(random.randrange(0, 10))


def motor_loop1(mhub):
    mhub.motor_A.timed(2, 0.5)
    mhub.motor_B.timed(2, 0.1)
    mhub.motor_B.timed(1, 0.5)
    mhub.motor_AB.timed(0.5, 0.5)
    mhub.motor_A.timed(2, -0.5)
    mhub.motor_B.timed(1, -0.5)
    mhub.motor_B.timed(2, 0.2)
    # mhub.motor_AB.timed(-0.5,  0.5)


def sequence(mhub):
    motor_loop1(mhub)
    led_random(mhub)


def run(mhub):
    def callback_a(speed):
        data_send("motor_a", speed)

    def callback_b(speed):
        data_send("motor_b", speed)

    def rgb_callback(values):
        data_send("rgb", values)

    def axis_callback(x, y, z):
        data_send("x", x)
        data_send("y", y)
        data_send("z", z)

    def battery_callback(values):
        data_send("voltage", values)

    mhub.motor_A.subscribe(callback_a, mode=EncodedMotor.SENSOR_SPEED)
    mhub.motor_B.subscribe(callback_b, mode=EncodedMotor.SENSOR_SPEED)
    mhub.led.subscribe(rgb_callback)
    mhub.tilt_sensor.subscribe(axis_callback, mode=TiltSensor.MODE_3AXIS_ACCEL)
    mhub.voltage.subscribe(battery_callback)
    sequence(mhub)
    mhub.led.unsubscribe(rgb_callback)
    mhub.tilt_sensor.unsubscribe(axis_callback)
    mhub.voltage.unsubscribe(battery_callback)
    mhub.motor_B.unsubscribe(callback_b)
    mhub.motor_A.unsubscribe(callback_a)


name, UUID = asyncio.run(auto_search())

if __name__ == '__main__':

    parameters = {}

    hub = None
    try:
        client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
        client.ping()
        write_api = client.write_api(write_options=SYNCHRONOUS)

        client_mqtt = connect_mqtt()

        logging.info("Connecting to Lego Hub...")
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
