import asyncio
import datetime
from time import sleep
import random
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


client_mqtt = connect_mqtt()
data = {"speed_a":random.randint(1,100), "speed_b":random.randint(1,100),"voltage":random.randrange(7,8),
        "x_axis":random.randrange(1,200),  "y_axis":random.randrange(1,200),  "z_axis":random.randrange(1,200),
        }
while True:
    data = {"speed_a": random.randint(1, 100), "speed_b": random.randint(1, 100), "voltage": random.randrange(7, 8),
            "x_axis": random.randrange(1, 200), "y_axis": random.randrange(1, 200), "z_axis": random.randrange(1, 200),
            }

    send(data)

    sleep(5)