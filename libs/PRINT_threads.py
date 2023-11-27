#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


####################################################   IMPORTS  ####################################################

# python standard libraries
import os
import sys
import copy
import math as m

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore   import QObject,QTimer,QMutex,pyqtSignal


# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod  import MtecMod

# import my own libs
import libs.PRINT_data_utilities    as UTIL
import libs.PRINT_pump_utilities    as PUTIL







####################################################   WORKER   ####################################################

class PumpCommWorker( QObject ):
    """ manages data updates and keepalive commands to pump """

    connActive      = pyqtSignal()
    dataReceived    = pyqtSignal( UTIL.PumpTelemetry )
    dataSend        = pyqtSignal( int, str, int )
    logError        = pyqtSignal( str, str )

    mtecInterface   = MtecMod( '01' )





    def run( self ):
        """ start timer with standard operation on timeout,
            connect to pump via M-Tec Interface """

        self.loopTimer = QTimer()
        self.loopTimer.setInterval      ( 250 )
        self.loopTimer.timeout.connect  ( self.send )
        self.loopTimer.timeout.connect  ( self.receive )
        self.loopTimer.timeout.connect  ( self.mtecInterface.keepAlive )
        self.loopTimer.start()

        self.mtecInterface.serial_port = UTIL.PUMP1_tcpip.port
        self.mtecInterface.connect()





    def stop( self ):
        """ stop loop """
        
        self.loopTimer.stop()
        self.mtecInterface.stop()
        self.mtecInterface.disconnect()
        self.loopTimer.deleteLater()





    def send( self ):
        """ send pump speed to pump, uses modified setter in mtec's script (changed to function),
            which recognizes a value change and returns the machines answer and the original command string,
            uses user-set pump speed if no script is running """

        if( UTIL.SC_qProcessing ):  newSpeed = PUTIL.calcSpeed()
        else:                       newSpeed = UTIL.PUMP1_speed

        if( newSpeed is not None ):
            res = self.mtecInterface.setSpeed( int(newSpeed * UTIL.PUMP1_liveAd) )

            if( res is not None ): 
                command, ans = res[ 0 ], res[ 1 ]
                self.dataSend.emit( newSpeed, command, ans )
        
        else:
            self.logError.emit( 'CONN', 'Pump1 - Error during speed calculation for queue processing' )
    




    def receive( self ):
        """ request data updates for frequency, voltage, current and torque from pump, pass to mainframe """

        # get data 
        freq    = self.mtecInterface.frequency
        volt    = self.mtecInterface.voltage
        amps    = self.mtecInterface.current
        torq    = self.mtecInterface.torque
 
        if( None in [ freq, volt, amps, torq ] ): 
            self.logError.emit( 'CONN', 'Pump1 telemetry package broken or not received...' )
        
        else:
            telem = UTIL.PumpTelemetry( freq, volt, amps, torq )
            telem = round( telem, 3 )
            
            if( telem != UTIL.PUMP1_lastTelem ):
                mutex.lock()
                UTIL.PUMP1_lastTelem     = telem
                UTIL.STT_dataBlock.Pump1 = telem
                mutex.unlock()
                self.dataReceived.emit( telem )
            
            self.connActive.emit()

        






