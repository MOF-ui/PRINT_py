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
#include "WebServer.h"
#include "ESPmDNS.h"
#include "OneWire.h"
#include "DallasTemperature.h"

#include "data_AP_support.h"

/* --------------------------- VARIABLES & CLASSES ------------------------ */

// ETH
const struct daq_block g_EMPTY_DAQ_BLOCK = {0};
struct daq_block g_measure_buff[BACKLOG_SIZE] = {0};
TickType_t g_ticks_last_req = 0;
int g_backlog_idx = 0;
bool g_data_lost = false;

// DS18B20
OneWire OWB(ONE_WIRE_PIN);
DallasTemperature DS18B20(&OWB);

/* -------------------------------- FUNCTIONS ----------------------------- */

// init bus, find known devices
void init_DS18B20(
        struct t_block* TSensor,
        String t_sensor_names[MAX_TEMP_SENSORS]
)
{
	DS18B20.begin();
	Serial.println("TEMP:\tsearching for DS18B20..");
	uint8_t num_temp_devices = DS18B20.getDeviceCount();
	Serial.printf(
		"TEMP:\tfound: %d of %u.\n",
		num_temp_devices,
		MAX_TEMP_SENSORS
	);

	// FIRST DEVICE ROM ADDRESS READING
	Serial.print("TEMP:\tpre_lim addresses ");
	for (int i=0; i<MAX_TEMP_SENSORS; i++) {
        for (int k=0; k<sizeof(t_sensor_names[i]); k++) {
		    TSensor[i].name[k] = t_sensor_names[i][k];
        }
		DS18B20.getAddress(TSensor[i].addr, i);
		Serial.printf("-- Device %d ->", i);
		for (int j=0; j<8; j++) {
			Serial.printf("%d:", TSensor[i].addr[j]);
		}
	}
	Serial.println();
	// END OF: FIRST DEVICE ROM ADDRESS READING

	for (int i=0; i<MAX_TEMP_SENSORS; i++) {
		TSensor[i].is_connected = DS18B20.isConnected(TSensor[i].addr);
		if (!TSensor[i].is_connected) {
			Serial.printf("TEMP:\t%s DS18B20 missing!\n", TSensor[i].name);
		}
		else {
			DS18B20.setResolution(TSensor[i].addr, 12); // setting to 12-bit res
		}
	}
}

// initialize g_MUTEX handle
void init_uri()
{
	Serial.println("HTTP:\tsetting up ETH events..");
    http_server.on("/", HTTP_GET, root_handler);
    http_server.on("/data", HTTP_GET, data_request);
    http_server.on("/ping", HTTP_GET, ping_request);
    http_server.on("/restart", HTTP_POST, restart_post);
    http_server.onNotFound(http_404_handler);
}

void root_handler() 
{
    _print_client_ip("root");
    http_server.send(200, "text/plain", "The Krauts want you for 3DCP.");
}

// returns all backlogged data to IP request (LIFO) with heading data-lost
// token; prints requests IP first
void data_request()
{
    static char data_str[DAQB_STR_SIZE * BACKLOG_SIZE];
    _print_client_ip("data");

    if(g_backlog_idx == 0) {
        strlcpy(data_str, "no data available", DAQB_STR_SIZE * BACKLOG_SIZE);
    } else {
        // if avaiable write everything to http str, reset data struct to 0
        if (g_data_lost) {
            strlcpy(data_str, "DL=true&", DAQB_STR_SIZE * BACKLOG_SIZE);
        }
        else {
            strlcpy(data_str, "DL=false&", DAQB_STR_SIZE * BACKLOG_SIZE);
        }

        // calc current uptime to get the age of each value in _daq2str
        TickType_t curr_uptime_ticks = xTaskGetTickCount() - g_ticks_last_req;
        u64_t curr_uptime = (u64_t)(curr_uptime_ticks * portTICK_PERIOD_MS);
        u64_t curr_uptime_s = (u64_t)(curr_uptime / 1000);

        // build ans str
        for (int idx=0; idx < g_backlog_idx; idx++) {
            static char daqb_str[DAQB_STR_SIZE];
            memset(daqb_str, '\0', sizeof(daqb_str));
            _daq2str(
                &g_measure_buff[idx],
                daqb_str,
                DAQB_STR_SIZE,
                curr_uptime_s
            );
            strlcpy(data_str, daqb_str, DAQB_STR_SIZE * BACKLOG_SIZE);
            g_measure_buff[idx] = g_EMPTY_DAQ_BLOCK;
        }
        g_backlog_idx = 0;
        g_data_lost = false;
        g_ticks_last_req = xTaskGetTickCount();
    }

    // send answer
    http_server.sendHeader("Allow", "GET");
    http_server.send(200, "text/plain", data_str);
    Serial.printf("HTTP:\treturning: %s\n", data_str);
}

// returns 'ack' to ping request from IP client
void ping_request()
{
    _print_client_ip("ping");
    http_server.sendHeader("Allow", "GET");
    http_server.send(200, "text/plain", "ack");
    Serial.printf("HTTP:\treturning: ack\n");
}

