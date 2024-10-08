#ifndef TEMP_READOUT_H
#define TEMP_READOUT_H

/* --------------------------------- IMPORTS ------------------------------ */

#include <stdio.h>
#include <string.h>
#include <nvs_flash.h>
#include <sys/param.h>
#include <sys/socket.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"

#include "esp_netif.h"
#include "esp_eth.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_http_server.h"

#include "driver\gpio.h"
#include "driver\i2c.h"
#include "owb.h"
#include "owb_rmt.h"
#include "ds18b20.h"

#include "sdkconfig.h"
#include "uri_handlers_inline.h"

/* -------------------------------- VARIABLES ----------------------------- */

#define GPIO_DS18B20_0      4
#define DS18B20_RESOLUTION  DS18B20_RESOLUTION_12_BIT
#define SAMPLE_PERIOD       5000   // milliseconds
#define T_FALSE             -274.0

#ifdef __cplusplus
extern "C" {
#endif

// global const
const char *g_OWB_TAG;

// global vars
int g_sensors_found;
DS18B20_Info *temp_sensors[MAX_TEMP_SENSORS];
OneWireBus *g_owb;

/* -------------------------------- FUNCTIONS ----------------------------- */

void temp_readout_init(void);
void temp_readout_find(void);
void temp_readout_all(float* readings[MAX_TEMP_SENSORS], u64_t* uptime);
void temp_readout_uninit_owb(void);

#ifdef __cplusplus
}
#endif

#endif