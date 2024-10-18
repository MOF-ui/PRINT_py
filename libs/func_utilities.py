#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

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


###########################     FUNCTIONS      ###############################

def pre_check_gcode_file(
        txt:str
) -> (
        tuple[int | Exception, float, str]
):
    """extracts the number of GCode commands and the filament length from
    text, ignores Z movement for now, slicing only in x-y-plane yet

    accepts:
        txt:
            whole file txt as single string
    """

    try:
        if txt == '':
            return 0, 0.0, 'empty'

        rows = txt.split('\n')
        x = 0.0
        y = 0.0
        z = 0.0
        comm_num = 0
        filament_length = 0.0

        x_regex = ['X\d+[,.]\d+', 'X\d+', 'X-\d+[,.]\d+', 'X-\d+']
        y_regex = ['Y\d+[,.]\d+', 'Y\d+', 'Y-\d+[,.]\d+', 'Y-\d+']
        z_regex = ['Z\d+[,.]\d+', 'Z\d+', 'Z-\d+[,.]\d+', 'Z-\d+']

        for row in rows:
            if len(re.findall('G\d+', row)) > 0:
                comm_num += 1

            x_new = float(re_short(x_regex, row, 'X' + str(x))[1:])
            y_new = float(re_short(y_regex, row, 'Y' + str(y))[1:])
            z_new = float(re_short(z_regex, row, 'Z' + str(z))[1:])

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

    except Exception as err:
        return err, 0.0, ''

    return comm_num, filament_length, ''


def pre_check_rapid_file(
        txt:str
) -> (
        tuple[int | Exception, float, str]
):
    """extracts the number of GCode commands and the filament length from
    text, does not handle Offs commands yet

    accepts:
        txt:
            whole file txt as single string
    """

    try:
        if txt == "":
            return 0, 0.0, 'empty'

        rows = txt.split("\n")
        x = 0.0
        y = 0.0
        z = 0.0
        comm_num = 0
        filament_length = 0.0

        for row in rows:
            # the ' p' expression is to differ between 'MoveJ pHome,[...]'
            # and 'MoveJ Offs(pHome [...]'
            if ('Move' in row) and (' p' not in row):
                comm_num += 1
                x_new = float(re.findall('\d+\.\d+', row)[0])
                y_new = float(re.findall('\d+\.\d+', row)[1])
                z_new = float(re.findall('\d+\.\d+', row)[2])

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

    except Exception as err:
        return err, 0.0, ''

    return comm_num, filament_length, ''


def re_short(
        regex:list,
        txt:str,
        default:object,
        find_coor=''
) -> str | object:
    """tries all given regular expressions to match the txt,
    returns first match found, returns default if no match occurs;
    sure you could game it out with regex, but this way is less
    brain-hurty
    
    accepts:
        regex:
            regular expression to be matched (using re lib), given as a list
            of re, first re to match anything is used
        txt:
            string to be searched
        default:
            default return value if nothing is found, can be any type
        find_coor:
            short-hand parameter to find expressions like 'X-1.2' or similar
    """

    # if only used to find GCode coordinates like 'X1.2', use this shortcut:
    # regular expression for e.g. 'X1', 'X2.2' or 'X-3,3' with find_coor='X':
    #   'X-?': 
    #       matches 'X' and 'X-'
    #   '\d+': 
    #       matches any amount of consecutive decimal numbers
    #   '[,\.]?[\d+]?': 
    #       matches any amount of fractional digits, indifferent to ',' or '.'
    #   '(' and ')' brackets:
    #       specify only the inner part to be contained in the actual match
    if find_coor != '':
        regex = [find_coor + '(-?\d+[,\.]?[\d+]?)']
    
    if not isinstance(regex, list):
        raise ValueError

    ans = default
    for curr_regex in regex:
        try:
            ans = re.findall(curr_regex, txt)[0]
            break
        except IndexError:
            continue

    return ans


