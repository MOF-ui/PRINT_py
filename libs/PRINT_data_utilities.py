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

    def __init__( self
                 ,x  	= 0.0
                 ,y  	= 0.0
                 ,z  	= 0.0
                 ,rx     = 0.0
                 ,ry     = 0.0
                 ,rz     = 0.0
                 ,q      = 0.0
                 ,ext    = 0.0):
        
        self.x      = float(x)
        self.y      = float(y)
        self.z      = float(z)
        self.rx     = float(rx)
        self.ry     = float(ry)
        self.rz     = float(rz)
        self.q      = float(q)
        self.ext    = float(ext)
    


    def __str__( self ):

        return f"X: {self.x}   Y: {self.y}   Z: {self.z}   Rx: {self.rx}   Ry: {self.ry}   Rz: {self.rz}   " \
               f"Q: {self.q}   EXT: {self.ext}"
    


    def __add__( self, summand ):

        try:
            return round( Coordinate( ( self.x        + summand.x )
                                     ,( self.y        + summand.y )
                                     ,( self.z        + summand.z )
                                     ,( self.rx       + summand.rx )
                                     ,( self.ry       + summand.ry )
                                     ,( self.rz       + summand.rz )
                                     ,( self.q        + summand.q )
                                     ,( self.ext      + summand.ext ) )
                         , 2 )
        except AttributeError:
            return round( Coordinate( ( self.x        + summand )
                                     ,( self.y        + summand )
                                     ,( self.z        + summand )
                                     ,( self.rx       + summand )
                                     ,( self.ry       + summand )
                                     ,( self.rz       + summand )
                                     ,( self.q        + summand )
                                     ,( self.ext      + summand ) )
                         , 2 )
    


    def __sub__( self, subtrahend ):

        try:
            return round( Coordinate( ( self.x        - subtrahend.x )
                                     ,( self.y        - subtrahend.y )
                                     ,( self.z        - subtrahend.z )
                                     ,( self.rx       - subtrahend.rx )
                                     ,( self.ry       - subtrahend.ry )
                                     ,( self.rz       - subtrahend.rz )
                                     ,( self.q        - subtrahend.q )
                                     ,( self.ext      - subtrahend.ext ) )
                        , 2 )
        except AttributeError:
            return round( Coordinate( ( self.x        - subtrahend )
                                     ,( self.y        - subtrahend )
                                     ,( self.z        - subtrahend )
                                     ,( self.rx       - subtrahend )
                                     ,( self.ry       - subtrahend )
                                     ,( self.rz       - subtrahend )
                                     ,( self.q        - subtrahend )
                                     ,( self.ext      - subtrahend ) )
                        , 2 )
    


    def __round__( self, digits ):
        
        return Coordinate( round( self.x,   digits )
                          ,round( self.y,   digits )
                          ,round( self.z,   digits )
                          ,round( self.rx,  digits )
                          ,round( self.ry,  digits )
                          ,round( self.rz,  digits )
                          ,round( self.q,   digits )
                          ,round( self.ext, digits ) )
    


    def __eq__( self, other ):

        try:
            if(     self.x     == other.x
                and self.y     == other.y
                and self.z     == other.z
                and self.rx    == other.rx
                and self.ry    == other.ry
                and self.rz    == other.rz
                and self.q     == other.q
                and self.ext   == other.ext ):
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

    def __init__( self 
                 ,acr    = 50 
                 ,dcr    = 50 
                 ,ts     = 200 
                 ,os     = 50):
        
        self.acr    = int( round( acr, 0) )
        self.dcr    = int( round( dcr, 0) )
        self.ts     = int( round( ts,  0) )
        self.os     = int( round( os,  0) )



    def __str__( self ):

        return f"TS: {self.ts}   OS: {self.os}   ACR: {self.acr}   DCR: {self.dcr}"
    


    def __mul__( self, other ):

        return SpeedVector( ts  = int( round( self.ts *  other, 0) ) 
                           ,os  = int( round( self.os *  other, 0) ) 
                           ,acr = int( round( self.acr * other, 0) ) 
                           ,dcr = int( round( self.dcr * other, 0) ) )
    


    def __rmul__( self, other ):

        return self.__mul__( other )
    


    def __eq__( self, other ):

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
        pan_id:
            motor 1 ID (fiber pivoting)
        pan_steps:
            motor 1 steps/position
        fibDeliv_id:
            motor 2 ID (fiber delivery)
        fibDeliv_steps:
            motor 2 steps/position
            used as [%] when move type is 'V'
            used as motor steps when move type is 'T'
        morPump_id:
            motor 3 ID (mortar pump)
        morPump_steps:
            motor 3 steps/position
        pnmtcClamp_id:
            pneumatic fiber clamp ID
        pnmtcClamp_yn:
            pneumatic fiber clamp on/off
        knifePos_id:
            knife delivery ID
        knifePos_yn:
            knife delivery on/off
        knife_id:
            motor 4 ID (rotation knife)
        knife_yn:
            motor 4 on/off
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

    def __init__( self
                 ,pan_id            = 0
                 ,pan_steps         = 0
                 ,fibDeliv_id       = 0
                 ,fibDeliv_steps    = 0
                 ,morPump_id        = 0
                 ,morPump_steps     = 0
                 ,pnmtcClamp_id     = 0
                 ,pnmtcClamp_yn     = 0
                 ,knifePos_id       = 0
                 ,knifePos_yn       = 0
                 ,knife_id          = 0
                 ,knife_yn          = 0
                 ,pnmtcFiber_id     = 0
                 ,pnmtcFiber_yn     = 0
                 ,time_id           = 0
                 ,time_time         = 0 ):
        
        self.pan_id         = int (pan_id)          # pivoting value
        self.pan_steps      = int (pan_steps)
        self.fibDeliv_id    = int (fibDeliv_id)     # fiber value (calculated with V-option)
        self.fibDeliv_steps = int (fibDeliv_steps)
        self.morPump_id     = int (morPump_id)      # mortar pump
        self.morPump_steps  = int (morPump_steps)
        self.pnmtcClamp_id  = int (pnmtcClamp_id)
        self.pnmtcClamp_yn  = bool(pnmtcClamp_yn)
        self.knifePos_id    = int (knifePos_id)
        self.knifePos_yn    = bool(knifePos_yn)
        self.knife_id       = int (knife_id)
        self.knife_yn       = bool(knife_yn)
        self.pnmtcFiber_id  = int (pnmtcFiber_id)
        self.pnmtcFiber_yn  = bool(pnmtcFiber_yn)
        self.time_id        = int (time_id)
        self.time_time      = int (time_time)



    def __str__( self ):

        return  f"PAN: {self.pan_id}, {self.pan_steps}   FB: {self.fibDeliv_id}, {self.fibDeliv_steps}   "\
                f"MP: {self.morPump_id}, {self.morPump_steps}   "\
                f"PC: {self.pnmtcClamp_id}, {self.pnmtcClamp_yn}   KP: {self.knifePos_id}, {self.knifePos_yn}   "\
                f"K: {self.knife_id}, {self.knife_yn}   PF: {self.pnmtcFiber_id}, {self.pnmtcFiber_yn}   "\
                f"TIME: {self.time_id}, {self.time_time}"
    


    def __eq__( self, other ):

        try:
            if(     self.pan_id         == other.pan_id
                and self.pan_steps      == other.pan_steps
                and self.fibDeliv_id    == other.fibDeliv_id
                and self.fibDeliv_steps == other.fibDeliv_steps
                and self.morPump_id     == other.morPump_id
                and self.morPump_steps  == other.morPump_steps
                and self.pnmtcClamp_id  == other.pnmtcClamp_id
                and self.pnmtcClamp_yn  == other.pnmtcClamp_yn
                and self.knifePos_id    == other.knifePos_id
                and self.knifePos_yn    == other.knifePos_yn
                and self.knife_id       == other.knife_id
                and self.knife_yn       == other.knife_yn
                and self.pnmtcFiber_id  == other.pnmtcFiber_id
                and self.pnmtcFiber_yn  == other.pnmtcFiber_yn
                and self.time_id        == other.time_id
                and self.time_time      == other.time_time ):
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

        printShort:
            prints only most important parameters
    """

    def __init__( self
                 ,id     = 0
                 ,mt     = "L"
                 ,pt     = "E"
                 ,Coor1  = None
                 ,Coor2  = None
                 ,Speed  = None
                 ,sbt    = 0
                 ,sc     = "V"
                 ,z      = 10
                 ,Tool   = None
                 ,pMode  = None):
        
        self.id     = int(id)
        self.mt     = str(mt)
        self.pt     = str(pt)
        self.sbt    = int(sbt)
        self.sc     = str(sc)
        self.z      = int(z)
        self.pMode  = str(pMode)

        # handle those beasty mutables
        self.Coor1  = Coordinate()  if (Coor1 is None) else Coor1
        self.Coor2  = Coordinate()  if (Coor2 is None) else Coor2
        self.Speed  = SpeedVector() if (Speed is None) else Speed
        self.Tool   = ToolCommand() if (Tool is None)  else Tool
    


    def __str__( self ):
        
        return  f"ID: {self.id}  MT: {self.mt}  PT: {self.pt} \t|| COOR_1: {self.Coor1}"\
                f"\n\t\t|| COOR_2: {self.Coor2}"\
                f"\n\t\t|| SV:     {self.Speed} \t|| SBT: {self.sbt}   SC: {self.sc}   Z: {self.z}"\
                f"\n\t\t|| TOOL:   {self.Tool}"\
                f"\n\t\t|| PMODE:  {self.pMode}"
    


    def __eq__( self, other ):

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
                and self.pMode  == other.pMode ):
                return True
            else: return False

        except AttributeError:
            return False
    


    def printShort( self ):
        """ prints only most important parameters, saving display space """

        return  f"ID: {self.id} -- {self.mt}, {self.pt} -- COOR_1: {self.Coor1} -- SV: {self.Speed} -- PMODE:  {self.pMode}"





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
            idPos:
                returns queue entry index(!) of given ID
            entryBeforeID:
                returns entry before given ID
            display:
                returns queue as a str list (uses __str__ of QEntry)
            increment:
                increments all QEntry.ID to handle DC commands send before the queue
            add:
                adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given
            addList:
                adds another queue, hopefully less time-consuming than a for loop with self.add
            append:
                other than '.add' this simply appends an entry indifferently to its ID
            clear:
                deletes single or multiple QEntry from queue, adjusts following ID accordingly
            popFirstItem:
                returns and deletes the QEntry at index 0
    """

    def __init__( self, queue= None ):

        self.queue = [] if( queue is None ) else queue



    def __getitem__( self, i ):

        try:                return self.queue[i]
        except IndexError:  return None


    
    def __len__( self ):

        return len(self.queue)
    


    def __str__( self ):

        if( len(self.queue) != 0 ):
            i   = 0
            ans = ''
            for x in self.queue:
                i   += 1
                ans += f"Element {i}: {x}\n"
            return ans
        
        return "Queue is empty!"
    


    def __eq__( self, other ):

        length = len(self)
        if( length != len(other) ): return False

        for elem in range(length):
            if( self[ elem ] != other[ elem ] ): return False
        
        return True
    


    def lastEntry( self ):
        """ returns last item in queue (surprise!), returns None if queue is empty"""

        if( len(self.queue) == 0 ): 
            return None
        return self.queue[ len(self.queue) - 1 ]
    


    def idPos( self, ID ):
        """ return queue entry index(!) at given ID, not the entry itself, returns None if no such entry """

        length  = len(self.queue)
        i       = 0
        if( length <= 0 ): return None

        for entry in range(length):
            if( self.queue[ entry ].id == ID ): break
            else:                               i += 1
        
        if( (i < 1) or (i >= length) ): 
            raise AttributeError
        
        return i
        

    
    


    def entryBeforeID( self, ID ):
        """ return queue entry before (index - 1) a specific ID, raises AttributeError if no such entry """

        length = len(self.queue)
        i      = 0

        if( length <= 0 ):  raise AttributeError

        for entry in range(length):
            if( self.queue[ entry ].id == ID ): break
            else:                               i += 1
        
        if( (i < 1) or (i >= length) ): 
            raise AttributeError
        
        return self.queue[ i - 1 ]



    def display( self ):
        """ returns queue as a str list (uses __str__ of QEntry) """

        if( len(self.queue) != 0 ):
            ans = []
            for x in self.queue: ans.append( x.printShort() )
            return ans
        return ["Queue is empty!"]



    def increment( self ):
        """ increments all QEntry.ID to handle DC commands send before the queue """

        for i in self.queue:
            i.id += 1



    def add( self, entry, threadCall= False ):
        """ adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given 
            threadCall option allows the first ID to be 0 """

        newEntry = copy.deepcopy( entry )
        lastItem = len(self.queue) - 1 
        if( lastItem < 0 ):
            global SC_currCommId

            if( not threadCall ):
                newEntry.id = SC_currCommId

            self.queue.append( newEntry )
            return None
        
        lastID  = self.queue[ lastItem ].id
        firstID = self.queue[0].id
        
        if( (newEntry.id == 0) or (newEntry.id > lastID) ):
            if( threadCall and (newEntry.id == 0) ): 
                self.increment()
                self.queue.insert( 0, newEntry )
            else:
                newEntry.id = lastID + 1
                self.queue.append( newEntry )

        elif( newEntry.id < 0 ):
            return ValueError

        else:
            if( newEntry.id < firstID ):  newEntry.id = firstID
            
            frontSkip = newEntry.id - firstID
            self.queue.insert( frontSkip,newEntry )
            for i in range( lastItem + 1 - frontSkip ):
                i += 1
                self.queue[ i + frontSkip ].id += 1

        return None
    


    def addList( self, list ):
        """ adds another queue, hopefully less time-consuming than a for loop with self.add """

        newList = copy.deepcopy( list )

        try:                        nlFirstID = newList[0].id
        except Exception as err:    return err
        
        lastItem    = len(self.queue) - 1 
        lenNewList  = len(newList)
        
        if( lastItem < 0 ):
            global SC_currCommId
            if( nlFirstID != SC_currCommId ):
                i = 0
                for entry in newList.queue:
                    entry.id = SC_currCommId + i
                    i += 1

            self.queue.extend( newList.queue )
            return None
        
        lastID  = self.queue[ lastItem ].id
        firstID = self.queue[0].id
        
        if( nlFirstID == (lastID + 1) ):
            self.queue.extend( newList.queue )

        elif( nlFirstID == 0 ):
            i = 1
            for entry in newList.queue:
                entry.id = lastID + i
                i += 1
            self.queue.extend( newList.queue )
        
        else:
            if( nlFirstID < firstID ): 
                i = 0
                for entry in newList.queue:
                    entry.id = firstID + i
                    i += 1
            
            frontSkip = newList[0].id - firstID
            self.queue[ frontSkip:frontSkip ] = newList.queue
            for i in range( lastItem + 1 - frontSkip ):
                i += lenNewList
                self.queue[ i + frontSkip ].id += lenNewList

        return None



    def append( self, entry ):
        """ other than '.add' this simply appends an entry indifferently to its ID """

        newEntry = copy.deepcopy( entry )
        self.queue.append( newEntry )
        return None
    


    def clear( self, all = True, ID = '' ):
        """ deletes single or multiple QEntry from queue, adjusts following ID accordingly """

        if( all ):
            self.queue = []
            return self.queue

        if( len(self.queue) == 0 ):
            return None

        ids     = re.findall('\d+',ID)
        idNum   = len(ids)
        firstID = self.queue[0].id
        lastID  = self.queue[ len(self.queue) - 1 ].id
        
        match idNum:

            case 1:
                id1 = int(ids[0])

                if( (id1 < firstID) or (id1 > lastID) ):  return ValueError

                i = 0
                for entry in self.queue:
                    if( entry.id == id1 ):  break
                    else:                   i += 1
                
                self.queue.__delitem__(i)
                while( i < len(self.queue) ):
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
                    if( entry.id == id1 ):  break
                    else:                   i += 1
                
                for n in range( idDist ):
                    self.queue.__delitem__(i)
                
                while ( i < len(self.queue) ):
                    self.queue[i].id -= idDist
                    i += 1

            case _: 
                return ValueError      

        return self.queue 



    def popFirstItem( self ):        
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

    def __init__( self
                 ,tSpeed = 0.0
                 ,id     = -1
                 ,Coor   = None):
        
        self.tSpeed = float(tSpeed)
        self.id     = int(id)

        # handle those beasty mutables
        self.Coor = Coordinate()   if (Coor is None) else Coor




    def __str__( self ):

        return  f"ID: {self.id}   X: {self.Coor.x}   Y: {self.Coor.y}   Z: {self.Coor.z}   Rx: {self.Coor.rx}   Ry: {self.Coor.ry}   Rz: {self.Coor.rz}   "\
                f"EXT:   {self.Coor.ext}   TOOL_SPEED: {self.tSpeed}"
    


    def __round__( self, digits ):

        return RoboTelemetry( round( self.tSpeed, digits ) 
                             ,self.id
                             ,round( self.Coor,   digits ) )
    


    def __eq__( self, other ):

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

    def __init__( self
                 ,freq = 0.0
                 ,volt = 0.0
                 ,amps = 0.0
                 ,torq = 0.0 ):
        
        self.freq = float(freq)
        self.volt = float(volt)
        self.amps = float(amps)
        self.torq = float(torq)



    def __str__( self ):

        return  f"FREQ: {self.freq}   VOLT: {self.volt}   AMPS: {self.amps}   TORQ: {self.torq}"
    


    def __round__( self, digits ):

        return PumpTelemetry( round( self.freq, digits )
                             ,round( self.volt, digits )
                             ,round( self.amps, digits )
                             ,round( self.torq, digits ) )
    


    def __eq__( self, other ):

        try:
            if(     self.freq == other.freq
                and self.volt == other.volt
                and self.amps == other.amps
                and self.torq == other.torq ):
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

    def __init__( self
                 ,amb_temp =         0.0
                 ,amb_hum =          0.0
                 ,delivPump_temp =   0.0
                 ,robBase_temp =     0.0
                 ,kPump_temp =       0.0
                 ,delivPump_press =  0.0
                 ,kPump_press =      0.0
                 ,Pump1 =            None
                 ,Pump2 =            None
                 ,admPump_freq =     0.0
                 ,admPump_amps =     0.0
                 ,kPump_freq =       0.0
                 ,kPump_amps =       0.0
                 ,Robo =             None
                 ,porosAnalysis =    0.0
                 ,distanceFront =    0.0
                 ,distanceEnd =      0.0 ):
        
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
        self.Pump1  = PumpTelemetry()   if (Pump1 is None) else Pump1
        self.Pump2  = PumpTelemetry()   if (Pump2 is None) else Pump2
        self.Robo   = RoboTelemetry()   if (Robo  is None) else Robo



    def __str__( self ):

        return f"ambTemp: {self.amb_temp}    ambHum: {self.amb_hum}    delivPumpTemp: {self.delivPump_temp}    robBaseTemp: {self.robBase_temp}    "\
               f"kPumpTemp: {self.kPump_temp}    delivPumpPress: {self.delivPump_press}    kPumpPress: {self.kPump_press}    PUMP1: {self.Pump1}    "\
               f"PUMP2: {self.Pump2}    admPumpFreq: {self.admPump_freq}    admPumpAmps: {self.admPump_amps}    kPumpFreq: {self.kPump_freq}    "\
               f"kPumpAmps: {self.kPump_amps}    ROB: {self.Robo}    porosAnalysis: {self.porosAnalysis}    "\
               f"distanceFront: {self.distanceFront}    distanceEnd: {self.distanceEnd}"    
    


    def __eq__( self, other ):

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
    

    def __init__( self
                 ,ip         = ""
                 ,PORT       = 0
                 ,C_TOUT     = 1.0
                 ,RW_TOUT    = 1
                 ,R_BL       = 0
                 ,W_BL       = 0 ):
        
        self.ip         = str(ip)
        self.port       = str(PORT)
        self.c_tout     = float(C_TOUT)
        self.rw_tout    = float(RW_TOUT)
        self.r_bl       = int(R_BL)
        self.w_bl       = int(W_BL)

        self.connected  = False
        self.Socket     = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        self.Telemetry  = RoboTelemetry()
    

    def __str__( self ):

        return  f"IP: {self.ip}   PORT: {self.port}   C_TOUT: {self.c_tout}   RW_TOUT: {self.rw_tout}   "\
                f"R_BL: {self.r_bl}   W_BL: {self.w_bl}"
    


    def setParams( self, paramDict ):
        if( self.connected ): 
            raise PermissionError( 'params not changeable while connected to server!' )
        
        self.ip         = str  ( paramDict["IP"] )
        self.port       = str  ( paramDict["PORT"] )
        self.c_tout     = float( paramDict["C_TOUT"] )
        self.rw_tout    = float( paramDict["RW_TOUT"] )
        self.r_bl       = int  ( paramDict["R_BL"] )
        self.w_bl       = int  ( paramDict["W_BL"] )



    def connect( self ):
        """ tries to connect to the IP and PORT given, returns errors if not possible """

        try:                server_address = ( self.ip, int(self.port) )
        except ValueError:  raise ConnectionError('requested TCP/IP connection via COM-Port!')
        
        self.Socket.settimeout( self.c_tout )

        try:
            self.Socket.connect( server_address )
            self.connected = True
            self.Socket.settimeout( self.rw_tout )
            return True,server_address
        
        except TimeoutError:
            self.connected = 0
            return TimeoutError, server_address
        
        except ConnectionRefusedError:
            self.connected = 0
            return ConnectionError, server_address
        


    def send( self, entry ):
        """ sends data to server, packing according to robots protocol, additional function for pump needed """

        message = [] 
        if( not self.connected ): return ConnectionError, 0

        try:
            message = struct.pack( '<iccffffffffffffffffiiiiiciiiiiiiiiiiiiiiii'
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
                                   ,entry.Tool.pan_id
                                   ,entry.Tool.pan_steps
                                   ,entry.Tool.fibDeliv_id
                                   ,entry.Tool.fibDeliv_steps
                                   ,entry.Tool.morPump_id
                                   ,entry.Tool.morPump_steps
                                   ,entry.Tool.pnmtcClamp_id
                                   ,entry.Tool.pnmtcClamp_yn
                                   ,entry.Tool.knifePos_id
                                   ,entry.Tool.knifePos_yn
                                   ,entry.Tool.knife_id
                                   ,entry.Tool.knife_yn
                                   ,entry.Tool.pnmtcFiber_id
                                   ,entry.Tool.pnmtcFiber_yn
                                   ,entry.Tool.time_id
                                   ,entry.Tool.time_time )
            
            if( len(message) != self.w_bl ):  return ValueError, len(message) 
            
            try:                self.Socket.sendall( message )
            except OSError:     return False, OSError
            
            print( f"SEND:    { entry.id }, length: { len(message) }" )
            return True, len(message)
        
        except Exception as err:
            return False, err



    def receive( self ):
        """ receives and unpacks data from robot, addtional function needed for pump """

        data = ""

        try:
            while ( len(data) < self.r_bl ):        data = self.Socket.recv( self.r_bl )
        except TimeoutError:        return None, None, False
        except Exception as err:    return err, data, False

        if len(data) != self.r_bl:       return ValueError,data,False
        else:
            self.Telemetry.tSpeed   = struct.unpack( '<f',data[0:4]   )[0]
            self.Telemetry.id       = struct.unpack( '<i',data[4:8]   )[0]
            self.Telemetry.Coor.x   = struct.unpack( '<f',data[8:12]  )[0]
            self.Telemetry.Coor.y   = struct.unpack( '<f',data[12:16] )[0]
            self.Telemetry.Coor.z   = struct.unpack( '<f',data[16:20] )[0]
            self.Telemetry.Coor.rx  = struct.unpack( '<f',data[20:24] )[0]
            self.Telemetry.Coor.ry  = struct.unpack( '<f',data[24:28] )[0]
            self.Telemetry.Coor.rz  = struct.unpack( '<f',data[28:32] )[0]
            self.Telemetry.Coor.ext = struct.unpack( '<f',data[32:36] )[0]
            return self.Telemetry,data,True
            


    def close( self, end= False ):
        """ close TCP connection """
        
        self.Socket.close()
        self.connected  = False
        if( not end ): self.Socket = socket.socket( socket.AF_INET, socket.SOCK_STREAM )




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



