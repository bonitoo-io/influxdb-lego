import asyncio
import random

import influxdb_client
from influxdb_client import Point
from influxdb_client.client.write_api import ASYNCHRONOUS
from pylgbst import logging, get_connection_bleak
from pylgbst.hub import MoveHub
from pylgbst.peripherals import EncodedMotor, TiltSensor

from lego_utils import auto_search

# InfluxDB settings
bucket = "iot_center"
org = "my-org"
token = "my-token"
url = "http://localhost:8086"


def data_send(metric_name, data):
    p = Point("Lego").tag("device_ID", UUID).field(metric_name, float(data))
    logging.info("> " + p.to_line_protocol())
    write_api.write(bucket=bucket, org=org, record=p)


def do_work(mhub):
    mhub.motor_A.timed(1, 0.5)
    mhub.motor_B.timed(1, 0.1)
    mhub.motor_B.timed(1, 0.5)
    mhub.motor_AB.timed(0.5, 0.5)
    mhub.motor_A.timed(1, -0.5)
    mhub.motor_B.timed(1, -0.5)
    mhub.motor_B.timed(1, 0.2)
    mhub.motor_AB.timed(-0.5, 0.5)

    for x in range(20):
        mhub.led.set_color(random.randrange(0, 10))


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

    do_work(mhub)

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
        write_api = client.write_api(write_options=ASYNCHRONOUS)
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
