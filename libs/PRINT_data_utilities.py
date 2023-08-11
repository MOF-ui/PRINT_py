#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

import re 
import os
import copy
import socket
import struct
import math as m

from pathlib import Path
from datetime import datetime
# import time



#############################################################################################
#                                    CLASSES
#############################################################################################

class Coor:
    """standard 7-axis coordinate block (8 attributes, as quaterion positioning is possible)

    ATTRIBUTES:
        X, Y, Z:
            position in cartesian coordinates
        X_ori, Y_ori, Z_ori:
            angle relative to cartesian coordinates
        Q:
            additional var for fourth quaternion coordinate
        EXT:
            external axis position

    FUNCTIONS:
        __init__ \n
        __str__  \n
        __add__  \n
        __sub__  \n
        __round__\n
        __eq__
    """

    def __init__(self,
                 X  	= 0.0, 
                 Y  	= 0.0, 
                 Z  	= 0.0, 
                 X_ori  = 0.0, 
                 Y_ori  = 0.0, 
                 Z_ori  = 0.0, 
                 Q      = 0.0, 
                 EXT    = 0.0):
        
        self.X      = float(X)
        self.Y      = float(Y)
        self.Z      = float(Z)
        self.X_ori  = float(X_ori)
        self.Y_ori  = float(Y_ori)
        self.Z_ori  = float(Z_ori)
        self.Q      = float(Q)
        self.EXT    = float(EXT)
    


    def __str__(self):

        return f"X: {self.X}   Y: {self.Y}   Z: {self.Z}   Rx: {self.X_ori}   Ry: {self.Y_ori}   Rz: {self.Z_ori}   " \
               f"Q: {self.Q}   EXT: {self.EXT}"
    


    def __add__(self,summand):

        try:
            return round( Coor( (self.X        + summand.X)
                               ,(self.Y        + summand.Y)
                               ,(self.Z        + summand.Z)
                               ,(self.X_ori    + summand.X_ori)
                               ,(self.Y_ori    + summand.Y_ori)
                               ,(self.Z_ori    + summand.Z_ori)
                               ,(self.Q        + summand.Q)
                               ,(self.EXT      + summand.EXT) )
                         , 6)
        except AttributeError:
            return round( Coor( (self.X        + summand)
                               ,(self.Y        + summand)
                               ,(self.Z        + summand)
                               ,(self.X_ori    + summand)
                               ,(self.Y_ori    + summand)
                               ,(self.Z_ori    + summand)
                               ,(self.Q        + summand)
                               ,(self.EXT      + summand) )
                         , 6)
    


    def __sub__(self,subtrahend):

        try:
            return round( Coor( (self.X        - subtrahend.X)
                               ,(self.Y        - subtrahend.Y)
                               ,(self.Z        - subtrahend.Z)
                               ,(self.X_ori    - subtrahend.X_ori)
                               ,(self.Y_ori    - subtrahend.Y_ori)
                               ,(self.Z_ori    - subtrahend.Z_ori)
                               ,(self.Q        - subtrahend.Q)
                               ,(self.EXT      - subtrahend.EXT) )
                        , 6)
        except AttributeError:
            return round( Coor( (self.X        - subtrahend)
                               ,(self.Y        - subtrahend)
                               ,(self.Z        - subtrahend)
                               ,(self.X_ori    - subtrahend)
                               ,(self.Y_ori    - subtrahend)
                               ,(self.Z_ori    - subtrahend)
                               ,(self.Q        - subtrahend)
                               ,(self.EXT      - subtrahend) )
                        , 6)
    


    def __round__(self, digits):
        
        return Coor( round(self.X    , digits) 
                    ,round(self.Y    , digits)
                    ,round(self.Z    , digits)
                    ,round(self.X_ori, digits)
                    ,round(self.Y_ori, digits)
                    ,round(self.Z_ori, digits)
                    ,round(self.Q    , digits)
                    ,round(self.EXT  , digits) )
    


    def __eq__(self,other):

        try:
            if(     self.X     == other.X
                and self.Y     == other.Y
                and self.Z     == other.Z
                and self.X_ori == other.X_ori
                and self.Y_ori == other.Y_ori
                and self.Z_ori == other.Z_ori
                and self.Q     == other.Q
                and self.EXT   == other.EXT):
                return True
            else: return False

        except AttributeError:
            return False





class Speed:
    """standard speed vector (4 attributes).

    ATTRIBUTES:
        TS:
            transition speed
        OR:
            orientation speed
        ACR:
            acceleration ramp
        DCR:
            deceleration ramp
    
    FUNCTIONS:
        __init__\n
        __str__ \n
        __mul__ \n
        __rmul__\n
        __eq__
    """

    def __init__(self, 
                 ACR    = 50, 
                 DCR    = 50, 
                 TS     = 200, 
                 OS     = 50):
        
        self.ACR    = int( round( ACR , 0) )
        self.DCR    = int( round( DCR , 0) )
        self.TS     = int( round( TS  , 0) )
        self.OS     = int( round( OS  , 0) )



    def __str__(self):

        return f"TS: {self.TS}   OS: {self.OS}   ACR: {self.ACR}   DCR: {self.DCR}"
    


    def __mul__(self,other):

        return Speed( TS = int(  round( self.TS *  other, 0) ) 
                     ,OS = int(  round( self.OS *  other, 0) ) 
                     ,ACR = int( round( self.ACR * other, 0) ) 
                     ,DCR = int( round( self.DCR * other, 0) ) )
    


    def __rmul__(self,other):

        return self.__mul__(other)
    


    def __eq__(self,other):

        try:
            if(     self.ACR == other.ACR
                and self.DCR == other.DCR
                and self.TS  == other.TS
                and self.OS  == other.OS):
                return True
            else: return False

        except AttributeError:
            return False




