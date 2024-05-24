#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

import re
import os
import sys
import copy
import math as m
import requests

from pathlib import Path
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import my own libs
import libs.data_utilities as du


#############################################################################################
#                                    FUNCTIONS
#############################################################################################

def pre_check_ccode_file(txt=""):
    """extracts the number of GCode commands and the filament length from
    text, ignores Z movement for now, slicing only in x-y-plane yet
    """

    try:
        if txt == "":
            return 0, 0, "empty"

        rows = txt.split("\n")
        x = 0.0
        y = 0.0
        z = 0.0
        comm_num = 0
        filament_length = 0.0

        for row in rows:
            if len(re.findall("G\d+", row)) > 0:
                comm_num += 1

            x_new = float(
                    re_short("X\d+[,.]\d+", row, "X" + str(x), "X\d+")[0][1:]
                )
            y_new = float(
                    re_short("Y\d+[,.]\d+", row, "Y" + str(y), "Y\d+")[0][1:]
                )
            z_new = float(
                    re_short("Z\d+[,.]\d+", row, "Z" + str(z), "Z\d+")[0][1:]
                )

            # do the Pythagoras for me, baby
            filament_length += m.sqrt(
                m.pow(x_new - x, 2)
                + m.pow(y_new - y, 2)
                + m.pow(z_new - z, 2)
            )

            x, y, z = x_new, y_new, z_new

        # convert filamentLength to meters and round
        filament_length /= 1000
        filament_length = round(filament_length, 2)

    except Exception as e:
        return None, None, e

    return comm_num, filament_length, ""


def pre_check_rapid_file(txt=""):
    """extracts the number of GCode commands and the filament length from
    text, does not handle Offs commands yet
    """

    try:
        if txt == "":
            return 0, 0, "empty"

        rows = txt.split("\n")
        x = 0.0
        y = 0.0
        z = 0.0
        comm_num = 0
        filament_length = 0.0

        for row in rows:
            # the ' p' expression is to differ between 'MoveJ pHome,[...]'
            # and 'MoveJ Offs(pHome [...]'
            if ("Move" in row) and (" p" not in row):
                comm_num += 1
                x_new = float(re.findall("\d+\.\d+", row)[0])
                y_new = float(re.findall("\d+\.\d+", row)[1])
                z_new = float(re.findall("\d+\.\d+", row)[2])

                # do the Pythagoras for me, baby
                filament_length += m.sqrt(
                    m.pow(x_new - x, 2)
                    + m.pow(y_new - y, 2)
                    + m.pow(z_new - z, 2)
                )

                x, y, z = x_new, y_new, z_new

        # convert filamentLength to meters and round
        filament_length /= 1000
        filament_length = round(filament_length, 2)

    except Exception as e:
        return None, None, e

    return comm_num, filament_length, ""


def re_short(regex, txt, default, fallback_regex=""):
    """tries 2 regular expressions on expressions like 'X1.23 Y4.56',
    returns first match without the leading letter (e.g. '1.23' for '\d+[.,]\d+'),
    returns default value and 'False' if no match occurs"""

    try:
        ans = re.findall(regex, txt)[0]

    except IndexError:
        if fallback_regex == "":
            return default, False

        try:
            ans = re.findall(fallback_regex, txt)[0]
        except IndexError:
            return default, False

    return ans, True


