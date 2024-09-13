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
import copy
import math as m

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import my own libs
import libs.data_utilities as du



###########################     FUNCTIONS      ###############################

def calc_speed() -> tuple[int | None, float]:
    """main function to be called from outside this file, calculates speed the
    pump needs to be set to for the current robot position
    """
    global START_SUPP_PTS
    global END_SUPP_PTS
    global preceeding_comm
    global preceeding_speed
    global last_speed

    p_mode = 'None'
    try:
        curr_comm = du.ROBCommQueue[0]
    except IndexError:
        curr_comm = None

    if isinstance(curr_comm, du.QEntry):
        p_mode = curr_comm.p_mode
        p_ratio = curr_comm.p_ratio

        if curr_comm != preceeding_comm:
            preceeding_comm = copy.deepcopy(curr_comm)
            preceeding_speed = last_speed

    match p_mode:
        case 'None':
            speed = du.PMP_speed
        case 'default':
            speed = default_mode(command=curr_comm)
        case 'start':
            speed = profile_mode(command=curr_comm, profile=START_SUPP_PTS)
        case 'end':
            speed = profile_mode(command=curr_comm, profile=END_SUPP_PTS)
        case 'class1':
            speed = du.DEF_PUMP_CLASS1
        case 'class2':
            speed = du.DEF_PUMP_CLASS2
        case 'zero':
            speed = 0
        case _:
            speed = 0

    # check value domain for speed
    if speed is None:
        return None
    if speed > 100.0:
        speed = 100.0
    if speed < -100.0:
        speed = -100.0

    last_speed = float(speed)
    return int(round(speed, 0)), p_ratio


def default_mode(command=None) -> float | None:
    """standard modus for script-controlled operation, just sets the speed
    according to the current travel speed (TS)

    accepts: 
        command:
            QEntry-like object specifying next movement
    """
    global last_def_command
    global last_speed

    if not isinstance(command, du.QEntry):
        return None
    else:
        Comm = command

    if Comm != last_def_command:
        # determine current volume output:
        lps = (du.PMP1_liter_per_s * du.PMP_output_ratio) + (
            du.PMP2_liter_per_s * (1.0 - du.PMP_output_ratio)
        )

        # [%] =      ( [mm/s]       * [L/m]           * [m/mm]/ [L/s])*100.0
        speed = float(Comm.Speed.ts * du.SC_vol_per_m * 0.001 / lps) * 100.0
        last_def_command = copy.deepcopy(Comm)

    else:
        speed = last_speed

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
            list[dict{"until": float, "base": str, "mode": str},...]
    """
    global preceeding_speed
    global last_speed

    # check passed arguments
    if None in [command, profile]:
        return None
    elif not isinstance(command, du.QEntry):
        return None
    else:
        Comm = command

    # get default speed if profile isn't readable
    speed = default_mode(Comm)

    # as more complex pump scripts should only apply to linear movements,
    # the remaining travel distance can be calculated using pythagoras
    curr = copy.deepcopy(du.ROBTelem.Coor)

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
            settings = copy.deepcopy(item)
            break
        prev_set = item

    if settings is None:
        return speed

    # calc speed accorrding to 'mode' settings
    base = get_base_speed(settings['base'], speed)
    match settings['mode']:

        case 'instant':
            speed = base

        case 'linear':
            # if prev_set is None this is the first setting, need to calculate
            # time from the movements starting point
            time_0 = 0.0
            base_0 = 0.0
            if prev_set is not None:
                time_0 = prev_set['until']
                base_0 = get_base_speed(prev_set['base'], speed)

            else:
                strt = copy.deepcopy(du.ROBMovStartP)
                dist_total = m.sqrt(
                    m.pow(Comm.Coor1.x - strt.x, 2)
                    + m.pow(Comm.Coor1.y - strt.y, 2)
                    + m.pow(Comm.Coor1.z - strt.z, 2)
                )

                # get the remaining time ( [mm] / [mm/s] = [s] )
                time_0 = dist_total / Comm.Speed.ts
                base_0 = preceeding_speed

            slope = (base - base_0) / (settings['until'] - time_0)
            speed = float(time_remaining * slope + base)

        case 'smoothstep':
            # same principle as 'linear' but as sigmoid-like smoothstep
            time_0 = 0.0
            base_0 = 0.0
            if prev_set is not None:
                time_0 = prev_set['until']
                base_0 = get_base_speed(prev_set['base'], speed)

            else:
                strt = copy.deepcopy(du.ROBMovStartP)
                dist_total = m.sqrt(
                    m.pow(Comm.Coor1.x - strt.x, 2)
                    + m.pow(Comm.Coor1.y - strt.y, 2)
                    + m.pow(Comm.Coor1.z - strt.z, 2)
                )

                # get the remaining time ( [mm] / [mm/s] = [s] )
                time_0 = dist_total / Comm.Speed.ts
                base_0 = preceeding_speed

            normalized_t = float(
                (time_remaining - time_0) 
                / (settings['until'] - time_0)
            )
            # get sigmoid function with x * x * ( 3 - 2 * x )
            speed = (
                (base - base_0)
                * normalized_t
                * normalized_t
                * (3-2 * normalized_t)
            )
            speed = float(speed + base_0)

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

last_def_command = None
last_speed = 0.0
