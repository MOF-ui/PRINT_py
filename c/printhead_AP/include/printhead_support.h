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

#ifndef PRINTHEAD_SUPPORT_H
#define PRINTHEAD_SUPPORT_H

/* -------------------------- IMPORTS & DEFINITIONS ----------------------- */

#include <Arduino.h>

#include "WebServer.h"
#include "ESPmDNS.h"
#include "OneWire.h"
#include "DallasTemperature.h"

// open server on 'quote of the day' port because we can
#define HTTP_SERVER_PORT    17

#define MAX_TEMP_SENSORS    2
#define BACKLOG_SIZE        200
#define DAQB_STR_SIZE       128
#define POST_MAX_CONT_LEN   100
#define IP_MAX_STR_LEN      64

#define ONE_WIRE_PIN 		0

#define PINCH_PIN 			33
#define P_CTRL_CONST        0.02    // 2 %
#define P_CTRL_MAX_STEP     200

/* --------------------------- VARIABLES & CLASSES ------------------------ */

#ifdef __cplusplus
extern "C" {
#endif

// ETH
extern WebServer http_server;
struct daq_block
{
    float temp[MAX_TEMP_SENSORS];
    u64_t upt_s;
};

extern const struct daq_block g_EMPTY_DAQ_BLOCK;
extern struct daq_block g_measure_buff[BACKLOG_SIZE];
extern unsigned long g_millis_last_req;
extern float g_motor_rpm;
extern int g_backlog_idx;
extern bool g_pinch_state;
extern bool g_data_lost;

// DS18B20
extern OneWire OWB;
extern DallasTemperature DS18B20;
struct t_block {
	char name[16];
	DeviceAddress addr; // = { 0x28, 0x1D, 0x39, 0x31, 0x2, 0x0, 0x0, 0xF0 };
	float last_reading;
	bool is_connected;
};
extern uint8_t g_num_temp_devices;


/* -------------------------------- FUNCTIONS ----------------------------- */

// DS18B20
void init_DS18B20(struct t_block* TSensor, String* t_sensor_names);

// ETH
void init_uri(void);
void root_handler(void);
void freq_post(void);
void pinch_post(void);
void data_request(void);
void ping_request(void);
void restart_post(void);
void http_404_handler(void);
void http_405_handler(void);

/* ---------------------------- PRIVATE FUNCTIONS ------------------------- */

void _daq2str(
        struct daq_block *daqb,
        char *sz_ret,
        int buff_len,
        u16_t curr_upt_s
);
void _copy_to_daqb(const t_block* tb, u64_t* uptime);
void _print_client_ip(const char* source);
boolean _retrieve_post_body(char* recv_c);

#ifdef __cplusplus
}
#endif

#endif