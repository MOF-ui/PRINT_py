/* 
following examples from
    danak6jq: https://github.com/danak6jq/ESP32-WSPR
    espressif.com
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
#include "driver\i2c.h"

#include "si5351.h"
#include "uri_handlers.h"

#define I2C_MASTER_SCL_IO   16      // siehe https://github.com/OLIMEX/ESP32-POE-ISO/blob/master/HARDWARE/ESP32-PoE-ISO-Rev.K/ESP32-PoE-ISO_Rev_K.pdf
#define I2C_MASTER_SDA_IO   13
#define SAMPLE_PERIOD       5000   // milliseconds
#define FQ_STEP             50ULL
#define P_CTRL_CONST        0.2

static const char *g_TAG = "DAQ_S";
static bool g_connected = false;
static uint64_t freq_target = 0;

extern "C" void app_main();

Si5351 clk_gen;

/* --------------------------------- SI5351A ------------------------------ */

static esp_err_t i2c_master_init() 
{
    i2c_port_t i2C_master_port = I2C_NUM_1;
    i2c_config_t i2c_cfg;

    i2c_cfg.mode = I2C_MODE_MASTER;
    i2c_cfg.sda_io_num = I2C_MASTER_SDA_IO;
    i2c_cfg.sda_pullup_en = 0;
    i2c_cfg.scl_io_num = I2C_MASTER_SCL_IO;
    i2c_cfg.scl_pullup_en = 0;
    i2c_cfg.clk_flags = 0;
    i2c_cfg.master.clk_speed = 400000;
    i2c_cfg.clk_flags = 0;
    
    ESP_ERROR_CHECK(i2c_driver_install(i2C_master_port, i2c_cfg.mode, 0, 0, 0));
    ESP_ERROR_CHECK(i2c_param_config(i2C_master_port, &i2c_cfg));

    return (ESP_OK);
}

void si5351_main()
{
    float curr_freq = 0;
    float steps_per_rot = 20000.0;
    bool clk_running = false;

    i2c_master_init();
    clk_gen.init(I2C_NUM_1, SI5351_CRYSTAL_LOAD_10PF, 25000000, 0);    
    clk_gen.set_ms_source(SI5351_CLK0, SI5351_PLLA);
    clk_gen.set_pll_input(SI5351_PLLA, SI5351_PLL_INPUT_XO);

    while (true) {
        float rps = g_motor_rpm / 60.0;
        uint64_t freq_target = (uint64_t)(rps * steps_per_rot);

        if (curr_freq != freq_target) {
            xSemaphoreTake(g_MUTEX, portMAX_DELAY);

            if (freq_target == 0) {
                clk_gen.output_enable(SI5351_CLK0, 0);
                curr_freq = 0;
                clk_running = false;
                ESP_LOGI("CLK_F", "clk stopped.");

            } else {
                // use simple p-controller for acceleration ramp
                curr_freq += P_CTRL_CONST * (freq_target - curr_freq);
                clk_gen.set_freq(curr_freq * 100ULL, SI5351_CLK0);

                if (!clk_running) {
                    clk_gen.output_enable(SI5351_CLK0, 1);
                    clk_gen.drive_strength(SI5351_CLK0, SI5351_DRIVE_2MA);
                    clk_running = true;
                    ESP_LOGI("CLK_F", "clk started.");
                }
            }
            
            curr_freq = g_motor_rpm;
            ESP_LOGI("CLK_F", "freq set to %f", curr_freq);
            xSemaphoreGive(g_MUTEX);
        }

        vTaskDelay(100 / portTICK_PERIOD_MS);
    }
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
    uint8_t mac_addr[6] = {0};
    
    switch (event_id) 
    {
        case ETHERNET_EVENT_CONNECTED:
            g_connected = true;

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

    init_uri();

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
    const gpio_num_t phy_power_pin = (gpio_num_t)12;
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
    si5351_main();

    while (daqs) {
        TickType_t loop_delay = 100 / portTICK_PERIOD_MS; 
        vTaskDelay(loop_delay);
    }
}