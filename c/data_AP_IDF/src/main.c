/* 
following examples from
    espressif: http_server, ethernet_example
    OLIMEX: ESP32_PoE_Ethernet_IDFv5.3
    David Antliff: ds18b20_example
*/

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
#include "owb.h"
#include "owb_rmt.h"
#include "ds18b20.h"

#include "sdkconfig.h"

#define GPIO_DS18B20_0      4
#define DS18B20_RESOLUTION  DS18B20_RESOLUTION_12_BIT
#define SAMPLE_PERIOD       10000   // milliseconds
#define BACKLOG_SIZE        1000
#define DAQB_STR_SIZE       20

SemaphoreHandle_t xMutex = NULL;

struct daq_block
{
    float temp;
    bool error;
    unsigned int upt_s;
};

static const char *g_TAG = "DAQ_S";
static bool g_connected = false;

static struct daq_block g_measure_buff[BACKLOG_SIZE];
static int g_backlog_idx = 0;
static bool data_lost = false;
static const struct daq_block g_EMPTY_DAQ_BLOCK = {0};

static TickType_t ticks_last_data_req = 0;



/* -------------------------------- OWB MAIN ----------------------------- */

void owb_main()
{
    // initialize
    const char *OWB_TAG = "OWB_COMM";
    OneWireBus *owb;
    owb_rmt_driver_info rmt_driver_info;
    owb = owb_rmt_initialize(&rmt_driver_info, GPIO_DS18B20_0, RMT_CHANNEL_1, RMT_CHANNEL_0);
    owb_use_crc(owb, true);  // enable CRC check for ROM code

    // Find all connected devices
    ESP_LOGI(OWB_TAG, "Searching connected devices:");
    int num_devices = 0;
    OneWireBus_SearchState search_state = {0};
    bool found = false;

    owb_search_first(owb, &search_state, &found);
    while (found) 
    {
        char rom_code_s[17];
        owb_string_from_rom_code(search_state.rom_code, rom_code_s, sizeof(rom_code_s));
        ESP_LOGI(OWB_TAG, " Device %d: %s", num_devices, rom_code_s);
        ++num_devices;
        owb_search_next(owb, &search_state, &found);
    }
    ESP_LOGI(OWB_TAG, "Found %d device%s", num_devices, num_devices == 1 ? "" : "s");

    // see how many
    if (num_devices == 1) 
    {
        OneWireBus_ROMCode rom_code;
        owb_status status = owb_read_rom(owb, &rom_code);

        if (status == OWB_STATUS_OK) 
        {
            char rom_code_s[OWB_ROM_CODE_STRING_LENGTH];
            owb_string_from_rom_code(rom_code, rom_code_s, sizeof(rom_code_s));
            ESP_LOGI(OWB_TAG, "Devise ROM code: %s", rom_code_s);
        
        } else {
            ESP_LOGE(OWB_TAG, "An error occurred reading ROM code: %d", status);
        }

        // Create DS18B20 devices on the 1-Wire bus
        DS18B20_Info *ds18b20_info = ds18b20_malloc();  // heap allocation

        ESP_LOGI(OWB_TAG, "Single device optimisations enabled");
        ds18b20_init_solo(ds18b20_info, owb);
        ds18b20_use_crc(ds18b20_info, true); // enable CRC check on all reads
        ds18b20_set_resolution(ds18b20_info, DS18B20_RESOLUTION);

        // turn of parasitic power
        owb_use_parasitic_power(owb, false);
        
        // start measurement loop
        while(1) 
        {
            float reading = 0;
            DS18B20_ERROR error = {0};
            bool commError = false;

            // read temp, wait for DS18B20
            ds18b20_convert_all(owb);
            ds18b20_wait_for_conversion(ds18b20_info);
            error = ds18b20_read_temp(ds18b20_info, &reading);
            if (error != DS18B20_OK) commError = true;

            // get mutex
            xSemaphoreTake( xMutex, portMAX_DELAY );

            TickType_t uptimeTicks = xTaskGetTickCount() - ticks_last_data_req;
            long unsigned uptime = (long unsigned)(uptimeTicks * portTICK_PERIOD_MS);
            ESP_LOGI(OWB_TAG, "  %i: T [°C]: %.1f; err: %d; uptime [ms]: %lu", g_backlog_idx, reading, commError, uptime);

            // save to the backlog, first check needed to avoid index error
            if (g_backlog_idx != 0) 
            {
                g_measure_buff[g_backlog_idx].temp = reading;
                g_measure_buff[g_backlog_idx].error = commError;
                g_measure_buff[g_backlog_idx].upt_s = (int)(uptime / 1000); // just communicate seconds

                g_backlog_idx++;

                // check if the backlog is full, if so throw of the oldest measurement
                if (g_backlog_idx >= (BACKLOG_SIZE - 1)) 
                {
                    data_lost = true;
                    for (int idx=1; idx < BACKLOG_SIZE; idx++) 
                    {
                        g_measure_buff[idx - 1] = g_measure_buff[idx];
                    }
                    g_backlog_idx = BACKLOG_SIZE - 2; // -1 for of-by-zero & -1 since we made 1 space
                    ESP_LOGE(OWB_TAG, "Backlog full, oldest entry overwritten!");
                }
            } 
            else // first measurement since last request, reset error_counter
            {
                g_measure_buff[g_backlog_idx].temp = reading;
                g_measure_buff[g_backlog_idx].error = commError;
                g_measure_buff[g_backlog_idx].upt_s = (int)(uptime / 1000);
                g_backlog_idx++;
            }

            // release mutex
            xSemaphoreGive( xMutex );

            // wait
            vTaskDelay(SAMPLE_PERIOD / portTICK_PERIOD_MS);
        }

    } else {
        ESP_LOGI(OWB_TAG, "Found %i devises, expected 1!", num_devices);
    }

    owb_uninitialize(owb);
    ESP_LOGI(OWB_TAG, "Restarting in 1s.");
    fflush(stdout);
    vTaskDelay(1000 / portTICK_PERIOD_MS);
    esp_restart();
}