def preCheckGcodeFile( txt='' ):
    """ extracts the number of GCode commands and the filament length from text,
        ignores Z movement for now, slicing only in x-y-plane yet """
    
    try:
        if( txt == '' ):  return 0, 0, 'empty'

        rows            = txt.split( '\n' )
        x               = 0.0
        y               = 0.0
        z               = 0.0
        commNum         = 0
        filamentLength  = 0.0

        for row in rows:
            if ( len( re.findall('G\d+', row) ) > 0 ):   commNum += 1

            xNew = float( reShort( 'X\d+[,.]\d+', row, 'X' + str(x), 'X\d+' )[0][1:] )
            yNew = float( reShort( 'Y\d+[,.]\d+', row, 'Y' + str(y), 'Y\d+' )[0][1:] )
            zNew = float( reShort( 'Z\d+[,.]\d+', row, 'Z' + str(z), 'Z\d+' )[0][1:] )

            # do the Pythagoras for me, baby
            filamentLength += m.sqrt( m.pow( (xNew - x), 2 ) 
                                     +m.pow( (yNew - y), 2 ) 
                                     +m.pow( (zNew - z), 2 ) )

            x = xNew
            y = yNew
            z = zNew
        
        # convert filamentLength to meters and round
        filamentLength /= 1000
        filamentLength = round( filamentLength, 2 )

    except Exception as e:
        return None, None, e

    return commNum, filamentLength, ''



