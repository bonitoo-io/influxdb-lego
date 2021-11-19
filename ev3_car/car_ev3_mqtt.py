#!/usr/bin/python3
import time
import datetime
import paho.mqtt.client as mqtt

from ev3dev2.auto import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_D
from ev3dev2.motor import MediumMotor
from ev3dev2.sensor.lego import InfraredSensor, TouchSensor
from influxdb_client import Point
from ev3dev2.power import PowerSupply


class LegoCar:
    current_speed = 0
    steering_motor = MediumMotor(address=OUTPUT_D)
    tank_drive = MoveTank(OUTPUT_A, OUTPUT_B)
    ir = InfraredSensor()
    ts = TouchSensor()
    mqtt = mqtt.Client()
    power = PowerSupply()

    def __init__(self, device_id) -> None:
        super().__init__()
        self.device_id = device_id

    def run(self):
        self.mqtt.connect("10.100.0.150", 1883, 60)

        self.ir.on_channel1_top_left = self.steer_right
        self.ir.on_channel1_bottom_left = self.steer_left
        self.ir.on_channel1_top_right = self.backward
        self.ir.on_channel1_bottom_right = self.forward
        self.ir.on_channel1_beacon = self.stop

        self.ir.process()

        while True:
            p = Point("lego").tag("device_id", self.device_id) \
                .field("steer_position", self.steering_motor.position) \
                .field("RPM", self.tank_drive.left_motor.speed) \
                .field("motor_position", self.tank_drive.left_motor.position) \
                .field("power_voltage", self.power.measured_volts) \
                .field("power_amps", self.power.measured_amps) \
                .field("motor_position", self.tank_drive.left_motor.position) \
                .time(datetime.datetime.utcnow())

            if self.ts.is_pressed:
                self.crash()
                p.field("status", "crash")
            else:
                p.field("status", "ok")

            print(p.to_line_protocol())

            self.mqtt.publish("topic/test", p.to_line_protocol())

            time.sleep(0.01)

    def steer_right(self, state):
        print("top left on channel 1: %s" % state)
        if state:
            self.steering_motor.on_for_degrees(speed=30, degrees=90)
        else:
            self.steering_motor.on_for_degrees(speed=30, degrees=-90)

    def steer_left(self, state):
        print("bottom left on channel 1: %s" % state)

        if state:
            self.steering_motor.on_for_degrees(speed=30, degrees=-90)
        else:
            self.steering_motor.on_for_degrees(speed=30, degrees=90)

    def forward(self, state):
        print("forward: %s" % self.current_speed)
        if self.current_speed >= 100:
            return

        if state:
            self.current_speed = self.current_speed + 20
            self.tank_drive.on(left_speed=self.current_speed, right_speed=self.current_speed)

    def backward(self, state):
        print("backward: %s" % self.current_speed)
        if self.current_speed <= -100:
            return

        if state:
            self.current_speed = self.current_speed - 20
            self.tank_drive.on(left_speed=self.current_speed, right_speed=self.current_speed)

    def stop(self, state):
        print("stop: %s" % self.current_speed)
        self.current_speed = 0
        if state:
            self.tank_drive.on(left_speed=self.current_speed, right_speed=self.current_speed)

    def crash(self):
        self.tank_drive.on(left_speed=0, right_speed=0)


if __name__ == '__main__':
    print("Starting program...")
    lego_car = LegoCar("EV3Car")
    lego_car.run()