def gcode_to_qentry(mut_pos, mut_speed, zone, txt=""):
    """converts a single line of GCode G1 command to a QEntry, can be used in
    loops for multiline code, "pos" should be the pos before this command is
    executed (before its EXECUTED, not before its added to SC_queue) as its
    the fallback option if no new X, Y, Z or EXT posistion is passed
    """

    # handle mutuables here
    pos = copy.deepcopy(mut_pos)
    speed = copy.deepcopy(mut_speed)
    zero = copy.deepcopy(du.DCCurrZero)

    try:
        if not isinstance(pos, du.Coordinate):
            raise ValueError(f"{pos} is not an instance of QEntry!")
        if not isinstance(speed, du.SpeedVector):
            raise ValueError(f"{speed} is not an instance of SpeedVector!")
        command = re_short("G\d+", txt, 0, "^;")[0]

    except IndexError:
        return None, None

    # act according to GCode command
    match command:

        case "G1":
            entry = du.QEntry(id=0, Coor1=pos, Speed=speed, z=zone)

            # set position and speed
            x, res = re_short("X\d+[,.]\d+", txt, pos.x, "X\d+")
            if res:
                entry.Coor1.x = float(x[1:].replace(",", "."))
                entry.Coor1.x += zero.x

                # calculate following position of external axis
                if entry.Coor1.x > 0:
                    entry.Coor1.ext = (
                        int(entry.Coor1.x / du.SC_ext_fllw_bhvr[0])
                        * du.SC_ext_fllw_bhvr[1]
                    )
                    entry.Coor1.ext += zero.ext

                else:
                    entry.Coor1.ext = zero.ext

            y, res = re_short("Y\d+[,.]\d+", txt, pos.y, "Y\d+")
            if res:
                entry.Coor1.y = float(y[1:].replace(",", "."))
                entry.Coor1.y += zero.y

            z, res = re_short("Z\d+[,.]\d+", txt, pos.z, "Z\d+")
            if res:
                entry.Coor1.z = float(z[1:].replace(",", "."))
                entry.Coor1.z += zero.z

            fr, res = re_short("F\d+[,.]\d+", txt, speed.ts, "F\d+")
            if res:
                fr = float(fr[1:].replace(",", "."))
                entry.Speed.ts = int(fr * du.IO_fr_to_ts)

            ext, res = re_short("EXT\d+[,.]\d+", txt, pos.ext, "EXT\d+")
            if res:
                entry.Coor1.ext = float(ext[3:].replace(",", "."))
                entry.Coor1.ext += zero.ext

            entry.Coor1 = round(entry.Coor1, 2)

            # set pump settings
            pump = re.findall("P_([a-zA-Z]+)", txt)
            if pump:
                pump = pump[0]

            if "start" in pump or "end" in pump or "default" in pump:
                entry.p_mode = pump

            elif "class" in pump:
                p_class = re.findall("P_(class\d+)", txt)

                if p_class:
                    entry.p_mode = p_class[0]
                else:
                    return None, None

            # set tool settings
            if "TOOL" in txt:
                entry.Tool.fib_deliv_steps = int(
                    du.TOOL_fib_ratio * du.DEF_TOOL_FIB_STPS
                )
                entry.Tool.pnmtc_fiber_yn = True

        case "G28":
            entry = du.QEntry(id=0, Coor1=pos, Speed=speed, z=zone)
            if "X0" in txt:
                entry.Coor1.x = zero.x
            if "Y0" in txt:
                entry.Coor1.y = zero.y
            if "Z0" in txt:
                entry.Coor1.z = zero.z
            if "EXT0" in txt:
                entry.Coor1.ext = zero.ext

            # set tool settings
            entry.Tool.fib_deliv_steps = 0
            entry.Tool.pnmtc_fiber_yn = False

            pump = re.findall("P_([a-zA-Z]+)", txt)
            if pump:
                pump = pump[0]

            if "start" in pump or "end" in pump or "default" in pump:
                entry.p_mode = pump

            elif "class" in pump:
                p_class = re.findall("P_(class\d+)", txt)

                if p_class:
                    entry.p_mode = p_class[0]
                else:
                    return None, None

        case "G92":
            if "X0" in txt:
                du.DCCurrZero.x = pos.x
            if "Y0" in txt:
                du.DCCurrZero.y = pos.y
            if "Z0" in txt:
                du.DCCurrZero.z = pos.z
            if "EXT0" in txt:
                du.DCCurrZero.ext = pos.ext
            return None, command

        case ";":
            return None, command

        case _:
            return None, None

    return entry, command


def rapid_to_qentry(txt=""):
    """converts a single line of MoveL, MoveJ, MoveC or Move* Offs command 
    (no Reltool) to a QEntry (relative to DC_curr_zero for 'Offs'), can be
    used in loops for multiline code, returns entry and any Exceptions
    """

    entry = du.QEntry(id=0)
    try:
        entry.mt = re.findall("Move[J,L,C]", txt, 0)[0][4]

        ext, res = re_short("EXT:\d+\.\d+", txt, "error", "EXT:\d+")
        ext = float(ext[4:])

        if "Offs" in txt:
            res_coor = [
                du.DCCurrZero.x,
                du.DCCurrZero.y,
                du.DCCurrZero.z,
                du.DCCurrZero.rx,
                du.DCCurrZero.ry,
                du.DCCurrZero.rz,
                du.DCCurrZero.q,
            ]

            xyzOff = re.findall("pHome,\d+\.\d+,\d+\.\d+,\d+\.\d+", txt)[0]
            xyzOff = re.findall("\d+\.\d+", xyzOff)

            for i in range(3):
                res_coor[i] += float(xyzOff[i])
            ext += du.DCCurrZero.ext

        else:
            entry.pt = "Q"
            res_coor = []
            xyzOff = re.findall("\d+\.\d+", txt)
            for i in range(7):
                res_coor.append(float(xyzOff[i]))

        res_speed = re.findall("\d+,\d+,\d+,\d+(?=\],z)", txt)[0]
        res_speed = re.findall("\d+", res_speed)

        entry.Coor1.x = res_coor[0]
        entry.Coor1.y = res_coor[1]
        entry.Coor1.z = res_coor[2]
        entry.Coor1.rx = res_coor[3]
        entry.Coor1.ry = res_coor[4]
        entry.Coor1.rz = res_coor[5]
        entry.Coor1.q = res_coor[6]
        entry.Coor1.ext = ext

        entry.Speed.ts = int(res_speed[0])
        entry.Speed.ors = int(res_speed[1])
        entry.Speed.acr = int(res_speed[2])
        entry.Speed.dcr = int(res_speed[3])

        zone, res = re_short("z\d+", txt, 10)
        entry.z = int(zone[1:])

        entry.Coor1 = round(entry.Coor1, 2)

        # set tool settings
        if "TOOL" in txt:
            entry.Tool.fib_deliv_steps = int(
                du.TOOL_fib_ratio * du.DEF_TOOL_FIB_STPS
            )
            entry.Tool.pnmtc_fiber_yn = True

        pump = re.findall("P_([a-zA-Z]+)", txt)
        if pump:
            pump = pump[0]

        if "start" in pump or "end" in pump or "default" in pump or "None" in pump:
            entry.p_mode = pump

    except Exception as e:
        return None, e

    return entry, None