def preCheckRapidFile( txt='' ):
    """ extracts the number of GCode commands and the filament length from text,
        does not handle Offs commands yet """
    
    try:
        if( txt == '' ):  return 0, 0, 'empty'

        rows            = txt.split( '\n' )
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
                xNew = float( re.findall( '\d+\.\d+', row )[0] )
                yNew = float( re.findall( '\d+\.\d+', row )[1] )
                zNew = float( re.findall( '\d+\.\d+', row )[2] )

                # do the Pythagoras for me, baby
                filamentLength += m.sqrt( m.pow( (xNew - x), 2 )
                                         +m.pow( (yNew - y), 2 )
                                         +m.pow( (zNew - z), 2 ) )

                x = xNew
                y = yNew
                z = zNew
        
        # convert filamentLength to meters and round
        filamentLength /= 1000
        filamentLength = round( filamentLength, 2 )

    except Exception as e:
        return None, None, e

    return commNum, filamentLength, ''



def reShort( regEx, txt, default, fallbackRegEx = '' ):
    """ tries 2 regular expressions on expressions like 'X1.23 Y4.56', 
        returns first match without the leading letter (e.g. '1.23' for '\d+[.,]\d+'),
        returns default value and 'False' if no match occurs """
    
    try:    ans = re.findall( regEx, txt )[0]

    except IndexError:
        if( fallbackRegEx == '' ):  return default, False
        try:                        ans = re.findall( fallbackRegEx, txt )[0]
        except IndexError:          return default, False

    return ans, True



