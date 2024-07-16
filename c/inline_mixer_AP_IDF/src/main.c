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

#include "sdkconfig.h"

#define GPIO_DS18B20_0      4
#define DS18B20_RESOLUTION  DS18B20_RESOLUTION_12_BIT
#define SAMPLE_PERIOD       5000   // milliseconds
#define BACKLOG_SIZE        1000
#define DAQB_STR_SIZE       25

SemaphoreHandle_t xMutex = NULL;

struct daq_block
{
    float temp;
    bool error;
    u16_t upt_s;
};

static const char *g_TAG = "DAQ_S";
static bool g_connected = false;

static struct daq_block g_measure_buff[BACKLOG_SIZE];
static int g_backlog_idx = 0;
static bool g_data_lost = false;
static const struct daq_block g_EMPTY_DAQ_BLOCK = {0};

static TickType_t g_ticks_last_req = 0;


/* --------------------------------- DAQ2STR ------------------------------ */

// sz_ret for string-zero (\0 terminated) return
void daq2str(
        struct daq_block *daqb,
        char *sz_ret,
        int buff_len,
        u16_t curr_upt_s
) {  
    // save bytes by setting wrong T measurements to -274
    // (impossible temperature)
    if (daqb->error == true) daqb->temp = -274.0;
    int temp_len = snprintf(NULL, 0, "%.2f", daqb->temp);
    char *temp = malloc(temp_len + 1); // +1 for string terminator
    snprintf(temp, temp_len + 1, "%.2f", daqb->temp);
     
    /* int err_len = snprintf(NULL, 0, "%d", daqb->error);
    char *err = malloc(err_len + 1);
    snprintf(err, err_len + 1, "%d", daqb->error); */
    
    // calc age of entry
    u16_t age_s = curr_upt_s - daqb->upt_s;
    int age_len = snprintf(NULL, 0, "%u", age_s);
    char *age = malloc(age_len + 1);
    snprintf(age, age_len + 1, "%u", age_s);
    
    // build str
    strlcpy(sz_ret, "T", buff_len);
    strlcat(sz_ret, temp, buff_len);
    /* strlcat(sz_ret, "E", buff_len);
    strlcat(sz_ret, err, buff_len); */
    strlcat(sz_ret, "/U", buff_len);
    strlcat(sz_ret, age, buff_len);
    strlcat(sz_ret, ";", buff_len);

    free(temp);
    // free(err);
    free(age);
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
    
    // convert to IPv6 string
    inet_ntop(AF_INET6, &addr.sin6_addr, ipstr, sizeof(ipstr));
    ESP_LOGI(g_TAG, "data request from: %s", ipstr);
    
    // set answering header
    httpd_resp_set_hdr(req, "Allow", "GET");

    // get mutex
    xSemaphoreTake(xMutex, portMAX_DELAY);
    
    // answer with data if available
    static char data_str[BACKLOG_SIZE * DAQB_STR_SIZE];
    if(g_backlog_idx == 0) 
    {
        strlcpy(data_str, "no data available", sizeof(data_str));
    } else {
        // if avaiable write everything to http str, reset data struct to 0
        if (g_data_lost) {
            strlcpy(data_str, "DL=true&", sizeof(data_str));
        } else {
            strlcpy(data_str, "DL=false&", sizeof(data_str));
        }

        // calc current uptime to get the age of each value in daq2str
        TickType_t curr_uptime_ticks = xTaskGetTickCount() - g_ticks_last_req;
        u64_t curr_uptime = (u64_t)(curr_uptime_ticks * portTICK_PERIOD_MS);
        u16_t curr_uptime_s = (u16_t)(curr_uptime / 1000);

        // build ans str
        for (int idx=0; idx < g_backlog_idx; idx++) 
        {
            static char daqb_str[DAQB_STR_SIZE];
            memset(daqb_str, '\0', sizeof(daqb_str));
            daq2str(
                &g_measure_buff[idx],
                daqb_str,
                DAQB_STR_SIZE,
                curr_uptime_s
            );
            strlcat(data_str, daqb_str, sizeof(data_str));
            g_measure_buff[idx] = g_EMPTY_DAQ_BLOCK;
        }
        g_backlog_idx = 0;
        g_data_lost = false;
    }
    g_ticks_last_req = xTaskGetTickCount();

    // release mutex handle
    xSemaphoreGive(xMutex);

    ESP_LOGI(g_TAG, "returning: %s", data_str);
    httpd_resp_send(req, data_str, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

static const httpd_uri_t data_req = {
    .uri       = "/temp",
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
        httpd_register_err_handler(
            server,
            HTTPD_400_BAD_REQUEST,
            http_400_handler
        );
        httpd_register_err_handler(
            server,
            HTTPD_404_NOT_FOUND,
            http_404_handler
        );
        httpd_register_err_handler(
            server,
            HTTPD_405_METHOD_NOT_ALLOWED,
            http_405_handler
        );

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
) {
    esp_eth_handle_t eth_handle = *(esp_eth_handle_t *)event_data;
    httpd_handle_t* server = (httpd_handle_t*) arg;

    switch (event_id) 
    {
        case ETHERNET_EVENT_CONNECTED:
            g_connected = true;
            uint8_t mac_addr[6] = {0};

            esp_eth_ioctl(eth_handle, ETH_CMD_G_MAC_ADDR, mac_addr);
            ESP_LOGI(g_TAG, "Ethernet Link Up");
            ESP_LOGI(
                g_TAG,
                "Ethernet HW Addr %02x:%02x:%02x:%02x:%02x:%02x",
                mac_addr[0],
                mac_addr[1],
                mac_addr[2],
                mac_addr[3],
                mac_addr[4],
                mac_addr[5]
            );
            
            if (*server == NULL) *server = start_daqs();
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
static void got_ip_event_handler(
        void *arg,
        esp_event_base_t event_base,
        int32_t event_id,
        void *event_data
) {
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
    //emac_cfg.clock_config.rmii.clock_gpio = 17;
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

    while (daqs) {
        TickType_t loop_delay = 100 / portTICK_PERIOD_MS; 
        vTaskDelay(loop_delay);
    }
}