/* --------------------------------- DAQ2STR ------------------------------ */

void daq2str(struct daq_block *daqb, char *sz_ret, int buff_len) {  
    // sz_ret for string-zero (\0 terminated) return 
    
    int temp_len = snprintf(NULL, 0, "%.2f", daqb->temp);
    char *temp = malloc(temp_len + 1); // +1 for string terminator
    snprintf(temp, temp_len + 1, "%.2f", daqb->temp);
    
    int err_len = snprintf(NULL, 0, "%d", daqb->error);
    char *err = malloc(err_len + 1);
    snprintf(err, err_len + 1, "%d", daqb->error);
    
    int upt_len = snprintf(NULL, 0, "%u", daqb->upt_s);
    char *upt = malloc(upt_len + 1);
    snprintf(upt, upt_len + 1, "%u", daqb->upt_s);
    
    // build str
    strlcpy(sz_ret, "T", buff_len);
    strlcat(sz_ret, temp, buff_len);
    strlcat(sz_ret, "/E", buff_len);
    strlcat(sz_ret, err, buff_len);
    strlcat(sz_ret, "/U", buff_len);
    strlcat(sz_ret, upt, buff_len);
    strlcat(sz_ret, ";", buff_len);

    free(temp);
    free(err);
    free(upt);
}


/* -------------------------------- WEBSERVER ----------------------------- */

// http GET handler as data request
static esp_err_t data_request(httpd_req_t *req)
{
    // get client IP
    int sockfd = httpd_req_to_sockfd(req);
    char ipstr[INET6_ADDRSTRLEN];
    struct sockaddr_in6 addr;   // esp_http_server uses IPv6 addressing
    socklen_t addr_size = sizeof(addr);
    getpeername(sockfd, (struct sockaddr *)&addr, &addr_size);
    
    // Convert to IPv6 string
    inet_ntop(AF_INET6, &addr.sin6_addr, ipstr, sizeof(ipstr));
    ESP_LOGI(g_TAG, "data request from: %s", ipstr);
    
    // set answering header
    httpd_resp_set_hdr(req, "Allow", "GET");

    // get mutex
    xSemaphoreTake( xMutex, portMAX_DELAY );
    
    // answer with data if available
    static char data_str[BACKLOG_SIZE * DAQB_STR_SIZE];
    
    if(g_backlog_idx == 0) 
    {
        strlcpy(data_str, "no data available", sizeof(data_str));
    }
    else
    {
    // if avaiable write everything to http str, reset data struct to 0

        if (data_lost) {
            strlcpy(data_str, "DL=true&", sizeof(data_str));
        } else {
            strlcpy(data_str, "DL=false&", sizeof(data_str));
        }

        for (int idx=0; idx < g_backlog_idx; idx++) 
        {
            static char daqb_str[DAQB_STR_SIZE];
            memset(daqb_str, '\0', sizeof(daqb_str));

            daq2str(&g_measure_buff[idx], daqb_str, DAQB_STR_SIZE);
            strlcat(data_str, daqb_str, sizeof(data_str));
            g_measure_buff[idx] = g_EMPTY_DAQ_BLOCK;
        }
        g_backlog_idx = 0;
        data_lost = false;
    }
    ticks_last_data_req = xTaskGetTickCount();

    // release mutex handle
    xSemaphoreGive( xMutex );

    ESP_LOGI(g_TAG, "returning: %s", data_str);
    httpd_resp_send(req, data_str, HTTPD_RESP_USE_STRLEN);


    return ESP_OK;
}