def gcodeToQEntry( mutPos, mutSpeed, zone, txt = '', wTool= False ):
    """ converts a single line of GCode G1 command to a QEntry, can be used in loops for multiline code,
        "pos" should be the pos before this command is executed (before its EXECUTED, not before its added  
        to SC_queue) as its the fallback option if no new X, Y, Z or EXT posistion is passed"""
    global DC_currZero
    global SC_extFllwBhvr
    global TOOL_fibRatio
    global DEF_TOOL_FIB_STPS

    # handle mutuables here
    pos   = copy.deepcopy( mutPos )
    speed = copy.deepcopy( mutSpeed )
    zero  = copy.deepcopy( DC_currZero )

    try:                command = reShort( '^G\d+', txt, 0, '^;' )[0]
    except IndexError:  return None, None

    # act according to GCode command
    match command:
        
        case 'G1':
            entry = QEntry( id= 0, Coor1= pos, Speed= speed, z= zone )

            # set position and speed    
            x, res = reShort( 'X\d+[,.]\d+', txt, pos.x, 'X\d+' )
            if( res ): 
                entry.Coor1.x =  float( x[ 1: ].replace( ',', '.' ) )
                entry.Coor1.x += zero.x
                if( entry.Coor1.x > 0 ):
                    entry.Coor1.ext = int( entry.Coor1.x / SC_extFllwBhvr[0] ) * SC_extFllwBhvr[1]
                    entry.Coor1.ext += zero.ext
                else:
                    entry.Coor1.ext = zero.ext

            y, res = reShort( 'Y\d+[,.]\d+', txt, pos.y, 'Y\d+' )
            if( res ): 
                entry.Coor1.y =  float( y[ 1: ].replace( ',', '.' ) )
                entry.Coor1.y += zero.y

            z, res = reShort( 'Z\d+[,.]\d+', txt, pos.z, 'Z\d+' )
            if( res ): 
                entry.Coor1.z =  float( z[ 1: ].replace( ',', '.' ) )
                entry.Coor1.z += zero.z
            
            fr, res  = reShort( 'F\d+[,.]\d+', txt, speed.ts, 'F\d+' )
            if( res ):
                fr              = float( fr[ 1: ].replace( ',', '.' ) )
                entry.Speed.ts  = int( fr * IO_frToTs )

            ext, res = reShort( 'EXT\d+[,.]\d+', txt, pos.ext, 'EXT\d+' )
            if( res ): 
                entry.Coor1.ext =  float( ext[ 3: ].replace( ',', '.' ) )
                entry.Coor1.ext += zero.ext
            
            entry.Coor1 = round( entry.Coor1, 2 )

            # set tool settings
            if( wTool ):
                entry.Tool.fibDeliv_steps   = int( TOOL_fibRatio * DEF_TOOL_FIB_STPS )
                entry.Tool.pnmtcFiber_yn    = True
            
        case 'G28':
            entry = QEntry( id = 0, Coor1 = pos, Speed = speed, z  = zone )
            if( 'X0'   in txt ):  entry.Coor1.x   = zero.x
            if( 'Y0'   in txt ):  entry.Coor1.y   = zero.y
            if( 'Z0'   in txt ):  entry.Coor1.z   = zero.z
            if( 'EXT0' in txt ):  entry.Coor1.ext = zero.ext

            # set tool settings
            entry.Tool.fibDeliv_steps         = 0
            entry.Tool.pnmtcFiber_yn    = False
        
        case 'G92':
            if( 'X0'   in txt ):  DC_currZero.x   = pos.x
            if( 'Y0'   in txt ):  DC_currZero.y   = pos.y
            if( 'Z0'   in txt ):  DC_currZero.z   = pos.z
            if( 'EXT0' in txt ):  DC_currZero.ext = pos.ext
            return None, command
        
        case ';':
            return None, command
        
        case _:
            return None, None
        
    return entry, command



