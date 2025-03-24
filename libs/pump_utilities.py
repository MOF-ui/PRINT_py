#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# import re
import os
import sys
import math as m
from copy import deepcopy as dcpy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import my own libs
import libs.data_utilities as du
import libs.func_utilities as fu



###########################     FUNCTIONS      ###############################

def get_pmp_speeds() -> tuple[int, int, bool | None]:
    """see if pump settings have been scripted, otherwise use user 
    input;
    """
    global last_speed

    if du.SC_q_processing:
        ans = calc_speed()
        if ans is None:
            return None
        p1_speed, p2_speed, pinch = ans
    else: 
        p1_speed, p2_speed = speed_by_ratio(du.PMP_speed, du.PMP_output_ratio)
        pinch = None #to-do: implement pinch

    # look for user overwrite, no mutex, as changing
    # global PUMP_user_speed would not harm the process
    if du.PMP1_user_speed != du.DEF_PUMP_NO_USER_SPEED:
        p1_speed = du.PMP1_user_speed
        du.PMP1_user_speed = du.DEF_PUMP_NO_USER_SPEED
    if du.PMP2_user_speed != du.DEF_PUMP_NO_USER_SPEED:
        p2_speed = du.PMP2_user_speed
        du.PMP2_user_speed = du.DEF_PUMP_NO_USER_SPEED
    
    last_speed = (p1_speed + p2_speed)
    return p1_speed, p2_speed, pinch


def speed_by_ratio(t_speed, ratio) -> tuple[float, float]:
    """calculates the speed of the pumps according to the given ratio"""

    # get speed
    if du.PMP1Serial.connected and du.PMP2Serial.connected:
        p1_speed = t_speed * ratio
        p2_speed = t_speed * (1.0 - ratio)
    else:
        p1_speed = p2_speed = t_speed
    return p1_speed, p2_speed


def look_ahead(p1_speed, p2_speed) -> tuple[float, float]:
    """determines the pump speed by looking at the next movement
    in the queue, retracts current pump"""
    try:
        # get current and next command, if no p_ratio change
        # check following commands, protocol path length & 
        # break if to many commands with the same p_ratio
        num_comm = 1
        curr_pos = du.ROBTelem.Coor
        curr_comm = du.ROBCommQueue[0]
        next_comm = du.ROBCommQueue[1]
        dist = curr_pos.distance(curr_comm.Coor1)
        while (
                curr_comm.p_ratio == next_comm.p_ratio
                and num_comm <= du.PMP_look_ahead_max_comms
        ):
            dist += curr_comm.Coor1.distance(next_comm.Coor1)
            num_comm += 1
            curr_comm = next_comm
            next_comm = du.ROBCommQueue[num_comm]

        if dist < du.PMP_look_ahead_dist:
            # reverse direction on currently running pump
            # to reduce pressure in the hose system
            next_speed = next_comm.p_mode
            if -100 < next_speed < 100:
                next_p1_speed, next_p2_speed = speed_by_ratio(
                    next_speed, next_comm.p_ratio
                )
                if p1_speed > 0:
                    p1_speed = -p1_speed * du.PMP_look_ahead_retract
                    p2_speed = next_p2_speed * du.PMP_look_ahead_prerun
                elif p2_speed > 0:
                    p1_speed = next_p1_speed * du.PMP_look_ahead_prerun
                    p2_speed = -p2_speed * du.PMP_look_ahead_retract
    except:
        pass
    
    return p1_speed, p2_speed


def calc_speed() -> tuple[int | None, int, bool]:
    """main function to be called from outside this file, calculates speed the
    pump needs to be set to for the current robot position
    """
    global START_SUPP_PTS
    global END_SUPP_PTS
    global preceeding_comm
    global preceeding_speed
    global last_speed

    p_mode = -1001 # = no p_mode given
    p_ratio = 1.0
    pinch = False
    try:
        curr_comm = du.ROBCommQueue[0]
    except IndexError:
        curr_comm = None

    if isinstance(curr_comm, du.QEntry):
        p_mode = curr_comm.p_mode
        p_ratio = curr_comm.p_ratio
        pinch = curr_comm.pinch

        if curr_comm != preceeding_comm:
            preceeding_comm = dcpy(curr_comm)
            preceeding_speed = last_speed

    speed = None
    if p_mode in du.DEF_PUMP_VALID_COMMANDS:
        match p_mode:
            case -1001:
                speed = du.PMP_speed
            case 1001:
                speed = default_mode(command=curr_comm)
            case 1002:
                speed = profile_mode(command=curr_comm, profile=START_SUPP_PTS)
            case 1003:
                speed = profile_mode(command=curr_comm, profile=END_SUPP_PTS)
            case 1101:
                speed = du.DEF_PUMP_CLASS1
            case 1102:
                speed = du.DEF_PUMP_CLASS2
            case _:
                speed = 0
    if -100 <= p_mode <= 100:
        speed = p_mode
    if speed is None:
        return None

    p1_speed, p2_speed = speed_by_ratio(speed, p_ratio)
    if du.PMP_look_ahead:
        p1_speed, p2_speed = look_ahead(p1_speed, p2_speed)

    # check value domain for speed
    p1_speed = int(fu.domain_clip(p1_speed, -100.0, 100.0))
    p2_speed = int(fu.domain_clip(p2_speed, -100.0, 100.0))
    return p1_speed, p2_speed, pinch