def re_pump_tool(entry:du.QEntry, txt:str) -> du.QEntry:
    """short-hand for pump & tool settings detection"""
    
    # set pump settings
    p_mode = re_short(None, txt, None, find_coor='PMP')
    match p_mode:
        case '1': entry.p_mode = 'default'
        case '2': entry.p_mode = 'class1'
        case '3': entry.p_mode = 'class2'
        case '10': entry.p_mode = 'start'
        case '11': entry.p_mode = 'end'
        case _: entry.p_mode = 'None'
    p_ratio = re_short(None, txt, None, find_coor='PR')
    try:
        p_ratio = float(p_ratio)
        if p_ratio > 1.0: p_ratio = 1.0
        if p_ratio < 0: p_ratio = 0.0
        entry.p_ratio = p_ratio
    except:
        pass

    # set tool settings
    if 'TOOL' in txt:
        entry.Tool.pnmtc_fiber_yn = True
        entry.Tool.fib_deliv_steps = int(
            du.TOOL_fib_ratio * du.DEF_TOOL_FIB_STPS
        )
    
    return entry


def gcode_to_qentry(
        mut_pos:du.Coordinate,
        mut_speed:du.SpeedVector,
        zone:int,
        txt:str,
        ext_trail=True
    ) -> (
        tuple[du.QEntry|None, str]
    ):
    """converts a single line of GCode G1 command to a QEntry, can be used in
    loops for multiline code, "pos" should be the pos before this command is
    executed (before its EXECUTED, not before its added to SC_queue) as its
    the fallback option if no new X, Y, Z or EXT posistion is passed

    accepts:
        mut_pos: 
            postion immediately prior to planned command execution,
            is deepcopied inside function to avoid mutuable behavior
        mut_speed:
            speed to be used in this movement,
            is deepcopied inside function to avoid mutuable behavior
        zone:
            RAPID-like accuracy zone for the movement
        txt: 
            GCode line to be converted
        ext_trail:
            toggle for external trailing (fllwBhvr), True to turn on
    """

    # handle mutuables here
    pos = copy.deepcopy(mut_pos)
    speed = copy.deepcopy(mut_speed)
    zero = copy.deepcopy(du.DCCurrZero)

    if not isinstance(pos, du.Coordinate):
        raise ValueError(f"{pos} is not an instance of Coordinate!")
    if not isinstance(speed, du.SpeedVector):
        raise ValueError(f"{speed} is not an instance of SpeedVector!")
    
    command = re_short(['G\d+', '^;'], txt, None)
    if command is None:
        return None, ''

    # act according to GCode command
    match command:

        case 'G1':
            entry = du.QEntry(id=0, Coor1=pos, Speed=speed, z=zone)

            # set position and speed
            x = re_short(None, txt, pos.x, find_coor='X')
            if x != pos.x:
                entry.Coor1.x = float(x.replace(',', '.'))
                entry.Coor1.x += zero.x
                
                if ext_trail:
                    # calculate following position of external axis
                    if entry.Coor1.x > 0:
                        entry.Coor1.ext = (
                            int(entry.Coor1.x / du.SC_ext_fllw_bhvr[0])
                            * du.SC_ext_fllw_bhvr[1]
                        )
                        entry.Coor1.ext += zero.ext

                    else:
                        entry.Coor1.ext = zero.ext

            y = re_short(None, txt, pos.y, find_coor='Y')
            if y != pos.y:
                entry.Coor1.y = float(y.replace(',', '.'))
                entry.Coor1.y += zero.y

            z = re_short(None, txt, pos.z, find_coor='Z')
            if z != pos.z:
                entry.Coor1.z = float(z.replace(',', '.'))
                entry.Coor1.z += zero.z

            # set tool angulation
            rx = re_short(None, txt, pos.rx, find_coor='XR')
            if rx != pos.rx:
                entry.Coor1.rx = float(rx.replace(',', '.'))
                entry.Coor1.rx += zero.rx #to-do: check if running out of 0-359 crashes the robot
                
            ry = re_short(None, txt, pos.ry, find_coor='YR')
            if ry != pos.ry:
                entry.Coor1.ry = float(ry.replace(',', '.'))
                entry.Coor1.ry += zero.ry
                
            rz = re_short(None, txt, pos.rz, find_coor='ZR')
            if rz != pos.rz:
                entry.Coor1.rz = float(rz.replace(',', '.'))
                entry.Coor1.rz += zero.rz

            # set speed and external axis
            fr = re_short(None, txt, speed.ts, find_coor='F')
            if fr != speed.ts:
                fr = float(fr.replace(',', '.'))
                entry.Speed.ts = int(fr * du.IO_fr_to_ts)

            ext = re_short(None, txt, pos.ext, find_coor='EXT')
            if ext != pos.ext:
                entry.Coor1.ext = float(ext.replace(',', '.'))
                entry.Coor1.ext += zero.ext

            entry.Coor1 = round(entry.Coor1, 2)
            entry = re_pump_tool(entry, txt)

        case 'G28':
            entry = du.QEntry(id=0, Coor1=pos, Speed=speed, z=zone)
            if 'X0' in txt:
                entry.Coor1.x = zero.x
            if 'Y0' in txt:
                entry.Coor1.y = zero.y
            if 'Z0' in txt:
                entry.Coor1.z = zero.z
            if 'EXT0' in txt:
                entry.Coor1.ext = zero.ext

            entry = re_pump_tool(entry, txt)

        case 'G92':
            if 'X0' in txt:
                du.DCCurrZero.x = pos.x
            if 'Y0' in txt:
                du.DCCurrZero.y = pos.y
            if 'Z0' in txt:
                du.DCCurrZero.z = pos.z
            if 'EXT0' in txt:
                du.DCCurrZero.ext = pos.ext
            return None, command

        case ';':
            return None, command

        case _:
            return None, ''

    return entry, command