class ToolCommand:
    """standard tool command according to Jonas' protocol

    ATTRIBUTES:
        M1_ID:
            motor 1 ID (fiber pivoting)
        M1_STEPS:
            motor 1 steps/position
        M2_ID:
            motor 2 ID (fiber delivery)
        M2_STEPS:
            motor 2 steps/position
        M3_ID:
            motor 3 ID (mortar pump)
        M3_STEPS:
            motor 3 steps/position
        PNMTC_CLAMP_ID:
            pneumatic fiber clamp ID
        PNMTC_CLAMP_YN:
            pneumatic fiber clamp on/off
        KNIFE_ID:
            knife delivery ID
        KNIFE_YN:
            knife delivery on/off
        M4_ID:
            motor 4 ID (rotation knife)
        M4_STEPS:
            motor 4 steps/position
        PNMTC_FIBER_ID:
            pneumatic fiber conveyer ID
        PNMTC_FIBER_YN:
            pneumatic fiber conveyer on/off
        TIME_ID:
            time ID
        TIME_TIME:
            current time in milli seconds at EE
        
    FUNCTIONS:
        __def__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 M1_ID          = 0,
                 M1_STEPS       = 0,
                 M2_ID          = 0,
                 M2_STEPS       = 0,
                 M3_ID          = 0,
                 M3_STEPS       = 0,
                 PNMTC_CLAMP_ID = 0,
                 PNMTC_CLAMP_YN = 0,
                 KNIFE_ID       = 0,
                 KNIFE_YN       = 0,
                 M4_ID          = 0,
                 M4_STEPS       = 0,
                 PNMTC_FIBER_ID = 0,
                 PNMTC_FIBER_YN = 0,
                 TIME_ID        = 0,
                 TIME_TIME      = 0):
        
        self.M1_ID          = int(M1_ID)
        self.M1_STEPS       = int(M1_STEPS)
        self.M2_ID          = int(M2_ID)
        self.M2_STEPS       = int(M2_STEPS)
        self.M3_ID          = int(M3_ID)
        self.M3_STEPS       = int(M3_STEPS)
        self.PNMTC_CLAMP_ID = int(PNMTC_CLAMP_ID)
        self.PNMTC_CLAMP_YN = bool(PNMTC_CLAMP_YN)
        self.KNIFE_ID       = int(KNIFE_ID)
        self.KNIFE_YN       = bool(KNIFE_YN)
        self.M4_ID          = int(M4_ID)
        self.M4_STEPS       = bool(M4_STEPS)
        self.PNMTC_FIBER_ID = int(PNMTC_FIBER_ID)
        self.PNMTC_FIBER_YN = bool(PNMTC_FIBER_YN)
        self.TIME_ID        = int(TIME_ID)
        self.TIME_TIME      = int(TIME_TIME)



    def __str__(self):

        return  f"M1: {self.M1_ID}, {self.M1_STEPS}   M2: {self.M2_ID}, {self.M2_STEPS}   M3: {self.M3_ID}, {self.M3_STEPS}   "\
                f"P_C: {self.PNMTC_CLAMP_ID}, {self.PNMTC_CLAMP_YN}   KN: {self.KNIFE_ID}, {self.KNIFE_YN}   "\
                f"M4: {self.M4_ID}, {self.M4_STEPS}   P_F: {self.PNMTC_FIBER_ID}, {self.PNMTC_FIBER_YN}   "\
                f"TIME: {self.TIME_ID}, {self.TIME_TIME}"
    


    def __eq__(self,other):

        try:
            if(     self.M1_ID          == other.M1_ID
                and self.M1_STEPS       == other.M1_STEPS
                and self.M2_ID          == other.M2_ID
                and self.M2_STEPS       == other.M2_STEPS
                and self.M3_ID          == other.M3_ID
                and self.M3_STEPS       == other.M3_STEPS
                and self.PNMTC_CLAMP_ID == other.PNMTC_CLAMP_ID
                and self.PNMTC_CLAMP_YN == other.PNMTC_CLAMP_YN
                and self.KNIFE_ID       == other.KNIFE_ID
                and self.KNIFE_YN       == other.KNIFE_YN
                and self.M4_ID          == other.M4_ID
                and self.M4_STEPS       == other.M4_STEPS
                and self.PNMTC_FIBER_ID == other.PNMTC_FIBER_ID
                and self.PNMTC_FIBER_YN == other.PNMTC_FIBER_YN
                and self.TIME_ID        == other.TIME_ID
                and self.TIME_TIME      == other.TIME_TIME):
                return True
            else: return False

        except AttributeError:
            return False





class QEntry:
    """standard 159 byte command queue entry for TCP robot according to the protocol running on the robot
    
    ATTRIBUTES:
        ID: 
            command ID, list number in robot internal queue
        MT:
            type of movement or special command (L = linear, J = joint, C = circular, S = stop after current movement
            & delete robot internal queue, E = end TCP protocol on robot)
        PT:
            position type, type of rotation given (E = Euler angles, Q = quaternion, A = axis positioning)
        COOR_1:
            coordinates of the first given point
        COOR_2:
            coordinates of the second given point
        SV:
            speed vector for given movement
        SBT:
            time to calculate speed by
        SC:
            speed command, set movement speed by movement time (SBT) or speed vector (SV), (T = time, V = vector)
        Z:
            zone, endpoint precision
        TOOL:
            tool command in Jonas' standard format
        
    FUNCTIONS:
        __init__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 ID     = 0,
                 MT     = "L",
                 PT     = "E",
                 COOR_1 = None,
                 COOR_2 = None,
                 SV     = None,
                 SBT    = 0,
                 SC     = "V",
                 Z      = 10,
                 TOOL   = None):
        
        self.ID     = int(ID)
        self.MT     = str(MT)
        self.PT     = str(PT)
        self.SBT    = int(SBT)
        self.SC     = str(SC)
        self.Z      = int(Z)

        # handle those beasty mutables
        self.COOR_1 = Coor()        if (COOR_1 == None) else COOR_1
        self.COOR_2 = Coor()        if (COOR_2 == None) else COOR_2
        self.SV     = Speed()       if (SV == None)     else SV
        self.TOOL   = ToolCommand() if (TOOL == None)   else TOOL
    


    def __str__(self):
        
        return  f"ID: {self.ID}  MT: {self.MT}  PT: {self.PT} \t|| COOR_1: {self.COOR_1}"\
                f"\n\t\t|| COOR_2: {self.COOR_2}"\
                f"\n\t\t|| SV:     {self.SV} \t|| SBT: {self.SBT}   SC: {self.SC}   Z: {self.Z}"\
                f"\n\t\t|| TOOL:   {self.TOOL}"
    


    def __eq__(self,other):

        try:
            if(     self.ID     == other.ID
                and self.MT     == other.MT
                and self.PT     == other.PT
                and self.COOR_1 == other.COOR_1
                and self.COOR_2 == other.COOR_2
                and self.SV     == other.SV
                and self.SBT    == other.SBT
                and self.SC     == other.SC
                and self.Z      == other.Z
                and self.TOOL   == other.TOOL):
                return True
            else: return False

        except AttributeError:
            return False





