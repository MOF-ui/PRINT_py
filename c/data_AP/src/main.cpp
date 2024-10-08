/*  This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
/   International (CC BY-SA 4.0).
/   (https://creativecommons.org/licenses/by-sa/4.0/)
/   Feel free to use, modify or distribute this code as far as you like, so
/   long as you make anything based on it publicly avialable under the same
/   license.
*/
/* 
following examples from
    danak6jq: https://github.com/danak6jq/ESP32-WSPR
    espressif.com
*/

/* -------------------------- IMPORTS & DEFINITIONS ----------------------- */

#include <Arduino.h>

#include "ETH.h"

#include "data_AP_support.h"

/* --------------------------- VARIABLES & CLASSES ------------------------ */

// ETH
WebServer http_server(HTTP_SERVER_PORT);
bool eth_connected = false;

// DS18B20
struct t_block TSensor[MAX_TEMP_SENSORS];
String t_sensor_names[MAX_TEMP_SENSORS] = {"IN", "OUT"};
u64_t last_temp_reading = 0;
int temp_reading_freq = 500; // [ms]

/* -------------------------- FUNCTION DECLARATIONS ----------------------- */

// handle Ethernet events
void WiFiEvent(WiFiEvent_t event)
{
  switch (event) {
    case ARDUINO_EVENT_ETH_START:
		// This will happen during setup, when the Ethernet service starts
		Serial.println("HTTP:\tETH started.");
		ETH.setHostname("printhead_interface");
		break;

    case ARDUINO_EVENT_ETH_CONNECTED:
		// This will happen when the Ethernet cable is plugged 
		Serial.println("HTTP:\tETH connected.");
		break;

    case ARDUINO_EVENT_ETH_GOT_IP:
    	// This will happen when we obtain an IP address through DHCP:
		Serial.print("HTTP:\tGot an IP Address for ETH MAC: ");
		Serial.print(ETH.macAddress());
		Serial.print(", IPv4: ");
		Serial.print(ETH.localIP());
		if (ETH.fullDuplex()) {
			Serial.print(", FULL_DUPLEX");
		}
		Serial.print(", ");
		Serial.print(ETH.linkSpeed());
		Serial.println("Mbps.");

	  	// set up web server
		http_server.begin();
		Serial.println("HTTP:\tweb server running.");
		eth_connected = true;
		break;

    case ARDUINO_EVENT_ETH_DISCONNECTED:
		// This will happen when the Ethernet cable is unplugged 
		Serial.println("HTTP:\tETH disconnected.");

		// stopping web server
		http_server.stop();
		Serial.println("HTTP:\tweb server stopped.");
		eth_connected = false;
		break;

    case ARDUINO_EVENT_ETH_STOP:
		// This will happen when the ETH interface is stopped but this never happens
		Serial.println("HTTP:\tETH stopped.");
		eth_connected = false;
		break;

    default:
		break;
  }
}

/* ---------------------------------- SETUP ------------------------------- */

void setup() {
	// PHdM -- printhead main
	Serial.begin(115200);
	Serial.println("\n\nPHdM:\t--------------------------------");
	Serial.println("PHdM:\t             DATA_AP            ");
	Serial.println("PHdM:\t--------------------------------\n");

	// ETH
	Serial.println("ETHN:\tsetting up event handler..");
	// using the WiFi event handling setup here, but this response
	// to the Ethernet port of the OLIMEX PoE IsO when using ETH.h
	WiFi.onEvent(WiFiEvent);
	ETH.begin();
	init_uri();
	if (!MDNS.begin("data_AP")) {
		Serial.println("ETHN:\tmDNS setup failed, restarting..");
		Serial.flush();
		ESP.restart();
	}

	// TEMP_READOUT
	Serial.println("TEMP:\tinit DS18B20..");
	init_DS18B20(TSensor, t_sensor_names);
}


/* ---------------------------------- LOOP -------------------------------- */

void loop() {

	// TEMP_READOUT
	TickType_t uptimeTicks = xTaskGetTickCount() - g_ticks_last_req;
	u64_t uptime = (u64_t)(uptimeTicks * portTICK_PERIOD_MS);
	
	if (uptime > (last_temp_reading + temp_reading_freq)) {
		for (int i=0; i<MAX_TEMP_SENSORS; i++) {
			TSensor[i].last_reading = DS18B20.getTempC(TSensor[i].addr);
		}
		_copy_to_daqb(TSensor, &uptime);
		last_temp_reading = uptime;
	}

	// SERVER
	http_server.handleClient();
	delay(5);
}