def rapidToQEntry( txt = '', wTool= False ):
    """ converts a single line of MoveL, MoveJ, MoveC or Move* Offs command (no Reltool) to a QEntry (relative to
        DC_curr_zero), can be used in loops for multiline code, returns entry and any Exceptions"""
    global DC_currZero
    global TOOL_fibRatio
    global DEF_TOOL_FIB_STPS
    
    entry = QEntry( id=0 )
    try:
        entry.mt    = re.findall( 'Move[J,L,C]', txt, 0 )[ 0 ][ 4 ]
        ext, res    = reShort( 'EXT:\d+\.\d+',txt,'error','EXT:\d+' )
        ext         = float(ext[ 4: ])
        
        if( 'Offs' in txt ):
            res_coor            = [ DC_currZero.x
                                   ,DC_currZero.y
                                   ,DC_currZero.z
                                   ,DC_currZero.rx
                                   ,DC_currZero.ry
                                   ,DC_currZero.rz
                                   ,DC_currZero.q ]
            xyzOff              = re.findall( 'pHome,\d+\.\d+,\d+\.\d+,\d+\.\d+', txt )[ 0 ]
            xyzOff              = re.findall( '\d+\.\d+', xyzOff )
            for i in range( 3 ):  res_coor[ i ] += float(xyzOff[ i ])
            ext                += DC_currZero.ext

        else:
            entry.pt = 'Q'
            res_coor = []
            xyzOff      = re.findall( '\d+\.\d+', txt )
            for i in range(7):    res_coor.append( float(xyzOff[ i ]) )
        res_speed       = re.findall( '\d+,\d+,\d+,\d+(?=\],z)', txt )[ 0 ]
        res_speed       = re.findall( '\d+', res_speed )

        entry.Coor1.x   = res_coor[ 0 ]
        entry.Coor1.y   = res_coor[ 1 ]
        entry.Coor1.z   = res_coor[ 2 ]
        entry.Coor1.rx  = res_coor[ 3 ]
        entry.Coor1.ry  = res_coor[ 4 ]
        entry.Coor1.rz  = res_coor[ 5 ]
        entry.Coor1.q   = res_coor[ 6 ]
        entry.Coor1.ext = ext
        entry.Speed.ts  = int(res_speed[ 0 ])
        entry.Speed.os  = int(res_speed[ 1 ])
        entry.Speed.acr = int(res_speed[ 2 ])
        entry.Speed.dcr = int(res_speed[ 3 ])

        zone, res       = reShort( 'z\d+', txt, 10 )
        entry.z         = int(zone[ 1: ])

        entry.Coor1 = round( entry.Coor1, 5 )

        # # for later, if tool is implemented
        # tool    = reShort(',[^,]*$',txt,'tool0')[0]
        # tool    = re.findall('^.* ',tool)[0]
        # tool    = tool [: len(tool) - 1]

        # set tool settings
        if( wTool ):
            entry.Tool.fibDeliv_steps   = int( TOOL_fibRatio * DEF_TOOL_FIB_STPS )
            entry.Tool.pnmtcFiber_yn    = True

    except Exception as e:
        return None,e
    
    return entry,None