class Queue:
    """QEntry-based list incl. data handling
    
        ATTRIBUTES:
            queue:
                a list of QEntry elements, careful: list index does not match QEntry.ID

        FUNCTIONS:
            __init__\n
            __getitem__\n
            __len__\n
            __str__\n
            __eq__

            lastEntry:
                returns last entry
            entryBeforeID:
                returns entry before given ID
            display:
                returns queue as a str list (uses __str__ of QEntry)
            increment:
                increments all QEntry.ID to handle DC commands send before the queue
            add:
                adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given
            clear:
                deletes single or multiple QEntry from queue, adjusts following ID accordingly
            popFirstItem:
                returns and deletes the QEntry at index 0
    """

    def __init__(self,queue = None):

        self.queue = [] if (queue == None) else queue



    def __getitem__(self,i):

        try:                return self.queue[i]
        except IndexError:  return None


    
    def __len__(self):

        return len(self.queue)
    


    def __str__(self):

        if (len(self.queue) != 0):
            i   = 0
            ans = ''
            for x in self.queue:
                i   += 1
                ans += f"Element {i}: {x}\n"
            return ans
        return "Queue is empty!"
    


    def __eq__(self, other):

        length = len(self)
        if( length != len(other) ): return False

        for elem in range(length):
            if (self[elem] != other[elem]): return False
        
        return True
    


    def lastEntry(self):
        """ returns last item in queue (surprise!), returns None if queue is empty"""

        if (len(self.queue) == 0): 
            return None
        return self.queue[ len(self.queue) - 1 ]
    

    def entryBeforeID(self,ID):
        """ return queue entry before (index - 1) a specific ID, return last entry if ID not found,
            returns None if queue is empty or if ID was not matched """

        length = len(self.queue)
        i      = 0

        if (length == 0):  return None

        for entry in range(length):
            if (self.queue[entry].ID == ID): break
            else:                            i += 1
        
        if ( (i < 1) or (i >= length) ): 
            return None
        
        return self.queue[ i - 1 ]



    def display(self):
        """ returns queue as a str list (uses __str__ of QEntry) """

        if (len(self.queue) != 0):
            ans = []
            for x in self.queue: ans.append( str(x) )
            return ans
        return ["Queue is empty!"]



    def increment(self):
        """ increments all QEntry.ID to handle DC commands send before the queue """

        for i in self.queue:
            i.ID += 1



    def add(self, newEntry):
        """ adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given """

        lastItem = len(self.queue) - 1 
        if(lastItem < 0):
            global SC_curr_comm_id

            newEntry.ID = SC_curr_comm_id
            self.queue.append(newEntry)
            return None
        
        lastID  = self.queue[lastItem].ID
        firstID = self.queue[0].ID
        if( (newEntry.ID == 0) or (newEntry.ID > lastID) ):
            newEntry.ID = lastID + 1
            self.queue.append(newEntry)

        elif( newEntry.ID < 0 ):     return ValueError

        else:
            if( newEntry.ID < firstID ):  newEntry.ID = firstID
            
            frontSkip = newEntry.ID - self.queue[0].ID
            self.queue.insert(frontSkip,newEntry)
            for i in range(lastItem + 1 - frontSkip):
                i += 1
                self.queue[i + frontSkip].ID += 1

        return None
    


    def clear(self, all = True, ID = ''):
        """ deletes single or multiple QEntry from queue, adjusts following ID accordingly """

        if(all):
            self.queue = []
            return self.queue

        ids     = re.findall('\d+',ID)
        idNum   = len(ids)
        firstID = self.queue[0].ID
        lastID  = self.queue[len(self.queue) - 1].ID
        
        match idNum:

            case 1:
                id1 = int(ids[0])

                if( (id1 < firstID) or (id1 > lastID) ):  return ValueError

                i = 0
                for entry in self.queue:
                    if(entry.ID == id1):    break
                    else:                   i += 1
                
                self.queue.__delitem__(i)
                while (i < len(self.queue)):
                    self.queue[i].ID -= 1
                    i += 1

            case 2:
                id1,id2 = int(ids[0]), int(ids[1])

                if( (id1 < firstID) 
                     or (id1 > lastID) 
                     or (id2 < id1) 
                     or (id2 > lastID) 
                     or (ID.find('..') == -1) ):
                    return ValueError
                
                idDist = (id2 - id1) + 1
                i = 0
                for entry in self.queue:
                    if(entry.ID == id1):    break
                    else:                   i += 1
                
                for n in range(idDist):
                    self.queue.__delitem__(i)
                
                while ( i < len(self.queue) ):
                    self.queue[i].ID -= idDist
                    i += 1

            case _: 
                return ValueError      

        return self.queue 



    def popFirstItem(self):        
        """ returns and deletes the QEntry at index 0"""

        try:                entry = self.queue[0]
        except IndexError:  return IndexError
        self.queue.__delitem__(0)
        return entry





