#include <WiFi.h>
#include "Boost.h"
#include "custom_dev.h" //Custom development configuration - remove or comment it out 

// create a hub instance
Boost myMoveHub;
byte portC = (byte)MoveHubPort::C;
byte portD = (byte)MoveHubPort::D;

void initMQTT( const char* url, const String& topic, const String& user, const String& passowrd, const String& options);
bool readyMQTT();
bool writeMQTT( const String& data);
String deviceID;

bool updatedMQTT = false;
double distance = 340;
int x = 0;
int y = 0;
double voltage = 0;
double current = 0;
int color = 0;

String getTimeStr() {
  struct timeval tv;
  gettimeofday(&tv, NULL);
  unsigned long long tsVal = tv.tv_sec * 1000LL + tv.tv_usec / 1000LL;
  static char buff[50];
  snprintf(buff, 50, "%llu", tsVal);
  return String(buff);
}

void setup() {
  Serial.begin(115200);
  myMoveHub.init(); // initalize the MoveHub instance
  // Setup wifi
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Connecting to wifi ");
  Serial.print(WIFI_SSID);
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    _delay(100);
  }
  Serial.println();
  Serial.println("Connected " + WiFi.SSID() + " " +  WiFi.localIP().toString());
  
  configTzTime(TZ_INFO, "pool.ntp.org", "time.nis.gov");

  // Wait till time is synced
  Serial.print("Syncing time");
  int i = 0;
  while (time(nullptr) < 1000000000l && i < 40) {
    Serial.print(".");
    _delay(500);
    i++;
  }
  Serial.println();

  // Show time
  time_t tnow = time(nullptr);
  Serial.print("Synchronized time: ");
  Serial.println(ctime(&tnow));

  deviceID = "ROBOT";
  initMQTT( MQTT_URL, "iot_center", "", "", "");  
}

void hubPropertyChangeCallback(void *hub, HubPropertyReference hubProperty, uint8_t *pData)
{
  Lpf2Hub *myHub = (Lpf2Hub *)hub;

  /*Serial.print("HubProperty: ");
  Serial.println((byte)hubProperty, HEX);*/

  if (hubProperty == HubPropertyReference::RSSI)
  {
    return;
    Serial.print("RSSI: ");
    Serial.println(myHub->parseRssi(pData), DEC);
    return;
  }

  if (hubProperty == HubPropertyReference::ADVERTISING_NAME)
  {
    return;
    Serial.print("Advertising Name: ");
    Serial.println(myHub->parseHubAdvertisingName(pData).c_str());
    return;
  }

  if (hubProperty == HubPropertyReference::BATTERY_VOLTAGE)
  {
    return;
    Serial.print("BatteryLevel: ");
    Serial.println(myHub->parseBatteryLevel(pData), DEC);
    return;
  }

  if (hubProperty == HubPropertyReference::BUTTON)
  {
    Serial.print("Button: ");
    Serial.println((byte)myHub->parseHubButton(pData), HEX);
    if ( (byte)myHub->parseHubButton(pData) == 1) {
      myHub->shutDownHub();
      Serial.println("Shutdown robot");
      //myHub->setAbsoluteMotorEncoderPosition(portD, 1);
    }
    return;
  }

  if (hubProperty == HubPropertyReference::BATTERY_TYPE)
  {
    Serial.print("BatteryType: ");
    Serial.println(myHub->parseBatteryType(pData), HEX);
    return;
  }

  if (hubProperty == HubPropertyReference::FW_VERSION)
  {
    Version version = myHub->parseVersion(pData);
    Serial.print("FWVersion: ");
    Serial.print(version.Major);
    Serial.print("-");
    Serial.print(version.Minor);
    Serial.print("-");
    Serial.print(version.Bugfix);
    Serial.print(" Build: ");
    Serial.println(version.Build);
    return;
  }

  if (hubProperty == HubPropertyReference::HW_VERSION)
  {
    Version version = myHub->parseVersion(pData);
    Serial.print("HWVersion: ");
    Serial.print(version.Major);
    Serial.print("-");
    Serial.print(version.Minor);
    Serial.print("-");
    Serial.print(version.Bugfix);
    Serial.print(" Build: ");
    Serial.println(version.Build);
    return;
  }
}

