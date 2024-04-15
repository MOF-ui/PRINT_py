// C++ program to run on an ESP32 or 8266 mounted on the robot tool head or similar,
// controls pinch valve, 2k motor and admixture pump and enables connectivity to PRINT_py
// via TCP & WiFi


/* #ifdef ESP32
    #include <WiFi.h>
#else 
    #include <ESP8266WiFi.h>
#endif */
#include <WiFi.h>
#include <AccelStepper.h>

//const
#define DRV_ENN         32          // Enable
#define DIR_PIN         14          // Direction
#define STEP_PIN        13          // Step
#define PINCH_PIN       1

#define MAXSPEED        7000
#define MAXATTEMPTS     10

// status vars 
bool mixerSpeed         = false;
bool admixture          = false;
bool pinched            = false;
bool clientConnected    = false;

// wifi vars
char AUTH[]     = "AUTH";
char SSID[]     = "WIFI";
char PASSWORD[] = "PASS";
byte MAC[6];

// comm vars
typedef struct {
    float   mixerSpeed  = 0.0;  // unit by accelstepper, conversion is on to do list
    float   admixture   = 0.0;  // 0 - 100% (in theory)
    bool    pinch       = false;
} remoteCommand;
remoteCommand   currComm;
remoteCommand   lastComm;
const int       commLen = sizeof( remoteCommand );
byte            recvMsg[ commLen + 2 ]; // command + checksum
byte            lastRecvMsg[ commLen + 2 ];

// internal vars
bool mutexLock = false;     // simple check for mutual exclusion

//classes
AccelStepper    stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);
TaskHandle_t    C0;
WiFiServer      socket(3000);


void core0assignments( void *pvParameters ) { 
    while( true ) {

        // wait for client
        WiFiClient client = socket.available();
        if( client ) {
            Serial.print( " Connected by: " );
            Serial.println( client.localIP() );

            while( client.connected() ) {

                // check for data to read
                int bytesToRead = client.available();
                int chkSum = 0;
                int chkSumExpected = 0;

                // write msg to buffer
                for( int i = 0; i < bytesToRead; i++ ) {
                    recvMsg[i] = client.read();
                }

                // process msg if its new, compare checksum
                if( recvMsg != lastRecvMsg ) {
                    for( int j = 0; j < commLen; j++ ) {
                        chkSum += (int) recvMsg[j];
                    }
                    chkSumExpected |= ( recvMsg[ commLen ] << 8 );
                    chkSumExpected |= ( recvMsg[ commLen + 1 ] );

                    if( chkSum != chkSumExpected ) {
                        Serial.printf( "chkSum error -- calc: %i, recv: %i\n", chkSum, chkSumExpected );
                    
                    } else {

                        // overwrite currComm with new values, check value range
                        lastComm = currComm;
                        currComm = remoteCommand();
                        byte newSpeed[4];
                        byte newAdmix[4];
                        
                        for( int k = 0; k < 4; k++ ) {
                            newSpeed[k] = recvMsg[k];
                            newAdmix[k] = recvMsg[k + 4];
                        }

                        // stop loop check while copying & delay to wait for the loop to stop
                        mutexLock = true;
                        delay( 10 );
                        memcpy( &currComm.mixerSpeed, &newSpeed, sizeof(float) );
                        memcpy( &currComm.admixture, &newAdmix, sizeof(float) );
                        currComm.pinch = recvMsg[8];

                        if( 0.0 <= currComm.mixerSpeed && currComm.mixerSpeed <= 100.0
                            && 0.0 <= currComm.admixture && currComm.admixture <= 50.0 ) {

                            client.write(true);
                            Serial.println( "received valid" );

                        } else {
                            client.write(false);
                            Serial.println( "data out of range, not acknowlegded" );
                            currComm = remoteCommand();
                        }
                        mutexLock = false;
                    }
                    
                    // set lastRecvMsg to newest buffer
                    for( int i = 0; i < sizeof( recvMsg ); i++) {
                        lastRecvMsg[i] = recvMsg[i];
                    }
                }
            }
        }
    }
}



void move_motor(){
// set motor to desired speed, set admixutre pump as well (to do)

    if( currComm.mixerSpeed != 0.0 ) {
        stepper.enableOutputs();
        stepper.setSpeed( currComm.mixerSpeed );
        stepper.runSpeed();
    } else {
        stepper.stop();
        stepper.disableOutputs();
    }
    mixerSpeed = currComm.mixerSpeed;
    admixture  = currComm.admixture;
}

void switch_pinch_valve() {
// switch 3-2 pressure valve

    if( pinched ) {
        digitalWrite( PINCH_PIN, LOW );
        pinched = false;
    } else {
        digitalWrite( PINCH_PIN, HIGH );
        pinched = true;
    }
}


//program
void setup() {
    
    // timing for WiFi connection attempts
    long setupStart = millis();

    // Init serial port and set baudrate
    Serial.begin(19200);
    Serial.println( "Starting up.." );

    // setup GPIOs & stepper
    Serial.println( "GPIO & stepper setup.." );
    pinMode(DRV_ENN,  OUTPUT);
    pinMode(STEP_PIN, OUTPUT);
    pinMode(DIR_PIN,  OUTPUT);
    pinMode(PINCH_PIN,OUTPUT);
    stepper.setEnablePin        (DRV_ENN);
    stepper.setPinsInverted     (false, false, true);
    stepper.disableOutputs      ();
    stepper.setMaxSpeed         (MAXSPEED);
    stepper.setSpeed            (MAXSPEED);
    stepper.setAcceleration     (3000);
    stepper.setCurrentPosition  (0);

    // connect Wifi
    int attempt = 1;
    int wifiStatus = WL_IDLE_STATUS;
    
    while( true ) {
        Serial.printf( "WS -- connection attempt: %i, time since boot: %i\n", attempt, setupStart );
        int wifiStatus = WiFi.begin();

        if( wifiStatus == WL_CONNECTED ) {
            WiFi.macAddress( MAC );
            break;
        }
        if( attempt >= MAXATTEMPTS ) {
            Serial.printf( "WS -- failed. Reached maximum number of attempts, restarting..." );
            ESP.restart();
        } else {
            Serial.println( "WS -- failed. Idle for 60s." );
            delay( 60000 );
            attempt++;
        }
    }

    Serial.print( "WS -- connected. MAC: ");
    for( int i = 0; i < 5; i++) Serial.printf( "%02X:", MAC[ 5 - i ] );
    Serial.printf( "%02X\n", MAC[0] );

    Serial.println( "WS -- start server.." );
    socket.begin();
    Serial.print( "WS -- running, connect locally under: "); 
    Serial.println( WiFi.localIP() );

    Serial.println( "WS -- assign WiFi r/w to Core0.." );
    // assign WiFi functions to Core0
    disableCore0WDT();
    xTaskCreatePinnedToCore(
        core0assignments,       // Function that should be called
        "Core_0",               // Name of the task (for debugging)
        10000,                  // Stack size (bytes)
        NULL,                   // Parameter to pass
        1,                      // Task priority//0
        &C0,                    // Task handle
        0                       // Core you want to run the task on (0 or 1)
    );

    Serial.println( "Setup done.\n" );
}


void loop() {
    if( !mutexLock ) {
        if( ( mixerSpeed != currComm.mixerSpeed ) || ( admixture != currComm.admixture ) ) move_motor();
        if( pinched != currComm.pinch ) switch_pinch_valve();
    }
    delay( 10 );
}