class RoboTelemetry:
    """ class used to store the standard 36 byte telemetry data comming from the robot 
    
    
    FUNCTIONS:
        __init__\n
        __str__\n
        __round__\n
        __eq__
    """

    def __init__(self,
                 TOOL_SPEED  = 0.0,
                 ID          = -1,
                 POS         = None):
        
        self.TOOL_SPEED = float(TOOL_SPEED)
        self.ID         = int(ID)

        # handle those beasty mutables
        self.POS = Coor()   if (POS == None) else POS




    def __str__(self):

        return  f"ID: {self.ID}   X: {self.POS.X}   Y: {self.POS.Y}   Z: {self.POS.Z}   Rx: {self.POS.X_ori}   Ry: {self.POS.Y_ori}   Rz: {self.POS.Z_ori}   "\
                f"EXT:   {self.POS.EXT}   TOOL_SPEED: {self.TOOL_SPEED}"
    


    def __round__(self, digits):

        return RoboTelemetry( round(self.TOOL_SPEED, digits) 
                             ,self.ID
                             ,round(self.POS,        digits))
    


    def __eq__(self, other):

        try:
            if(     self.TOOL_SPEED == other.TOOL_SPEED
                and self.ID         == other.ID
                and self.POS        == other.POS):
                return True
            else: return False

        except AttributeError:
            return False






class PumpTelemetry:
    """ class used to store the standard telemetry data the pump 
    
    FUNCTIONS:
        __init__\n
        __str__\n
        __round__\n
        __eq__
    """

    def __init__(self,
                 FREQ = 0.0,
                 VOLT = 0.0,
                 AMPS = 0.0,
                 TORQ = 0.0):
        
        self.FREQ = float(FREQ)
        self.VOLT = float(VOLT)
        self.AMPS = float(AMPS)
        self.TORQ = float(TORQ)



    def __str__(self):

        return  f"FREQ: {self.FREQ}   VOLT: {self.VOLT}   AMPS: {self.AMPS}   TORQ: {self.TORQ}"
    


    def __round__(self, digits):

        return PumpTelemetry( round(self.FREQ, digits)
                             ,round(self.VOLT, digits)
                             ,round(self.AMPS, digits)
                             ,round(self.TORQ, digits) )
    


    def __eq__(self, other):

        try:
            if(     self.FREQ == other.FREQ
                and self.VOLT == other.VOLT
                and self.AMPS == other.AMPS
                and self.TORQ == other.TORQ):
                return True
            else: return False

        except AttributeError:
            return False
    




