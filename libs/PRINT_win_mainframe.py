#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# python standard libraries
import os
import sys
import copy
from pathlib import Path
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# PyQt stuff
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer, QMutex, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_mainframe_v6 import Ui_MainWindow


# import my own libs
from libs.PRINT_win_daq import daqWindow
from libs.PRINT_win_dialogs import strdDialog, fileDialog
from libs.PRINT_threads import RoboCommWorker,PumpCommWorker
import libs.PRINT_data_utilities as UTIL




####################################### MAINFRAME CLASS  #####################################################

class Mainframe(QMainWindow, Ui_MainWindow):
    """ main UI of PRINT_py (further details pending) """
    
    logpath     = ''            # reference for logEntry, set by __init__
    testrun     = False         # switch for mainframe_test.py
    pump1Conn   = False         # switch to enable pump1
    pump2Conn   = False         # switch to enable pump2
    DAQ         = False         # reference for DAQ main window, instance is loaded in __init__
    firstPos    = True          # one-time switch to get robot home position




    #####################################################################################################
    #                                           SETUP                                                   #
    #####################################################################################################
    
    def __init__(self, lpath = None, connDef = (False,False), testrun = False, parent=None):
        """ setup main window """

        super().__init__(parent)
        
        self.setupUi(self)
        self.setWindowTitle("---   PRINT_py  -  Main Window  ---")
        self.setWindowFlags(Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        self.testrun = testrun

        if(lpath is None):
            logWarning = strdDialog('No path for logfile!\n\nPress OK to continue anyways or\n\
                                     Cancel to exit the program.'
                                    ,'LOGFILE ERROR')
            logWarning.exec()

            if( logWarning.result() == 0 ):
                self.logEntry('GNRL','no logpath given, user choose to exit, exit after setup...')
                # suicide after the actual .exec is finished, exit without chrash
                QTimer.singleShot(0, self.close)
            else:
                self.logEntry('GNRL','no logpath given, user chose to continue without...')

        else:
            self.logpath = lpath
            self.logEntry('GNRL','main GUI running.')

        self.DAQ = daqWindow()
        self.DAQTimer = QTimer()
        self.DAQTimer.setInterval(1000)
        self.DAQTimer.timeout.connect(self.DAQ.timeUpdate)
        self.DAQTimer.start()
        if (not testrun): self.DAQ.show()
        self.logEntry('GNRL','DAQ GUI running.')

        self.logEntry('GNRL','init threading...')
        self.connectThreads()
        self.logEntry('GNRL','connecting mainsignals...')
        self.connectMainSignals()
        self.logEntry('GNRL','load default settings...')
        self.loadDefaults(setup= True)

        if(testrun):
            self.logEntry('TEST','testrun, skipping robot connection...')
            self.logEntry('GNRL','setup finished.')
            self.logEntry('newline')
            return
        
        self.logEntry('GNRL','connect to Robot...') 
        res = self.connectTCP(1)
        if(res == False):
            self.logEntry('GNRL','failed, exiting...')
            # suicide after the actual .exec is finished, exit without chrash
            QTimer.singleShot(0, self.close)
            return

        self.logEntry('GNRL','start threading and setup robot TCP connection watchdog...')
        self.roboCommThread.start()
        self.setWatchdog()

        # connect pumps if told so
        if (connDef[0]): 
            self.logEntry('GNRL','connect to pump1...')
            self.connectTCP(2)
        # if (connDef[1]):  
            # self.logEntry('GNRL','connect to pump2...')
            # self.connectTCP(3)

        self.logEntry('GNRL','setup finished.')
        self.logEntry('newline')






    def connectMainSignals(self):
        """ create signal-slot-links"""

        self.DC_btt_xPlus.pressed.connect                   ( lambda: self.sendDCCommand('X','+') )
        self.DC_btt_xMinus.pressed.connect                  ( lambda: self.sendDCCommand('X','-') )
        self.DC_btt_yPlus.pressed.connect                   ( lambda: self.sendDCCommand('Y','+') )
        self.DC_btt_yMinus.pressed.connect                  ( lambda: self.sendDCCommand('Y','-') )
        self.DC_btt_zPlus.pressed.connect                   ( lambda: self.sendDCCommand('Z','+') )
        self.DC_btt_zMinus.pressed.connect                  ( lambda: self.sendDCCommand('Z','-') )
        self.DC_btt_extPlus.pressed.connect                 ( lambda: self.sendDCCommand('EXT','+') )
        self.DC_btt_extMinus.pressed.connect                ( lambda: self.sendDCCommand('EXT','-') )
        self.DC_btt_xyzZero.pressed.connect                 ( lambda: self.setZero([1,2,3]) )
        self.DC_btt_extZero.pressed.connect                 ( lambda: self.setZero([8]) )
        self.DC_btt_home.pressed.connect                    (self.homeCommand)

        self.IO_btt_newFile.pressed.connect                 (self.openFile)
        self.IO_btt_loadFile.pressed.connect                (self.loadFile)
        self.IO_btt_addByID.pressed.connect                 ( lambda: self.loadFile(lf_adID = True) )
        self.IO_btt_xyzZero.pressed.connect                 ( lambda: self.setZero([1,2,3]) )
        self.IO_btt_extZero.pressed.connect                 ( lambda: self.setZero([8]) )

        self.NC_btt_xyzSend.pressed.connect                 ( lambda: self.sendNCCommand([1,2,3]) )
        self.NC_btt_xyzExtSend.pressed.connect              ( lambda: self.sendNCCommand([1,2,3,8]) )
        self.NC_btt_orientSend.pressed.connect              ( lambda: self.sendNCCommand([4,5,6]) )
        self.NC_btt_orientZero.pressed.connect              ( lambda: self.setZero([4,5,6]) )

        self.PUMP_btt_setSpeed.pressed.connect              (self.setSpeed)
        self.SCTRL_num_liveAd_pump1.valueChanged.connect    (self.setSpeed)
        self.PUMP_btt_plus1.pressed.connect                 ( lambda: self.setSpeed('1') )
        self.PUMP_btt_minus1.pressed.connect                ( lambda: self.setSpeed('-1') )
        self.PUMP_btt_stop.pressed.connect                  ( lambda: self.setSpeed('0') )
        self.PUMP_btt_reverse.pressed.connect               ( lambda: self.setSpeed('r') )

        self.SCTRL_btt_startQProcessing.pressed.connect     (self.startSCTRLQueue )
        self.SCTRL_btt_holdQProcessing.pressed.connect      ( lambda: self.stopSCTRLQueue(prepEnd = True) )
        self.SCTRL_btt_addSIB1_atFront.pressed.connect      ( lambda: self.addSIB(1) )
        self.SCTRL_btt_addSIB1_atEnd.pressed.connect        ( lambda: self.addSIB(1, atEnd = True) )
        self.SCTRL_btt_addSIB2_atFront.pressed.connect      ( lambda: self.addSIB(2) )
        self.SCTRL_btt_addSIB2_atEnd.pressed.connect        ( lambda: self.addSIB(2, atEnd = True) )
        self.SCTRL_btt_addSIB3_atFront.pressed.connect      ( lambda: self.addSIB(3) )
        self.SCTRL_btt_addSIB3_atEnd.pressed.connect        ( lambda: self.addSIB(3, atEnd = True) )
        self.SCTRL_btt_clrQ.pressed.connect                 ( lambda: self.clrQueue(partial = False) )
        self.SCTRL_btt_clrByID.pressed.connect              ( lambda: self.clrQueue(partial = True) )
        self.SCTRL_btt_forcedStop.pressed.connect           ( lambda: self.forcedStopCommand() )
        
        self.SET_btt_apply.pressed.connect                  (self.applySettings)
        self.SET_btt_default.pressed.connect                (self.loadDefaults)

        self.SGLC_btt_gcodeSglComm.pressed.connect          (self.addGcodeSgl)
        self.SGLC_btt_rapidSglComm.pressed.connect          (self.addRapidSgl)
        self.SGLC_btt_sendFirstQComm.pressed.connect        ( lambda: self.sendCommand(UTIL.SC_queue.popFirstItem()) )
        self.SGLC_btt_gcodeSglComm_addByID.pressed.connect  ( lambda: self.addGcodeSgl( atID = True
                                                                                       ,ID = self.SGLC_num_gcodeSglComm_addByID.value()) )
        self.SGLC_btt_rapidSglComm_addByID.pressed.connect  ( lambda: self.addRapidSgl( atID = True
                                                                                       ,ID = self.SGLC_num_rapidSglComm_addByID.value()) )

        # self.TCP_ROB_btt_reconn.pressed.connect             ( lambda: self.connectTCP(1) )
        # self.TCP_PUMP1_btt_reconn.pressed.connect           ( lambda: self.connectTCP(2) )
        # self.TCP_PUMP2_btt_reconn.pressed.connect           ( lambda: self.connectTCP(3) )
        self.TCP_ROB_btt_discon.pressed.connect             ( lambda: self.disconnectTCP(1) )
        self.TCP_PUMP1_btt_discon.pressed.connect           ( lambda: self.disconnectTCP(2) )
        self.TCP_PUMP2_btt_discon.pressed.connect           ( lambda: self.disconnectTCP(3) )
        
        self.TERM_btt_gcodeInterp.pressed.connect           (self.sendGcodeCommand)
        self.TERM_btt_rapidInterp.pressed.connect           (self.sendRapidCommand)






    def loadDefaults(self, setup = False):
        """ load default settings to settings display """
        
        self.TCP_num_commForerun.setValue       ( UTIL.DEF_ROB_COMM_FR )

        self.SET_float_volPerE.setValue         ( UTIL.DEF_SC_VOL_PER_MM )
        self.SET_float_frToMms.setValue         ( UTIL.DEF_IO_FR_TO_TS )

        self.SET_num_zone.setValue              ( UTIL.DEF_IO_ZONE )
        self.SET_num_transSpeed_dc.setValue     ( UTIL.DEF_DC_SPEED.ts )
        self.SET_num_orientSpeed_dc.setValue    ( UTIL.DEF_DC_SPEED.os )
        self.SET_num_accelRamp_dc.setValue      ( UTIL.DEF_DC_SPEED.acr )
        self.SET_num_decelRamp_dc.setValue      ( UTIL.DEF_DC_SPEED.dcr )
        self.SET_num_transSpeed_print.setValue  ( UTIL.DEF_PRIN_SPEED.ts )
        self.SET_num_orientSpeed_print.setValue ( UTIL.DEF_PRIN_SPEED.os )
        self.SET_num_accelRamp_print.setValue   ( UTIL.DEF_PRIN_SPEED.acr )
        self.SET_num_decelRamp_print.setValue   ( UTIL.DEF_PRIN_SPEED.dcr )

        if(not setup): self.logEntry('SETS','User resetted all properties to default values.')
        






    #####################################################################################################
    #                                        CONNECTIONS                                                #
    #####################################################################################################

    def connectTCP(self,TCPslot = 0):
        """slot-wise connection management, mostly to shrink code length, maybe more functionality later"""

        css = ("border-radius: 25px; \
                background-color: #00aaff;")

        match TCPslot:

            case 1:  
                res,conn = UTIL.ROB_tcpip.connect()
                self.TCP_ROB_indi_connected.setStyleSheet(css)
                
                if (res == True):
                    self.logEntry('CONN',f"connected to {conn[0]} at {conn[1]}.")
                    return True
                
                elif (res == TimeoutError):             self.logEntry('CONN',f"timed out while trying to connect {conn[0]} at {conn[1]} .")
                elif (res == ConnectionRefusedError):   self.logEntry('CONN',f"server {conn[0]} at {conn[1]} refused the connection.")
                else:                                   self.logEntry('CONN',f"connection to {conn[0]} at {conn[1]} failed ({res})!")
                
                return False

            case 2:
                if('COM' in UTIL.PUMP1_tcpip.port): self.pumpCommThread.start()
                else:                               raise ConnectionError('TCP not supported') # res,conn = UTIL.PUMP1_tcpip.connect()

                self.TCP_PUMP1_indi_connected.setStyleSheet (css)
                self.logEntry                               ('GNRL',f"connected to Pump1 at {UTIL.PUMP1_tcpip.port}.")
                self.pump1Conn = True
                return True

            case 3:  
                raise ConnectionError('Pump2 not supported')
                # if('COM' in UTIL.PUMP2_tcpip.PORT): self.pumpCommThread_2.start()
                # else:                               raise ConnectionError('TCP not supported') # res,conn = UTIL.PUMP1_tcpip.connect()

                # self.TCP_PUMP2_indi_connected.setStyleSheet (css)
                # self.logEntry                               ('GNRL','connected to Pump2.')
                # self.pump2Conn = True
                # return True

            case _:
                return False        







    def disconnectTCP(self,TCPslot = 0):
        """ disconnect works, reconnect crashes the app, problem probably lies here
            should also send E command to robot on disconnect """

        css = ("border-radius: 25px; \
                background-color: #4c4a48;")

        match TCPslot:

            case 1:  
                self.killWatchdog(1)
                self.receiveWorker.pause()
                UTIL.ROB_tcpip.close()

                self.logEntry('CONN',f"user disconnected robot.")
                self.TCP_ROB_indi_connected.setStyleSheet(css)

            case 2:  
                if( 'COM' in UTIL.PUMP1_tcpip.port ):
                    self.pumpCommThread.quit()
                    self.pumpCommThread.wait()
                else:
                    raise ConnectionError('TCP not supported, unable to disconnect') # UTIL.PUMP1_tcpip.close()
                
            case 3:  
                pass
                # if( 'COM' in UTIL.PUMP2_tcpip.PORT ):
                #     self.pumpCommThread_2.quit()
                #     self.pumpCommThread_2.wait()
                # else:
                #     raise ConnectionError('TCP not supported, unable to disconnect') # UTIL.PUMP1_tcpip.close()
            
            case _:
                pass








    #####################################################################################################
    #                                          THREADS                                                  #
    #####################################################################################################

    def connectThreads(self):
        """load all threads from PRINT_threads and set signal-slot-connections"""

        self.roboCommThread = QThread()
        self.roboCommWorker = RoboCommWorker()
        self.roboCommWorker.moveToThread            (self.roboCommThread)
        self.roboCommThread.started.connect         (self.roboCommWorker.run)
        self.roboCommThread.finished.connect        (self.roboCommWorker.stop)
        self.roboCommThread.finished.connect        (self.roboCommWorker.deleteLater)
        self.roboCommWorker.dataReceived.connect    ( lambda: self.resetWatchdog(1) )
        self.roboCommWorker.dataReceived.connect    (self.labelUpdate_onTerminalChange)
        self.roboCommWorker.dataUpdated.connect     (self.posUpdate)
        self.roboCommWorker.endDcMoving.connect     ( lambda: self.switchRobMoving(end= True) )
        self.roboCommWorker.endProcessing.connect   (self.stopSCTRLQueue)
        self.roboCommWorker.logError.connect        (self.logEntry)
        self.roboCommWorker.queueEmtpy.connect      ( lambda: self.stopSCTRLQueue(prepEnd= True) )
        self.roboCommWorker.sendElem.connect        (self.sendCommand)

        self.pumpCommThread = QThread()
        self.pumpCommWorker = PumpCommWorker()
        self.pumpCommWorker.moveToThread            (self.pumpCommThread)
        self.pumpCommThread.started.connect         (self.pumpCommWorker.run)
        self.pumpCommThread.finished.connect        (self.pumpCommWorker.stop)
        self.pumpCommThread.finished.connect        (self.pumpCommWorker.deleteLater)
        self.pumpCommWorker.logError.connect        (self.logEntry)
        self.pumpCommWorker.dataSend.connect        (self.pump1Send)
        self.pumpCommWorker.dataReceived.connect    (self.pump1Update)
        
    





    def posUpdate(self, rawDataString, telem):
        """ write robots telemetry to global variables """

        # set the fist given position to zero as this is usually the standard position for Rob2
        if (self.firstPos):
            UTIL.ROB_movStartP = copy.deepcopy( UTIL.ROB_telem.Coor )
            UTIL.ROB_movEndP   = copy.deepcopy( UTIL.ROB_telem.Coor )
            self.setZero([1,2,3,4,5,6,8])
            self.firstPos = False

        self.logEntry('RTel',f"ID {telem.id},   {telem.Coor}   ToolSpeed: {telem.tSpeed}")
        self.labelUpdate_onReceive(rawDataString)
        self.DAQ.dataUpdate()





    def pump1Send(self, newSpeed, command, ans):
        """ display pump communication """

        mutex.lock()
        UTIL.PUMP1_speed = newSpeed
        mutex.unlock()

        self.TCP_PUMP1_disp_writeBuffer.setText     ( str(command) )
        self.TCP_PUMP1_disp_bytesWritten.setText    ( str(len(command)) )
        self.TCP_PUMP1_disp_readBuffer.setText      ( str(ans) )
        self.PUMP_disp_currSpeed.setText            ( f"{UTIL.PUMP1_speed}%" )
    
        self.logEntry('PMP1',f"speed set to {UTIL.PUMP1_speed}, command: {command}")





    def pump1Update(self, telem):
        """ display pump telemetry """

        self.PUMP_disp_freq.setText ( str( UTIL.STT_dataBlock.Pump1.freq ) )
        self.PUMP_disp_volt.setText ( str( UTIL.STT_dataBlock.Pump1.volt ) )
        self.PUMP_disp_amps.setText ( str( UTIL.STT_dataBlock.Pump1.amps ) )
        self.PUMP_disp_torq.setText ( str( UTIL.STT_dataBlock.Pump1.torq ) )

        self.logEntry('PTel',f"PUMP1, freq: {telem.freq}, volt: {telem.volt}, amps: {telem.amps}, torq: {telem.torq}")







    #####################################################################################################
    #                                          WATCHDOGS                                                #
    #####################################################################################################

    def setWatchdog(self):
        """ set Watchdog, just one to check the robots TCP connection for now (receiveWD) at least every 10 sec """

        self.receiveWD = QTimer()
        self.receiveWD.setSingleShot    (True)
        self.receiveWD.setInterval      (10000)
        self.receiveWD.timeout.connect  (lambda: self.watchdogBite(1))

        self.receiveWD.start()
        self.logEntry('WDOG','Watchdog 1 (receiveWD) started.')
        




    def resetWatchdog(self, dognumber=0):
        """ reset the Watchdogs, receiveWD on every newly received data block """

        match dognumber:
            case 1:   self.receiveWD.start()
            case _:   self.logEntry('WDOG','Watchdog reset failed, invalid dog number given')





    def watchdogBite(self, dognumber = 0):
        """ close the UI on any biting WD, log info """

        match dognumber:
            case 1:   wdNum = '1'
            case _:   wdNum = '(unidentified)'
        
        if(UTIL.SC_qProcessing):
            self.logEntry           ('WDOG',f"Watchdog {wdNum} has bitten! Stopping script control & forwarding forced-stop to robot!")
            self.forcedStopCommand  ()
            self.stopSCTRLQueue     ()

            wdTxt = f"Watchdog {wdNum} has bitten!\n\nScript control was stopped and forced-stop "\
                    f"command was send to robot!\nPress OK to keep PRINT_py running or Cancel to "\
                    f"exit and close."

        else:
            self.logEntry           ('WDOG',f"Watchdog {wdNum} has bitten, robot disconnected!")

            wdTxt = f"Watchdog {wdNum} has bitten!\n\nRobot disconnected.\nPress OK to keep PRINT_py running or Cancel to "\
                    f"exit and close."

        if( UTIL.ROB_tcpip.connected ):
            watchdogWarning = strdDialog(wdTxt, 'WATCHDOG ALARM')
            watchdogWarning.exec()

            if( watchdogWarning.result() ):
                self.logEntry('WDOG',f"User chose to return to main screen.")
                self.resetWatchdog(1)

            else:
                self.logEntry('WDOG',f"User chose to close PRINT_py, exiting...")
                self.close()

        self.TCP_ROB_indi_connected.setStyleSheet( "border-radius: 25px;background-color: #4c4a48;" )
        UTIL.ROB_tcpip.connected = False
        self.resetWatchdog(1)

        



    # def killWatchdog(self, dognumber = 0):
    #     """ put them to sleep (dont do this to real dogs) """

    #     match dognumber:
    #         case 1:   self.receiveWD.stop()
    #         case _:   pass







    #####################################################################################################
    #                                          SETTINGS                                                 #
    #####################################################################################################

    def applySettings(self):
        """ load default settings to settings display """
        
        UTIL.ROB_commFr         = self.TCP_num_commForerun.value()

        UTIL.SC_volPerMm         = self.SET_float_volPerE.value()
        UTIL.IO_frToTs          = self.SET_float_frToMms.value()

        UTIL.IO_zone            = self.SET_num_zone.value()
        UTIL.DC_speed.ts        = self.SET_num_transSpeed_dc.value()
        UTIL.DC_speed.os        = self.SET_num_orientSpeed_dc.value()
        UTIL.DC_speed.acr       = self.SET_num_accelRamp_dc.value()
        UTIL.DC_speed.dcr       = self.SET_num_decelRamp_dc.value()
        UTIL.PRIN_speed.ts      = self.SET_num_transSpeed_print.value()
        UTIL.PRIN_speed.os      = self.SET_num_orientSpeed_print.value()
        UTIL.PRIN_speed.acr     = self.SET_num_accelRamp_print.value()
        UTIL.PRIN_speed.dcr     = self.SET_num_decelRamp_print.value()

        self.logEntry('SETS',f"Settings updated -- ComFR: {UTIL.ROB_commFr}, VolPerE: {UTIL.SC_volPerMm}"
                             f", FR2TS: {UTIL.IO_frToTs}, IOZ: {UTIL.IO_zone}, PrinTS: {UTIL.PRIN_speed.ts}"
                             f", PrinOS: {UTIL.PRIN_speed.os}, PrinACR: {UTIL.PRIN_speed.acr}"
                             f", PrinDCR: {UTIL.PRIN_speed.dcr}, DCTS: {UTIL.DC_speed.ts}"
                             f", DCOS: {UTIL.DC_speed.os}, DCACR: {UTIL.DC_speed.acr}, DCDCR: {UTIL.DC_speed.dcr}")






    #####################################################################################################
    #                                        LOG FUNCTION                                               #
    #####################################################################################################

    def logEntry(self, source='[    ]', text=''):
        """ set one-line for log entries, safes A LOT of code """

        text = text.replace('\n','')
        text = text.replace('\t','')
        if (self.logpath == ''):    return None
        if (source == 'newline'):   text = '\n'
        else:                       text = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}    [{source}]:        {text}\n"
        self.SET_disp_logEntry.setText(text)

        try:
            logfile = open(self.logpath,'a')
        except FileExistsError:
            pass

        logfile.write(text)
        logfile.close()







    #####################################################################################################
    #                                        QLABEL UPDATES                                             #
    #####################################################################################################

    def labelUpdate_onReceive(self,dataString):
        """ update all QLabels in the UI that may change with newly received data from robot """

        pos         = UTIL.ROB_telem.Coor
        zero        = UTIL.DC_currZero
        robID       = UTIL.ROB_telem.id
        comID       = UTIL.SC_currCommId
        try:                    progID = UTIL.SC_queue[0].ID
        except AttributeError:  progID = comID

        self.TCP_ROB_disp_readBuffer.setText    (dataString)  
        self.SCTRL_disp_buffComms.setText       ( str(progID - robID) )
        self.SCTRL_disp_robCommID.setText       ( str(robID) )
        self.SCTRL_disp_progCommID.setText      ( str(comID) )
        self.SCTRL_disp_elemInQ.setText         ( str(len(UTIL.SC_queue)) ) 

        self.DC_disp_x.setText                  ( str( round( pos.x   - zero.x  ,3 )) )
        self.DC_disp_y.setText                  ( str( round( pos.y   - zero.y  ,3 )) )
        self.DC_disp_z.setText                  ( str( round( pos.z   - zero.z  ,3 )) )
        self.DC_disp_ext.setText                ( str( round( pos.ext - zero.ext,3 )) )

        self.NC_disp_x.setText                  ( str(pos.x) )
        self.NC_disp_y.setText                  ( str(pos.y) )
        self.NC_disp_z.setText                  ( str(pos.z) )
        self.NC_disp_xOrient.setText            ( str(pos.rx) )
        self.NC_disp_yOrient.setText            ( str(pos.ry) )
        self.NC_disp_zOrient.setText            ( str(pos.rz) )
        self.NC_disp_ext.setText                ( str(pos.ext) )

        self.TERM_disp_tcpSpeed.setText         ( str(UTIL.ROB_telem.tSpeed) )
        self.TERM_disp_robCommID.setText        ( str(robID) )
        self.TERM_disp_progCommID.setText       ( str(comID) )






    def labelUpdate_onSend(self,entry):
        """ update all UI QLabels that may change when data was send to robot """

        self.labelUpdate_onQueueChange()
        self.labelUpdate_onTerminalChange()
        self.SCTRL_disp_elemInQ.setText  ( str(len(UTIL.SC_queue)) )

        try:
            robId = UTIL.ROB_telem.id    if( UTIL.ROB_telem.id != -1 )   else 0
            self.SCTRL_disp_buffComms.setText(str( UTIL.SC_queue[0].id - robId - 1 ))
        except AttributeError:  pass






    def labelUpdate_onQueueChange(self):
        """ show when new entries have been successfully placed in or taken from Queue """

        self.SCTRL_arr_queue.clear()
        self.SCTRL_arr_queue.addItems( UTIL.SC_queue.display() )

    



    def labelUpdate_onTerminalChange(self):
        """ show when data was send or received """
        
        self.TERM_arr_terminal.clear()
        self.TERM_arr_terminal.addItems ( UTIL.TERM_log )
        if (self.TERM_chk_autoScroll.isChecked()):  self.TERM_arr_terminal.scrollToBottom()

        self.ICQ_arr_terminal.clear()
        self.ICQ_arr_terminal.addItems  ( UTIL.ROB_commQueue.display() )

    

    def labelUpdate_onNewZero(self):
        """ show when DC_zero has changed """

        self.ZERO_disp_x.setText        ( str( UTIL.DC_currZero.x ) )
        self.ZERO_disp_y.setText        ( str( UTIL.DC_currZero.y ) )
        self.ZERO_disp_z.setText        ( str( UTIL.DC_currZero.z ) )
        self.ZERO_disp_xOrient.setText  ( str( UTIL.DC_currZero.rx ) )
        self.ZERO_disp_yOrient.setText  ( str( UTIL.DC_currZero.ry ) )
        self.ZERO_disp_zOrient.setText  ( str( UTIL.DC_currZero.rz ) )
        self.ZERO_disp_ext.setText      ( str( UTIL.DC_currZero.ext ) )
    




    #####################################################################################################
    #                                            FILE IO                                                #
    #####################################################################################################

    def openFile(self, testrun = False, testpath = None):
        """ prompts the user with a file dialog and estimates printing parameters in given file """

        # get file path and content
        if (testrun): ans = testpath
        else:            
            fDialog = fileDialog('select file to load')
            fDialog.exec()
            ans = Path(fDialog.selectedFiles()[0]) if( fDialog.result() ) else None
        
        if(ans is None):
            self.IO_disp_filename.setText("no file selected")
            UTIL.IO_currFilepath = None
            return None
        
        file    = open(ans,'r')
        txt     = file.read()
        file.close()

        # get number of commands and filament length
        if( ans.suffix == '.mod' ):     commNum, filamentLength, res = UTIL.preCheckRapidFile(txt)
        else:                           commNum, filamentLength, res = UTIL.preCheckGcodeFile(txt)
        
        if(commNum is None):
            self.IO_disp_filename.setText   ('COULD NOT READ FILE!')
            self.logEntry                   ('F-IO', f"Error while opening {ans} file: {res}")
            UTIL.IO_currFilepath           = None
            return None

        if(res == 'empty'):
            self.IO_disp_filename.setText('FILE EMPTY!')
            return None
        
        # display data
        filamentVol     = filamentLength * UTIL.SC_volPerMm
        filamentLength  = round(filamentLength, 3)
        filamentVol     = round(filamentVol, 3)

        self.IO_disp_filename.setText   (ans.name)
        self.IO_disp_commNum.setText    ( str(commNum) )
        self.IO_disp_estimLen.setText   ( str(filamentLength) )
        self.IO_disp_estimVol.setText   ( str(filamentVol) )

        self.logEntry('F-IO', f"Opened new file at {ans}:   {commNum} commands,   {filamentLength}mm filament, {filamentVol}L")
        UTIL.IO_currFilepath = ans
        return ans
    





    def loadFile(self, lf_atID = False, testrun = False, testpath = None):
        """ reads the file set in self.openFile, adds all readable G1 commands to command queue (at end or at ID) """

        fpath = testpath if(testrun) else UTIL.IO_currFilepath
        if (fpath is None):
            self.IO_lbl_loadFile.setText("... no valid file, not executed")
            return False
        
        # get file type and content
        file        = open(fpath,'r')
        txt         = file.read()
        file.close()

        # iterate over all lines in the file, add valid commands found to command queue
        rows            = txt.split('\n')
        lineID          = self.IO_num_addByID.value() if(lf_atID) else 0
        lineID_start    = lineID
        skips           = 0


        if (fpath.suffix == '.gcode'):
            for row in rows:
                entry,command = self.addGcodeSgl(atID= lf_atID, ID= lineID, fromFile= True, fileText= row)

                if(command == ValueError):
                    self.IO_lbl_loadFile.setText    ("VALUE ERROR, ABORTED")
                    self.logEntry                   ('F-IO',f"ERROR: file IO from {fpath} aborted! false entry: {entry}")
                    return False
                elif(command is None):              skips  += 1
                elif( (command == 'G1')  
                      or (command == 'G28')
                      or (command == 'G92') ):      lineID += 1
                else:
                    self.IO_lbl_loadFile.setText    (f"{command}!, ABORTED")
                    self.logEntry                   ('F-IO',f"ERROR: file IO from {fpath} aborted! {command}")

        else:
            for row in rows:
                entry,err = self.addRapidSgl(atID= lf_atID, ID= lineID, fromFile= True, fileText= row)

                if( err == ValueError ):
                    self.IO_lbl_loadFile.setText    ("VALUE ERROR, ABORTED")
                    self.logEntry                   ('F-IO',f"ERROR: file IO from {fpath} aborted! false entry: {entry}")
                    return False
                elif(entry is None):    skips += 1
                else:                   lineID += 1
        
        # update labels, return True if you made it here
        self.IO_num_addByID.setValue( lineID )

        if(skips == 0):     self.IO_lbl_loadFile.setText("... conversion successful")
        else:               self.IO_lbl_loadFile.setText(f"... {skips} command(s) skipped (syntax)")
        
        logTxt = f"Loaded new file from {fpath}:   {lineID - lineID_start} commands ({skips} skipped due to syntax)"
        if (lf_atID):   logTxt += f" starting fom {lineID_start}."
        else:           logTxt += f" at the end."
        self.logEntry('F-IO', logTxt)
        return True
        







    #####################################################################################################
    #                                         COMMAND QUEUE                                             #
    #####################################################################################################


    def startSCTRLQueue(self):
        """ set UI indicators, send the boring work of timing the command to our trusty threads """

        mutex.lock()
        UTIL.PUMP1_speed    = 0
        UTIL.SC_qProcessing = True
        UTIL.SC_qPrepEnd    = False
        mutex.unlock()
        self.logEntry('ComQ','queue processing started')

        css = "border-radius: 20px; background-color: #00aaff;"
        self.SCTRL_indi_qProcessing.setStyleSheet   (css)
        self.TCP_indi_qProcessing.setStyleSheet     (css)
        self.switchRobMoving()

        self.labelUpdate_onQueueChange()






    def stopSCTRLQueue(self, prepEnd = False):
        """ set UI indicators, turn off threads """

        if( prepEnd ):
            css = "border-radius: 20px; background-color: #ffda1e;"
            UTIL.SC_qPrepEnd = True
        
        else:
            mutex.lock()
            UTIL.PUMP1_speed    = 0
            UTIL.SC_qPrepEnd    = False
            UTIL.SC_qProcessing = False
            mutex.unlock()
            self.logEntry('ComQ','queue processing stopped')

            self.labelUpdate_onQueueChange()
            self.switchRobMoving(end= True)
            css = "border-radius: 20px; background-color: #4c4a48;"

        self.SCTRL_indi_qProcessing.setStyleSheet   (css)
        self.TCP_indi_qProcessing.setStyleSheet     (css)

    




    def addGcodeSgl(self, atID = False, ID = 0, fromFile = False, fileText = ''):
        """ function meant to convert any single gcode lines to QEntry,
            uses the position BEFORE PLANNED COMMAND EXECUTION, as this is the fallback option
            if no X, Y, Z or EXT position is given"""

        # get text and position BEFORE PLANNED COMMAND EXECUTION
        speed   = copy.deepcopy(UTIL.PRIN_speed)
        try:
            if( not atID ):     pos = copy.deepcopy( UTIL.SC_queue.lastEntry().Coor1 )
            else:               pos = copy.deepcopy( UTIL.SC_queue.entryBeforeID(ID).Coor1 )
        except AttributeError:  pos = UTIL.DC_currZero
        if( not fromFile ):     txt = self.SGLC_entry_gcodeSglComm.toPlainText() 
        else:                   txt = fileText
        
        # act according to GCode command
        entry,command = UTIL.gcodeToQEntry(pos, speed ,UTIL.IO_zone ,txt)
        if ( (command != 'G1') and (command != 'G28') and (command != 'G92') ):

            if(command == ';'):     panTxt = f"leading semicolon interpreted as comment:\n{txt}"
            elif(command is None):  panTxt = f"SYNTAX ERROR:\n{txt}"
            else:                   
                if(not fromFile):   self.SGLC_entry_gcodeSglComm.setText(f"{command}\n{txt}")
                return entry, command
            
            if(not fromFile):       self.SGLC_entry_gcodeSglComm.setText(panTxt)
            return entry, None
        
        elif( command == 'G92' ):   
            self.labelUpdate_onNewZero()
            return entry, None

        # set command ID if given, sorting is done later by "Queue" class
        if(atID):    entry.id = ID

        mutex.lock()
        res = UTIL.SC_queue.add(entry)
        mutex.unlock()
        
        if(res == ValueError):
            if(not fromFile):   self.SGLC_entry_gcodeSglComm.setText("VALUE ERROR: \n" + txt)
            return None, ValueError
        
        if(not fromFile):    self.logEntry('ComQ',f"single GCode command added -- "
                                                  f"ID: {entry.id}  MT: {entry.mt}  PT: {entry.pt}"
                                                  f"  --  COOR_1: {entry.Coor1}  --  COOR_2: {entry.Coor2}"
                                                  f"  --  SV: {entry.Speed}  --  SBT: {entry.sbt}   SC: {entry.sc}"
                                                  f"  --  Z: {entry.z}  --  TOOL: {entry.Tool}")
        self.labelUpdate_onQueueChange()
        return entry, command

    




    def addRapidSgl(self, atID = False, ID = 0, fromFile = False, fileText = ''):
        """ function meant to convert all RAPID single lines into QEntry """

        # get text and current position, (identify command -- to be added)
        if( not fromFile):      txt = self.SGLC_entry_rapidSglComm.toPlainText() 
        else:                   txt = fileText
        
        entry,err   = UTIL.rapidToQEntry(txt)
        if( entry == None ):
            if(not fromFile):   self.SGLC_entry_rapidSglComm.setText(f"SYNTAX ERROR: {err}\n" + txt)
            return None, err
        
        # set command ID if given, sorting is done later by "Queue" class
        if(atID):    entry.id = ID

        mutex.lock()
        res = UTIL.SC_queue.add(entry)
        mutex.unlock()

        if(res == ValueError):
            if(not fromFile):   self.SGLC_entry_rapidSglComm.setText("VALUE ERROR: \n" + txt)
            return None, ValueError
        
        if(not fromFile):    self.logEntry('ComQ',f"single RAPID command added -- "
                                                  f"ID: {entry.id}  MT: {entry.mt}  PT: {entry.pt}"
                                                  f"  --  COOR_1: {entry.Coor1}  --  COOR_2: {entry.Coor2}"
                                                  f"  --  SV: {entry.Speed}  --  SBT: {entry.sbt}   SC: {entry.sc}"
                                                  f"  --  Z: {entry.z}  --  TOOL: {entry.Tool}")

        # update displays
        self.labelUpdate_onQueueChange()
        return entry, None
    





    def addSIB(self,number,atEnd = False):
        """ add standard instruction block (SIB) to queue"""

        match number:
            case 1: txt = self.SIB_entry_sib1.toPlainText()
            case 2: txt = self.SIB_entry_sib2.toPlainText()
            case 3: txt = self.SIB_entry_sib3.toPlainText()
            case _: return False

        if ( (len(UTIL.SC_queue) == 0)  or  not atEnd ):    
            try:                        lineID = UTIL.SC_queue[0].id
            except AttributeError:      lineID = UTIL.ROB_telem.id + 1
        else:                           lineID = UTIL.SC_queue.lastEntry().id + 1

        if( lineID < 1 ): lineID = 1
        lineID_start    = lineID
        rows            = txt.split('\n')

        # interpret rows as either RAPID or GCode, row-wise, handling the entry is unnessecary as
        # its added to queue by the addRapidSgl / addGcodeSgl funcions already
        for row in rows:
            if('Move' in row):
                entry,err = self.addRapidSgl( atID= True, ID= lineID, fromFile=True, fileText= row)
                
                if(err is not None):
                    match number:
                        case 1: self.SIB_entry_sib1.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                        case 2: self.SIB_entry_sib2.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                        case 3: self.SIB_entry_sib3.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                    self.logEntry(f"SIB{number}",f"ERROR: SIB command import aborted ({err})! false entry: {txt}")
                    return False
                else:   lineID += 1

            else:
                entry,command = self.addGcodeSgl( atID= True, ID= lineID, fromFile=True, fileText= row)
                
                if( (command == 'G1')  or  (command == 'G28') ):    lineID  += 1
                else:
                    match number:
                        case 1: self.SIB_entry_sib1.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                        case 2: self.SIB_entry_sib2.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                        case 3: self.SIB_entry_sib3.setText    (f"COMMAND ERROR, ABORTED\n {txt}")
                    self.logEntry(f"SIB{number}",f"ERROR: SIB command import aborted ({command})! false entry: {txt}")
                    return False
        
        logTxt = f"{lineID - lineID_start} SIB lines added"
        if (atEnd): logTxt += " at end of queue"
        else:       logTxt += " in front of queue"
        self.logEntry(f"SIB{number}", logTxt)
        return True
    





    def clrQueue(self, partial = False):
        """ delete specific or all items from queue """

        mutex.lock()
        if (partial):   UTIL.SC_queue.clear( all = False
                                            ,ID  = self.SCTRL_entry_clrByID.text())
        else:           UTIL.SC_queue.clear( all = True )
        mutex.unlock()
        
        if(not partial): self.logEntry('ComQ','queue emptied by user')
        else:               self.logEntry('ComQ',f"queue IDs cleared: {self.SCTRL_entry_clrByID.text()}")
        self.labelUpdate_onQueueChange()
        return True








    #####################################################################################################
    #                                          DC COMMANDS                                              #
    #####################################################################################################

    def switchRobMoving(self, end= False):
        """ change UTIL.DC_robMoving """

        mutex.lock()
        if( end ):
            UTIL.DC_robMoving = False
            self.DC_indi_robotMoving.setStyleSheet("border-radius: 25px; background-color: #4c4a48;")
        else:
            UTIL.DC_robMoving = True
            self.DC_indi_robotMoving.setStyleSheet("border-radius: 25px; background-color: #00aaff;")
        mutex.unlock()



    def homeCommand(self):
        """ sets up a command to drive back to DC_curr_zero, gives it to the actual sendCommand function """

        if( UTIL.DC_robMoving ): return None, None
        self.switchRobMoving()

        zero    = copy.deepcopy(UTIL.DC_currZero)
        readMT  = self.DC_drpd_moveType.currentText()
        mt      = 'L'  if (readMT == 'LINEAR')  else 'J'

        command = UTIL.QEntry( id       = UTIL.SC_currCommId
                              ,mt       = mt
                              ,Coor1   = zero
                              ,Speed       = copy.deepcopy( UTIL.DC_speed )
                              ,z        = 0)
        
        self.logEntry('DCom','sending DC home command...')
        return self.sendCommand(command, DC = True)
        




    def sendDCCommand(self, axis= '0', dir= '+'):
        """ sets up a command accourding to the DC frames input, gives it to the actual sendCommand function """

        if( UTIL.DC_robMoving ): return None, None
        self.switchRobMoving()

        stepWidth = self.DC_sld_stepWidth.value()
        match stepWidth:
            case 1:     pass
            case 2:     stepWidth = 10
            case 3:     stepWidth = 100
            case _:     raise ValueError

        if(dir != '+' and dir != '-'):      raise ValueError
        if(dir == '-'):                     stepWidth = -stepWidth

        newPos = copy.deepcopy(UTIL.ROB_telem.Coor)

        match axis:
            case 'X':       newPos.x   += stepWidth
            case 'Y':       newPos.y   += stepWidth
            case 'Z':       newPos.z   += stepWidth
            case 'EXT':     newPos.ext += stepWidth
            case _:         raise ValueError
            
        
        readMT  = self.DC_drpd_moveType.currentText()
        mt      = 'L'  if (readMT == 'LINEAR')  else 'J'

        command = UTIL.QEntry( id       = UTIL.SC_currCommId
                              ,mt       = mt
                              ,Coor1    = newPos
                              ,Speed    = copy.deepcopy( UTIL.DC_speed )
                              ,z        = 0)
        
        self.logEntry('DCom',f"sending DC command: ({command})")
        return self.sendCommand(command, DC = True)






    def sendNCCommand(self, axis= None):
        """ sets up a command according to NC absolute positioning, gives it to the actual sendCommand function """

        if( UTIL.DC_robMoving ): return None, None
        self.switchRobMoving()

        newPos = copy.deepcopy(UTIL.ROB_telem.Coor)

        # 7 is a placeholder for Q, which can not be set by hand
        if 1 in axis:   newPos.x    = float(self.NC_float_x.value())
        if 2 in axis:   newPos.y    = float(self.NC_float_y.value())
        if 3 in axis:   newPos.z    = float(self.NC_float_z.value())
        if 4 in axis:   newPos.rx   = float(self.NC_float_xOrient.value())
        if 5 in axis:   newPos.ry   = float(self.NC_float_yOrient.value())
        if 6 in axis:   newPos.rz   = float(self.NC_float_zOrient.value())
        if 8 in axis:   newPos.ext  = float(self.NC_float_ext.value())

        readMT  = self.DC_drpd_moveType.currentText()
        mt      = 'L'  if (readMT == 'LINEAR')  else 'J'

        command = UTIL.QEntry( id       = UTIL.SC_currCommId
                              ,mt       = mt
                              ,Coor1    = newPos
                              ,Speed    = copy.deepcopy( UTIL.DC_speed )
                              ,z        = 0)
        
        self.logEntry('DCom',f"sending NC command: ({newPos})")
        return self.sendCommand(command, DC = True)
    




    def sendGcodeCommand(self):
        """ send the GCode interpreter line on the TERM panel to robot,
            uses the current position as it is executed directly, otherwise DONT do that
            if no X, Y, Z or EXT position is given"""
            
        if( UTIL.DC_robMoving ): return None, None
        self.switchRobMoving()

        # get text 
        speed   = copy.deepcopy(UTIL.DC_speed)
        pos     = copy.deepcopy(UTIL.ROB_telem.Coor)
        txt     = self.TERM_entry_gcodeInterp.text()
        
        # act according to GCode command
        entry,command = UTIL.gcodeToQEntry(pos, speed ,UTIL.IO_zone ,txt)
        
        if   ( command == 'G92'):       self.labelUpdate_onNewZero()

        elif ( (command != 'G1') and (command != 'G28') ):
            if  (command == ';'):       panTxt = f"leading semicolon interpreted as comment:\n{txt}"
            elif(command is None):      panTxt = f"SYNTAX ERROR:\n{txt}"
            else:                       panTxt = f"{command}\n{txt}"

            self.TERM_entry_gcodeInterp.setText(panTxt)
            return entry, None
        
        entry.id = UTIL.SC_currCommId

        self.logEntry('DCom',f"sending GCode DC command: ({entry})")
        return self.sendCommand(entry, DC = True)






    def sendRapidCommand(self):
        """ send the GCode interpreter line on the TERM panel to robot, absolute coordinates
            or relative to "pHome" (DC_currZero) """

        if( UTIL.DC_robMoving ): return None, None
        self.switchRobMoving()

        txt         = self.TERM_entry_rapidInterp.text()
        entry,err   = UTIL.rapidToQEntry(txt)

        if( entry == None ):
            self.TERM_entry_rapidInterp.setText(f"SYNTAX ERROR: {err}\n" + txt)
            return None, err
        
        entry.id = UTIL.SC_currCommId

        self.logEntry('DCom',f"sending RAPID DC command: ({entry})")
        return self.sendCommand(entry, DC = True)






    def forcedStopCommand(self):
        """ sets up non-moving-type commands, gives it to the actual sendCommand function """
        
        command = UTIL.QEntry( id = 0
                              ,mt = 'S')
        
        if (self.testrun): return self.sendCommand(command, DC = True)
        FSWarning = strdDialog('WARNING!\n\nRobot will stop after current movement!\n\
                                OK to delete buffered commands on robot\n\
                                Cancel to contuinue queue processing.'
                                ,'FORCED STOP COMMIT')
        FSWarning.exec()

        if(FSWarning.result()):
            self.logEntry('SysC',f"FORCED STOP (user committed).")
            if( UTIL.SC_qProcessing ): 
                self.stopSCTRLQueue()
            return self.sendCommand(command, DC = True)
        
        else:
            self.logEntry('SysC',f"user denied FS-Dialog, continuing...")
            return None
    





    def robotStopCommand(self, directly = True):
        """ close connection signal for robot, add it to Queue or gives it to the actual sendCommand function """

        command = UTIL.QEntry( id = 1
                              ,mt = 'E')
        
        if(directly):
            self.logEntry('SysC',"sending robot stop command directly")
            if( UTIL.SC_qProcessing ): 
                self.stopSCTRLQueue()
            return self.sendCommand(command, DC = True)
        else:
            command.id = 0
            UTIL.SC_queue.add(command)
            self.logEntry('SysC',"added robot stop command to queue")
            return command








    #####################################################################################################
    #                                         SEND COMMANDS                                             #
    #####################################################################################################
    
    def sendCommand(self,command, DC = False):
        """ actual sendCommand function, uses the TCPIP class from utilies, handles errors (not done yet) """
        
        if (command == IndexError): return None
        # if (not DC):                command.SV *= self.SCTRL_num_liveAd_robot.value() / 100.0
        if (self.testrun):          msg, msgLen = True, 1
        else:                       msg, msgLen = UTIL.ROB_tcpip.send(command)

        if (msg == True):
            
            mutex.lock()

            UTIL.ROB_commQueue.add    (command)
            UTIL.addToCommProtocol    (f"SEND:    ID: {command.id}  MT: {command.mt}  PT: {command.pt} \t|| COOR_1: {command.Coor1}"\
                                       f"\n\t\t\t|| COOR_2: {command.Coor2}"\
                                       f"\n\t\t\t|| SV:     {command.Speed} \t|| SBT: {command.sbt}   SC: {command.sc}   Z: {command.z}"\
                                       f"\n\t\t\t|| TOOL:   {command.Tool}")
            UTIL.SC_currCommId += 1
            if (DC): UTIL.SC_queue.increment()

            mutex.unlock()
                
            self.TCP_ROB_disp_writeBuffer.setText   (str(command))
            self.TCP_ROB_disp_bytesWritten.setText  (str(msgLen))

            self.labelUpdate_onSend(command)
            if (not DC): self.logEntry('ComQ',f"Command send  --  ID: {command.id}  MT: {command.mt}  PT: {command.pt}"
                                              f"  --  COOR_1: {command.Coor1}  --  COOR_2: {command.Coor2}"
                                              f"  --  SV: {command.Speed}  --  SBT: {command.sbt}   SC: {command.sc}"
                                              f"  --  Z: {command.z}  --  TOOL: {command.Tool}  --  PMOD: {command.pMode}")

        elif (msg == ValueError):
            self.logEntry('CONN','TCPIP class "ROB_tcpip" encountered ValueError in sendCommand, data length: ' + str(msgLen))
            self.TCP_ROB_disp_writeBuffer.setText   ('ValueError')
            self.TCP_ROB_disp_bytesWritten.setText  (str(msgLen))
        
        elif (msg == RuntimeError or msg == OSError):
            self.logEntry('CONN','TCPIP class "ROB_tcpip" encountered RuntimeError/OSError in sendCommand..')
            self.TCP_ROB_disp_writeBuffer.setText   ('RuntimeError/OSError')
            self.TCP_ROB_disp_bytesWritten.setText  (str(msgLen))
        
        else:
            self.logEntry('CONN','TCPIP class "ROB_tcpip" encountered ' + str(msg))
            self.TCP_ROB_disp_writeBuffer.setText   ('unspecified error')
            self.TCP_ROB_disp_bytesWritten.setText  (str(msgLen))

        return (msg, command)






    def setZero(self,axis):
        """ overwrite DC_curr_zero, uses deepcopy to avoid mutual large mutual exclusion blocks """

        newZero = copy.deepcopy(UTIL.DC_currZero)
        currPos = copy.deepcopy(UTIL.ROB_telem.Coor)

        if axis:
            # 7 is a placeholder for Q, which can not be set by hand
            if 1 in axis:   newZero.x   = currPos.x
            if 2 in axis:   newZero.y   = currPos.y
            if 3 in axis:   newZero.z   = currPos.z
            if 4 in axis:   newZero.rx  = currPos.rx
            if 5 in axis:   newZero.ry  = currPos.ry
            if 6 in axis:   newZero.rz  = currPos.rz
            if 8 in axis:   newZero.ext = currPos.ext
            
            mutex.lock()
            UTIL.DC_currZero = newZero
            mutex.unlock()
        
        self.labelUpdate_onNewZero()
        self.logEntry('ZERO',f"current zero position updated: ({UTIL.DC_currZero})")






    

    #####################################################################################################
    #                                         PUMP CONTROL                                              #
    #####################################################################################################

    def setSpeed(self, type = ''):
        """ handle user inputs regarding pump frequency """

        mutex.lock()
        UTIL.PUMP1_liveAd = self.SCTRL_num_liveAd_pump1.value() / 100.0
        match type:
            case '1':   UTIL.PUMP1_speed += 1
            case '-1':  UTIL.PUMP1_speed -= 1
            case '0':   UTIL.PUMP1_speed =  0
            case 'r':   UTIL.PUMP1_speed *= -1
            case _:     UTIL.PUMP1_speed = self.PUMP_num_setSpeed.value()
        mutex.unlock()




    

    #####################################################################################################
    #                                           CLOSE UI                                                #
    #####################################################################################################

    def closeEvent(self, event):
        """ exit all threads and connections clean(ish) """

        self.logEntry('newline')
        self.logEntry('GNRL','closeEvent signal.')
        self.logEntry('GNRL','end threading, delete threads...')
        
        if(UTIL.ROB_tcpip.connected):
            self.logEntry('CONN','closing TCP connections...')
            self.robotStopCommand()

            UTIL.ROB_tcpip.close( end= True )
        
        self.roboCommThread.quit()
        self.roboCommThread.wait()

        # if(self.pump1Conn):
        if( 'COM' in UTIL.PUMP1_tcpip.port ):
            self.pumpCommThread.quit()
            self.pumpCommThread.wait()
        else:
            raise ConnectionError('TCP not supported, unable to disconnect') # UTIL.PUMP1_tcpip.close()

        # if(self.pump2Conn):
        #     if( 'COM' in UTIL.PUMP2_tcpip.PORT ):
        #         self.pumpCommThread_2.quit()
        #         self.pumpCommThread_2.wait()
        #     else:
        #         raise ConnectionError('TCP not supported, unable to disconnect') # UTIL.PUMP1_tcpip.close()

        self.roboCommThread.deleteLater()
        self.pumpCommThread.deleteLater()

        self.logEntry('GNRL','exiting GUI.')
        self.DAQTimer.stop()
        self.DAQ.close()
        event.accept()








####################################################   MAIN  ####################################################

# mutual exclusion object, used to manage global data exchange
mutex = QMutex()




# only do the following if run as main program
if __name__ == '__main__':

    from libs.PRINT_win_dialogs import strdDialog
    import libs.PRINT_data_utilities as UTIL

    # import PyQT UIs (converted from .ui to .py)
    from ui.UI_mainframe_v5 import Ui_MainWindow



    logpath = UTIL.createLogfile()

    # overwrite ROB_tcpip for testing, delete later
    UTIL.ROB_tcpip.ip = 'localhost'
    UTIL.ROB_tcpip.port = 10001

    # start the UI and assign to app
    app = 0                             # leave that here so app doesnt include the remnant of a previous QApplication instance
    win = 0
    app = QApplication(sys.argv)
    win = Mainframe(lpath=logpath)
    win.show()

    # start application (uses sys for CMD)
    app.exec()
    # sys.exit(app.exec())