def rapid_to_qentry(txt:str) -> du.QEntry | None | Exception:
    """converts a single line of MoveL, MoveJ, MoveC or Move* Offs command 
    (no Reltool) to a QEntry (relative to DC_curr_zero for 'Offs'), can be
    used in loops for multiline code, returns entry or any Exceptions, 
    return None if no movement-type keyword is found

    accepts:
        txt: RAPID-like command line specifying movement
    """

    entry = du.QEntry(id=0)

    # if no movement-type command is given, return None
    try:
        entry.mt = re.findall('Move[J,L,C]', txt, 0)[0][4]
    except IndexError:
        return None
    
    ext = re_short(None, txt, None, find_coor='EXT')
    if ext is None:
        return None # to-do: add missing value handler
    
    # otherwise try to decode
    # re matches '12', '12.3' or '12.34'
    num_regex = '-?\d+\.?[\d+]*'
    # but only if they follow a '[' or ','
    regex = f"[\[,]({num_regex})" 
    decimals = re.findall(regex, txt)
    try:
        ext = float(ext)

        # look for relative coordinates
        if 'Offs' in txt:
            res_coor = [
                du.DCCurrZero.x,
                du.DCCurrZero.y,
                du.DCCurrZero.z,
                du.DCCurrZero.rx,
                du.DCCurrZero.ry,
                du.DCCurrZero.rz,
                du.DCCurrZero.q,
            ]
            for i in range(3):
                res_coor[i] += float(decimals[i])
            ext += du.DCCurrZero.ext

        # or standard robtarget
        else:
            entry.pt = 'Q'
            res_coor = []
            for i in range(7):
                res_coor.append(float(decimals[i]))

        speed_regex = f"{num_regex},{num_regex},{num_regex},{num_regex}\],z"
        res_speed = re.findall(speed_regex, txt)[0]
        res_speed = re.findall(num_regex, res_speed)

        entry.Coor1.x = res_coor[0]
        entry.Coor1.y = res_coor[1]
        entry.Coor1.z = res_coor[2]
        entry.Coor1.rx = res_coor[3]
        entry.Coor1.ry = res_coor[4]
        entry.Coor1.rz = res_coor[5]
        entry.Coor1.q = res_coor[6]
        entry.Coor1.ext = ext

        # converting '1.2'-like strings to int throws an error
        # convert to float first
        entry.Speed.ts = int(float(res_speed[0]))
        entry.Speed.ors = int(float(res_speed[1]))
        entry.Speed.acr = int(float(res_speed[2]))
        entry.Speed.dcr = int(float(res_speed[3]))

        zone = re_short(['z\d+'], txt, du.IO_zone)
        entry.z = int(zone[1:])

        # rounding everything to 2 decimals causes inaccuarcy on quaternions
        # entry.Coor1 = round(entry.Coor1, 2)
        entry = re_pump_tool(entry, txt)

    except Exception as err:
        return err

    return entry