// restart ESP, if correct token is passed
void restart_post()
{
    static char recv_c[POST_MAX_CONT_LEN] = {0};
    static const char* token = "always_look_on_the_bright_side_of_life";
    _print_client_ip("restart");
    _retrieve_post_body(recv_c);

    if ( strcmp(recv_c, token) == 0 ) { //strcmp returns 0 on match
        Serial.println("HTTP:\tcorrect restart token.");
        Serial.println("HTTP:\trestarting in 1s");
        Serial.flush();
        http_server.send(200, "text/plain", "ack");
        delay(1000);
        http_server.stop();
        ESP.restart();
    } else {
        Serial.println("HTTP:\trestart token invalid.");
        http_server.send(400, "text/plain", "token invalid");
    }
}

// 400 HANDLER
void http_404_handler(void)
{
    Serial.printf(
        "HTTP:\t404 error on %s by %s",
        http_server.method(),
        http_server.client().remoteIP().toString()
    );
    http_server.send(404, "text/plain", "no such ressource");
}

/* ---------------------------- PRIVATE FUNCTIONS ------------------------- */

// short-hand function to construct string from daq_block list entry
// sz_ret for string-zero ('\0' terminated) return
void _daq2str(
        struct daq_block *daqb,
        char *sz_ret,
        int buff_len,
        u16_t curr_upt_s
) {  
    // save bytes by setting wrong T measurements to -274
    // (impossible temperature)
    for (int i=0; i<MAX_TEMP_SENSORS; i++){
        int temp_len = snprintf(NULL, 0, "%.2f", daqb->temp[i]);
        char *temp_char = (char *) malloc(temp_len + 1); // +1 for string terminator
        snprintf(temp_char, temp_len + 1, "%.2f", daqb->temp[i]);
        
        // build str
        char *count = (char *) malloc(5);
        snprintf(count, 5, "_T%d>", i);
        strlcpy(sz_ret, count, buff_len);
        strlcat(sz_ret, temp_char, buff_len);
        
        free(temp_char);
        free(count);
    }

    // calc age of entry
    u64_t age_s = curr_upt_s - daqb->upt_s;
    int age_len = snprintf(NULL, 0, "%llu", age_s);
    char *age = (char *) malloc(age_len + 1);
    snprintf(age, age_len + 1, "%llu", age_s);

    // attach uptime
    strlcat(sz_ret, "/U", buff_len);
    strlcat(sz_ret, age, buff_len);
    strlcat(sz_ret, ";", buff_len);

    free(age);
}

// copies pointer-array stored data to daqb struct
// keeps track of backlog_idx & data loss
void _copy_to_daqb(const t_block* tb, u64_t* uptime)
{
    // xSemaphoreTake(g_MUTEX, portMAX_DELAY);
    // save to the backlog, first check needed to avoid index error
    if (g_backlog_idx != 0)
    {
        for (int i=0; i<MAX_TEMP_SENSORS; i++) {
            g_measure_buff[g_backlog_idx].temp[i] = tb[i].last_reading;
        }
        // just communicate seconds
        g_measure_buff[g_backlog_idx].upt_s = (u64_t)(*uptime / 1000);
        g_backlog_idx++;

        // check if the backlog is full
        // if so throw of the oldest measurement
        if (g_backlog_idx >= (BACKLOG_SIZE - 1)) 
        {
            g_data_lost = true;
            for (int idx=1; idx < BACKLOG_SIZE; idx++) 
            {
                g_measure_buff[idx - 1] = g_measure_buff[idx];
            }
            // -1 for off-by-zero & -1 since we made 1 space
            g_backlog_idx = BACKLOG_SIZE - 2; 
            Serial.println("TEMP:\tBacklog full, oldest entry overwritten!");
        }
    } else { 
        // first measurement since last request, reset error_counter
        for (int i=0; i<MAX_TEMP_SENSORS; i++) {
            g_measure_buff[g_backlog_idx].temp[i] = tb[i].last_reading;
        }
        g_measure_buff[g_backlog_idx].upt_s = (u16_t)(*uptime / 1000);
        g_backlog_idx++;
    }
    // xSemaphoreGive(g_MUTEX);
}

void _print_client_ip(const char* source)
{
    // convert the bloody String so it can be printed
    static char ip[IP_MAX_STR_LEN];
    String ip_str = http_server.client().remoteIP().toString();

    for (int i=0; i<ip_str.length(); i++) ip[i] = ip_str[i];
    ip[ip_str.length() + 1] = '\0';

    // print
    Serial.printf(
        "HTTP:\t%s %s request from: %s\n",
        source,
        (http_server.method() == HTTP_GET) ? "GET" : "POST",
        ip
    );
}

// writes plain text body of POST request to recv_c buffer;
// which have to have the minimum size of POST_MAX_CONT_LEN 
void _retrieve_post_body(char* recv_c)
{
    // read content; fight with the String again
    String recv = http_server.arg("plain");
    int recv_len = recv.length();
    if (recv_len >= POST_MAX_CONT_LEN) {
        http_server.send(400, "text/plain", "body to large");
        Serial.printf("HTTP:\tFAILED. Body to large.\n");
        return;
    }
    for (int i=0; i<recv.length(); i++) {
        recv_c[i] = recv[i];
    }
    recv_c[recv.length() + 1] = '\0';
    Serial.printf("HTTP:\treceived: %s\n", recv_c);
}