class RoboCommWorker( QObject ):
    """ a worker object that check every 50 ms if the Robot queue has empty slots (according to ROBO_comm_forerun),
        emits signal to send data if so, beforehand
        checks the TCPIP connection every 50 ms and writes the result to global vars """


    dataReceived    = pyqtSignal()
    dataUpdated     = pyqtSignal( str, UTIL.RoboTelemetry )
    endDcMoving     = pyqtSignal()
    endProcessing   = pyqtSignal()
    logError        = pyqtSignal( str, str )
    queueEmtpy      = pyqtSignal()
    sendElem        = pyqtSignal( UTIL.QEntry, object, int, bool, bool )



    def run( self ):
        """ start timer, receive and send on timeout """

        self.commTimer = QTimer()
        self.commTimer.setInterval      ( 10 )
        self.commTimer.timeout.connect  ( self.receive )
        self.commTimer.timeout.connect  ( self.send )
        self.commTimer.start()

        self.checkTimer = QTimer()
        self.checkTimer.setInterval     ( 200 )
        self.checkTimer.timeout.connect ( self.checkSC_queue )
        self.checkTimer.start()




    def stop( self ):
        """ stop loop """

        self.commTimer.stop()
        self.commTimer.deleteLater()

        self.checkTimer.stop()
        self.checkTimer.deleteLater()    





    def receive( self ):
        """ receive 36-byte data block, write to ROB vars """

        telem, rawData, state = UTIL.ROB_tcpip.receive()

        if( state == True ):
            if( telem is not None ): 
                telem = round( telem, 1 )
            self.dataReceived.emit()

            mutex.lock()
            UTIL.addToCommProtocol( f"RECV:    ID { telem.id },   { telem.Coor }   TCP: { telem.tSpeed }" )

            # check for ID overflow, reduce SC_queue IDs & get rid off ROB_commQueue entries with IDs at ~3000
            if( telem.id < UTIL.ROB_lastTelem.id ): 
                for x in UTIL.SC_queue.queue:  x.id -= 3000
                try: 
                    id = UTIL.ROB_commQueue[ 0 ].id
                    while( id <= 3000 ): 
                        UTIL.ROB_commQueue.popFirstItem()
                        try:                id = UTIL.ROB_commQueue[ 0 ].id
                        except Exception:   break
                except AttributeError:
                    pass


            # delete all finished command from ROB_commQueue
            try:
                while( UTIL.ROB_commQueue[ 0 ].id < telem.id ):  UTIL.ROB_commQueue.popFirstItem()
            except AttributeError:
                pass
            

            # refresh data only if new
            if( telem != UTIL.ROB_lastTelem ):
                    
                # check if robot is processing a new command (length check to skip in first loop)
                if( ( telem.id != UTIL.ROB_lastTelem.id ) and ( len(UTIL.ROB_commQueue) > 0 ) ):
                    UTIL.ROB_movStartP  = UTIL.ROB_movEndP
                    UTIL.ROB_movEndP    = copy.deepcopy( UTIL.ROB_commQueue[ 0 ].Coor1 )

                # set new values to globals
                UTIL.ROB_telem      = copy.deepcopy( telem )
                UTIL.ROB_lastTelem  = copy.deepcopy( telem )

                # prep database entry
                zero = copy.deepcopy( UTIL.DC_currZero )
                UTIL.STT_dataBlock.Robo      =  copy.deepcopy( telem )
                UTIL.STT_dataBlock.Robo.Coor -= zero
                self.dataUpdated.emit( str(rawData), telem )
                
                print(f"RECV:    {telem}")

            mutex.unlock()

            # reset robMoving indicator if near end, skip if queue is processed
            if( UTIL.DC_robMoving and not UTIL.SC_qProcessing ):
                checkDist = self.checkRobCommZeroDist()
                if( checkDist is not None ):
                    if( checkDist < 1 ): self.endDcMoving.emit()


            
        elif( telem is not None ):
            self.logError.emit( 'CONN', f"error ({telem}) from TCPIP class ROB_tcpip, data: {rawData}" )

            mutex.lock()
            UTIL.addToCommProtocol( f"RECV:    error ({telem}) from TCPIP class ROB_tcpip, data: {rawData}" )
            mutex.unlock()
        


    
    
    def checkSC_queue( self ):
        """  add queue element to sendList if qProcessing and robot queue has space """

        lenSc  = len( UTIL.SC_queue )
        lenRob = len( UTIL.ROB_commQueue )
        robId  = UTIL.ROB_telem.id

        # if qProcessing is ending, define end as being in 1mm range of the last robtarget
        if( UTIL.SC_qPrepEnd ):
            checkDist = self.checkRobCommZeroDist()
            if( checkDist is not None ):
                if( checkDist < 1 ): self.endProcessing.emit()

        # if qProcessing is active and not ending, pop first queue item if robot is nearer than ROB_commFr
        # if no entries in SC_queue left, end qProcessing (immediately if ROB_commQueue is empty as well)
        elif( UTIL.SC_qProcessing ):
            
            if( lenSc > 0 ):
                mutex.lock()
                try:
                    while( ( robId + UTIL.ROB_commFr ) >= UTIL.SC_queue[ 0 ].id ):
                        commTuple = ( UTIL.SC_queue.popFirstItem(), False )
                        UTIL.ROB_sendList.append( commTuple ) 
                except AttributeError:
                    pass
                mutex.unlock()
            
            else:
                if( lenRob == 0 ):  self.endProcessing.emit()
                else:               self.queueEmtpy.emit()
    




    def send( self, testrun= False ):
        """ send sendList entries if not empty """

        numToSend   = len( UTIL.ROB_sendList )
        numSend     = 0
        while( numToSend > 0 ):

            commTuple   = UTIL.ROB_sendList.pop( 0 )
            numToSend   = len( UTIL.ROB_sendList )
            command     = commTuple[ 0 ]
            directCtrl  = commTuple[ 1 ]

            if    ( command == IndexError ):    break
            while ( command.id > 3000 ):        command.id -= 3000

            command.Speed.ts = int( command.Speed.ts * UTIL.ROB_liveAd )
            
            if( not testrun):   msg, msgLen = UTIL.ROB_tcpip.send( command )
            else:               msg, msgLen = True, 159

            if( msg ):
                
                numSend += 1
                
                mutex.lock()
                UTIL.ROB_commQueue.append( command )
                UTIL.addToCommProtocol( f"SEND:    ID: {command.id}  MT: {command.mt}  PT: {command.pt} \t|| COOR_1: {command.Coor1}"\
                                        f"\n\t\t\t|| COOR_2: {command.Coor2}"\
                                        f"\n\t\t\t|| SV:     {command.Speed} \t|| SBT: {command.sbt}   SC: {command.sc}   Z: {command.z}"\
                                        f"\n\t\t\t|| TOOL:   {command.Tool}" )
                if( directCtrl ): UTIL.SC_queue.increment()
                mutex.unlock()
            
            else: 
                print( f" Message Error: {msgLen} " )
                self.sendElem.emit( command, msg, msgLen, directCtrl, False )
            
            if( numToSend == 0 ):
                if( not testrun ): print( " Block send " )
                self.sendElem.emit( command, msg, numSend, directCtrl, True )
            # else                :   self.sendElem.emit(command, msg, msgLen, directCtrl, False)

    
    


    def checkRobCommZeroDist( self ):
        """ calculates distance between next entry in ROB_commQueue and current position """

        if( len(UTIL.ROB_commQueue) == 1 ):
            return  m.sqrt(  m.pow( UTIL.ROB_commQueue[ 0 ].Coor1.x   - UTIL.ROB_telem.Coor.x, 2 )
                           + m.pow( UTIL.ROB_commQueue[ 0 ].Coor1.y   - UTIL.ROB_telem.Coor.y, 2 )
                           + m.pow( UTIL.ROB_commQueue[ 0 ].Coor1.z   - UTIL.ROB_telem.Coor.z, 2 )
                           + m.pow( UTIL.ROB_commQueue[ 0 ].Coor1.ext - UTIL.ROB_telem.Coor.ext, 2 ) )
        else:
            return None