def create_logfile():
    """defines and creates a logfile (and folder if necessary), which carries
    its creation datetime in the title
    """

    try:
        desk = os.environ["USERPROFILE"]
        logpath = desk / Path("Desktop/PRINT_py_log")
        logpath.mkdir(parents=True, exist_ok=True)

        time = datetime.now().strftime("%Y-%m-%d_%H%M%S")

        logpath = logpath / Path(f"{time}.txt")
        text = f"{time}    [GNRL]:        program booting, starting GUI...\n"

        logfile = open(logpath, "x")
        logfile.write(text)
        logfile.close()

    except Exception as e:
        print(f"Exception occured during log file creation: {e}")
        return None

    return logpath


def add_to_comm_protocol(txt):
    """puts entries in terminal list an keep its length below TERM_maxLen"""

    du.TERM_log.append(txt)

    if len(du.TERM_log) > du.DEF_TERM_MAX_LINES:
        du.TERM_log.__delitem__(0)


def connect_pump(p_num):
    """creates the defalt serial connection if needed, connects required pump.
    necessary to do this via default bus, as multiple connections to on COM
    port are forbitten by pyserial
    """

    if PMP_serial_def_bus is None:
        PMP_serial_def_bus=du.serial.Serial(
            baudrate=du.DEF_SERIAL_PUMP["BR"],
            parity=du.DEF_SERIAL_PUMP["P"],
            stopbits=du.DEF_SERIAL_PUMP["SB"],
            bytesize=du.DEF_SERIAL_PUMP["BS"],
            port=du.DEF_SERIAL_PUMP["PORT"],
        )
        du.PMP1Serial.serial_default = PMP_serial_def_bus
        du.PMP2Serial.serial_default = PMP_serial_def_bus

    match p_num:
        case "P1":
            du.PMP1Serial.connect()
        case "P2":
            du.PMP2Serial.connect()
        case _:
            raise ValueError(f"wrong pNum given: {p_num}")


def calc_pump_ratio(p1_speed, p2_speed):
    """keep track if pumpRatio changes"""

    curr_total = p1_speed + p2_speed
    p1_ratio = (p1_speed / curr_total) if (curr_total != 0) else 0.5
    curr_total = curr_total / 2

    return curr_total, p1_ratio


def sensor_data_req(ip=None, raise_dl_flag=False):
    """http request to data AP, decode
    accepts: 
        ip: 
            str with server address, specify IP & port!
        get_missed_data:
            server also sends back data that has been collected before the
            current measurement but was not yet transmitted (request slower) 
    """

    if ip is not None:
        try:
            ans = requests.get(ip + "/data")
            ans.raise_for_status()
        except Exception as err:
            return err, None, None

        ans_str = ans.text
        data_loss_pos = ans_str.find('&')
        entry_pos = ans_str.find(';')
        if (data_loss_pos <= -1 or entry_pos <= -1):
            return ValueError(f"no readable data retrieved: {ans_str}!"), None, None

        if raise_dl_flag:
            data_loss = ans_str[: data_loss_pos-1]
            if data_loss.find('true') == -1:
                #to-do: build a flag for data loss
                pass

        temp = []
        t_err = []
        uptime = []
        remain_str = ans_str[data_loss_pos+1 :]
        entry_pos -= data_loss_pos+1

        while entry_pos != -1:
            next_entry = remain_str[: entry_pos-1]
            data = next_entry.split('/')
            try:
                temp.append(float(data[0][1 :]))
                t_err.append(bool(data[1][1 :]))
                uptime.append(int(data[2][1 :]))
            except Exception:
                break

            remain_str = ans_str[entry_pos+1 :]
            entry_pos = remain_str.find(';')


        return temp, t_err, uptime    