// callback function to handle updates of sensor values
void portValueChangeCallback(void *hub, byte portNumber, DeviceType deviceType, uint8_t *pData)
{
  Lpf2Hub *myHub = (Lpf2Hub *)hub;

  if (deviceType == DeviceType::VOLTAGE_SENSOR)
  {
    voltage = myHub->parseVoltageSensor(pData);
    Serial.print("Voltage: ");
    Serial.println(voltage, 2);
    updatedMQTT = true;
    return;
  }

  if (deviceType == DeviceType::CURRENT_SENSOR)
  {
    current = myHub->parseCurrentSensor(pData);
    Serial.print("Current: ");
    Serial.println(current, 2);
    updatedMQTT = true;
    return;
  }

  if (deviceType == DeviceType::MOVE_HUB_TILT_SENSOR)
  {
    x = myHub->parseBoostTiltSensorX(pData);
    y = myHub->parseBoostTiltSensorY(pData);
    Serial.print("Tilt X: ");
    Serial.print(x, DEC);
    Serial.print(" Y: ");
    Serial.println(y, DEC);
    updatedMQTT = true;
    return;
  }

  if (deviceType == DeviceType::COLOR_DISTANCE_SENSOR) {
    color = myHub->parseColor(pData);
    distance = myHub->parseDistance(pData);
    Serial.print("Color: ");
    Serial.print(LegoinoCommon::ColorStringFromColor(color).c_str());
    Serial.print(" Distance: ");
    Serial.println(distance, DEC);
    updatedMQTT = true;
    return;
  }
  
  if (deviceType == DeviceType::MEDIUM_LINEAR_MOTOR || deviceType == DeviceType::MOVE_HUB_MEDIUM_LINEAR_MOTOR) {
    int rotation = myHub->parseTachoMotor(pData);
    Serial.print("RotationD: ");
    Serial.println(rotation, DEC);
    return;
  }
  
  Serial.print("Unknown sensor: ");
  Serial.println( (int)deviceType);
}

void _delay( unsigned long t) {
  for (unsigned int i = 0; i < (t/10); i++) {
    if (updatedMQTT) {
      writeMQTT( "environment,clientId=" + deviceID + " Temperature=" + String( distance) + ",Humidity=" + String( x) + ",Pressure=" + String( y) + ",CO2=" + String( voltage) + ",TVOC=" + String( current) + " " + getTimeStr());
      updatedMQTT = false;
    }
    delay(10);
  }
  delay(t%10);
}

// main loop
void loop() {
  // connect flow. Search for BLE services and try to connect if the uuid of the hub is found
  if (myMoveHub.isConnecting())
  {
    myMoveHub.connectHub();
    if (myMoveHub.isConnected()) {
      Serial.println("Connected to HUB");
      _delay(50); //needed because otherwise the message is to fast after the connection procedure and the message will get lost
      myMoveHub.activateHubPropertyUpdate(HubPropertyReference::ADVERTISING_NAME, hubPropertyChangeCallback);
      _delay(50);
      myMoveHub.activateHubPropertyUpdate(HubPropertyReference::BATTERY_VOLTAGE, hubPropertyChangeCallback);
      _delay(50);
      myMoveHub.activateHubPropertyUpdate(HubPropertyReference::BUTTON, hubPropertyChangeCallback);
      _delay(50);
      myMoveHub.activateHubPropertyUpdate(HubPropertyReference::RSSI, hubPropertyChangeCallback);
      _delay(50);
      myMoveHub.activatePortDevice((byte)MoveHubPort::TILT, portValueChangeCallback);
      _delay(50);
      myMoveHub.activatePortDevice((byte)MoveHubPort::CURRENT, portValueChangeCallback);
      _delay(50);
      myMoveHub.activatePortDevice((byte)MoveHubPort::VOLTAGE, portValueChangeCallback);
      _delay(50);
      myMoveHub.activatePortDevice(portD, portValueChangeCallback);
      _delay(50);
      byte portForDevice = myMoveHub.getPortForDeviceType((byte)DeviceType::COLOR_DISTANCE_SENSOR);
      if (portForDevice != 255)
        myMoveHub.activatePortDevice( portForDevice, portValueChangeCallback);
    } else {
      Serial.println("Failed to connect to HUB");
      ESP.restart();
    }
  } else {
    Serial.print('.');
    _delay( 500);
  }

  // if connected, you can set the name of the hub, the led color and shut it down
  if (myMoveHub.isConnected()) {

    char hubName[] = "myMoveHub";
    myMoveHub.setHubName(hubName);
    myMoveHub.setLedColor(RED);
    _delay(1000);

    // lets do some movements on the boost map
    /*myMoveHub.moveForward(1);
    _delay(2000);
    myMoveHub.rotateLeft(5);
    _delay(2000);
    myMoveHub.moveBack(1);
    _delay(2000);
    myMoveHub.rotateRight(5);
    _delay(2000);
    myMoveHub.moveArcLeft(90);
    _delay(2000);
    myMoveHub.moveArcRight(5);
    _delay(2000);*/
/*    myMoveHub.setTachoMotorSpeedForDegrees(portD, 2, 20*4.5);
    _delay(2000);
    myMoveHub.setTachoMotorSpeedForDegrees(portD, -2, 20*4.5);
    _delay(2000);
    myMoveHub.setTachoMotorSpeedForDegrees(portD, -2, 20*4.5);
    _delay(2000);
    myMoveHub.setTachoMotorSpeedForDegrees(portD, 2, 20*4.5);
    _delay(2000);*/
    myMoveHub.setAbsoluteMotorEncoderPosition(portD, 0);

    myMoveHub.setLedColor(GREEN);
    _delay(1000);
  }
  readyMQTT();
} // End of loop