def createLogfile():
    """ defines and creates a logfile (and folder if necessary), which carries its creation datetime in the title """

    try:
        desk    = os.environ[ 'USERPROFILE' ]
        logpath = desk / Path( "Desktop/PRINT_py_log" )
        logpath.mkdir( parents=True, exist_ok=True )

        logpath = logpath / Path( f"{ datetime.now().strftime( '%Y-%m-%d_%H%M%S' ) }.txt" )
        text    = f"{ datetime.now().strftime('%Y-%m-%d_%H%M%S') }    [GNRL]:        program booting, starting GUI...\n"

        logfile = open( logpath, 'x' )
        logfile.write ( text )
        logfile.close ()

    except Exception as e:
        print( f"Exception occured during log file creation: { e }" )
        return None

    return ( logpath )



def addToCommProtocol( txt ):
    """ puts entries in terminal list an keep its length below TERM_maxLen"""
    global TERM_log
    global DEF_TERM_MAX_LINES

    TERM_log.append( txt )

    if( len(TERM_log) > DEF_TERM_MAX_LINES ):   TERM_log.__delitem__( 0 )
    




#############################################################################################
#                                    GLOBALS
#############################################################################################

###################################### global constants #####################################
# defaut connection settings (the byte length for writing to the robot wont be user setable
# for safety reasons, it can only be changed here, but only if you know what your doing!)

