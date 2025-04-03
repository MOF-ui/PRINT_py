#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

import os
import sys
import yaml
from pathlib import Path

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod

# import my own libs
from data_utilities import (Coordinate, Queue, DaqBlock, PumpTelemetry,
    RoboTelemetry, RoboConnection)



##############################     MAIN     ##################################

with open('config.yml', 'r') as ymlfile:
    cfg = yaml.full_load(ymlfile)

# constants
PMP_LPS = cfg['PMP']['LPS']
PMP_CLASS1 = cfg['PMP']['CLASS1']
PMP_CLASS2 = cfg['PMP']['CLASS2']
PMP_RETR_SPEED = cfg['PMP']['RETRACT_SPEED']
PMP_SAFE_RANGE = cfg['PMP']['SAFE_RANGE']
PMP_VALID_COMMANDS = cfg['PMP']['VALID_COMMANDS']
PMP1_MODBUS_ID = cfg['PMP']['P1_MODBUS_ID']
PMP2_MODBUS_ID = cfg['PMP']['P2_MODBUS_ID']
ROB_COMM_FR = cfg['ROBOT']['COMMAND_FORERUN']
ROB_SAFE_RANGE = (
    cfg['ROBOT']['SAFE_RANGE_MIN'],
    cfg['ROBOT']['SAFE_RANGE_MAX'],
)
SC_VOL_PER_M = cfg['SC']['VOL_PER_M']
WD_TIMEOUT = cfg['WATCHDOG']['TIMEOUT']
IO_FR_TO_TS = cfg['IO']['FR_TO_TS']
IO_ZONE = cfg['IO']['ZONE']
DC_SPEED = cfg['SPEED']['DIRECT']
SC_SPEED = cfg['SPEED']['SCRIPT']
SC_EXT_TRAIL = cfg['SC']['EXT_TRAIL']

# cameras
CAM_urls = [
    'rtsp://admin:KameraNr4@192.168.178.51:554/ch1/main/av_stream',
    'rtsp://admin:KameraNr1@192.168.178.38:554/ch1/main/av_stream',
]

# direct movement control
DC_rob_moving = False
DCSpeed = DC_SPEED

# general control properties
CTRL_log_path = Path()

# file IO
IO_curr_filepath = None
IO_fr_to_ts = IO_FR_TO_TS
IO_zone = IO_ZONE

# script controlled movement
SC_curr_comm_id = 1
SC_ext_trail = SC_EXT_TRAIL
SC_q_prep_end = False
SC_q_processing = False
SC_vol_per_m = SC_VOL_PER_M
SCBreakPoint = Coordinate() # to-do: write routine to stop at predefined point during SC using this Coordinate + decide if useful
SCQueue = Queue()
SCSpeed = SC_SPEED

# terminal
TERM_log = []

# database
DB_log_interval = cfg['DATABASE']['LOG_INTERVAL']
DB_org = 'MC3DB'
DB_session = 'not set'
DB_token = None
DB_url = '192.168.178.50:8086'
DB_valid_time = cfg['DATABASE']['VALID_TIME']
DBDataBlock = DaqBlock()

# printhead
MIX_last_speed = 0.0
MIX_max_speed = 300.0 # [rpm]
MIX_speed = 0.0
PRH_act_with_pump = False
PRH_connected = False
PRH_trol_ratio = cfg['PRINTHEAD']['TROLL_RATIO']
PRH_url = '192.168.178.58:17'

# general pump settings
PMP_output_ratio = cfg['PMP']['OUTP_RATIO']
PMP_port = cfg['PMP']['SERIAL']['PORT']
PMP_retract_speed = PMP_RETR_SPEED
PMPSerialDefBus = None  # is created after user input in win_mainframe
PMP_speed = 0
PMP_look_ahead = False
PMP_look_ahead_dist = cfg['PMP']['LOOK_AHEAD_DIST']
PMP_look_ahead_prerun = cfg['PMP']['LOOK_AHEAD_PRERUN']
PMP_look_ahead_retract = cfg['PMP']['LOOK_AHEAD_RETRACT']
PMP_look_ahead_max_comms = cfg['PMP']['LOOK_AHEAD_MAX_COMMS']
# mtec P20-1
PMP1_liter_per_s = PMP_LPS
PMP1_live_ad = 1.0
PMP1_speed = 0
PMP1_user_speed = cfg['PMP']['NO_USER_SPEED']
PMP1LastTelem = PumpTelemetry()
PMP1Serial = MtecMod(None, PMP1_MODBUS_ID)
# mtec P20-1
PMP2_liter_per_s = PMP_LPS
PMP2_live_ad = 1.0
PMP2_speed = 0
PMP2_user_speed = cfg['PMP']['NO_USER_SPEED']
PMP2LastTelem = PumpTelemetry()
PMP2Serial = MtecMod(None, PMP2_MODBUS_ID)

# robot
ROB_comm_fr = ROB_COMM_FR
ROB_live_ad = 1.0
ROB_max_r_speed = cfg['ROBOT']['MAX_ROTATION_SPEED']
ROB_min_target_dist = cfg['ROBOT']['MIN_TARGET_DIST']
ROB_safe_range = (
    cfg['ROBOT']['SAFE_RANGE_MIN'],
    cfg['ROBOT']['SAFE_RANGE_MAX'],
)
ROB_send_list = []
ROB_speed_overwrite = -1
ROBCommQueue = Queue()
ROBCurrZero = cfg['ROBOT']['ZERO']
ROBLastTelem = RoboTelemetry()
ROBMovStartP = Coordinate()
ROBMovEndP = Coordinate()
ROBTelem = RoboTelemetry()
ROBTcp = RoboConnection(
    cfg['ROBOT']['TCP']['ip'],
    cfg['ROBOT']['TCP']['port'],
    cfg['ROBOT']['TCP']['c_tout'],
    cfg['ROBOT']['TCP']['rw_tout'],
    cfg['ROBOT']['TCP']['r_bl'],
    cfg['ROBOT']['TCP']['w_bl'],
)

# sensor array
SEN_timeout = 0.5
SEN_dict = { # add available datasources here
    'amb': { # AMBient
        'ip': '192.168.178.36:17',
        'err': False,
        'temp': False,
        'humid': False,
    },
    'asp': { # Admixture Supply Pump
        'ip': '',
        'err': False,
        'freq': False,
        'amps': False,
    },
    'rb': { # Robot Base
        'ip': '',
        'err': False,
        'temp': False,
    },
    'msp': { # Main Supply Pump
        'ip': '192.168.178.36:17',
        'err': False,
        'temp': True,
        'pressure': False,
    },
    'imp': { # Inline Mixing Pump
        'ip': '',
        'err': False,
        'temp': False,
        'pressure': False,
        'freq': False,
        'amps': False
    },
    'phc': { # Print Head Controller
        'ip': '',
        'err': False,
        'aircon': False,
        'fdist': False,
        'edist': False
    }
}