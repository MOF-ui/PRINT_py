#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# import re 
import os
import sys
import copy
import math as m

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import my own libs
import libs.PRINT_data_utilities as UTIL



#############################################################################################
#                                    FUNCTIONS
#############################################################################################

def calcSpeed():
    """ main function to be called from outside this file, calculates speed the pump needs to
        be set to for the current robot position """
    global START_SUPP_PTS
    global END_SUPP_PTS
    global preceedingCom
    global preceedingSpeed
    global lastSpeed

    pMode = 'None'
    try:                currCommand = UTIL.ROB_commQueue[0]
    except IndexError:  currCommand = None

    if( currCommand is not None ): 
        pMode = currCommand.pMode
        if( currCommand != preceedingCom ):
            preceedingCom   = copy.deepcopy( currCommand )
            preceedingSpeed = lastSpeed

    match pMode:
        
        case 'None':    
            speed = UTIL.PUMP1_speed

        case 'default': 
            speed = defaultMode( command= currCommand )
        
        case 'start':
            speed = profileMode( command= currCommand, profile= START_SUPP_PTS )

        case 'end':
            speed = profileMode( command= currCommand, profile= END_SUPP_PTS )

        case _:        
            speed = 0

    # check value domain for speed
    if( speed >  100.0 ): speed =  100.0
    if( speed < -100.0 ): speed = -100.0

    lastSpeed = speed
    return speed





def defaultMode( command= None ):
    """ standard modus for script-controlled operation, just sets the speed according
        to the current travel speed (TS) """
    global lastDefCommand
    global lastSpeed

    if( command is None ):   return None
    if( command != lastDefCommand ):
                # ([mm/s]          * [L/mm]           / [L/s]                ) * 100.0  =  [%]
        speed = ( command.Speed.ts * UTIL.SC_volPerMm / UTIL.PUMP1_literPerS ) * 100.0
        lastDefCommand = copy.deepcopy(command)

    else:
        speed = lastSpeed

    return speed




def profileMode( command= None, profile= None ):
    """ pump mode for preset pump speed profiles, set with support points, can be used to 
        drive custom pump speed slopes before, while or after printing """
    global DIFF_CONST
    global preceedingSpeed

    if( None in [command, profile] ): return None
    speed = ( command.Speed.ts * UTIL.SC_volPerMm / UTIL.PUMP1_literPerS ) * 100.0

    # as more complex pump scripts should only apply to linear movements, 
    # the remaining travel distance can be calculated using pythagoras
    end  = copy.deepcopy( UTIL.ROB_movEndP )
    curr = copy.deepcopy( UTIL.ROB_telem.Coor.x )

    distRemainng    = m.sqrt(  m.pow(end.x - curr.x, 2)
                             + m.pow(end.y - curr.y, 2)
                             + m.pow(end.z - curr.z, 2) )

    # get the remaining time ( [mm] / [mm/s] = [s] )
    timeRemainung   = distRemainng / command.Speed.ts

    # get time-dependent settings
    settings    = None
    prevSett    = None
    for item in profile:
        if( item['until'] < timeRemainung ):
            settings = copy.deepcopy(item)
            break
        prevSett = item
    
    if( settings is None ): 
        return speed
    
    base = getBaseSpeed( settings['base'], speed )

    match settings['mode']:
        case 'instant': speed = base
        case 'diff':    speed += ( base - speed ) * DIFF_CONST
        case 'linear':  
            # if settDur is 0.0 this is the first setting, need to calculate time from the 
            # movements starting point
            timeNull = 0.0
            baseNull = 0.0
            if( prevSett is not None): 
                timeNull = prevSett['until']
                baseNull = getBaseSpeed( prevSett['base'] )

            else:
                strt        = copy.deepcopy( UTIL.ROB_movStartP )
                distTotal   = m.sqrt(  m.pow(end.x - strt.x, 2)
                                     + m.pow(end.y - strt.y, 2)
                                     + m.pow(end.z - strt.z, 2) )

                # get the remaining time ( [mm] / [mm/s] = [s] )
                timeNull = distTotal / command.Speed.ts
                baseNull = preceedingSpeed

            slope = ( baseNull - base ) / ( timeNull - settings['until'] )
            speed = timeRemainung * slope + baseNull

    return speed    
    
    



def getBaseSpeed(base = 'default', fallback = 0.0):

    base = 0.0
    match base:
        case 'zero':    baseSpeed = 0.0
        case 'max':     baseSpeed = 100.0
        case 'min':     baseSpeed = -100.0
        case 'default': baseSpeed = fallback
        case 'retract': baseSpeed = UTIL.PUMP1_retractSpeed
        case 'conn':    
            try:                nextCommand = UTIL.ROB_commQueue[1]
            except IndexError:  nextCommand = None
            baseSpeed = ( nextCommand.Speed.ts * UTIL.SC_volPerMm / UTIL.PUMP1_literPerS ) * 100.0
        
    return baseSpeed






#############################################################################################
#                                     GLOBALS
#############################################################################################

DIFF_CONST      = 0.25
START_SUPP_PTS  = [   { 'until': 3.0,   'base': 'zero',     'mode': 'instant' },
                      { 'until': 1.0,   'base': 'max',      'mode': 'diff'    },
                      { 'until': 0.0,   'base': 'conn',     'mode': 'linear'  } ]

END_SUPP_PTS    = [   { 'until': 5.0,   'base': 'default',  'mode': 'instant' },
                      { 'until': 1.0,   'base': 'retract',  'mode': 'diff'    },
                      { 'until': 0.0,   'base': 'zero',     'mode': 'instant' } ]


preceedingCom   = None
preceedingSpeed = 0.0

lastDefCommand  = None
lastSpeed       = 0.0