static const httpd_uri_t data_req = {
    .uri       = "/data",
    .method    = HTTP_GET,
    .handler   = data_request,
    .user_ctx  = NULL,
};

// 400 handler
esp_err_t http_400_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "malformed request!");
    return ESP_FAIL;
}

// 404 handler
esp_err_t http_404_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_send_err(req, HTTPD_404_NOT_FOUND, "no such resource");
    return ESP_FAIL;
}

// 405 handler
esp_err_t http_405_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_set_hdr(req, "Allow", "GET");
    httpd_resp_send_err(req, HTTPD_405_METHOD_NOT_ALLOWED, "only GET methods");
    return ESP_FAIL;
}

// start server
static httpd_handle_t start_daqs(void)
{
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    // start the server on 'quote of the day' port for funsies
    config.server_port = 17;

    // Start the httpd server
    ESP_LOGI(g_TAG, "Starting server on port: '%d'", config.server_port);
    if (httpd_start(&server, &config) == ESP_OK) {
        
        // set URIs
        httpd_register_uri_handler(server, &data_req);

        // set error handlers
        httpd_register_err_handler(server, HTTPD_400_BAD_REQUEST, http_400_handler);
        httpd_register_err_handler(server, HTTPD_404_NOT_FOUND, http_404_handler);
        httpd_register_err_handler(server, HTTPD_405_METHOD_NOT_ALLOWED, http_405_handler);

        return server;
    }

    ESP_LOGI(g_TAG, "Error starting server!");
    return NULL;
}

// stop server
static esp_err_t stop_daqs(httpd_handle_t server)
{
    return httpd_stop(server);
}


/* ----------------------------- ETHERNET EVENTS -------------------------- */

static void eth_event_handler(
        void *arg,
        esp_event_base_t event_base,
        int32_t event_id,
        void *event_data
    )
{
    esp_eth_handle_t eth_handle = *(esp_eth_handle_t *)event_data;
    httpd_handle_t* server = (httpd_handle_t*) arg;

    switch (event_id) {

    case ETHERNET_EVENT_CONNECTED:
        g_connected = true;

        uint8_t mac_addr[6] = {0};
        esp_eth_ioctl(eth_handle, ETH_CMD_G_MAC_ADDR, mac_addr);

        ESP_LOGI(g_TAG, "Ethernet Link Up");
        ESP_LOGI(g_TAG, "Ethernet HW Addr %02x:%02x:%02x:%02x:%02x:%02x",
                 mac_addr[0], mac_addr[1], mac_addr[2], mac_addr[3], mac_addr[4], mac_addr[5]);

        if (*server == NULL) {
            *server = start_daqs();
        }

        break;

    case ETHERNET_EVENT_DISCONNECTED:
        g_connected = false;

        ESP_LOGI(g_TAG, "Ethernet Link Down..");

        if (*server) {
            ESP_LOGI(g_TAG, "stopping http server");
            if (stop_daqs(*server) == ESP_OK) {
                *server = NULL;
            } else {
                ESP_LOGE(g_TAG, "Failed to stop http server");
            }
        }

        break;

    case ETHERNET_EVENT_START:
        ESP_LOGI(g_TAG, "Ethernet Started");

        break;

    case ETHERNET_EVENT_STOP:
        ESP_LOGI(g_TAG, "Ethernet Stopped");

        break;

    default:
        break;
    }
}

