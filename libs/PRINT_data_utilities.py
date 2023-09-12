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

class Coordinate:
    """standard 7-axis coordinate block (8 attributes, as quaterion positioning is possible)

    ATTRIBUTES:
        x, y, z:
            position in cartesian coordinates
        rx, ry, rz:
            angle relative to cartesian coordinates
        q:
            additional var for fourth quaternion coordinate
        ext:
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
                 x  	= 0.0, 
                 y  	= 0.0, 
                 z  	= 0.0, 
                 rx     = 0.0, 
                 ry     = 0.0, 
                 rz     = 0.0, 
                 q      = 0.0, 
                 ext    = 0.0):
        
        self.x      = float(x)
        self.y      = float(y)
        self.z      = float(z)
        self.rx     = float(rx)
        self.ry     = float(ry)
        self.rz     = float(rz)
        self.q      = float(q)
        self.ext    = float(ext)
    


    def __str__(self):

        return f"X: {self.x}   Y: {self.y}   Z: {self.z}   Rx: {self.rx}   Ry: {self.ry}   Rz: {self.rz}   " \
               f"Q: {self.q}   EXT: {self.ext}"
    


    def __add__(self,summand):

        try:
            return round( Coordinate( (self.x        + summand.x)
                                      ,(self.y        + summand.y)
                                      ,(self.z        + summand.z)
                                      ,(self.rx       + summand.rx)
                                      ,(self.ry       + summand.ry)
                                      ,(self.rz       + summand.rz)
                                      ,(self.q        + summand.q)
                                      ,(self.ext      + summand.ext) )
                         , 6)
        except AttributeError:
            return round( Coordinate( (self.x        + summand)
                                      ,(self.y        + summand)
                                      ,(self.z        + summand)
                                      ,(self.rx       + summand)
                                      ,(self.ry       + summand)
                                      ,(self.rz       + summand)
                                      ,(self.q        + summand)
                                      ,(self.ext      + summand) )
                         , 6)
    


    def __sub__(self,subtrahend):

        try:
            return round( Coordinate( (self.x        - subtrahend.x)
                                      ,(self.y        - subtrahend.y)
                                      ,(self.z        - subtrahend.z)
                                      ,(self.rx       - subtrahend.rx)
                                      ,(self.ry       - subtrahend.ry)
                                      ,(self.rz       - subtrahend.rz)
                                      ,(self.q        - subtrahend.q)
                                      ,(self.ext      - subtrahend.ext) )
                        , 6)
        except AttributeError:
            return round( Coordinate( (self.x        - subtrahend)
                                      ,(self.y        - subtrahend)
                                      ,(self.z        - subtrahend)
                                      ,(self.rx       - subtrahend)
                                      ,(self.ry       - subtrahend)
                                      ,(self.rz       - subtrahend)
                                      ,(self.q        - subtrahend)
                                      ,(self.ext      - subtrahend) )
                        , 6)
    


    def __round__(self, digits):
        
        return Coordinate( round(self.x,   digits) 
                           ,round(self.y,   digits)
                           ,round(self.z,   digits)
                           ,round(self.rx,  digits)
                           ,round(self.ry,  digits)
                           ,round(self.rz,  digits)
                           ,round(self.q,   digits)
                           ,round(self.ext, digits) )
    


    def __eq__(self,other):

        try:
            if(     self.x     == other.x
                and self.y     == other.y
                and self.z     == other.z
                and self.rx    == other.rx
                and self.ry    == other.ry
                and self.rz    == other.rz
                and self.q     == other.q
                and self.ext   == other.ext):
                return True
            else: return False

        except AttributeError:
            return False





class SpeedVector:
    """standard speed vector (4 attributes).

    ATTRIBUTES:
        acr:
            acceleration ramp
        dcr:
            deceleration ramp
        ts:
            transition speed
        os:
            orientation speed
    
    FUNCTIONS:
        __init__\n
        __str__ \n
        __mul__ \n
        __rmul__\n
        __eq__
    """

    def __init__(self, 
                 acr    = 50, 
                 dcr    = 50, 
                 ts     = 200, 
                 os     = 50):
        
        self.acr    = int( round( acr, 0) )
        self.dcr    = int( round( dcr, 0) )
        self.ts     = int( round( ts,  0) )
        self.os     = int( round( os,  0) )



    def __str__(self):

        return f"TS: {self.ts}   OS: {self.os}   ACR: {self.acr}   DCR: {self.dcr}"
    


    def __mul__(self,other):

        return SpeedVector( ts  = int( round( self.ts *  other, 0) ) 
                           ,os  = int( round( self.os *  other, 0) ) 
                           ,acr = int( round( self.acr * other, 0) ) 
                           ,dcr = int( round( self.dcr * other, 0) ) )
    


    def __rmul__(self,other):

        return self.__mul__(other)
    


    def __eq__(self,other):

        try:
            if(     self.acr == other.acr
                and self.dcr == other.dcr
                and self.ts  == other.ts
                and self.os  == other.os):
                return True
            else: return False

        except AttributeError:
            return False




class ToolCommand:
    """standard tool command according to Jonas' protocol

    ATTRIBUTES:
        m1_id:
            motor 1 ID (fiber pivoting)
        m1_steps:
            motor 1 steps/position
        m2_id:
            motor 2 ID (fiber delivery)
        m2_steps:
            motor 2 steps/position
        m3_id:
            motor 3 ID (mortar pump)
        M3_steps:
            motor 3 steps/position
        pnmtcClamp_id:
            pneumatic fiber clamp ID
        pnmtcClamp_yn:
            pneumatic fiber clamp on/off
        knife_id:
            knife delivery ID
        knife_steps:
            knife delivery on/off
        m4_id:
            motor 4 ID (rotation knife)
        m4_steps:
            motor 4 steps/position
        pnmtcFiber_id:
            pneumatic fiber conveyer ID
        pnmtcFiber_yn:
            pneumatic fiber conveyer on/off
        time_id:
            time ID
        time_time:
            current time in milli seconds at EE
        
    FUNCTIONS:
        __def__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 m1_id          = 0,
                 m1_steps       = 0,
                 m2_id          = 0,
                 m2_steps       = 0,
                 m3_id          = 0,
                 m3_steps       = 0,
                 pnmtcClamp_id  = 0,
                 pnmtcClamp_yn  = 0,
                 knife_id       = 0,
                 knife_yn       = 0,
                 m4_id          = 0,
                 m4_steps       = 0,
                 pnmtcFiber_id  = 0,
                 pnmtcFiber_yn  = 0,
                 time_id        = 0,
                 time_time      = 0):
        
        self.m1_id          = int (m1_id)
        self.m1_steps       = int (m1_steps)
        self.m2_id          = int (m2_id)
        self.m2_steps       = int (m2_steps)
        self.m3_id          = int (m3_id)
        self.m3_steps       = int (m3_steps)
        self.pnmtcClamp_id  = int (pnmtcClamp_id)
        self.pnmtcClamp_yn  = bool(pnmtcClamp_yn)
        self.knife_id       = int (knife_id)
        self.knife_yn       = bool(knife_yn)
        self.m4_id          = int (m4_id)
        self.m4_steps       = bool(m4_steps)
        self.pnmtcFiber_id  = int (pnmtcFiber_id)
        self.pnmtcFiber_yn  = bool(pnmtcFiber_yn)
        self.time_id        = int (time_id)
        self.time_time      = int (time_time)



    def __str__(self):

        return  f"M1: {self.m1_id}, {self.m1_steps}   M2: {self.m2_id}, {self.m2_steps}   M3: {self.m3_id}, {self.m3_steps}   "\
                f"P_C: {self.pnmtcClamp_id}, {self.pnmtcClamp_yn}   KN: {self.knife_id}, {self.knife_yn}   "\
                f"M4: {self.m4_id}, {self.m4_steps}   P_F: {self.pnmtcFiber_id}, {self.pnmtcFiber_yn}   "\
                f"TIME: {self.time_id}, {self.time_time}"
    


    def __eq__(self,other):

        try:
            if(     self.m1_id          == other.m1_id
                and self.m1_steps       == other.m1_steps
                and self.m2_id          == other.m2_id
                and self.m2_steps       == other.m2_steps
                and self.m3_id          == other.m3_id
                and self.m3_steps       == other.m3_steps
                and self.pnmtcClamp_id  == other.pnmtcClamp_id
                and self.pnmtcClamp_yn  == other.pnmtcClamp_yn
                and self.knife_id       == other.knife_id
                and self.knife_yn       == other.knife_yn
                and self.m4_id          == other.m4_id
                and self.m4_steps       == other.m4_steps
                and self.pnmtcFiber_id  == other.pnmtcFiber_id
                and self.pnmtcFiber_yn  == other.pnmtcFiber_yn
                and self.time_id        == other.time_id
                and self.time_time      == other.time_time):
                return True
            else: return False

        except AttributeError:
            return False





