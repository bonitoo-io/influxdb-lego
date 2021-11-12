# influxdb-lego

Demo Lego Boost, InfluxDB, IoT Center, MQTT realtime dashboards

## Python3 requirements

I recommend to use Python Virtual Environment <https://docs.python.org/3/tutorial/venv.html>
to have clean setup.

```bash
https://github.com/bonitoo-io/influxdb-lego.git
cd influxdb-lego

python3 -m venv venv
source venv/bin/activate

pip install bleak pylgbst influxdb_client paho_mqtt
```

## Realtime monitoring of Lego Boost robot using IoT Center demo

In the separate directory:

```bash
# clone iot-center-v2 repo
git clone https://github.com/bonitoo-io/iot-center-v2.git
cd iot-center-v2  

# switch to feat/lego_demo branch
git checkout feat/lego_demo

# edit .env and set your local network IP address
nano .env

#Iot Center requires following free ports that are not bind:
# 1883 (mqtt broker)
# 8086 (influxdb 2.0 OSS)
# 5000, 3000 nodejs server and UI app

docker-compose up
```

It will take several minutes to build and run the IotCenter.

Then the open http://localhost:5000/devices and click `Register` to add a new device. Enter `lego_boost` as a device id
and click `Register`.

## Prepare Lego Boost for Bluetooth pairing

- Install Lego Boost app on iPhone or Android device and run firmware upgrade
- Ensure that Robot is working with your iOS or Android device

## Run Python demo

```bash
python ./boost-iot-center.py
```
On first time you will need to enable BlueTooth access in MacOS security preferences dialog popup.

Run again and **immediately press green button on lego brick**.  

Demo will autodetect your lego hub and starts in 5-10s. 
The output should look like:

```text
(venv) ➜  influxdb-lego git:(main) ✗ python ./boost-iot-center.py
462	INFO	root	Searching for Lego Hub...
10524	INFO	root	Connecting to Lego Hub...
10526	INFO	comms-bleak	Discovering devices... Press green button on Hub
11618	INFO	comms	Found Move Hub at BBF17DA9-7FC1-408F-B829-B58A9B8507CA
11618	INFO	comms-bleak	Device matched: BBF17DA9-7FC1-408F-B829-B58A9B8507CA: Move Hub
12390	INFO	hub	Attached peripheral: EncodedMotor on port 0x0
12402	INFO	hub	Attached peripheral: EncodedMotor on port 0x1
12413	INFO	hub	Attached peripheral: VisionSensor on port 0x2
12424	INFO	hub	Attached peripheral: EncodedMotor on port 0x3
12437	INFO	hub	Attached peripheral: EncodedMotor on port 0x10
12448	INFO	hub	Attached peripheral: LEDRGB on port 0x32
12461	INFO	hub	Attached peripheral: TiltSensor on port 0x3a
12472	INFO	hub	Attached peripheral: Current on port 0x3b
12482	INFO	hub	Attached peripheral: Voltage on port 0x3c
12495	WARNING	hub	Have no dedicated class for peripheral type 0x42 (UNKNOWN) on port 0x46
12495	INFO	hub	Attached peripheral: Peripheral on port 0x46
12723	INFO	hub	b'Move Hub' on b'001653bf6d29'
12833	INFO	hub	Voltage: 100%
12935	INFO	root	Running Demo...
13049	INFO	root	> environment,CO2Sensor=virtual_CO2Sensor,HumiditySensor=virtual_HumiditySensor,PressureSensor=virtual_PressureSensor,TVOCSensor=virtual_TVOCSensor,clientId=lego_boost TVOC=-1 1636729176045009000
13148	INFO	root	> environment,CO2Sensor=virtual_CO2Sensor,HumiditySensor=virtual_HumiditySensor,PressureSensor=virtual_PressureSensor,TVOCSensor=virtual_TVOCSensor,clientId=lego_boost TVOC=-1 1636729176145016000
13251	INFO	root	> environment,CO2Sensor=virtual_CO2Sensor,HumiditySensor=virtual_HumiditySensor,PressureSensor=virtual_PressureSensor,TVOCSensor=virtual_TVOCSensor,clientId=lego_boost rgb=3 1636729176247289000
13351	INFO	root	> environment,CO2Sensor=virtual_CO2Sensor,HumiditySensor=virtual_HumiditySensor,PressureSensor=virtual_PressureSensor,TVOCSensor=virtual_TVOCSensor,clientId=lego_boost Pressure=2 1636729176347604000

```

IoT Center should look like:

!![screen](docs/iot-center-lego-stream.gif)