/** Event handler for IP_EVENT_ETH_GOT_IP */
static void got_ip_event_handler(void *arg, esp_event_base_t event_base,
                                 int32_t event_id, void *event_data)
{
    ip_event_got_ip_t *event = (ip_event_got_ip_t *) event_data;
    const esp_netif_ip_info_t *ip_info = &event->ip_info;

    ESP_LOGI(g_TAG, "Ethernet Got IP Address");
    ESP_LOGI(g_TAG, "~~~~~~~~~~~");
    ESP_LOGI(g_TAG, "ETHIP:" IPSTR, IP2STR(&ip_info->ip));
    ESP_LOGI(g_TAG, "ETHMASK:" IPSTR, IP2STR(&ip_info->netmask));
    ESP_LOGI(g_TAG, "ETHGW:" IPSTR, IP2STR(&ip_info->gw));
    ESP_LOGI(g_TAG, "~~~~~~~~~~~");
}


/* ---------------------------------- MAIN ------------------------------- */

void app_main(void)
{
    
    static httpd_handle_t daqs = NULL;
    ESP_ERROR_CHECK(nvs_flash_init());
    ESP_LOGI(g_TAG, "                     ");
    ESP_LOGI(g_TAG, "   DAQS STARTING UP  ");
    ESP_LOGI(g_TAG, "                     ");

    // mutual exclusion init
    xMutex = xSemaphoreCreateMutex();

    // init MAC
    ESP_LOGI(g_TAG, "init mac..");
    eth_mac_config_t mac_cfg = ETH_MAC_DEFAULT_CONFIG();
    eth_esp32_emac_config_t emac_cfg = ETH_ESP32_EMAC_DEFAULT_CONFIG();
    //emac_cfg.smi_mdc_gpio_num = 23;
    //emac_cfg.smi_mdio_gpio_num = 18;
    // emac_cfg.clock_config.rmii.clock_gpio = 17;
    esp_eth_mac_t *mac = esp_eth_mac_new_esp32(&emac_cfg, &mac_cfg);

    // turn on PHY on designated pin following espressif/esp-idf issue #12557 (github)
    ESP_LOGI(g_TAG, "turn on phy via pin..");
    const gpio_num_t phy_power_pin = 12;
    gpio_config_t phy_power_conf = {0};
    phy_power_conf.mode = GPIO_MODE_OUTPUT;
    phy_power_conf.pin_bit_mask = (1ULL << phy_power_pin);
    ESP_ERROR_CHECK(gpio_config(&phy_power_conf));
    ESP_ERROR_CHECK(gpio_set_level(phy_power_pin, 1));

    // give the phy time to power up
    TickType_t phy_wait = 1000 / portTICK_PERIOD_MS;
    vTaskDelay(phy_wait);

    // init PHY
    ESP_LOGI(g_TAG, "init phy..");
    eth_phy_config_t phy_cfg = ETH_PHY_DEFAULT_CONFIG();
    //phy_cfg.reset_gpio_num = -1;
    //phy_cfg.phy_addr = 0;
    esp_eth_phy_t *phy = esp_eth_phy_new_lan87xx(&phy_cfg);

    // create eth handle
    ESP_LOGI(g_TAG, "install ethernet..");
    esp_eth_handle_t eth_handle = NULL;
    esp_eth_config_t eth_cfg = ETH_DEFAULT_CONFIG(mac, phy);
    esp_eth_driver_install(&eth_cfg, &eth_handle);
    ESP_LOGI(g_TAG, "starting network interface..");

    // setup network interface
    ESP_ERROR_CHECK(esp_netif_init());
    esp_netif_config_t netif_cfg = ESP_NETIF_DEFAULT_ETH();
    esp_netif_t *eth_netif = esp_netif_new(&netif_cfg);

    // start event handling and glue handle to netif
    ESP_ERROR_CHECK(esp_event_loop_create_default());
    ESP_ERROR_CHECK(
        esp_netif_attach(eth_netif,esp_eth_new_netif_glue(eth_handle))
    );
    ESP_ERROR_CHECK(
        esp_event_handler_register(
            ETH_EVENT,
            ESP_EVENT_ANY_ID,
            &eth_event_handler,
            &daqs)
    );
    ESP_ERROR_CHECK(
        esp_event_handler_register(
            IP_EVENT,
            IP_EVENT_ETH_GOT_IP,
            &got_ip_event_handler,
            &daqs)
    );

    ESP_ERROR_CHECK(esp_eth_start(eth_handle));

    ESP_LOGI(g_TAG, "waiting for network..");
    while (!g_connected) {
        TickType_t netw_wait = 3000 / portTICK_PERIOD_MS;
        vTaskDelay(netw_wait);
    }

    if (!daqs) daqs = start_daqs();

    owb_main();

    while (daqs) {
        TickType_t loop_delay = 100 / portTICK_PERIOD_MS; 
        vTaskDelay(loop_delay);
    }
}