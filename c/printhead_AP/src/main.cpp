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
#include "si5351.h"

#include "printhead_support.h"

/* --------------------------- VARIABLES & CLASSES ------------------------ */

// ETH
WebServer http_server(HTTP_SERVER_PORT);
bool eth_connected = false;

// SI5351
Si5351 clk_gen;
float curr_freq = 0;
float steps_per_rot = 20000.0;
bool clk_running = false;

// PINCH
bool curr_pinch = false;

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
	Serial.println("PHdM:\t           PRINTHEAD_AP         ");
	Serial.println("PHdM:\t--------------------------------\n");

	// ETH
	Serial.println("ETHN:\tsetting up event handler..");
	// using the WiFi event handling setup here, but this response
	// to the Ethernet port of the OLIMEX PoE IsO when using ETH.h
	WiFi.onEvent(WiFiEvent);
	ETH.begin();
	init_uri();
	if (!MDNS.begin("printhead_interface")) {
		Serial.println("ETHN:\tmDNS setup failed, restarting..");
		Serial.flush();
		ESP.restart();
	}

	// SI5351
	Serial.println("CLKG:\tinit SI5351 clock generation..");
    clk_gen.init(SI5351_CRYSTAL_LOAD_10PF, 25000000, 0);    
    clk_gen.set_ms_source(SI5351_CLK0, SI5351_PLLA);
    clk_gen.set_pll_input(SI5351_PLLA, SI5351_PLL_INPUT_XO);

	// PINCH
	pinMode(PINCH_PIN, OUTPUT);
	digitalWrite(PINCH_PIN, LOW);

	// TEMP_READOUT
	Serial.println("TEMP:\tinit DS18B20..");
	init_DS18B20(TSensor, t_sensor_names);
	//xTaskCreate()
}


/* ---------------------------------- LOOP -------------------------------- */

void loop() {
	// SI5351
	float rps = g_motor_rpm / 60.0;
	uint64_t freq_target = (uint64_t)(rps * steps_per_rot);

	if (curr_freq != freq_target) {
		if (freq_target == 0) {
			clk_gen.output_enable(SI5351_CLK0, 0);
			curr_freq = 0;
			clk_running = false;
			Serial.println("CLKG:\tclk stopped.");
		} else {
			// use simple p-controller for acceleration ramp
			curr_freq += P_CTRL_CONST * (freq_target - curr_freq);
			clk_gen.set_freq(curr_freq * 100ULL, SI5351_CLK0);

			if (!clk_running) {
				clk_gen.output_enable(SI5351_CLK0, 1);
				clk_gen.drive_strength(SI5351_CLK0, SI5351_DRIVE_2MA);
				clk_running = true;
				Serial.println("CLKG:\tclk started.");
			}
		}
		Serial.printf("CLKG:\tfreq set to %f\n", curr_freq);
	}

	// PINCH
	bool new_pinch = g_pinch_state;
	if (curr_pinch != new_pinch) {
		curr_pinch = new_pinch;
		if (new_pinch) digitalWrite(PINCH_PIN, HIGH);
		else digitalWrite(PINCH_PIN, LOW);
	}

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