def default_mode(command=None) -> float | None:
    """standard modus for script-controlled operation, just sets the speed
    according to the current travel speed (TS)

    accepts: 
        command:
            QEntry-like object specifying next movement
    """

    if not isinstance(command, du.QEntry):
        return None
    else:
        Comm = command

    # determine current volume output:
    lps = (du.PMP1_liter_per_s * du.PMP_output_ratio) + (
        du.PMP2_liter_per_s * (1.0 - du.PMP_output_ratio)
    )
    # [%] =      ( [mm/s]       * [L/m]           * [m/mm]/ [L/s])*100.0
    speed = float(Comm.Speed.ts * du.SC_vol_per_m * 0.001 / lps) * 100.0

    return speed


def profile_mode(command=None, profile=None) -> float | None:
    """pump mode for preset pump speed profiles, set with support points,
    can be used to drive custom pump speed slopes before, while or after
    printing
    
    accepts: 
        command:
            QEntry-like object specifying next movement
        profile:
            pump profile for this movement in the struct of 
            list[dict{'until': float, 'base': str, 'mode': str},...]
    """
    global preceeding_speed

    # check passed arguments
    if (
            profile is None
            or not isinstance(command, du.QEntry)
    ):
        return None
    else:
        Comm = command

    # get default speed in case profile isn't readable
    speed = default_mode(Comm)
    # as more complex pump scripts should only apply to linear movements,
    # the remaining travel distance can be calculated using pythagoras
    curr = dcpy(du.ROBTelem.Coor)
    dist_remaining = m.sqrt(
        m.pow(Comm.Coor1.x - curr.x, 2)
        + m.pow(Comm.Coor1.y - curr.y, 2)
        + m.pow(Comm.Coor1.z - curr.z, 2)
    )

    # get the remaining time ( [mm] / [mm/s] = [s] )
    time_remaining = float(dist_remaining / Comm.Speed.ts)
    # get time-dependent settings
    settings = None
    prev_set = None
    for item in profile:
        if item['until'] <= time_remaining:
            settings = dcpy(item)
            break
        prev_set = item
    # if no active settings are found, return the default speed
    if settings is None:
        return speed

    # calc speed accorrding to 'mode' settings
    base = get_base_speed(settings['base'], speed)
    time_0 = 0.0
    base_0 = 0.0
    # if prev_set is None this is the first setting, need to calculate
    # time from the movements starting point
    if prev_set is not None:
        time_0 = prev_set['until']
        base_0 = get_base_speed(prev_set['base'], speed)
    else:
        strt = dcpy(du.ROBMovStartP)
        dist_total = m.sqrt(
            m.pow(Comm.Coor1.x - strt.x, 2)
            + m.pow(Comm.Coor1.y - strt.y, 2)
            + m.pow(Comm.Coor1.z - strt.z, 2)
        )

        # get the remaining time ( [mm] / [mm/s] = [s] )
        time_0 = dist_total / Comm.Speed.ts
        base_0 = preceeding_speed

    match settings['mode']:
        case 'linear':
            slope = (base - base_0) / (settings['until'] - time_0)
            speed = float(time_remaining * slope + base)
        case 'smoothstep':
            normalized_t = float(
                (time_remaining - time_0) / (settings['until'] - time_0)
            )
            # get sigmoid function with x * x * ( 3 - 2 * x )
            speed = (
                (base - base_0)
                * normalized_t
                * normalized_t
                * (3-2 * normalized_t)
            )
            speed = float(speed + base_0)
        case _:
            speed = base

    return speed


def get_base_speed(base='default', fallback=0.0) -> float | None:

    match base:
        case 'zero':
            base_speed = 0.0
        case 'max':
            base_speed = 100.0
        case 'min':
            base_speed = -100.0
        case 'default':
            base_speed = fallback
        case 'retract':
            base_speed = du.PMP_retract_speed
        case 'conn':

            try:
                next_comm = du.ROBCommQueue[1]
                lps = (du.PMP1_liter_per_s * du.PMP_output_ratio) + (
                    du.PMP2_liter_per_s * (1.0 - du.PMP_output_ratio)
                )

                base_speed = next_comm.Speed.ts * du.SC_vol_per_m * 0.001 / lps
                base_speed = float(base_speed *100)

            except AttributeError:
                base_speed = fallback

        case _:
            return None

    return base_speed



############################     GLOBALS      ################################

START_SUPP_PTS = [
    {'until': 5.0, 'base': 'zero', 'mode': 'instant'},
    {'until': 1.0, 'base': 'max', 'mode': 'instant'},
    {'until': 0.0, 'base': 'conn', 'mode': 'linear'},
]

END_SUPP_PTS = [
    {'until': 5.0, 'base': 'default', 'mode': 'instant'},
    {'until': 1.0, 'base': 'retract', 'mode': 'smoothstep'},
    {'until': 0.0, 'base': 'zero', 'mode': 'instant'},
]

preceeding_comm = None
preceeding_speed = 0.0

last_speed = 0.0
