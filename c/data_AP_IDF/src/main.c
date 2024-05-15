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

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#include "esp_netif.h"
#include "esp_eth.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_http_server.h"

#include "driver\gpio.h"

#include "sdkconfig.h"

static const char *g_TAG = "DAQ_S";
static bool g_connected = false;


/* -------------------------------- WEBSERVER ----------------------------- */

// http GET handler as data request
static esp_err_t data_request(httpd_req_t *req)
{

    httpd_resp_set_hdr(req, "Allow", "GET");

    // answer with data if available
    const char* data_str = "not data measured";
    httpd_resp_send(req, data_str, HTTPD_RESP_USE_STRLEN);

    return ESP_OK;
}

static const httpd_uri_t data_req = {
    .uri       = "/data",
    .method    = HTTP_GET,
    .handler   = data_request,
    .user_ctx  = NULL,
};

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
        httpd_register_err_handler(server, HTTPD_404_NOT_FOUND, http_404_handler);

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
            ESP_LOGI(g_TAG, "Starting webserver");
            *server = start_daqs();
        }

        break;

    case ETHERNET_EVENT_DISCONNECTED:
        ESP_LOGI(g_TAG, "Ethernet Link Down..");

        if (*server) {
            ESP_LOGI(g_TAG, "Stopping webserver");
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

    // init MAC
    ESP_LOGI(g_TAG, "init mac..");
    eth_mac_config_t mac_cfg = ETH_MAC_DEFAULT_CONFIG();
    eth_esp32_emac_config_t emac_cfg = ETH_ESP32_EMAC_DEFAULT_CONFIG();
    emac_cfg.smi_mdc_gpio_num = 23;
    emac_cfg.smi_mdio_gpio_num = 18;
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

    // init PHY
    ESP_LOGI(g_TAG, "init phy..");
    eth_phy_config_t phy_cfg = ETH_PHY_DEFAULT_CONFIG();
    phy_cfg.reset_gpio_num = -1;
    phy_cfg.phy_addr = 0;
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