class DataBlock:
    """ structure for DAQ 
    
    FUNCTIONS:
        __init__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 ambTemp =          0.0,
                 ambHum =           0.0,
                 delivPumpTemp =    0.0,
                 robBaseTemp =      0.0,
                 kPumpTemp =        0.0,
                 delivPumpPress =   0.0,
                 kPumpPress =       0.0,
                 PUMP1 =            None,
                 PUMP2 =            None,
                 admPumpFreq =      0.0,
                 admPumpAmps =      0.0,
                 kPumpFreq =        0.0,
                 kPumpAmps =        0.0,
                 id =               0,
                 toolSpeed =        0.0,
                 POS =              None,
                 porosAnalysis =    0.0,
                 distanceFront =    0.0,
                 distanceEnd =      0.0):
        
        self.ambTemp =          float(ambTemp)
        self.ambHum =           float(ambHum)
        self.delivPumpTemp =    float(delivPumpTemp)
        self.robBaseTemp =      float(robBaseTemp)
        self.kPumpTemp =        float(kPumpTemp)
        self.delivPumpPress =   float(delivPumpPress)
        self.kPumpPress =       float(kPumpPress)
        self.admPumpFreq =      float(admPumpFreq)
        self.admPumpAmps =      float(admPumpAmps)
        self.kPumpFreq =        float(kPumpFreq)
        self.kPumpAmps =        float(kPumpAmps)
        self.id =               int(id)
        self.toolSpeed =        float(toolSpeed)
        self.porosAnalysis =    float(porosAnalysis)
        self.distanceFront =    float(distanceFront)
        self.distanceEnd =      float(distanceEnd)

        # handle those beasty mutables
        self.PUMP1  = PumpTelemetry()   if (PUMP1 == None) else PUMP1
        self.PUMP2  = PumpTelemetry()   if (PUMP2 == None) else PUMP2
        self.POS    = Coor()            if (POS == None) else POS



    def __str__(self):

        return f"ambTemp: {self.ambTemp}    ambHum: {self.ambHum}    delivPumpTemp: {self.delivPumpTemp}    robBaseTemp: {self.robBaseTemp}    "\
               f"kPumpTemp: {self.kPumpTemp}    delivPumpPress: {self.delivPumpPress}    kPumpPress: {self.kPumpPress}    PUMP1: {self.PUMP1}    "\
               f"PUMP2: {self.PUMP2}    admPumpFreq: {self.admPumpFreq}    admPumpAmps: {self.admPumpAmps}    kPumpFreq: {self.kPumpFreq}    "\
               f"kPumpAmps: {self.kPumpAmps}    id: {self.id}    toolspeed: {self.toolSpeed}    POS: {self.POS}    porosAnalysis: {self.porosAnalysis}    "\
               f"distanceFront: {self.distanceFront}    distanceEnd: {self.distanceEnd}"    
    


    def __eq__(self, other):

        try:
            if(     self.ambTemp        == other.ambTemp
                and self.ambHum         == other.ambHum
                and self.delivPumpTemp  == other.delivPumpTemp
                and self.robBaseTemp    == other.robBaseTemp
                and self.kPumpTemp      == other.kPumpTemp
                and self.delivPumpPress == other.delivPumpPress
                and self.kPumpPress     == other.kPumpPress
                and self.PUMP1          == other.PUMP1
                and self.PUMP2          == other.PUMP2
                and self.admPumpFreq    == other.admPumpFreq
                and self.admPumpAmps    == other.admPumpAmps
                and self.kPumpFreq      == other.kPumpFreq
                and self.kPumpAmps      == other.kPumpAmps
                and self.id             == other.id
                and self.toolSpeed      == other.toolSpeed
                and self.POS            == other.POS
                and self.porosAnalysis  == other.porosAnalysis
                and self.distanceFront  == other.distanceFront
                and self.distanceEnd    == other.distanceEnd):
                return True
            else: return False

        except AttributeError:
            return False



class TCPIP:
    """ setup class for TCP/IP connection, provides all functions concerning the connection, cement pump communication not yet implemented

    ATTRIBUTES:
        IP:
            endpoint IP address
        PORT:
            endpoint port nummber
        C_TOUT:
            timeout for connection attempts to endpoint
        RW_TOUT:
            timeout for reading from or writing to endpoint
        R_BL:
            data block length to read
        W_BL:
            data block length to write
    
    FUNCTIONS:
        __init__\n
        __str__\n

        connect:
            tries to connect to the IP and PORT given, returns errors if not possible
        send: 
            sends data to server, packing according to robots protocol, additional function for pump needed
        receive:
            receives and unpacks data from robot, addtional function needed for pump
        close:
            close TCP/IP connection
    """
    

    def __init__(self, 
                 IP         = "",
                 PORT       = 0,
                 C_TOUT     = 1.0,
                 RW_TOUT    = 1,
                 R_BL       = 0,
                 W_BL       = 0):
        
        self.IP         = str(IP)
        self.PORT       = str(PORT)
        self.C_TOUT     = float(C_TOUT)
        self.RW_TOUT    = float(RW_TOUT)
        self.R_BL       = int(R_BL)
        self.W_BL       = int(W_BL)

        self.connected  = False
        self.sock       = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.telemetry  = RoboTelemetry()
    

    def __str__(self):

        return  f"IP: {self.IP}   PORT: {self.PORT}   C_TOUT: {self.C_TOUT}   RW_TOUT: {self.RW_TOUT}   "\
                f"R_BL: {self.R_BL}   W_BL: {self.W_BL}"
    


    def setParams(self, paramDict):
        if(self.connected): 
            raise PermissionError('params not changeable while connected to server!')
        
        self.IP         = str  ( paramDict["IP"] )
        self.PORT       = str  ( paramDict["PORT"] )
        self.C_TOUT     = float( paramDict["CTOUT"] )
        self.RW_TOUT    = float( paramDict["RWTOUT"] )
        self.R_BL       = int  ( paramDict["R_BL"] )
        self.W_BL       = int  ( paramDict["W_BL"] )



    def connect(self):
        """ tries to connect to the IP and PORT given, returns errors if not possible """

        try:                server_address = (self.IP, int(self.PORT))
        except ValueError:  raise ConnectionError('requested TCP/IP connection via COM-Port!')
        
        self.sock.settimeout(self.C_TOUT)

        try:
            self.sock.connect(server_address)
            self.connected = True
            self.sock.settimeout(self.RW_TOUT)
            return True,server_address
        
        except TimeoutError:
            self.connected = 0
            return TimeoutError,server_address
        
        except ConnectionRefusedError:
            self.connected = 0
            return ConnectionError,server_address
        


    def send(self,entry):
        """ sends data to server, packing according to robots protocol, additional function for pump needed """

        message = [] 
        if( not self.connected ): return ConnectionError, None

        try:
            message = struct.pack('<iccffffffffffffffffiiiiiciiiiiiiiiiiiiiiii'
                                  ,entry.ID
                                  ,bytes(entry.MT,"utf-8")
                                  ,bytes(entry.PT,"utf-8")
                                  ,entry.COOR_1.X
                                  ,entry.COOR_1.Y
                                  ,entry.COOR_1.Z
                                  ,entry.COOR_1.X_ori
                                  ,entry.COOR_1.Y_ori
                                  ,entry.COOR_1.Z_ori
                                  ,entry.COOR_1.Q
                                  ,entry.COOR_1.EXT
                                  ,entry.COOR_2.X
                                  ,entry.COOR_2.Y
                                  ,entry.COOR_2.Z
                                  ,entry.COOR_2.X_ori
                                  ,entry.COOR_2.Y_ori
                                  ,entry.COOR_2.Z_ori
                                  ,entry.COOR_2.Q
                                  ,entry.COOR_2.EXT
                                  ,entry.SV.ACR
                                  ,entry.SV.DCR
                                  ,entry.SV.TS
                                  ,entry.SV.OS
                                  ,entry.SBT
                                  ,bytes(entry.SC,"utf-8")
                                  ,entry.Z
                                  ,entry.TOOL.M1_ID
                                  ,entry.TOOL.M1_STEPS
                                  ,entry.TOOL.M2_ID
                                  ,entry.TOOL.M2_STEPS
                                  ,entry.TOOL.M3_ID
                                  ,entry.TOOL.M3_STEPS
                                  ,entry.TOOL.PNMTC_CLAMP_ID
                                  ,entry.TOOL.PNMTC_CLAMP_YN
                                  ,entry.TOOL.KNIFE_ID
                                  ,entry.TOOL.KNIFE_YN
                                  ,entry.TOOL.M4_ID
                                  ,entry.TOOL.M4_STEPS
                                  ,entry.TOOL.PNMTC_FIBER_ID
                                  ,entry.TOOL.PNMTC_FIBER_YN
                                  ,entry.TOOL.TIME_ID
                                  ,entry.TOOL.TIME_TIME)
            
            if(len(message) != self.W_BL):  return ValueError,len(message) 
            
            try:                self.sock.sendall(message)
            except OSError:     return OSError,None

            return True,len(message)
        
        except Exception as err:
            return err,None



    def receive(self):
        """ receives and unpacks data from robot, addtional function needed for pump """

        data = ""

        try:
            while ( len(data) < self.R_BL ):        data = self.sock.recv(self.R_BL)
        except TimeoutError:        return None, None, False
        except Exception as err:    return err, data, False

        if len(data) != self.R_BL:       return ValueError,data,False
        else:
            self.telemetry.TOOL_SPEED  = struct.unpack('<f',data[0:4])[0]
            self.telemetry.ID          = struct.unpack('<i',data[4:8])[0]
            self.telemetry.POS.X       = struct.unpack('<f',data[8:12])[0]
            self.telemetry.POS.Y       = struct.unpack('<f',data[12:16])[0]
            self.telemetry.POS.Z       = struct.unpack('<f',data[16:20])[0]
            self.telemetry.POS.X_ori   = struct.unpack('<f',data[20:24])[0]
            self.telemetry.POS.Y_ori   = struct.unpack('<f',data[24:28])[0]
            self.telemetry.POS.Z_ori   = struct.unpack('<f',data[28:32])[0]
            self.telemetry.POS.EXT     = struct.unpack('<f',data[32:36])[0]
            return self.telemetry,data,True
            


    def close(self, end= False):
        """ close TCP connection """
        
        self.sock.close()
        self.connected  = False
        if(not end): self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)




#############################################################################################
#                                    FUNCTIONS
#############################################################################################

# def txtEntryToFloat(txt = ''):
#     """ used to convert QLineEdit entries into float, returns error if pattern is not matched """
#     if(txt == ''):
#         return ValueError
#     res = ''
#     try:
#         res = re.findall('\d+[,.]\d+',txt)[0]
#     except IndexError:
#         try:
#             res = re.findall('\d+',txt)[0]
#         except IndexError:
#             return IndexError
#     res = res.replace(',','.')
#     return float(res)



def preCheckGcodeFile(txt=''):
    """ extracts the number of GCode commands and the filament length from text,
        ignores Z movement for now, slicing only in x-y-plane yet """
    
    try:
        if (txt == ''):    return 0, 0, 'empty'

        rows            = txt.split('\n')
        X               = 0.0
        Y               = 0.0
        commNum         = 0
        filamentLength  = 0.0

        for row in rows:
            if ( len( re.findall('G\d+', row) ) > 0 ):   commNum += 1

            Y_new = float( reShort('Y\d+[,.]\d+', row, 'Y' + str(Y), 'Y\d+')[0][1:] )
            X_new = float( reShort('X\d+[,.]\d+', row, 'X' + str(X), 'X\d+')[0][1:] )

            # do the Pythagoras for me, baby
            filamentLength += m.sqrt( m.pow( (X_new - X), 2 ) + m.pow( (Y_new - Y), 2 ) )

            X = X_new
            Y = Y_new

    except Exception as e:
        return None, None, e

    return commNum, filamentLength, ''



def preCheckRapidFile(txt=''):
    """ extracts the number of GCode commands and the filament length from text,
        does not handle Offs commands yet """
    
    try:
        if (txt == ''):    return 0, 0, 'empty'

        rows            = txt.split('\n')
        X               = 0.0
        Y               = 0.0
        commNum         = 0
        filamentLength  = 0.0

        for row in rows:
            if ( ('Move' in row)  
                  and ('pStart' not in row)
                  and ('pHome' not in row) ):   
                commNum += 1
                Y_new = float( re.findall('\d+\.\d+', row)[0] )
                X_new = float( re.findall('\d+\.\d+', row)[1] )

                # do the Pythagoras for me, baby
                filamentLength += m.sqrt( m.pow( (X_new - X), 2 ) + m.pow( (Y_new - Y), 2 ) )

                X = X_new
                Y = Y_new

    except Exception as e:
        return None, None, e

    return commNum, filamentLength, ''



def reShort(regEx,txt,default,fallbackRegEx = ''):
    """ tries 2 regular expressions on expressions like 'X1.23 Y4.56', 
        returns first match without the leading letter (e.g. '1.23' for '\d+[.,]\d+'),
        returns default value and 'False' if no match occurs """
    
    try:    ans = re.findall(regEx,txt)[0]

    except IndexError:
        if(fallbackRegEx == ''):    return default, False
        try:                        ans = re.findall(fallbackRegEx,txt)[0]
        except IndexError:          return default, False

    return ans, True



def gcodeToQEntry(mutPos, mutSpeed, zone, txt = ''):
    """ converts a single line of GCode G1 command to a QEntry, can be used in loops for multiline code,
        "pos" should be the pos before this command is executed (before its EXECUTED, not before its added  
        to SC_queue) as its the fallback option if no new X, Y, Z or EXT posistion is passed"""
    global DC_curr_zero

    # handle mutuables here
    pos   = copy.deepcopy(mutPos)
    speed = copy.deepcopy(mutSpeed)
    zero  = copy.deepcopy(DC_curr_zero)

    try:                command = reShort('^G\d+', txt, 0, '^;')[0]
    except IndexError:  return None, None

    # act according to GCode command
    match command:
        
        case 'G1':
            entry = QEntry(ID=0, COOR_1=pos, SV=speed, Z=zone)
                
            X,res                       = reShort('X\d+[,.]\d+', txt, pos.X, 'X\d+')
            if(res): entry.COOR_1.X     = float( X[1:] .replace(',','.') )

            Y,res                       = reShort('Y\d+[,.]\d+', txt, pos.Y, 'Y\d+')
            if(res): entry.COOR_1.Y     = float( Y[1:] .replace(',','.') )

            Z,res                       = reShort('Z\d+[,.]\d+', txt, pos.Z, 'Z\d+')
            if(res): entry.COOR_1.Z     = float( Z[1:] .replace(',','.') )
            
            F,res                       = reShort('F\d+[,.]\d+', txt, speed.TS, 'F\d+')
            if(res):
                F                       = float( F[1:] .replace(',','.') )
                entry.SV.TS             = int(F * IO_fr_to_ts)

            EXT,res                     = reShort('EXT\d+[,.]\d+', txt, pos.EXT, 'EXT\d+')
            if(res): entry.COOR_1.EXT   = float( EXT[3:] .replace(',','.') )

            entry.COOR_1 += zero
            
        case 'G28':
            entry = QEntry( ID = 0, COOR_1 = zero, SV = speed, Z  = zone)
            if ('X0' not in txt):   entry.COOR_1.X   += pos.X
            if ('Y0' not in txt):   entry.COOR_1.Y   += pos.Y
            if ('Z0' not in txt):   entry.COOR_1.Z   += pos.Z
            if ('EXT0' not in txt): entry.COOR_1.EXT += pos.EXT
        
        case 'G92':
            return None, KeyError('G92 commands are not supported')
            # if ('X0' in txt):   DC_curr_zero.X   = pos.X
            # if ('Y0' in txt):   DC_curr_zero.Y   = pos.Y
            # if ('Z0' in txt):   DC_curr_zero.Z   = pos.Z
            # if ('EXT0' in txt): DC_curr_zero.EXT = pos.EXT
            # return None, command
        
        case ';':
            return None, command
        
        case _:
            return None, None
        
    return entry,command



def rapidToQEntry(txt = ''):
    """ converts a single line of MoveL, MoveJ, MoveC or Move* Offs command (no Reltool) to a QEntry (relative to
        DC_curr_zero), can be used in loops for multiline code, returns entry and any Exceptions"""
    global DC_curr_zero
    
    entry = QEntry(ID=0, PT='Q')
    try:
        entry.MT            = re.findall('Move[J,L,C]', txt, 0)[0][4]
        
        if( 'Offs' in txt):
            res_coor            = [ DC_curr_zero.X
                                   ,DC_curr_zero.Y
                                   ,DC_curr_zero.Z
                                   ,DC_curr_zero.X_ori
                                   ,DC_curr_zero.Y_ori
                                   ,DC_curr_zero.Z_ori
                                   ,DC_curr_zero.Q
                                   ,DC_curr_zero.EXT]
            xyzOff              = re.findall('pHome,\d+\.\d+,\d+\.\d+,\d+\.\d+',txt)[0]
            xyzOff              = re.findall('\d+\.\d+', xyzOff)
            for i in range(3):  res_coor[i] += float(xyzOff[i])

        else:
            res_coor = []
            xyzOff              = re.findall('\d+\.\d+',txt)
            for i in range(7):  res_coor.append(float(xyzOff[i]))
        
        ext, res        = reShort('EXT:\d+\.\d+',txt,'error','EXT:\d+')
        ext             = float(ext[4:])
        res_speed       = re.findall('\d+,\d+,\d+,\d+(?=\],z)',txt)[0]
        res_speed       = re.findall('\d+',res_speed)

        entry.COOR_1.X      = res_coor[0]
        entry.COOR_1.Y      = res_coor[1]
        entry.COOR_1.Z      = res_coor[2]
        entry.COOR_1.X_ori  = res_coor[3]
        entry.COOR_1.Y_ori  = res_coor[4]
        entry.COOR_1.Z_ori  = res_coor[5]
        entry.COOR_1.Q      = res_coor[6]
        entry.COOR_1.EXT    = ext
        entry.SV.TS         = int(res_speed[0])
        entry.SV.OS         = int(res_speed[1])
        entry.SV.ACR        = int(res_speed[2])
        entry.SV.DCR        = int(res_speed[3])

        zone,res            = reShort('z\d+',txt,10)
        entry.Z             = int( zone[1:] )

        # for later, if tool is implemented
        tool    = reShort(',[^,]*$',txt,'tool0')[0]
        tool    = re.findall('^.* ',tool)[0]
        tool    = tool [: len(tool) - 1]

    except Exception as e:
        return None,e
    
    return entry,None



def createLogfile():
    """ defines and creates a logfile (and folder if necessary), which carries its creation datetime in the title """

    try:
        desk    = os.environ['USERPROFILE']
        logpath = desk / Path("Desktop/PRINT_py_log")
        logpath.mkdir( parents=True, exist_ok=True )

        logpath = logpath / Path(str(datetime.now().strftime('%Y-%m-%d_%H%M%S')) + ".txt")
        text    = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}    GNRL:        program booting, starting GUI...\n"

        logfile = open(logpath,'x')
        logfile.write(text)
        logfile.close()

    except Exception as e:
        print(f"Exception occured during log file creation: {e}")
        return None

    return(logpath)



def showOnTerminal(txt):
    """ puts entries in terminal list an keep its length below TERM_maxLen"""
    global TERM_log
    global TERM_maxLen

    TERM_log.append(txt)

    if ( len(TERM_log) > TERM_maxLen ):   TERM_log.__delitem__(0)
    




#############################################################################################
#                                    GLOBALS
#############################################################################################

############################ global constants
# defaut connection settings (the byte length for writing to the robot wont be user setable
# for safety reasons, it can only be changed here, but only if you know what your doing!)
DEF_TCP_ROB =      { "IP":       "192.168.125.1"
                    ,"PORT":     10001
                    ,"CTOUT":    60000
                    ,"RWTOUT":   10
                    ,"R_BL":     36
                    ,"W_BL":     159 }

DEF_TCP_PUMP1 =    { "IP":       ""
                    ,"PORT":     "COM3"
                    ,"CTOUT":    0
                    ,"RWTOUT":   0
                    ,"R_BL":     0
                    ,"W_BL":     0  }

DEF_TCP_PUMP2 =    { "IP":       ""
                    ,"PORT":     "COM4"
                    ,"CTOUT":    0
                    ,"RWTOUT":   0
                    ,"R_BL":     0
                    ,"W_BL":     0  }

# default user settings
DEF_DC_SPEED        = Speed()
DEF_IO_ZONE         = 10
DEF_IO_FR_TO_TS     = 0.1
DEF_PRIN_SPEED      = Speed()
DEF_ROB_COMM_FR     = 10
DEF_SC_VOL_PER_E    = 1.0



############################ global variables
DC_curr_zero        = Coor()
DC_speed            = copy.deepcopy(DEF_DC_SPEED)

IO_zone             = DEF_IO_ZONE
IO_curr_filepath    = None
IO_fr_to_ts         = DEF_IO_FR_TO_TS

PRIN_speed          = copy.deepcopy(DEF_PRIN_SPEED)

PUMP1_tcpip         = TCPIP( DEF_TCP_PUMP1["IP"]
                            ,DEF_TCP_PUMP1["PORT"]
                            ,DEF_TCP_PUMP1["CTOUT"]
                            ,DEF_TCP_PUMP1["RWTOUT"]
                            ,DEF_TCP_PUMP1["R_BL"]
                            ,DEF_TCP_PUMP1["W_BL"])
PUMP1_speed         = 0
PUMP1_liveAd        = 1

PUMP2_tcpip         = TCPIP( DEF_TCP_PUMP2["IP"]
                            ,DEF_TCP_PUMP2["PORT"]
                            ,DEF_TCP_PUMP2["CTOUT"]
                            ,DEF_TCP_PUMP2["RWTOUT"]
                            ,DEF_TCP_PUMP2["R_BL"]
                            ,DEF_TCP_PUMP2["W_BL"])

ROB_tcpip          = TCPIP( DEF_TCP_ROB["IP"]
                            ,DEF_TCP_ROB["PORT"]
                            ,DEF_TCP_ROB["CTOUT"]
                            ,DEF_TCP_ROB["RWTOUT"]
                            ,DEF_TCP_ROB["R_BL"]
                            ,DEF_TCP_ROB["W_BL"])
ROB_comm_fr         = DEF_ROB_COMM_FR
ROB_comm_queue      = Queue()
ROB_pos             = Coor()
ROB_toolSpeed       = 0
ROB_comm_id         = 0

SC_vol_per_e        = DEF_SC_VOL_PER_E
SC_curr_comm_id     = 1
SC_queue            = Queue()
SC_qProcessing      = False

STT_datablock       = DataBlock()

TERM_log            = []
TERM_maxLen         = 2000