def create_logfile() -> Path | None:
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


def add_to_comm_protocol(txt:str) -> None:
    """puts entries in terminal list an keep its length below TERM_maxLen
    
    accepts:
        txt: str to appear as terminal entry
    """

    du.TERM_log.append(txt)

    if len(du.TERM_log) > du.DEF_TERM_MAX_LINES:
        du.TERM_log.__delitem__(0)


def connect_pump(p_num:int) -> None:
    """creates the default serial connection if needed, connects required pump.
    necessary to do this via default bus, as multiple connections to on COM
    port are forbitten by pyserial

    accepts:
        p_num: number of pump to be connected
    """

    if du.PMP_serial_def_bus is None:
        du.PMP_serial_def_bus=du.serial.Serial(
            baudrate=du.DEF_SERIAL_PUMP["BR"],
            parity=du.DEF_SERIAL_PUMP["P"],
            stopbits=du.DEF_SERIAL_PUMP["SB"],
            bytesize=du.DEF_SERIAL_PUMP["BS"],
            port=du.DEF_SERIAL_PUMP["PORT"],
        )
        du.PMP1Serial.serial_default = du.PMP_serial_def_bus
        du.PMP2Serial.serial_default = du.PMP_serial_def_bus

    match p_num:
        case "P1":
            ret = du.PMP1Serial.connect()
        case "P2":
            ret = du.PMP2Serial.connect()
        case _:
            raise ValueError(f"wrong pNum given: {p_num}")
    
    return ret


def calc_pump_ratio(p1_speed:int, p2_speed:int) -> tuple[float, float]:
    """keep track if pumpRatio changes, returns total volume flow and 
    pump ratio as floats for 2 pump speeds

    accepts:
        p1_speed:
            speed of pump 1 expressed as 0-100
        p2_speed:
            speed of pump 2 expressed as 0-100
    """

    curr_total = p1_speed + p2_speed
    p1_ratio = (p1_speed / curr_total) if (curr_total != 0) else 1.0
    curr_total = curr_total / 2

    return curr_total, p1_ratio


def sensor_req(
        ip:str,
        key:str,
        raise_dl_flag=False
    ) -> (
        list
        | None
        | Exception
    ):
    """requests and decodes data from sensor, returns ValueError if request
    fails, returns None if there is no new data available on the data server

    ATTRIBUTES:
        ip:
            server IP
        key:
            kind of data to retrieve
        raise_dl_flag:
            check if data was lost, if so raise a flag (not supported yet)
    """

    try:
        ans = requests.get(f"http://{ip}/{key}", timeout=du.SEN_timeout)
        ans.raise_for_status()
    except Exception as err:
        return ValueError(f"request failed: {err}!")

    ans_str = ans.text
    if 'no data available' in ans_str:
        return None
    
    data_loss_pos = ans_str.find('&')
    entry_pos = ans_str.find(';')
    if (data_loss_pos <= -1 or entry_pos <= -1):
        return ValueError(f"no readable data retrieved: {ans_str}!")

    if raise_dl_flag:
        data_loss = ans_str[: data_loss_pos-1]
        if data_loss.find('true') == -1:
            #to-do: build a flag for data loss
            pass

    val = []
    remain_str = ans_str[data_loss_pos+1 :]
    entry_pos -= data_loss_pos+1

    while entry_pos != -1:
        next_entry = remain_str[: entry_pos]
        data = next_entry.split('/')
        datapoint = (float(data[0][1 :]), int(data[1][1 :])) #(val, uptime)
        try:
            val.append(datapoint)
        except Exception:
            break

        remain_str = remain_str[entry_pos+1 :]
        entry_pos = remain_str.find(';')

    return val