class QEntry:
    """standard 159 byte command queue entry for TCP robot according to the protocol running on the robot
    
    ATTRIBUTES:
        id: 
            command ID, list number in robot internal queue
        mt:
            type of movement or special command (L = linear, J = joint, C = circular, S = stop after current movement
            & delete robot internal queue, E = end TCP protocol on robot)
        pt:
            position type, type of rotation given (E = Euler angles, Q = quaternion, A = axis positioning)
        Coor1:
            coordinates of the first given point
        Coor2:
            coordinates of the second given point
        Speed:
            speed vector for given movement
        sbt:
            time to calculate speed by
        sc:
            speed command, set movement speed by movement time (SBT) or speed vector (SV), (T = time, V = vector)
        z:
            zone, endpoint precision
        Tool:
            tool command in Jonas' standard format
        
    FUNCTIONS:
        __init__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 id     = 0,
                 mt     = "L",
                 pt     = "E",
                 Coor1  = None,
                 Coor2  = None,
                 Speed  = None,
                 sbt    = 0,
                 sc     = "V",
                 z      = 10,
                 Tool   = None,
                 pMode  = None):
        
        self.id     = int(id)
        self.mt     = str(mt)
        self.pt     = str(pt)
        self.sbt    = int(sbt)
        self.sc     = str(sc)
        self.z      = int(z)
        self.pMode  = str(pMode)

        # handle those beasty mutables
        self.Coor1  = Coordinate() if (Coor1 == None) else Coor1
        self.Coor2  = Coordinate() if (Coor2 == None) else Coor2
        self.Speed  = SpeedVector() if (Speed == None) else Speed
        self.Tool   = ToolCommand() if (Tool == None)  else Tool
    


    def __str__(self):
        
        return  f"ID: {self.id}  MT: {self.mt}  PT: {self.pt} \t|| COOR_1: {self.Coor1}"\
                f"\n\t\t|| COOR_2: {self.Coor2}"\
                f"\n\t\t|| SV:     {self.Speed} \t|| SBT: {self.sbt}   SC: {self.sc}   Z: {self.z}"\
                f"\n\t\t|| TOOL:   {self.Tool}"\
                f"\n\t\t|| PMODE:  {self.pMode}"
    


    def __eq__(self,other):

        try:
            if(     self.id     == other.id
                and self.mt     == other.mt
                and self.pt     == other.pt
                and self.Coor1  == other.Coor1
                and self.Coor2  == other.Coor2
                and self.Speed  == other.Speed
                and self.sbt    == other.sbt
                and self.sc     == other.sc
                and self.z      == other.z
                and self.Tool   == other.Tool
                and self.pMode  == other.pMode):
                return True
            else: return False

        except AttributeError:
            return False





class Queue:
    """QEntry-based list incl. data handling
    
        ATTRIBUTES:
            queue:
                a list of QEntry elements, careful: list index does not match QEntry.id

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

        if (length <= 0):  raise AttributeError

        for entry in range(length):
            if (self.queue[entry].id == ID): break
            else:                            i += 1
        
        if ( (i < 1) or (i >= length) ): 
            raise AttributeError
        
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
            i.id += 1



    def add(self, entry):
        """ adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given """

        newEntry = copy.deepcopy(entry)
        lastItem = len(self.queue) - 1 
        if(lastItem < 0):
            global SC_currCommId

            newEntry.id = SC_currCommId
            self.queue.append(newEntry)
            return None
        
        lastID  = self.queue[lastItem].id
        firstID = self.queue[0].id
        
        if( (newEntry.id == 0) or (newEntry.id > lastID) ):
            newEntry.id = lastID + 1
            self.queue.append(newEntry)

        elif( newEntry.id < 0 ):
            return ValueError

        else:
            if( newEntry.id < firstID ):  newEntry.id = firstID
            
            frontSkip = newEntry.id - self.queue[0].id
            self.queue.insert(frontSkip,newEntry)
            for i in range(lastItem + 1 - frontSkip):
                i += 1
                self.queue[i + frontSkip].id += 1

        return None
    


    def clear(self, all = True, ID = ''):
        """ deletes single or multiple QEntry from queue, adjusts following ID accordingly """

        if(all):
            self.queue = []
            return self.queue

        ids     = re.findall('\d+',ID)
        idNum   = len(ids)
        firstID = self.queue[0].id
        lastID  = self.queue[len(self.queue) - 1].id
        
        match idNum:

            case 1:
                id1 = int(ids[0])

                if( (id1 < firstID) or (id1 > lastID) ):  return ValueError

                i = 0
                for entry in self.queue:
                    if(entry.id == id1):    break
                    else:                   i += 1
                
                self.queue.__delitem__(i)
                while (i < len(self.queue)):
                    self.queue[i].id -= 1
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
                i      = 0
                for entry in self.queue:
                    if(entry.id == id1):    break
                    else:                   i += 1
                
                for n in range(idDist):
                    self.queue.__delitem__(i)
                
                while ( i < len(self.queue) ):
                    self.queue[i].id -= idDist
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

    ATTRIBUTES:
        tSpeed:
            speed with that the tool center point (TCP) is moving
        id:
            command ID the robot is currently processing
        Coor:
            current coordinate of the TCP, see Coordinates class
    
    FUNCTIONS:
        __init__\n
        __str__\n
        __round__\n
        __eq__
    """

    def __init__(self,
                 tSpeed = 0.0,
                 id     = -1,
                 Coor   = None):
        
        self.tSpeed = float(tSpeed)
        self.id     = int(id)

        # handle those beasty mutables
        self.Coor = Coordinate()   if (Coor == None) else Coor




    def __str__(self):

        return  f"ID: {self.id}   X: {self.Coor.x}   Y: {self.Coor.y}   Z: {self.Coor.z}   Rx: {self.Coor.rx}   Ry: {self.Coor.ry}   Rz: {self.Coor.rz}   "\
                f"EXT:   {self.Coor.ext}   TOOL_SPEED: {self.tSpeed}"
    


    def __round__(self, digits):

        return RoboTelemetry( round(self.tSpeed, digits) 
                             ,self.id
                             ,round(self.Coor,   digits))
    


    def __eq__(self, other):

        try:
            if(     self.tSpeed == other.tSpeed
                and self.id     == other.id
                and self.Coor   == other.Coor):
                return True
            else: return False

        except AttributeError:
            return False






class PumpTelemetry:
    """ class used to store the standard telemetry data the pump 

    ATTRIBUTES:
        freq:
            motor frequency (currently only given as 0 - 100%)
        volt:
            voltage at motor coil (I thought in V, but the values seem to high)
        amps:
            current in motor coil (unit unknown, as for volt)
        torq:
            torque, probably in Nm
    
    FUNCTIONS:
        __init__\n
        __str__\n
        __round__\n
        __eq__
    """

    def __init__(self,
                 freq = 0.0,
                 volt = 0.0,
                 amps = 0.0,
                 torq = 0.0):
        
        self.freq = float(freq)
        self.volt = float(volt)
        self.amps = float(amps)
        self.torq = float(torq)



    def __str__(self):

        return  f"FREQ: {self.freq}   VOLT: {self.volt}   AMPS: {self.amps}   TORQ: {self.torq}"
    


    def __round__(self, digits):

        return PumpTelemetry( round(self.freq, digits)
                             ,round(self.volt, digits)
                             ,round(self.amps, digits)
                             ,round(self.torq, digits) )
    


    def __eq__(self, other):

        try:
            if(     self.freq == other.freq
                and self.volt == other.volt
                and self.amps == other.amps
                and self.torq == other.torq):
                return True
            else: return False

        except AttributeError:
            return False
    




class DaqBlock:
    """ structure for DAQ
    ATTRIBUTES:
        amb_temp:
            ambient temperatur [°C]
        amb_hum:
            ambient humidity [%]
        delivPump_temp:
            temperature behind pump1's moineur pump [°C]
        robBase_temp:
            temperature of the mortar tube at the second coupling [°C]
        kPump_temp:
            temperature behind the 2K pump [°C]
        delivPump_press:
            pressure behind pump1's moineur pump [bar]
        kPump_press:
            pressure in front of 2K pump [bar]
        Pump1:
            PumpTelemetry datablock for pump1
        Pump2:
            PumpTelemetry datablock for pump2
        admPump_freq:
            frequency of the admixture delivery pump
        admPump_amps:
            current of the admixture delivery pump
        kPump_freq:
            frequency of the 2K pump
        kPump_amps:
            current of the 2K pump
        Robo:
            RoboTelemetry datablock
        porosAnalysis:
            porosity analysis (not specified yet)
        distanceFront:
            deposition layer height in front of the nozzle
        distanceEnd:
            deposition layer height behind the nozzle

    FUNCTIONS:
        __init__\n
        __str__\n
        __eq__
    """

    def __init__(self,
                 amb_temp =         0.0,
                 amb_hum =          0.0,
                 delivPump_temp =   0.0,
                 robBase_temp =     0.0,
                 kPump_temp =       0.0,
                 delivPump_press =  0.0,
                 kPump_press =      0.0,
                 Pump1 =            None,
                 Pump2 =            None,
                 admPump_freq =     0.0,
                 admPump_amps =     0.0,
                 kPump_freq =       0.0,
                 kPump_amps =       0.0,
                 Robo =             None,
                 porosAnalysis =    0.0,
                 distanceFront =    0.0,
                 distanceEnd =      0.0):
        
        self.amb_temp =         float(amb_temp)
        self.amb_hum =          float(amb_hum)
        self.delivPump_temp =   float(delivPump_temp)
        self.robBase_temp =     float(robBase_temp)
        self.kPump_temp =       float(kPump_temp)
        self.delivPump_press =  float(delivPump_press)
        self.kPump_press =      float(kPump_press)
        self.admPump_freq =     float(admPump_freq)
        self.admPump_amps =     float(admPump_amps)
        self.kPump_freq =       float(kPump_freq)
        self.kPump_amps =       float(kPump_amps)
        self.porosAnalysis =    float(porosAnalysis)
        self.distanceFront =    float(distanceFront)
        self.distanceEnd =      float(distanceEnd)

        # handle those beasty mutables
        self.Pump1  = PumpTelemetry()   if (Pump1 == None) else Pump1
        self.Pump2  = PumpTelemetry()   if (Pump2 == None) else Pump2
        self.Robo   = RoboTelemetry()   if (Robo  == None) else Robo



    def __str__(self):

        return f"ambTemp: {self.amb_temp}    ambHum: {self.amb_hum}    delivPumpTemp: {self.delivPump_temp}    robBaseTemp: {self.robBase_temp}    "\
               f"kPumpTemp: {self.kPump_temp}    delivPumpPress: {self.delivPump_press}    kPumpPress: {self.kPump_press}    PUMP1: {self.Pump1}    "\
               f"PUMP2: {self.Pump2}    admPumpFreq: {self.admPump_freq}    admPumpAmps: {self.admPump_amps}    kPumpFreq: {self.kPump_freq}    "\
               f"kPumpAmps: {self.kPump_amps}    ROB: {self.Robo}    porosAnalysis: {self.porosAnalysis}    "\
               f"distanceFront: {self.distanceFront}    distanceEnd: {self.distanceEnd}"    
    


    def __eq__(self, other):

        try:
            if(     self.amb_temp        == other.amb_temp
                and self.amb_hum         == other.amb_hum
                and self.delivPump_temp  == other.delivPump_temp
                and self.robBase_temp    == other.robBase_temp
                and self.kPump_temp      == other.kPump_temp
                and self.delivPump_press == other.delivPump_press
                and self.kPump_press     == other.kPump_press
                and self.Pump1           == other.pump1
                and self.Pump2           == other.pump2
                and self.admPump_freq    == other.admPump_freq
                and self.admPump_amps    == other.admPump_amps
                and self.kPump_freq      == other.kPump_freq
                and self.kPump_amps      == other.kPump_amps
                and self.Robo            == other.robo
                and self.porosAnalysis   == other.porosAnalysis
                and self.distanceFront   == other.distanceFront
                and self.distanceEnd     == other.distanceEnd):
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
                 ip         = "",
                 PORT       = 0,
                 C_TOUT     = 1.0,
                 RW_TOUT    = 1,
                 R_BL       = 0,
                 W_BL       = 0):
        
        self.ip         = str(ip)
        self.port       = str(PORT)
        self.c_tout     = float(C_TOUT)
        self.rw_tout    = float(RW_TOUT)
        self.r_bl       = int(R_BL)
        self.w_bl       = int(W_BL)

        self.connected  = False
        self.Socket     = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.Telemetry  = RoboTelemetry()
    

    def __str__(self):

        return  f"IP: {self.ip}   PORT: {self.port}   C_TOUT: {self.c_tout}   RW_TOUT: {self.rw_tout}   "\
                f"R_BL: {self.r_bl}   W_BL: {self.w_bl}"
    


    def setParams(self, paramDict):
        if(self.connected): 
            raise PermissionError('params not changeable while connected to server!')
        
        self.ip         = str  ( paramDict["IP"] )
        self.port       = str  ( paramDict["PORT"] )
        self.c_tout     = float( paramDict["C_TOUT"] )
        self.rw_tout    = float( paramDict["RW_TOUT"] )
        self.r_bl       = int  ( paramDict["R_BL"] )
        self.w_bl       = int  ( paramDict["W_BL"] )



    def connect(self):
        """ tries to connect to the IP and PORT given, returns errors if not possible """

        try:                server_address = (self.ip, int(self.port))
        except ValueError:  raise ConnectionError('requested TCP/IP connection via COM-Port!')
        
        self.Socket.settimeout(self.c_tout)

        try:
            self.Socket.connect(server_address)
            self.connected = True
            self.Socket.settimeout(self.rw_tout)
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
                                  ,entry.id
                                  ,bytes(entry.mt,"utf-8")
                                  ,bytes(entry.pt,"utf-8")
                                  ,entry.Coor1.x
                                  ,entry.Coor1.y
                                  ,entry.Coor1.z
                                  ,entry.Coor1.rx
                                  ,entry.Coor1.ry
                                  ,entry.Coor1.rz
                                  ,entry.Coor1.q
                                  ,entry.Coor1.ext
                                  ,entry.Coor2.x
                                  ,entry.Coor2.y
                                  ,entry.Coor2.z
                                  ,entry.Coor2.rx
                                  ,entry.Coor2.ry
                                  ,entry.Coor2.rz
                                  ,entry.Coor2.q
                                  ,entry.Coor2.ext
                                  ,entry.Speed.acr
                                  ,entry.Speed.dcr
                                  ,entry.Speed.ts
                                  ,entry.Speed.os
                                  ,entry.sbt
                                  ,bytes(entry.sc,"utf-8")
                                  ,entry.z
                                  ,entry.Tool.m1_id
                                  ,entry.Tool.m1_steps
                                  ,entry.Tool.m2_id
                                  ,entry.Tool.m2_steps
                                  ,entry.Tool.m3_id
                                  ,entry.Tool.m3_steps
                                  ,entry.Tool.pnmtcClamp_id
                                  ,entry.Tool.pnmtcClamp_yn
                                  ,entry.Tool.knife_id
                                  ,entry.Tool.knife_yn
                                  ,entry.Tool.m4_id
                                  ,entry.Tool.m4_steps
                                  ,entry.Tool.pnmtcFiber_id
                                  ,entry.Tool.pnmtcFiber_yn
                                  ,entry.Tool.time_id
                                  ,entry.Tool.time_time)
            
            if(len(message) != self.w_bl):  return ValueError,len(message) 
            
            try:                self.Socket.sendall(message)
            except OSError:     return OSError,None
            
            print(f"SEND:    {entry.id}, length: {len(message)}")
            return True,len(message)
        
        except Exception as err:
            return err,None



    def receive(self):
        """ receives and unpacks data from robot, addtional function needed for pump """

        data = ""

        try:
            while ( len(data) < self.r_bl ):        data = self.Socket.recv(self.r_bl)
        except TimeoutError:        return None, None, False
        except Exception as err:    return err, data, False

        if len(data) != self.r_bl:       return ValueError,data,False
        else:
            self.Telemetry.tSpeed   = struct.unpack('<f',data[0:4])[0]
            self.Telemetry.id       = struct.unpack('<i',data[4:8])[0]
            self.Telemetry.Coor.x   = struct.unpack('<f',data[8:12])[0]
            self.Telemetry.Coor.y   = struct.unpack('<f',data[12:16])[0]
            self.Telemetry.Coor.z   = struct.unpack('<f',data[16:20])[0]
            self.Telemetry.Coor.rx  = struct.unpack('<f',data[20:24])[0]
            self.Telemetry.Coor.ry  = struct.unpack('<f',data[24:28])[0]
            self.Telemetry.Coor.rz  = struct.unpack('<f',data[28:32])[0]
            self.Telemetry.Coor.ext = struct.unpack('<f',data[32:36])[0]
            return self.Telemetry,data,True
            


    def close(self, end= False):
        """ close TCP connection """
        
        self.Socket.close()
        self.connected  = False
        if(not end): self.Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)




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
        if (txt == ''):   return 0, 0, 'empty'

        rows            = txt.split('\n')
        x               = 0.0
        y               = 0.0
        z               = 0.0
        commNum         = 0
        filamentLength  = 0.0

        for row in rows:
            if ( len( re.findall('G\d+', row) ) > 0 ):   commNum += 1

            xNew = float( reShort('X\d+[,.]\d+', row, 'X' + str(x), 'X\d+')[0][1:] )
            yNew = float( reShort('Y\d+[,.]\d+', row, 'Y' + str(y), 'Y\d+')[0][1:] )
            zNew = float( reShort('Z\d+[,.]\d+', row, 'Z' + str(z), 'Z\d+')[0][1:] )

            # do the Pythagoras for me, baby
            filamentLength += m.sqrt( m.pow( (xNew - x), 2 ) 
                                     +m.pow( (yNew - y), 2 ) 
                                     +m.pow( (zNew - z), 2 ) )

            x = xNew
            y = yNew
            z = zNew

    except Exception as e:
        return None, None, e

    return commNum, filamentLength, ''



def preCheckRapidFile(txt=''):
    """ extracts the number of GCode commands and the filament length from text,
        does not handle Offs commands yet """
    
    try:
        if (txt == ''):   return 0, 0, 'empty'

        rows            = txt.split('\n')
        x               = 0.0
        y               = 0.0
        z               = 0.0
        commNum         = 0
        filamentLength  = 0.0

        for row in rows:
            # the ' p' expression is to differ between 'MoveJ pHome,[...]'
            # and 'MoveJ Offs(pHome [...]'
            if ( ('Move' in row) and (' p' not in row) ):   
                commNum += 1
                xNew = float( re.findall('\d+\.\d+', row)[0] )
                yNew = float( re.findall('\d+\.\d+', row)[1] )
                zNew = float( re.findall('\d+\.\d+', row)[2] )

                # do the Pythagoras for me, baby
                filamentLength += m.sqrt( m.pow( (xNew - x), 2 ) 
                                         +m.pow( (yNew - y), 2 ) 
                                         +m.pow( (zNew - z), 2 ) )

                x = xNew
                y = yNew
                z = zNew

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
    global DC_currZero

    # handle mutuables here
    pos   = copy.deepcopy(mutPos)
    speed = copy.deepcopy(mutSpeed)
    zero  = copy.deepcopy(DC_currZero)

    try:                command = reShort('^G\d+', txt, 0, '^;')[0]
    except IndexError:  return None, None

    # act according to GCode command
    match command:
        
        case 'G1':
            entry = QEntry(id=0, Coor1=pos, Speed=speed, z=zone)
                
            x,res = reShort('X\d+[,.]\d+', txt, pos.x, 'X\d+')
            if(res): 
                entry.Coor1.x =  float( x[1:] .replace(',','.') )
                entry.Coor1.x += zero.x

            y,res = reShort('Y\d+[,.]\d+', txt, pos.y, 'Y\d+')
            if(res): 
                entry.Coor1.y =  float( y[1:] .replace(',','.') )
                entry.Coor1.y += zero.y

            z,res = reShort('Z\d+[,.]\d+', txt, pos.z, 'Z\d+')
            if(res): 
                entry.Coor1.z =  float( z[1:] .replace(',','.') )
                entry.Coor1.z += zero.z
            
            fr,res  = reShort('F\d+[,.]\d+', txt, speed.ts, 'F\d+')
            if(res):
                fr              = float( fr[1:] .replace(',','.') )
                entry.Speed.ts  = int(fr * IO_frToTs)

            ext,res = reShort('EXT\d+[,.]\d+', txt, pos.ext, 'EXT\d+')
            if(res): 
                entry.Coor1.ext =  float( ext[3:] .replace(',','.') )
                entry.Coor1.ext += zero.ext
            
        case 'G28':
            entry = QEntry( id = 0, Coor1 = pos, Speed = speed, z  = zone)
            if ('X0'   in txt):   entry.Coor1.x   = zero.x
            if ('Y0'   in txt):   entry.Coor1.y   = zero.y
            if ('Z0'   in txt):   entry.Coor1.z   = zero.z
            if ('EXT0' in txt):   entry.Coor1.ext = zero.ext
        
        case 'G92':
            if ('X0'   in txt):   DC_currZero.x   = pos.x
            if ('Y0'   in txt):   DC_currZero.y   = pos.y
            if ('Z0'   in txt):   DC_currZero.z   = pos.z
            if ('EXT0' in txt):   DC_currZero.ext = pos.ext
            return None, command
        
        case ';':
            return None, command
        
        case _:
            return None, None
        
    return entry,command



def rapidToQEntry(txt = ''):
    """ converts a single line of MoveL, MoveJ, MoveC or Move* Offs command (no Reltool) to a QEntry (relative to
        DC_curr_zero), can be used in loops for multiline code, returns entry and any Exceptions"""
    global DC_currZero
    
    entry = QEntry(id=0)
    try:
        entry.mt    = re.findall('Move[J,L,C]', txt, 0)[0][4]
        ext, res    = reShort('EXT:\d+\.\d+',txt,'error','EXT:\d+')
        ext         = float(ext[4:])
        
        if( 'Offs' in txt):
            res_coor            = [ DC_currZero.x
                                   ,DC_currZero.y
                                   ,DC_currZero.z
                                   ,DC_currZero.rx
                                   ,DC_currZero.ry
                                   ,DC_currZero.rz
                                   ,DC_currZero.q]
            xyzOff              = re.findall('pHome,\d+\.\d+,\d+\.\d+,\d+\.\d+',txt)[0]
            xyzOff              = re.findall('\d+\.\d+', xyzOff)
            for i in range(3):  res_coor[i] += float(xyzOff[i])
            ext                 += DC_currZero.ext

        else:
            entry.pt = 'Q'
            res_coor = []
            xyzOff              = re.findall('\d+\.\d+',txt)
            for i in range(7):  res_coor.append(float(xyzOff[i]))
        res_speed       = re.findall('\d+,\d+,\d+,\d+(?=\],z)',txt)[0]
        res_speed       = re.findall('\d+',res_speed)

        entry.Coor1.x   = res_coor[0]
        entry.Coor1.y   = res_coor[1]
        entry.Coor1.z   = res_coor[2]
        entry.Coor1.rx  = res_coor[3]
        entry.Coor1.ry  = res_coor[4]
        entry.Coor1.rz  = res_coor[5]
        entry.Coor1.q   = res_coor[6]
        entry.Coor1.ext = ext
        entry.Speed.ts  = int(res_speed[0])
        entry.Speed.os  = int(res_speed[1])
        entry.Speed.acr = int(res_speed[2])
        entry.Speed.dcr = int(res_speed[3])

        zone,res        = reShort('z\d+',txt,10)
        entry.z         = int( zone[1:] )

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
        text    = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}    [GNRL]:        program booting, starting GUI...\n"

        logfile = open(logpath,'x')
        logfile.write(text)
        logfile.close()

    except Exception as e:
        print(f"Exception occured during log file creation: {e}")
        return None

    return(logpath)



def addToCommProtocol(txt):
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
                    ,"C_TOUT":   60000
                    ,"RW_TOUT":  10
                    ,"R_BL":     36
                    ,"W_BL":     159 }

DEF_TCP_PUMP1 =    { "IP":       ""
                    ,"PORT":     "COM3"
                    ,"C_TOUT":   0
                    ,"RW_TOUT":  0
                    ,"R_BL":     0
                    ,"W_BL":     0  }

DEF_TCP_PUMP2 =    { "IP":       ""
                    ,"PORT":     "COM4"
                    ,"C_TOUT":   0
                    ,"RW_TOUT":  0
                    ,"R_BL":     0
                    ,"W_BL":     0  }

# default user settings
DEF_DC_SPEED        = SpeedVector()
DEF_IO_ZONE         = 10
DEF_IO_FR_TO_TS     = 0.1
DEF_PRIN_SPEED      = SpeedVector()
DEF_ROB_COMM_FR     = 10
DEF_SC_VOL_PER_MM   = 0.01



############################ global variables
DC_currZero         = Coordinate()
DC_speed            = copy.deepcopy(DEF_DC_SPEED)
DC_robMoving        = True

IO_zone             = DEF_IO_ZONE
IO_currFilepath     = None
IO_frToTs           = DEF_IO_FR_TO_TS

PRIN_speed          = copy.deepcopy(DEF_PRIN_SPEED)

PUMP1_tcpip         = TCPIP( DEF_TCP_PUMP1["IP"]
                            ,DEF_TCP_PUMP1["PORT"]
                            ,DEF_TCP_PUMP1["C_TOUT"]
                            ,DEF_TCP_PUMP1["RW_TOUT"]
                            ,DEF_TCP_PUMP1["R_BL"]
                            ,DEF_TCP_PUMP1["W_BL"])
PUMP1_lastTelem     = PumpTelemetry()
PUMP1_literPerS     = 0.5
PUMP1_liveAd        = 1.0
PUMP1_speed         = 0

PUMP2_tcpip         = TCPIP( DEF_TCP_PUMP2["IP"]
                            ,DEF_TCP_PUMP2["PORT"]
                            ,DEF_TCP_PUMP2["C_TOUT"]
                            ,DEF_TCP_PUMP2["RW_TOUT"]
                            ,DEF_TCP_PUMP2["R_BL"]
                            ,DEF_TCP_PUMP2["W_BL"])

ROB_tcpip          = TCPIP( DEF_TCP_ROB["IP"]
                           ,DEF_TCP_ROB["PORT"]
                           ,DEF_TCP_ROB["C_TOUT"]
                           ,DEF_TCP_ROB["RW_TOUT"]
                           ,DEF_TCP_ROB["R_BL"]
                           ,DEF_TCP_ROB["W_BL"])
ROB_commFr          = DEF_ROB_COMM_FR
ROB_commQueue       = Queue()
ROB_telem           = RoboTelemetry()
ROB_lastTelem       = RoboTelemetry()
ROB_movStartP       = Coordinate()
ROB_movEndP         = Coordinate()

SC_volPerMm         = DEF_SC_VOL_PER_MM
SC_currCommId       = 1
SC_queue            = Queue()
SC_qProcessing      = False
SC_qPrepEnd         = False

STT_dataBlock       = DaqBlock()

TERM_log            = []
TERM_maxLen         = 400