class SensorCommWorker( QObject ):
    """ cycle through all sensors, collect the data """

    cycleDone   = pyqtSignal( bool )



    def start( self ):
        """ start cycling through the sensors """

        self.cycleTimer = QTimer()
        self.cycleTimer.setInterval     ( 200 )
        self.cycleTimer.timeout.connect ( self.cycle )
        self.cycleTimer.start()
    


    def stop( self ):
        """ stop cycling """

        self.cycleTimer.stop()
        self.cycleTimer.deleteLater()
    


    def cycle( self ):
        """ check every sensor once """
        
        







class LoadFileWorker( QObject ):
    """ worker converts .gcode or .mod into QEntries, outsourced to worker as 
        these files can have more than 10000 lines """
    
    convFinished    = pyqtSignal( int, int, int )
    convFailed      = pyqtSignal( str )
    comList         = UTIL.Queue()



    def start( self ):
        """ get data, start conversion loop """

        global LFW_filePath
        global LFW_lineID
        global LFW_pCtrl
        global LFW_running
        global LFW_preRunTime

        LFW_running = True
        lineID      = LFW_lineID
        filePath    = LFW_filePath
        if( filePath is None ): 
            self.convFailed.emit( "No filepath given!" )
            LFW_running = False
            return
        
        file    = open( filePath, 'r' )
        txt     = file.read()
        file.close()

        # init vars
        self.comList.clear()
        rows    = txt.split( '\n' )
        skips   = 0
        startID = lineID

        # iterate over file rows
        if( filePath.suffix == '.gcode' ):
            for row in rows:
                entry,command = self.gcodeConv( ID= lineID, txt= row ) 

                if(   ( command == 'G92' ) 
                      or ( command == ';' ) 
                      or ( command is None ) ) :  skips  += 1
                elif( ( command == 'G1' )  
                      or ( command == 'G28' ) ):  lineID += 1
                elif( command == ValueError ): 
                    self.convFailed.emit( f"VALUE ERROR: { command }" )
                    LFW_running = False
                    return
                else:                           
                    self.convFailed.emit( f"{ command }!, ABORTED" )
                    LFW_running = False
                    return

        else:
            for row in rows:
                entry, err = self.rapidConv( ID= lineID, txt= row )

                if( err == ValueError ):        
                    self.convFailed.emit( f"VALUE ERROR: {command}" )
                    LFW_running = False
                    return
                elif( entry is None ):  skips += 1
                else:                   lineID += 1    
        
        if( len(self.comList) == 0 ): 
            self.convFailed.emit( "No commands found!" )
            LFW_running = False
            return

        # check for unidistance mode
        umCheck = UTIL.reShort( '\&\&: \d+.\d+', txt, None, '\&\&: \d+' )[ 0 ]
        if( umCheck is not None ):
            umDist = UTIL.reShort( '\d+.\d+', umCheck, ValueError, '\d+' )[ 0 ]
            umConvRes = self.addUmTool( umDist )
            if( umConvRes is not None ):
                self.convFailed.emit( umConvRes )
                return

        # automatic pump control
        if( LFW_pCtrl ):
            # set all entries to pmode=default
            for i in self.comList.queue:
                i.pMode = 'default'

            # add a 3mm long startvector with a speed of 3mm/s (so 3s of approach), with pMode=start
            startVector = copy.deepcopy( self.comList[0] )
            startVector.id          =  startID
            startVector.Coor1.x     += LFW_preRunTime
            startVector.Coor1.y     += LFW_preRunTime
            startVector.pMode       =  'zero'
            startVector.Speed       =  UTIL.SpeedVector( acr= 50, dcr= 50, ts= 200, os=100 )

            self.comList[0].Speed   =  UTIL.SpeedVector( acr= 1, dcr= 1, ts= 1, os=1 )
            self.comList[0].pMode   =  'start'
            self.comList.add( startVector, threadCall= True )

            # set the last entry to pMode=end
            self.comList[ len(self.comList) - 1 ].pMode = 'end'

        UTIL.SC_queue.addList  ( self.comList )
        self.convFinished.emit ( lineID, startID, skips )
        LFW_running = False





    def gcodeConv( self, ID, txt ):
        """ single line conversion from GCode """

        # get text and position BEFORE PLANNED COMMAND EXECUTION
        speed   = copy.deepcopy( UTIL.PRIN_speed )
        try:
            if( len(self.comList) == 0 ):   pos = copy.deepcopy( UTIL.SC_queue.entryBeforeID( ID ).Coor1 )
            else:                           pos = copy.deepcopy( self.comList.lastEntry().Coor1 )
        except AttributeError:              pos = UTIL.DC_currZero
        
        # act according to GCode command
        entry,command = UTIL.gcodeToQEntry( pos, speed, UTIL.IO_zone, txt )

        if( ( command != 'G1' ) and ( command != 'G28' ) ):    
            return entry, command
        
        entry.id    = ID
        res         = self.comList.add( entry, threadCall= True )
        
        if( res == ValueError ):
            return None, ValueError
        
        return entry, command
    




    def rapidConv( self, ID, txt ):
        """ single line conversion from RAPID """
                
        entry, err   = UTIL.rapidToQEntry( txt )
        if( entry == None ):
            return None, err
        
        entry.id    = ID
        res         = self.comList.add( entry, threadCall= True )

        if( res == ValueError ):
            return None, ValueError

        return entry, None
    




    def addUmTool( self, umd ):
        """ check if the data makes send, add the tooldata to entries """
        
        try:                umDist = float( umd )
        except Exception:   return f"UM-Mode failed reading { umd }"

        if( umDist < 0.0  or  umDist > 2000.0 ): 
            return f"UM-Distance <0 or >2000"

        for i in self.comList.queue:
            travelTime = umDist / i.Speed.ts
            if( ( umDist % i.Speed.ts ) != 0 ):
                return f"UM-Mode failed setting { travelTime } to int."
            
            i.sc                = 'T'
            i.sbt               = int( travelTime )
            i.Tool.time_time    = int( travelTime )
        return None







####################################################   MAIN  ####################################################

mutex           = QMutex()

LFW_filePath    = None
LFW_lineID      = 0
LFW_pCtrl       = False
LFW_running     = False
LFW_preRunTime  = 5
