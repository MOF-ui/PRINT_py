
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
#include "temp_readout.h"

/* -------------------------------- VARIABLES ----------------------------- */


int g_sensors_found = 0;
const char *g_OWB_TAG = "OWB_COMM";
DS18B20_Info *temp_sensors[MAX_TEMP_SENSORS] = {0};
OneWireBus *g_owb;

/* -------------------------------- FUNCTIONS ----------------------------- */

// initialize the one-wire bus
void temp_readout_init()
{
    owb_rmt_driver_info rmt_driver_info;
    g_owb = owb_rmt_initialize(
        &rmt_driver_info,
        GPIO_DS18B20_0,
        RMT_CHANNEL_1,
        RMT_CHANNEL_0
    );
    owb_use_crc(g_owb, true);  // enable CRC check for ROM code
}

// find & log all devices on the OWB, set sensors_found toggle
void temp_readout_find() 
{
    // Find all connected devices
    ESP_LOGI(g_OWB_TAG, "Searching connected devices:");
    int num_devices = 0;
    OneWireBus_SearchState search_state = {0};
    OneWireBus_ROMCode device_rom_codes[MAX_TEMP_SENSORS] = {0};
    bool found = false;

    owb_search_first(g_owb, &search_state, &found);
    while (found) 
    {
        char rom_code_s[17];
        owb_string_from_rom_code(
            search_state.rom_code,
            rom_code_s,
            sizeof(rom_code_s)
        );
        ESP_LOGI(g_OWB_TAG, " Device %d: %s", num_devices, rom_code_s);
        device_rom_codes[num_devices] = search_state.rom_code;
        ++num_devices;
        owb_search_next(g_owb, &search_state, &found);
    }
    ESP_LOGI(g_OWB_TAG, "Found %d devices", num_devices);

    // see if at least one was found
    if (num_devices > 0) {
        // Create DS18B20 devices on the 1-Wire bus
        for (int i=0; i < num_devices; i++) {
            DS18B20_Info *ds18b20_info = ds18b20_malloc();
            temp_sensors[i] = ds18b20_info;
            if (num_devices == 1) {
                ESP_LOGI(g_OWB_TAG, "Single device optimisations enabled");
                ds18b20_init_solo(ds18b20_info, g_owb);
            } else {
                ds18b20_init(ds18b20_info, g_owb, device_rom_codes[i]);
            }
            ds18b20_use_crc(ds18b20_info, true);
            ds18b20_set_resolution(ds18b20_info, DS18B20_RESOLUTION);
        }
        owb_use_parasitic_power(g_owb, false);
        g_sensors_found = num_devices;
    } else {
        g_sensors_found = 0;
    }
}

// get readings from all present devices
void temp_readout_all(float* readings[MAX_TEMP_SENSORS], u64_t* uptime)
{
    // dont use uninitialized pointers, init all to default
    float t_faulty = T_FALSE;
    u64_t upt_faulty = 0;
    for (int i=0; i<MAX_TEMP_SENSORS; i++) {
        readings[i] = &t_faulty;
    }
    uptime = &upt_faulty;

    // start readout
    if (g_sensors_found < 1) {
        ESP_LOGI(g_OWB_TAG, "Readout requested, but no devices present!");
        return;
    }
    ds18b20_convert_all(g_owb); // start temp reading
    // (time is the same for all, so just wait for the first one)
    ds18b20_wait_for_conversion(temp_sensors[0]);
    TickType_t uptimeTicks = xTaskGetTickCount() - g_ticks_last_req;
    *uptime = (u64_t)(uptimeTicks * portTICK_PERIOD_MS);

    // copy readings
    for (int i=0; i<g_sensors_found; i++) {
        DS18B20_ERROR err = ds18b20_read_temp(temp_sensors[i], readings[i]);
        if (err != DS18B20_OK) *readings[i] = T_FALSE;
        ESP_LOGI(
            g_OWB_TAG,
            "  %i: T [°C]: %.1f; uptime [ms]: %lu",
            g_backlog_idx,
            *readings[i],
            (long unsigned)*uptime
        );
    }
}

void temp_readout_uninit_owb()
{
    owb_uninitialize(g_owb);
}