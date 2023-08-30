#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


####################################################   IMPORTS  ####################################################

# python standard libraries
import os
import sys

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
        self.loopTimer.timeout.connect(self.loop)

        self.loopTimer.start()
        self.mtecInterface.serial_port = UTIL.PUMP1_tcpip.PORT
        self.mtecInterface.connect()



    def stop(self):
        """ stop timer """
        
        self.loopTimer.stop()
        self.mtecInterface.stop()
        self.loopTimer.deleteLater()



    def loop(self):
        """ not a real loop but you know what I mean,
            standard operations"""

        # use modified mtec setter (changed to function), recognizes value change by itself, returns ans and command str
        newSpeed    = UTIL.PUMP1_speed
        res         = self.mtecInterface.setSpeed( int(newSpeed * UTIL.PUMP1_liveAd) )
        if (res is not None): 
            command,ans = res[0],res[1]
            self.dataSend.emit(newSpeed,command,ans)

        # keepAlive
        self.mtecInterface.keepAlive()

        # get data 
        freq    = self.mtecInterface.frequency
        volt    = self.mtecInterface.voltage
        amps    = self.mtecInterface.current
        torq    = self.mtecInterface.torque
        telem   = UTIL.PumpTelemetry(freq,volt,amps,torq)

        if(None in [freq, volt, amps, torq]): 
            self.logError('CONN','Pump1 telemetry package broken or not received...')
        else:
            telem = round(telem, 3)
            self.dataReceived.emit(telem)
            print(telem)

        





class RoboCommWorker(QObject):
    """ a worker object that check every 50 ms if the Robot queue has empty slots (according to ROBO_comm_forerun),
        emits signal to send data if so, beforehand
        checks the TCPIP connection every 50 ms and writes the result to global vars """


    queueEmtpy      = pyqtSignal()
    sendElem        = pyqtSignal(UTIL.QEntry)
    dataUpdated     = pyqtSignal(str, UTIL.Coor, float, int)
    logError        = pyqtSignal(str,str)



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

        ans,rawData,state = UTIL.ROB_tcpip.receive()

        if (state == True):
            
            if(ans is not None): ans = round(ans, 2)
            print(f"RECV:    {ans}")
            pos             = UTIL.Coor( ans.POS.X
                                        ,ans.POS.Y
                                        ,ans.POS.Z
                                        ,ans.POS.X_ori
                                        ,ans.POS.Y_ori
                                        ,ans.POS.Z_ori
                                        ,0
                                        ,ans.POS.EXT)
            toolSpeed       = ans.TOOL_SPEED
            robo_comm_id    = ans.ID

            mutex.lock()
            UTIL.showOnTerminal(f"RECV:    ID {robo_comm_id},   {pos}   ToolSpeed: {toolSpeed}")
            try:
                while (UTIL.ROB_comm_queue[0].ID < robo_comm_id):  UTIL.ROB_comm_queue.popFirstItem()
            except AttributeError: pass
            mutex.unlock()

            self.dataUpdated.emit( str(rawData)
                                  ,pos
                                  ,toolSpeed
                                  ,robo_comm_id)
            
        elif (ans is not None):
            mutex.lock()
            UTIL.showOnTerminal(f"RECV:    error ({ans}) from TCPIP class ROB_tcpip, data: {rawData}")
            mutex.unlock()

            self.logError.emit('CONN', f"error ({ans}) from TCPIP class ROB_tcpip, data: {rawData}")
        
    
    
    def send(self):
        """  signal mainframe to send queue element if qProcessing and robot queue has space """

        if(UTIL.SC_qProcessing):
            if( len(UTIL.SC_queue) == 0 ):  self.queueEmtpy.emit()

            elif( (UTIL.ROB_comm_id + UTIL.ROB_comm_fr) 
                > UTIL.SC_queue[0].ID ):
                
                mutex.lock()

                elem = UTIL.SC_queue.popFirstItem()
                if (elem == IndexError):    self.queueEmtpy.emit()
                else:                       self.sendElem.emit(elem)
                
                mutex.unlock()







####################################################   MAIN  ####################################################

mutex = QMutex()