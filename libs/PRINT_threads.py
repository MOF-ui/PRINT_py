#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


####################################################   IMPORTS  ####################################################

# python standard libraries
import os
import sys
import copy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import QObject,QTimer,QMutex,pyqtSignal


# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod

# import my own libs
import libs.PRINT_data_utilities as UTIL
import libs.PRINT_pump_utilities as PUTIL







####################################################   WORKER   ####################################################

class PumpCommWorker(QObject):
    """ manages data updates and keepalive commands to pump """

    dataReceived    = pyqtSignal(UTIL.PumpTelemetry)
    dataSend        = pyqtSignal(int, str, int)
    logError        = pyqtSignal(str, str)

    mtecInterface   = MtecMod('01')



    def run(self):
        """ start timer with standard operation on timeout,
            connect to pump via M-Tec Interface """

        self.loopTimer = QTimer()
        self.loopTimer.setInterval(250)
        self.loopTimer.timeout.connect(self.send)
        self.loopTimer.timeout.connect(self.receive)
        self.loopTimer.timeout.connect(self.mtecInterface.keepAlive)

        self.loopTimer.start()
        self.mtecInterface.serial_port = UTIL.PUMP1_tcpip.port
        self.mtecInterface.connect()



    def stop(self):
        """ stop timer """
        
        self.loopTimer.stop()
        self.mtecInterface.stop()
        self.loopTimer.deleteLater()



    def send(self):
        """ send pump speed to pump, uses modified setter in mtec's script (changed to function),
            which recognizes a value change and returns the machines answer and the original command string,
            uses user-set pump speed if no script is running """

        if( UTIL.SC_qProcessing):   newSpeed = PUTIL.calcSpeed()
        else:                       newSpeed = UTIL.PUMP1_speed

        if( newSpeed is not None):
            res = self.mtecInterface.setSpeed( int(newSpeed * UTIL.PUMP1_liveAd) )

            if (res is not None): 
                command,ans = res[0],res[1]
                self.dataSend.emit(newSpeed,command,ans)
        
        else:
            self.logError.emit('CONN','Pump1 - Error during speed calculation for queue processing')
    


    def receive(self):
        """ request data updates for frequency, voltage, current and torque from pump, pass to mainframe """

        # get data 
        freq    = self.mtecInterface.frequency
        volt    = self.mtecInterface.voltage
        amps    = self.mtecInterface.current
        torq    = self.mtecInterface.torque

        if(None in [freq, volt, amps, torq]): 
            self.logError('CONN','Pump1 telemetry package broken or not received...')
        
        else:
            telem = UTIL.PumpTelemetry(freq,volt,amps,torq)
            telem = round(telem, 3)
            
            if( telem != UTIL.PUMP1_lastTelem ):
                mutex.lock()
                UTIL.PUMP1_lastTelem     = telem
                UTIL.STT_dataBlock.Pump1 = telem
                mutex.unlock()
                self.dataReceived.emit(telem)

        





class RoboCommWorker(QObject):
    """ a worker object that check every 50 ms if the Robot queue has empty slots (according to ROBO_comm_forerun),
        emits signal to send data if so, beforehand
        checks the TCPIP connection every 50 ms and writes the result to global vars """


    dataReceived    = pyqtSignal()
    dataUpdated     = pyqtSignal(str, UTIL.RoboTelemetry)
    endProcessing   = pyqtSignal()
    logError        = pyqtSignal(str,str)
    queueEmtpy      = pyqtSignal()
    sendElem        = pyqtSignal(UTIL.QEntry)



    def run(self):
        """ start timer, receive and send on timeout """

        self.checkTimer = QTimer()
        self.checkTimer.setInterval      (50)
        self.checkTimer.timeout.connect  (self.receive)
        self.checkTimer.timeout.connect  (self.send)
        self.checkTimer.start()



    def stop(self):
        """ stop timer """

        self.checkTimer.stop()
        self.checkTimer.deleteLater()    



    def receive(self):
        """ receive 36-byte data block, write to ROB vars """

        telem,rawData,state = UTIL.ROB_tcpip.receive()

        if (state == True):
            if(telem is not None): 
                telem = round(telem, 2)
            self.dataReceived.emit()

            mutex.lock()
            UTIL.addToCommProtocol(f"RECV:    ID {telem.id},   {telem.Coor}   ToolSpeed: {telem.tSpeed}")

            if ( len(UTIL.ROB_commQueue) > 0 ):
                while (UTIL.ROB_commQueue[0].id < telem.id): 
                    UTIL.ROB_commQueue.popFirstItem()

            if( telem != UTIL.ROB_lastTelem ):

                # check if robot is processing a new command (length check to skip in first loop)
                if( (telem.id != UTIL.ROB_lastTelem) and (len(UTIL.ROB_commQueue) > 0) ):
                    UTIL.ROB_movStartP  = UTIL.ROB_movEndP
                    UTIL.ROB_movEndP    = copy.deepcopy( UTIL.ROB_commQueue[0] )

                # set new values to globals
                UTIL.ROB_telem      = copy.deepcopy(telem)
                UTIL.ROB_lastTelem  = copy.deepcopy(telem)

                # prep database entry
                UTIL.STT_dataBlock.Robo      =  telem
                UTIL.STT_dataBlock.Robo.Coor -= UTIL.DC_currZero
                self.dataUpdated.emit( str(rawData), telem )

            mutex.unlock()
            print(f"RECV:    {telem}")
            
        elif (telem is not None):
            self.logError.emit('CONN', f"error ({telem}) from TCPIP class ROB_tcpip, data: {rawData}")

            mutex.lock()
            UTIL.addToCommProtocol(f"RECV:    error ({telem}) from TCPIP class ROB_tcpip, data: {rawData}")
            mutex.unlock()
        
    
    
    def send(self):
        """  signal mainframe to send queue element if qProcessing and robot queue has space """

        lenSc  = len(UTIL.SC_queue)
        lenRob = len(UTIL.ROB_commQueue)
        robId  = UTIL.ROB_telem.id

        if( UTIL.SC_qProcessing ):
            
            if( lenSc > 0):
                if( (robId + UTIL.ROB_commFr) > UTIL.SC_queue[0].id ):

                    mutex.lock()
                    self.sendElem.emit( UTIL.SC_queue.popFirstItem() )
                    mutex.unlock()
            
            else:
                if( lenRob == 0 ):  self.endProcessing.emit()
                else:               self.queueEmtpy.emit()

                







####################################################   MAIN  ####################################################

mutex = QMutex()