DEF_TCP_ROB =      { "IP":       "192.168.125.1"
                    ,"PORT":     10001
                    ,"C_TOUT":   60000
                    ,"RW_TOUT":  5
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
DEF_AMC_PANNING     = 0
DEF_AMC_FIB_DELIV   = 100
DEF_AMC_CLAMP       = False
DEF_AMC_KNIFE_POS   = False
DEF_AMC_KNIFE       = False
DEF_AMC_FIBER_PNMTC = False

DEF_DC_SPEED        = SpeedVector()

DEF_IO_ZONE         = 10
DEF_IO_FR_TO_TS     = 0.1

DEF_ICQ_MAX_LINES   = 200

DEF_PRIN_SPEED      = SpeedVector()

DEF_PUMP_LPS        = 0.5

DEF_ROB_COMM_FR     = 10

DEF_SC_VOL_PER_M    = 0.4       # calculated for 1m of 4cm wide and 1cm high filament
DEF_SC_MAX_LINES    = 400
DEF_SC_EXT_FLLW_BHVR= (500,200)

DEF_TERM_MAX_LINES  = 400

DEF_TOOL_FIB_STPS   = 10
DEF_TOOL_FIB_RATIO  = 1.0


###################################### global variables ######################################

ADC_panning         = DEF_AMC_PANNING
ADC_fibDeliv        = DEF_AMC_FIB_DELIV
ADC_clamp           = DEF_AMC_CLAMP
ADC_knifePos        = DEF_AMC_KNIFE_POS
ADC_knife           = DEF_AMC_KNIFE
ADC_fibPnmtc        = DEF_AMC_FIBER_PNMTC

DC_currZero         = Coordinate()
DC_speed            = copy.deepcopy(DEF_DC_SPEED)
DC_robMoving        = False

IO_currFilepath     = None
IO_frToTs           = DEF_IO_FR_TO_TS
IO_zone             = DEF_IO_ZONE

PRIN_speed          = copy.deepcopy(DEF_PRIN_SPEED)

PUMP1_tcpip         = TCPIP( DEF_TCP_PUMP1["IP"]
                            ,DEF_TCP_PUMP1["PORT"]
                            ,DEF_TCP_PUMP1["C_TOUT"]
                            ,DEF_TCP_PUMP1["RW_TOUT"]
                            ,DEF_TCP_PUMP1["R_BL"]
                            ,DEF_TCP_PUMP1["W_BL"])
PUMP1_lastTelem     = PumpTelemetry()
PUMP1_literPerS     = DEF_PUMP_LPS
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
ROB_sendList        = []
ROB_liveAd          = 1.0

SC_volPerM          = DEF_SC_VOL_PER_M
SC_currCommId       = 1
SC_queue            = Queue()
SC_qProcessing      = False
SC_qPrepEnd         = False
SC_extFllwBhvr      = DEF_SC_EXT_FLLW_BHVR

STT_dataBlock       = DaqBlock()

TERM_log            = []

TOOL_fibRatio       = DEF_TOOL_FIB_RATIO