# InfluxDB & Lego Boost real-time monitoring demo

This demo shows how to monitor your Lego Boost Robot using InfluxDB, Telegraf, IoT Center Demo with MQTT realtime
dashboards.
   
[![img.png](docs/video.png)](https://www.youtube.com/watch?v=Cp2gDleP8_M)

## Description 

This application was designed to display and store real-time data from LEGO Boost Robot and because the application from
LEGO lacks this feature. We used InfluxDB to store the data, MQTT, Telegraf, IotCenter Demo to show realtime since it's
the fastest way to do so.

In future we want to support monitoring of all lego robots, such as Robot Inventor and EV3, so that we can then store
time series for color, ultrasonic, and infrared sensors and not just gyro sensor and motors. Our program will also
provide some calculations based on the data it monitors such as speed, acceleration, trajectory, energy consumption,
lead (for racing), health (for robot battles), work performance (for lego factories), and more.

## How to install

### IoT Center setup

After cloning this repository, you should be ready to set up our IoT Center. 

We recommend using Python Virtual Environment <https://docs.python.org/3/tutorial/venv.html>
to have a clean setup.

```bash
https://github.com/bonitoo-io/influxdb-lego.git
cd influxdb-lego

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

At first, you should download and install docker from here: https://www.docker.com/get-started. 

Then start the latest version of IotCenter using:

```bash
docker-compose up
```

It will take several seconds to start the IotCenter.

Note that the IoT Center requires the following free ports that do not bind:

- **1883** (mqtt broker)
- **8086** (influxdb 2.0 OSS)
- **5000**, 3000 nodejs server and UI app

### Lego Boost registration 

The next step is to register your Lego Boost robot into IotCenter. Open the IoT Center UI
on <http://localhost:5000/devices> and click **Register** to add a new device. Enter `lego_boost` as a device id and
confirm by clicking **Register**.

![screen](docs/register.png)

### Prepare Lego Boost for Bluetooth pairing

- Install Lego Boost app on iPhone or Android device and run firmware upgrade
- Ensure that Robot is working with your iOS or Android device
- Press the green
### Run Python demo

```bash
python ./boost_iot_center.py
```

On the first time, you will need to enable BlueTooth access in the MacOS security preferences dialogue popup.

Run again and **immediately press the green button on lego brick**.

The demo will autodetect your lego hub and start in 5-10s. The output should look like this:

```text
355	INFO	root	Discovering devices... Press the green button on Hub
5450	INFO	comms-bleak	Discovering devices... Press green button on Hub
6538	INFO	comms	Found Move Hub at 24931243-B7C5-6CE4-C192-D4E69C5CB3E4
6538	INFO	comms-bleak	Device matched: 24931243-B7C5-6CE4-C192-D4E69C5CB3E4: Move Hub
6894	INFO	hub	Attached peripheral: EncodedMotor on port 0x0
6905	INFO	hub	Attached peripheral: EncodedMotor on port 0x1
6917	INFO	hub	Attached peripheral: VisionSensor on port 0x2
6929	INFO	hub	Attached peripheral: EncodedMotor on port 0x3
6941	INFO	hub	Attached peripheral: EncodedMotor on port 0x10
6953	INFO	hub	Attached peripheral: LEDRGB on port 0x32
6964	INFO	hub	Attached peripheral: TiltSensor on port 0x3a
6977	INFO	hub	Attached peripheral: Current on port 0x3b
6988	INFO	hub	Attached peripheral: Voltage on port 0x3c
7001	WARNING	hub	Have no dedicated class for peripheral type 0x42 (UNKNOWN) on port 0x46
7001	INFO	hub	Attached peripheral: Peripheral on port 0x46
7192	INFO	hub	b'Move Hub' on b'001653bf6d29'
7295	INFO	hub	Voltage: 100%
7399	INFO	root	Running Demo...
7709	INFO	root	> environment,clientId=lego_boost speed_a=0,speed_b=0,x_axis=2,y_axis=-62,z_axis=4 1644851818642053000
7719	INFO	root	> environment,clientId=lego_boost speed_a=0,speed_b=0,x_axis=2,y_axis=-61,z_axis=4 1644851818653587000
7741	INFO	root	> environment,clientId=lego_boost speed_a=0,speed_b=0,x_axis=3,y_axis=-63,z_axis=4 1644851818675525000
7823	INFO	root	> environment,clientId=lego_boost distance=0,speed_a=0,speed_b=0,x_axis=3,y_axis=-62,z_axis=4 1644851818757454000
7847	INFO	root	> environment,clientId=lego_boost distance=0,speed_a=0,speed_b=0,x_axis=3,y_axis=-62,z_axis=3 1644851818781242000
7916	INFO	root	> environment,clientId=lego_boost distance=9,speed_a=0,speed_b=0,x_axis=3,y_axis=-62,z_axis=4 1644851818849990000
```

Lego metrics are coded in following manner:

- axis x -> tilt axe X
- axis y -> tilt axe Y
- axis z -> tilt axe Z
- Distance -> distance sensor
- Voltage -> battery voltage
- Motor A/Motor B -> current motor output

Check IoT Center: [http://localhost:5000/realtime/lego_boost](http://localhost:5000/realtime/lego_boost)

![screen](docs/iot-centre-lego.gif)

### Note for macOS Monterey 12.2+

At the moment, the latest version of the pylgbst (1.2.2) doesn't support macOS Monterey 12.2+, install the latest
version from github using following pip command:

```bash
pip install git+https://github.com/undera/pylgbst
```
