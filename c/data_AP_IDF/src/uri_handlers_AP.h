#ifndef URI_HANDLERS_H
#define URI_HANDLERS_H

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

/* -------------------------------- VARIABLES ----------------------------- */

#define BACKLOG_SIZE        1000
#define DAQB_STR_SIZE       25

#ifdef __cplusplus
extern "C" {
#endif

// global structures
struct daq_block
{
    float temp;
    bool error;
    u16_t upt_s;
};

// global const
extern const struct daq_block g_EMPTY_DAQ_BLOCK;
extern const char *g_URI_TAG;

// global vars
extern struct daq_block g_measure_buff[BACKLOG_SIZE];
extern int g_backlog_idx;
extern bool g_data_lost;
extern SemaphoreHandle_t g_MUTEX;
extern TickType_t g_ticks_last_req;
extern float g_motor_rpm;

/* -------------------------------- FUNCTIONS ----------------------------- */

esp_err_t init_uri(void);
httpd_handle_t start_daqs(void);
esp_err_t stop_daqs(httpd_handle_t server);
void daq2str(
        struct daq_block *daqb,
        char *sz_ret,
        int buff_len,
        u16_t curr_upt_s
);
esp_err_t data_request(httpd_req_t *req);
esp_err_t ping_request(httpd_req_t *req);
esp_err_t http_400_handler(httpd_req_t *req, httpd_err_code_t err);
esp_err_t http_404_handler(httpd_req_t *req, httpd_err_code_t err);
esp_err_t http_405_handler(httpd_req_t *req, httpd_err_code_t err);


/* --------------------------------- URI TYPS ------------------------------ */

// get
static const httpd_uri_t data_req = {
    .uri       = "/data",
    .method    = HTTP_GET,
    .handler   = data_request,
    .user_ctx  = NULL,
};

static const httpd_uri_t ping_req = {
    .uri       = "/ping",
    .method    = HTTP_GET,
    .handler   = ping_request,
    .user_ctx  = NULL,
};

#ifdef __cplusplus
}
#endif

#endif