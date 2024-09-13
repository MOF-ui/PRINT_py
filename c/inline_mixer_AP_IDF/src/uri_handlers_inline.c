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
#include "uri_handlers_inline.h"

/* -------------------------------- VARIABLES ----------------------------- */

// global const
const struct daq_block g_EMPTY_DAQ_BLOCK = {0};
const char *g_URI_TAG = "URI_H";

// global vars
struct daq_block g_measure_buff[BACKLOG_SIZE] = {0};
int g_backlog_idx = 0;
bool g_data_lost = false;
SemaphoreHandle_t g_MUTEX = NULL;
TickType_t g_ticks_last_req = 0;
float g_motor_rpm = 0;

/* -------------------------------- FUNCTIONS ----------------------------- */

// initialize g_MUTEX handle
esp_err_t init_uri()
{
    g_MUTEX = xSemaphoreCreateMutex();
    return (ESP_OK);
}

// return server_handle with registered URI handlers;
// registered handles are: '/data', '/ping', '/motor'
httpd_handle_t start_daqs()
{
    httpd_handle_t server = NULL;
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();

    // start the server on 'quote of the day' port for funsies
    config.server_port = 17;

    // Start the httpd server
    ESP_LOGI(g_URI_TAG, "Starting server on port: '%d'", config.server_port);
    if (httpd_start(&server, &config) == ESP_OK) {
        
        // set URIs
        httpd_register_uri_handler(server, &data_req);
        httpd_register_uri_handler(server, &ping_req);
        httpd_register_uri_handler(server, &post_f);

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

    ESP_LOGI(g_URI_TAG, "Error starting server!");
    return NULL;
}

// stop server
esp_err_t stop_daqs(httpd_handle_t server)
{
    return httpd_stop(server);
}

// returns all backlogged data to IP request (LIFO) with heading data-lost
// token; prints requests IP first
esp_err_t data_request(httpd_req_t *req)
{
    // get client IP
    int sockfd = httpd_req_to_sockfd(req);
    char ipstr[INET6_ADDRSTRLEN];
    struct sockaddr_in6 addr; // esp_http_server uses IPv6 addressing
    socklen_t addr_size = sizeof(addr);
    getpeername(sockfd, (struct sockaddr *)&addr, &addr_size);
    
    // convert to IPv6 string
    inet_ntop(AF_INET6, &addr.sin6_addr, ipstr, sizeof(ipstr));
    ESP_LOGI(g_URI_TAG, "data request from: %s", ipstr);
    
    // set answering header
    httpd_resp_set_hdr(req, "Allow", "GET");

    // get mutex
    xSemaphoreTake(g_MUTEX, portMAX_DELAY);
    
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
    xSemaphoreGive(g_MUTEX);

    ESP_LOGI(g_URI_TAG, "returning: %s", data_str);
    httpd_resp_send(req, data_str, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

// returns 'ack' to ping request from IP client
esp_err_t ping_request(httpd_req_t *req)
{
    // get client IP
    int sockfd = httpd_req_to_sockfd(req);
    char ipstr[INET6_ADDRSTRLEN];
    struct sockaddr_in6 addr; // esp_http_server uses IPv6 addressing
    socklen_t addr_size = sizeof(addr);
    getpeername(sockfd, (struct sockaddr *)&addr, &addr_size);
    
    // convert to IPv6 string
    inet_ntop(AF_INET6, &addr.sin6_addr, ipstr, sizeof(ipstr));
    ESP_LOGI(g_URI_TAG, "ping request from: %s", ipstr);
    
    // set answering header
    httpd_resp_set_hdr(req, "Allow", "GET");
    
    httpd_resp_send(req, "ack", HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

// accepts motor rpm data from POST, expects string representing a float;
// returns string received and sets g_motor_rpm to value read
esp_err_t freq_post(httpd_req_t *req)
{
    /* Destination buffer for content of HTTP POST request.
     * httpd_req_recv() accepts char* only, but content could
     * as well be any binary data (needs type casting).
     * In case of string data, null termination will be absent, and
     * content length would give length of string */
    char content[100];

    /* Truncate if content length larger than the buffer */
    size_t recv_size = MIN(req->content_len, sizeof(content));

    int ret = httpd_req_recv(req, content, recv_size);
    if (ret <= 0) {  /* 0 return value indicates connection closed */
        /* Check if timeout occurred */
        if (ret == HTTPD_SOCK_ERR_TIMEOUT) {
            /* In case of timeout one can choose to retry calling
             * httpd_req_recv(), but to keep it simple, here we
             * respond with an HTTP 408 (Request Timeout) error */
            httpd_resp_send_408(req);
        }
        /* In case of error, returning ESP_FAIL will
         * ensure that the underlying socket is closed */
        ESP_LOGI(g_URI_TAG, "POST HANDLING FAILED!");
        return ESP_FAIL;
    }

    char* resp;
    uint16_t len = req->content_len;
    content[len+1] = '\0';
    ESP_LOGI(g_URI_TAG, "received: %s", content);

    xSemaphoreTake(g_MUTEX, portMAX_DELAY);
    sscanf(content, "%f", &g_motor_rpm);
    if (g_motor_rpm < 0.0) g_motor_rpm = 0.0;
    asprintf(&resp, "RECV%f", g_motor_rpm);
    xSemaphoreGive(g_MUTEX);
    
    // set response header
    httpd_resp_set_hdr(req, "Allow", "POST");

    httpd_resp_send(req, resp, HTTPD_RESP_USE_STRLEN);
    return ESP_OK;
}

// 400 HANDLER
esp_err_t http_400_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "malformed request!");
    return ESP_FAIL;
}

// 404 HANDLER
esp_err_t http_404_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_send_err(req, HTTPD_404_NOT_FOUND, "no such resource");
    return ESP_FAIL;
}

// 405 HANDLER
esp_err_t http_405_handler(httpd_req_t *req, httpd_err_code_t err)
{
    httpd_resp_set_hdr(req, "Allow", "GET");
    httpd_resp_send_err(req, HTTPD_405_METHOD_NOT_ALLOWED, "only GET methods");
    return ESP_FAIL;
}

/* -------------------------------- FUNCTIONS ----------------------------- */

// short-hand function to construct string from daq_block list entry
// sz_ret for string-zero ('\0' terminated) return
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
    
    // calc age of entry
    u16_t age_s = curr_upt_s - daqb->upt_s;
    int age_len = snprintf(NULL, 0, "%u", age_s);
    char *age = malloc(age_len + 1);
    snprintf(age, age_len + 1, "%u", age_s);
    
    // build str
    strlcpy(sz_ret, "T", buff_len);
    strlcat(sz_ret, temp, buff_len);
    strlcat(sz_ret, "/U", buff_len);
    strlcat(sz_ret, age, buff_len);
    strlcat(sz_ret, ";", buff_len);

    free(temp);
    free(age);
}