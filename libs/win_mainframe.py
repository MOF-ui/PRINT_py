#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# python standard libraries
import os
import re
import sys
import copy
import time
import requests
from pathlib import Path

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# PyQt stuff
from PyQt5.QtWidgets import QApplication, QShortcut


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from libs.win_mainframe_prearrange import PreMainframe, Watchdog, GlobalMutex


# import my own libs
from libs.win_dialogs import strd_dialog, file_dialog
from libs.pump_utilities import default_mode as PU_def_mode
import libs.threads as workers
import libs.data_utilities as du
import libs.func_utilities as fu

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod



####################### MAINFRAME CLASS  #####################################

class Mainframe(PreMainframe):
    """main UI of PRINT_py (further details pending)"""

    ##########################################################################
    #                                ATTRIBUTES                              #
    ##########################################################################

    _testrun = False  # switch for mainframe_test.py
    _first_pos = True  # one-time switch to get robot home position


    #########################################################################
    #                                  SETUP                                #
    #########################################################################

    def __init__(
            self,
            lpath=None,
            p_conn=(False, False),
            testrun=False,
            parent=None
        ) -> None:
        """setup main and daq UI, start subsystems & threads"""

        # getting all prearranged UI functions from PreMainframe
        super().__init__(lpath, testrun, parent)
        self._testrun = testrun

        # LOAD THREADS, SIGNALS & DEFAULT SETTINGS
        self.log_entry('GNRL', 'connecting signals...')
        self.connect_main_signals()
        self.connect_short_signals()

        self.log_entry('GNRL', 'load default settings...')
        self.load_defaults(setup=True)

        self.log_entry('GNRL', 'init threading...')
        self.connect_threads('OTHER')

        # TESTRUN OPTION
        if testrun:
            self.log_entry('TEST', 'testrun, skipping robot connection...')
            self.log_entry('GNRL', 'setup finished.')
            self.log_entry('newline')
            return

        # INIT WATCHDOGS
        self.log_entry('GNRL', "init watchdog...")
        self.connect_watchdogs()

        # CONNECTIONS SETUP
        self.log_entry('GNRL', "connect to Robot...")
        self.connect_tcp('ROB')

        if p_conn[0]:
            self.log_entry("GNRL", "connect to pump1...")
            self.connect_tcp("P1")
        if p_conn[1]:
            self.log_entry("GNRL", "connect to pump2...")
            self.connect_tcp("P2")

        # SENSOR ARRAY START-UP
        self._SensorArrThread.start()
        self.log_entry("GNRL", "started sensor array.")

        # FINISH SETUP
        self.log_entry("GNRL", "setup finished.")
        self.log_entry("newline")


    def connect_main_signals(self) -> None:
        """create signal-slot-links for UI buttons"""

        # AMCON CONTROL
        self.ADC_btt_resetAll.pressed.connect(lambda: self.load_ADC_defaults(send_changes=True))
        self.ADC_num_panning.valueChanged.connect(self.adc_user_change)
        self.ADC_num_fibDeliv.valueChanged.connect(self.adc_user_change)
        self.ADC_btt_clamp.released.connect(self.adc_user_change)
        self.ADC_btt_knifePos.released.connect(self.adc_user_change)
        self.ADC_btt_knife.released.connect(self.adc_user_change)
        self.ADC_btt_fiberPnmtc.released.connect(self.adc_user_change)
        self.ASC_btt_overwrSC.released.connect(self.amcon_script_overwrite)

        # DIRECT CONTROL
        self.DC_btt_xPlus.pressed.connect(lambda: self.send_DC_command("X", "+"))
        self.DC_btt_xMinus.pressed.connect(lambda: self.send_DC_command("X", "-"))
        self.DC_btt_yPlus.pressed.connect(lambda: self.send_DC_command("Y", "+"))
        self.DC_btt_yMinus.pressed.connect(lambda: self.send_DC_command("Y", "-"))
        self.DC_btt_zPlus.pressed.connect(lambda: self.send_DC_command("Z", "+"))
        self.DC_btt_zMinus.pressed.connect(lambda: self.send_DC_command("Z", "-"))
        self.DC_btt_extPlus.pressed.connect(lambda: self.send_DC_command("EXT", "+"))
        self.DC_btt_extMinus.pressed.connect(lambda: self.send_DC_command("EXT", "-"))
        self.DC_btt_xyzZero.pressed.connect(lambda: self.set_zero([1, 2, 3]))
        self.DC_btt_extZero.pressed.connect(lambda: self.set_zero([8]))
        self.DC_btt_home.pressed.connect(self.home_command)

        # FILE IO
        self.IO_btt_newFile.pressed.connect(self.open_file)
        self.IO_btt_loadFile.pressed.connect(self.load_file)
        self.IO_btt_addByID.pressed.connect(lambda: self.load_file(lf_atID=True))
        self.IO_btt_xyzextZero.pressed.connect(lambda: self.set_zero([1, 2, 3, 8]))
        self.IO_btt_orientZero.pressed.connect(lambda: self.set_zero([4, 5, 6]))

        # MIXER CONTROL
        self.MIX_btt_actWithPump.pressed.connect(
            lambda: self.mutex_setattr(
                du,
                'MIX_act_with_pump',
                not self.MIX_btt_actWithPump.isChecked())
        )
        self.MIX_btt_setSpeed.pressed.connect(self.mixer_set_speed)
        self.MIX_btt_stop.pressed.connect(lambda: self.mixer_set_speed('0'))
        self.MIX_sld_speed.sliderMoved.connect(lambda: self.mixer_set_speed('sld'))

        # NUMERIC CONTROL
        self.NC_btt_getValues.pressed.connect(self.values_to_DC_spinbox)
        self.NC_btt_xyzSend.pressed.connect(lambda: self.send_NC_command([1, 2, 3]))
        self.NC_btt_xyzExtSend.pressed.connect(lambda: self.send_NC_command([1, 2, 3, 8]))
        self.NC_btt_orientSend.pressed.connect(lambda: self.send_NC_command([4, 5, 6]))
        self.NC_btt_orientZero.pressed.connect(lambda: self.set_zero([4, 5, 6]))

        # PUMP CONTROL
        self.PUMP_sld_outputRatio.sliderMoved.connect(
            lambda: self.mutex_setattr(
                du,
                'PMP_output_ratio',
                1 - (self.PUMP_sld_outputRatio.value() / 100.0)
            )
        )
        self.SCTRL_num_liveAd_pump1.valueChanged.connect(lambda: self.pump_set_speed("c1"))
        self.SCTRL_num_liveAd_pump2.valueChanged.connect(lambda: self.pump_set_speed("c2"))
        self.PUMP_btt_setSpeedP1.pressed.connect(lambda: self.pump_set_speed("s1"))
        self.PUMP_btt_setSpeedP2.pressed.connect(lambda: self.pump_set_speed("s2"))
        self.PUMP_btt_plus1.pressed.connect(lambda: self.pump_set_speed("1"))
        self.PUMP_btt_minus1.pressed.connect(lambda: self.pump_set_speed("-1"))
        self.PUMP_btt_plus10.pressed.connect(lambda: self.pump_set_speed("10"))
        self.PUMP_btt_minus10.pressed.connect(lambda: self.pump_set_speed("-10"))
        self.PUMP_btt_plus25.pressed.connect(lambda: self.pump_set_speed("25"))
        self.PUMP_btt_minus25.pressed.connect(lambda: self.pump_set_speed("-25"))
        self.PUMP_btt_stop.pressed.connect(lambda: self.pump_set_speed("0"))
        self.PUMP_btt_reverse.pressed.connect(lambda: self.pump_set_speed("r"))
        self.PUMP_btt_ccToDefault.pressed.connect(lambda: self.pump_set_speed("def"))
        self.PUMP_btt_setSpeed.pressed.connect(self.pump_set_speed)
        self.PUMP_btt_scToDefault.pressed.connect(self.pump_script_overwrite)
        self.PUMP_btt_pinchValve.pressed.connect(self.pinch_valve_toggle)

        # SCRIPT CONTROL
        self.SCTRL_num_liveAd_robot.valueChanged.connect(
            lambda: self.mutex_setattr(
                du,
                'ROB_live_ad',
                self.SCTRL_num_liveAd_robot.value() / 100.0
            )
        )
        self.SCTRL_btt_holdQProcessing.pressed.connect(lambda: self.stop_SCTRL_queue(prep_end=True))
        self.SCTRL_chk_autoScroll.stateChanged.connect(lambda: self.SCTRL_arr_queue.scrollToBottom())
        self.ICQ_chk_autoScroll.stateChanged.connect(lambda: self.ICQ_arr_terminal.scrollToBottom())
        self.SCTRL_btt_forcedStop.pressed.connect(self.forced_stop_command)
        self.SCTRL_btt_startQProcessing.pressed.connect(self.start_SCTRL_queue)
        self.SCTRL_btt_addSIB1_atFront.pressed.connect(lambda: self.add_SIB(1))
        self.SCTRL_btt_addSIB2_atFront.pressed.connect(lambda: self.add_SIB(2))
        self.SCTRL_btt_addSIB3_atFront.pressed.connect(lambda: self.add_SIB(3))
        self.SCTRL_btt_addSIB1_atEnd.pressed.connect(lambda: self.add_SIB(1, at_end=True))
        self.SCTRL_btt_addSIB2_atEnd.pressed.connect(lambda: self.add_SIB(2, at_end=True))
        self.SCTRL_btt_addSIB3_atEnd.pressed.connect(lambda: self.add_SIB(3, at_end=True))
        self.SCTRL_btt_clrQ.pressed.connect(lambda: self.clr_queue(partial=False))
        self.SCTRL_btt_clrByID.pressed.connect(lambda: self.clr_queue(partial=True))

        # SETTINGS
        self.TCP_num_commForerun.valueChanged.connect(
            lambda: self.mutex_setattr(
                du,
                'ROB_comm_fr',
                self.TCP_num_commForerun.value()
            )
        )
        self.SET_btt_apply.pressed.connect(self.apply_settings)
        self.SET_btt_default.pressed.connect(self.load_defaults)
        self.SET_TE_btt_apply.pressed.connect(self.apply_TE_settings)
        self.SET_TE_btt_default.pressed.connect(self.load_TE_defaults)
        self.SID_btt_robToProgID.pressed.connect(self.reset_SC_id)

        # SINGLE COMMAND
        self.SGLC_btt_gcodeSglComm_addByID.pressed.connect(
            lambda: self.add_gcode_sgl(
                at_id=True,
                id=self.SGLC_num_gcodeSglComm_addByID.value()
            )
        )
        self.SGLC_btt_rapidSglComm_addByID.pressed.connect(
            lambda: self.add_rapid_sgl(
                at_id=True,
                id=self.SGLC_num_rapidSglComm_addByID.value()
            )
        )
        self.SGLC_btt_sendFirstQComm.pressed.connect(
            lambda: self.send_command(du.SCQueue.pop_first_item())
        )
        self.SGLC_btt_gcodeSglComm.pressed.connect(self.add_gcode_sgl)
        self.SGLC_btt_rapidSglComm.pressed.connect(self.add_rapid_sgl)

        # CONNECTIONS
        self.TCP_ROB_btt_reconn.pressed.connect(lambda: self.connect_tcp("ROB"))
        self.TCP_PUMP1_btt_reconn.pressed.connect(lambda: self.connect_tcp("P1"))
        self.TCP_PUMP2_btt_reconn.pressed.connect(lambda: self.connect_tcp("P2"))
        self.TCP_MIXER_btt_reconn.pressed.connect(lambda: self.connect_tcp("MIX"))
        self.TCP_ROB_btt_discon.pressed.connect(lambda: self.disconnect_tcp("ROB"))
        self.TCP_PUMP1_btt_discon.pressed.connect(lambda: self.disconnect_tcp("P1"))
        self.TCP_PUMP2_btt_discon.pressed.connect(lambda: self.disconnect_tcp("P2"))
        self.TCP_MIXER_btt_discon.pressed.connect(lambda: self.disconnect_tcp("MIX"))

        # TERMINAL
        self.TERM_btt_gcodeInterp.pressed.connect(self.send_gcode_command)
        self.TERM_btt_rapidInterp.pressed.connect(self.send_rapid_command)

        # ZERO
        self.ZERO_btt_newZero.pressed.connect(
            lambda: self.set_zero(axis=[1, 2, 3, 4, 5, 6, 8], from_sys_monitor=True)
        )


    def connect_short_signals(self) -> None:
        """create shortcuts and connect them to slots"""

        # CREATE SIGNALS
        self._ctrl_A = QShortcut("Ctrl+A", self)
        self._ctrl_E = QShortcut("Ctrl+E", self)
        self._ctrl_F = QShortcut("Ctrl+F", self)
        self._ctrl_I = QShortcut("Ctrl+I", self)
        self._ctrl_J = QShortcut("Ctrl+J", self)
        self._ctrl_K = QShortcut("Ctrl+K", self)
        self._ctrl_L = QShortcut("Ctrl+L", self)
        self._ctrl_M = QShortcut("Ctrl+M", self)
        self._ctrl_N = QShortcut("Ctrl+N", self)
        self._ctrl_O = QShortcut("Ctrl+O", self)
        self._ctrl_OE = QShortcut("Ctrl+Ö", self)
        self._ctrl_P = QShortcut("Ctrl+P", self)
        self._ctrl_Q = QShortcut("Ctrl+Q", self)
        self._ctrl_R = QShortcut("Ctrl+R", self)
        self._ctrl_alt_S = QShortcut("Ctrl+Alt+S", self)
        self._ctrl_T = QShortcut("Ctrl+T", self)
        self._ctrl_U = QShortcut("Ctrl+U", self)
        self._ctrl_Raute = QShortcut("Ctrl+#", self)
        self._ctrl_alt_I = QShortcut("Ctrl+Alt+I", self)

        # SCRIPT CONTROL
        self._ctrl_alt_S.activated.connect(self.start_SCTRL_queue)
        self._ctrl_A.activated.connect(lambda: self.stop_SCTRL_queue(prep_end=True))
        self._ctrl_F.activated.connect(lambda: self.send_command(du.SCQueue.pop_first_item()))
        self._ctrl_Raute.activated.connect(lambda: self.clr_queue(partial=False))
        self._ctrl_Q.activated.connect(self.forced_stop_command)
        self._ctrl_alt_I.activated.connect(self.reset_SC_id)

        # DIRECT CONTROL
        self._ctrl_U.activated.connect(lambda: self.send_DC_command("X", "+"))
        self._ctrl_J.activated.connect(lambda: self.send_DC_command("X", "-"))
        self._ctrl_I.activated.connect(lambda: self.send_DC_command("Y", "+"))
        self._ctrl_K.activated.connect(lambda: self.send_DC_command("Y", "-"))
        self._ctrl_O.activated.connect(lambda: self.send_DC_command("Z", "+"))
        self._ctrl_L.activated.connect(lambda: self.send_DC_command("Z", "-"))
        self._ctrl_P.activated.connect(lambda: self.send_DC_command("EXT", "+"))
        self._ctrl_OE.activated.connect(lambda: self.send_DC_command("EXT", "-"))

        # NUMERIC CONTROL
        self._ctrl_T.activated.connect(self.values_to_DC_spinbox)

        # FILE IO
        self._ctrl_N.activated.connect(self.open_file)
        self._ctrl_M.activated.connect(self.load_file)

        # PUMP CONTROL
        self._ctrl_E.activated.connect(lambda: self.pump_set_speed("0"))
        self._ctrl_R.activated.connect(lambda: self.pump_set_speed("-1"))


    ##########################################################################
    #                             CONNECTIONS                                #
    ##########################################################################

    def connect_tcp(self, slot='') -> bool:
        """slot-wise connection management, mostly to shrink code length,
        maybe more functionality later
        """

        def action_on_success(
                wd:Watchdog,
                indi:object,
                elem_group:list,
                log_txt=''
        ) -> None:
            wd.start()
            self.log_entry('CONN', log_txt)
            css = "border-radius: 25px; background-color: #00aaff;"
            indi.setStyleSheet(css)
            for elem in elem_group:
                elem.setEnabled(True)

        # ROBOT CONNECTION
        def rob_connect() -> bool:
            ip = du.ROBTcp.ip
            port = du.ROBTcp.port
            res = du.ROBTcp.connect()

            if isinstance(res, tuple):
                # if successful, start threading and watchdog
                if not self._RoboCommThread.isRunning():
                    # restart if necessary; if so reconnect threads
                    self.connect_threads(slot)
                    self._RoboCommThread.start()

                action_on_success(
                    self._RobRecvWd,
                    self.TCP_ROB_indi_connected,
                    self.ROB_group,
                    f"connected to {ip} at {port}.",
                )
                return True
            
            else:
                log_txt = f"failed to connect {ip}:{port} ({res})!"
                self.log_entry('CONN', log_txt)
                return False
        
        # PUMP CONNECTION
        def pmp_connect(
                serial:MtecMod,
                port:str,
                wd:Watchdog,
                indi,
                elem_group:list
        ) -> bool:
            if not 'COM' in port:
                raise ConnectionError("TCP not supported, yet")
            
            else:
                if fu.connect_pump(slot):
                    if not self._PumpCommThread.isRunning():
                        # restart if necessary; if so reconnect threads
                        self.connect_threads('PMP')
                        self._PumpCommThread.start()

                    self._P1RecvWd.start()
                    action_on_success(
                        wd,
                        indi,
                        elem_group,
                        f"connected to {slot} as inverter "
                        f"{serial.settings_inverter_id} at {port}",
                    )
                    return True

                else:
                    self.log_entry('CONN', f"connection to {slot} failed!")
                    return False
        
        # MIXER CONNECTION
        def mix_connect() -> bool:
            # mixer running as a http server for now, just ping to see
            # if the microcontroller is running
            ip = du.DEF_TCP_MIXER['IP']
            port = du.DEF_TCP_MIXER['PORT']
            ping_url = f"http://{ip}:{port}/ping"
            ping_resp = requests.get(ping_url)

            # if request is valid, consider it "connected"
            if ping_resp.ok and ping_resp.text == 'ack':
                GlobalMutex.lock()
                du.MIX_connected = True
                GlobalMutex.unlock()
                if not self._PumpCommThread.isRunning():
                    # restart if necessary; if so reconnect threads
                    self.connect_threads('PMP')
                    self._PumpCommThread.start()

                action_on_success(
                    self._MixRecvWd,
                    self.TCP_MIXER_indi_connected,
                    self.MIX_group,
                    f"mixer controller found at {ip}:{port}",
                )
                return True

            else:
                log_txt = f"mixer controller not present at {ip}:{port}!"
                self.log_entry('CONN', log_txt)
                return False
        
        # FUNCTION CALLS
        match slot:
            case 'ROB':
                return rob_connect()
            case 'P1':
                return pmp_connect(
                    du.PMP1Serial,
                    du.PMP1Tcp.port,
                    self._P1RecvWd,
                    self.TCP_PUMP1_indi_connected,
                    self.PMP1_group
                )
            case 'P2':
                return pmp_connect(
                    du.PMP2Serial,
                    du.PMP2Tcp.port,
                    self._P2RecvWd,
                    self.TCP_PUMP2_indi_connected,
                    self.PMP2_group
                )
            case 'MIX':
                return mix_connect()                    
            case _:
                return False


    def disconnect_tcp(self, slot='', internal_call=False) -> None:
        """disconnect works, reconnect crashes the app, problem probably lies
        here should also send E command to robot on disconnect
        """

        if internal_call:
            log_txt = "internal call to disconnect" 
        else:
            log_txt = "user disconnected"

        def safe_reset_positions() -> None:
            self.log_entry('SAFE', f"Last robot positions:")
            self.log_entry('SAFE', f"zero: {du.DCCurrZero}")
            self.log_entry('SAFE', f"curr: {du.ROBTelem.Coor}")
            self.log_entry('SAFE', f"rel: {du.ROBTelem.Coor - du.DCCurrZero}")
            self.log_entry('SAFE', f"last active ID was: {du.ROBTelem.id}")
            GlobalMutex.lock()
            du.ROBCommQueue.clear()
            du.ROB_send_list.clear()
            GlobalMutex.unlock()
            self.switch_rob_moving(end=True)

        def action_on_success(wd:Watchdog, indi:object, elem_group:list) -> None:
            wd.kill()
            self.log_entry('CONN', f"{log_txt} {slot}.")
            css = "border-radius: 25px; background-color: #4c4a48;"
            indi.setStyleSheet(css)
            for elem in elem_group:
                elem.setEnabled(False)
        
        # ROBOT DISCONNECT
        def rob_disconnect() -> None:
            if not du.ROBTcp.connected:
                return
            
            # send stop command to robot; stop threading & watchdog
            du.ROBTcp.send(du.QEntry(id=du.SC_curr_comm_id, mt="E"))
            action_on_success(
                self._RobRecvWd,
                self.TCP_ROB_indi_connected,
                self.ROB_group
            )
            self._RoboCommThread.quit()
            du.ROBTcp.close()

            # safe data & wait for thread:
            safe_reset_positions()
            self._RoboCommThread.wait()

        # PUMP DISCONNECT
        def pmp_disconnect(
                serial:MtecMod,
                port:str,
                wd:Watchdog,
                indi,
                elem_group:list
        ) -> None:
            if not serial.connected:
                return
            if not 'COM' in port:
                raise ConnectionError("TCP not supported yet")
            while du.PMP_comm_active: # finish communication first
                time.sleep(0.005)

            action_on_success(wd, indi, elem_group)
            serial.disconnect()
        
        # MIXER DISCONNECT
        def mix_disconnect() -> None:
            if not du.MIX_connected:
                return
            
            # no need to inform the server, just switch global toggle
            GlobalMutex.lock()
            du.MIX_connected = False
            GlobalMutex.unlock()
            action_on_success(
                self._MixRecvWd,
                self.TCP_MIXER_indi_connected,
                self.MIX_group
            )

        # FUNCTION CALLS
        match slot:
            case 'ROB':
                rob_disconnect()
            case 'P1':
                pmp_disconnect(
                    du.PMP1Serial,
                    du.PMP1Tcp.port,
                    self._P1RecvWd,
                    self.TCP_PUMP1_indi_connected,
                    self.PMP1_group
                )
            case 'P2':
                pmp_disconnect(
                    du.PMP2Serial,
                    du.PMP2Tcp.port,
                    self._P2RecvWd,
                    self.TCP_PUMP2_indi_connected,
                    self.PMP2_group
                )
            case 'MIX':
                mix_disconnect()
            case _:
                pass


    ##########################################################################
    #                               THREADS                                  #
    ##########################################################################

    def connect_threads(self, slot='') -> None:
        """load threads from PRINT_threads and set signal-slot-connections,
        this needs to be done for all thread during __init__, but you can call
        individual connectors via 'slot' as one needs to reconnect all signals
        if the Thread is restarted (after TCP/COM reconnects)
        """

        def rob_thread_connector():
            # thread for communication with robotic arms
            self.log_entry('THRT', 'initializing RoboComm thread..')
            self._RoboCommWorker = workers.RoboCommWorker()
            self._RoboCommWorker.moveToThread(self._RoboCommThread)
            self._RoboCommThread.started.connect(self._RoboCommWorker.run)
            self._RoboCommThread.finished.connect(self._RoboCommWorker.stop)
            self._RoboCommThread.finished.connect(self._RoboCommWorker.deleteLater)
            self._RoboCommWorker.logEntry.connect(self.log_entry)
            self._RoboCommWorker.sendElem.connect(self.robo_send)
            self._RoboCommWorker.dataUpdated.connect(self.robo_recv)
            self._RoboCommWorker.endProcessing.connect(self.stop_SCTRL_queue)
            self._RoboCommWorker.dataReceived.connect(self._RobRecvWd.reset)
            self._RoboCommWorker.dataReceived.connect(self.label_update_on_terminal_change)
            self._RoboCommWorker.endDcMoving.connect(lambda: self.switch_rob_moving(end=True))
            self._RoboCommWorker.queueEmtpy.connect(lambda: self.stop_SCTRL_queue(prep_end=True))
        
        def pmp_thread_connector():
            # thread for communication with pumps & inline mixer
            self.log_entry('THRT', 'initializing PumpComm thread..')
            self._PumpCommWorker = workers.PumpCommWorker()
            self._PumpCommWorker.moveToThread(self._PumpCommThread)
            self._PumpCommThread.started.connect(self._PumpCommWorker.run)
            self._PumpCommThread.finished.connect(self._PumpCommWorker.stop)
            self._PumpCommThread.finished.connect(self._PumpCommWorker.deleteLater)
            self._PumpCommWorker.logEntry.connect(self.log_entry)
            self._PumpCommWorker.dataSend.connect(self.pump_send)
            self._PumpCommWorker.dataRecv.connect(self.pump_recv)
            self._PumpCommWorker.dataMixerSend.connect(self.mixer_send)
            self._PumpCommWorker.dataMixerRecv.connect(self.mixer_recv)
            self._PumpCommWorker.p1Active.connect(self._P1RecvWd.reset)
            self._PumpCommWorker.p2Active.connect(self._P2RecvWd.reset)
        
        def other_threads_connector():
            # thread for file loading
            self.log_entry('THRT', 'initializing LoadFile thread..')
            self._LoadFileWorker = workers.LoadFileWorker()
            self._LoadFileWorker.moveToThread(self._LoadFileThread)
            self._LoadFileThread.started.connect(self._LoadFileWorker.run)
            self._LoadFileThread.destroyed.connect(self._LoadFileWorker.deleteLater)
            self._LoadFileWorker.convFailed.connect(self.load_file_failed)
            self._LoadFileWorker.convFinished.connect(self.load_file_finished)

            # thread for communication with sensor array
            self.log_entry('THRT', 'initializing SensorComm thread..')
            self._SensorArrWorker = workers.SensorCommWorker()
            self._SensorArrWorker.moveToThread(self._SensorArrThread)
            self._SensorArrThread.started.connect(self._SensorArrWorker.run)
            self._SensorArrThread.finished.connect(self._SensorArrWorker.stop)
            self._SensorArrThread.destroyed.connect(self._SensorArrWorker.deleteLater)
            self._SensorArrWorker.dataReceived.connect(self.Daq.data_update)
            self._SensorArrWorker.logEntry.connect(self.log_entry)

        # the actual function input is processed here
        match slot:
            case 'ROB':
                rob_thread_connector()
            case 'PMP':
                pmp_thread_connector()
            case 'OTHER':
                other_threads_connector()
            case 'ALL':
                rob_thread_connector()
                pmp_thread_connector()
                other_threads_connector()
            case _:
                raise KeyError(f"Thread to activate not specified: ({slot})")


    ##########################################################################
    #                               WATCHDOGS                                #
    ##########################################################################

    def connect_watchdogs(self):
        """connect all signals, the same for every WD"""

        for wd in self.WD_group:
            wd.logEntry.connect(self.log_entry)
            wd.criticalBite.connect(self.forced_stop_command)
            wd.criticalBite.connect(self.stop_SCTRL_queue)
            wd.disconnectDevice.connect(self.disconnect_tcp)
            wd.closeMainframe.connect(self.close)


    ##########################################################################
    #                               FILE IO                                  #
    ##########################################################################

    def open_file(self, testrun=False, testpath=None) -> None:
        """prompts the user with a file dialog and estimates printing
        parameters in given file
        """

        # get file path and content
        if testrun:
            file_path = testpath
        else:
            f_dialog = file_dialog("select file to load")
            f_dialog.exec()
            file_path = (
                Path(f_dialog.selectedFiles()[0])
                if (f_dialog.result())
                else None
            )

        if not isinstance(file_path, Path):
            self.IO_disp_filename.setText("no file selected")
            du.IO_curr_filepath = None
            return
        file = open(file_path, "r")
        txt = file.read()
        file.close()

        # get number of commands and filament length
        if file_path.suffix == ".mod":
            comm_num, filament_length, res = fu.pre_check_rapid_file(txt)
        else:
            comm_num, filament_length, res = fu.pre_check_gcode_file(txt)

        if isinstance(comm_num, Exception):
            self.IO_disp_filename.setText("COULD NOT READ FILE!")
            self.log_entry(
                "F-IO",
                f"Error while opening {file_path} file: {comm_num}"
            )
            du.IO_curr_filepath = None
            return

        if res == "empty":
            self.IO_disp_filename.setText("FILE EMPTY!")
            return

        # display data
        filament_vol = round(filament_length * du.SC_vol_per_m, 1)
        self.IO_disp_filename.setText(file_path.name)
        self.IO_disp_commNum.setText(str(comm_num))
        self.IO_disp_estimLen.setText(str(filament_length))
        self.IO_disp_estimVol.setText(str(filament_vol))

        self.log_entry(
            "F-IO",
            (
                f"Opened new file at {file_path}:   {comm_num} commands,   "
                f"{filament_length}m filament, {filament_vol}L"
            ),
        )
        du.IO_curr_filepath = file_path


    def load_file(self, lf_at_id=False, testrun=False) -> None:
        """reads the file set in self.openFile, adds all readable commands to
        command queue (at end or at ID) outsourced to loadFileWorker"""

        if workers.lfw_running:
            return

        # get user input
        start_id = self.IO_num_addByID.value() if (lf_at_id) else 0
        ext_trail = self.IO_chk_externalFllwBhvr.isChecked()
        p_ctrl = self.IO_chk_autoPCtrl.isChecked()
        fpath = du.IO_curr_filepath

        if fpath is None or not (
                fpath.suffix == ".gcode" or fpath.suffix == ".mod"
        ):
            self.IO_lbl_loadFile.setText("... no valid file, not executed")
            return

        self.IO_lbl_loadFile.setText("... conversion running ...")
        self.log_entry(
            "F-IO",
            (
                f"started to load file from {fpath}, task passed to "
                f"loadFileThread..."
            ),
        )

        # set up THREADS vars and start
        GlobalMutex.lock()
        workers.lfw_file_path = fpath
        workers.lfw_line_id = start_id
        workers.lfw_ext_trail = ext_trail
        workers.lfw_p_ctrl = p_ctrl
        GlobalMutex.unlock()

        if not testrun:
            self._LoadFileThread.start()
            self.IO_btt_loadFile.setStyleSheet(
                "font-size: 16pt; background-color: #a28230;"
            )


    def load_file_failed(self, txt:str) -> None:
        """handles convFailed emit from loadFileWorker"""

        self.IO_lbl_loadFile.setText(txt)
        self.log_entry("F-IO", f"ERROR: file IO from aborted! {txt}")

        # reset THREADS vars and exit
        GlobalMutex.lock()
        workers.lfw_file_path = None
        workers.lfw_line_id = 0
        workers.lfw_p_ctrl = False
        GlobalMutex.unlock()

        self.IO_btt_loadFile.setStyleSheet("font-size: 16pt;")
        self._LoadFileThread.exit()


    def load_file_finished(
            self,
            line_id:int,
            start_id:int,
            skips:int
    ) -> None:
        """handles convFinished emit from loadFileWorker"""

        # update labels, log entry if you made it here
        self.label_update_on_queue_change()
        self.label_update_on_new_zero()
        self.IO_num_addByID.setValue(line_id)

        if skips == 0:
            self.IO_lbl_loadFile.setText("... conversion successful")
        else:
            self.IO_lbl_loadFile.setText(
                f"... {skips} command(s) skipped (syntax)"
            )

        log_text = (
            f"File loading finished:   {line_id - start_id} commands added "
            f"({skips} skipped due to syntax),"
        )
        if start_id != 0:
            log_text += f" starting fom {start_id}."
        else:
            log_text += f" at the end."
        self.log_entry("F-IO", log_text)

        # reset THREADS vars and exit
        GlobalMutex.lock()
        workers.lfw_file_path = None
        workers.lfw_line_id = 0
        workers.lfw_p_ctrl = False
        GlobalMutex.unlock()

        self.IO_btt_loadFile.setStyleSheet("font-size: 16pt;")
        self._LoadFileThread.exit()



    ##########################################################################
    #                             COMMAND QUEUE                              #
    ##########################################################################

    def add_gcode_sgl(
            self,
            at_id=False,
            id=0,
            from_file=False,
            file_txt=''
    ) -> (
        tuple[du.QEntry | None | ValueError, str]
    ):
        """function meant to convert any single gcode lines to QEntry,
        uses the position BEFORE PLANNED COMMAND EXECUTION, as this is the
        fallback option if no X, Y, Z or EXT position is given
        """

        # get text and position BEFORE PLANNED COMMAND EXECUTION
        Speed = copy.deepcopy(du.PRINSpeed)

        try:
            if not at_id:
                Pos = copy.deepcopy(du.SCQueue.last_entry().Coor1)
            else:
                Pos = copy.deepcopy(du.SCQueue.entry_before_id(id).Coor1)

        except AttributeError:
            Pos = du.DCCurrZero

        if not from_file:
            txt = self.SGLC_entry_gcodeSglComm.toPlainText()
        else:
            txt = file_txt

        # act according to GCode command
        Entry, command = fu.gcode_to_qentry(Pos, Speed, du.IO_zone, txt)

        if command != "G1" and command != "G28" and command != "G92":
            if command == ";":
                pan_txt = f"leading semicolon interpreted as comment:\n{txt}"

            elif Entry is None:
                pan_txt = f"SYNTAX ERROR:\n{txt}"

            else:
                if not from_file:
                    self.SGLC_entry_gcodeSglComm.setText(f"{command}\n{txt}")
                return Entry, command

            if not from_file:
                self.SGLC_entry_gcodeSglComm.setText(pan_txt)
            return Entry, command

        elif command == "G92":
            self.label_update_on_new_zero()
            return Entry, command

        # set command ID if given, sorting is done later by "Queue" class
        if at_id:
            Entry.id = id

        GlobalMutex.lock()
        res = du.SCQueue.add(Entry)
        GlobalMutex.unlock()

        if res == ValueError:
            if not from_file:
                self.SGLC_entry_gcodeSglComm.setText(f"VALUE ERROR: \n {txt}")
            return ValueError, ''

        if not from_file:
            self.log_entry(
                "ComQ",
                f"single GCode command added -- "
                f"ID: {Entry.id}  MT: {Entry.mt}  PT: {Entry.pt}"
                f"  --  COOR_1: {Entry.Coor1}  --  COOR_2: {Entry.Coor2}"
                f"  --  SV: {Entry.Speed}  --  SBT: {Entry.sbt}"
                f"  SC: {Entry.sc}  --  Z: {Entry.z}"
                f"  --  TOOL: {Entry.Tool}",
            )

        self.label_update_on_queue_change()
        return Entry, command


    def add_rapid_sgl(
            self,
            at_id=False,
            id=0,
            from_file=False,
            file_txt=''
    ) -> du.QEntry | None | Exception:
        """function meant to convert all RAPID single lines into QEntry"""

        # get text and current position, (identify command -- to be added)
        if not from_file:
            txt = self.SGLC_entry_rapidSglComm.toPlainText()
        else:
            txt = file_txt

        Entry = fu.rapid_to_qentry(txt)

        if Entry is None:
            if not from_file:
                self.SGLC_entry_rapidSglComm.setText(
                    f"ERROR: no detectable move-type "
                    f"or missing 'EXT:' in:\n {txt}"
                )
            return Entry
        
        if isinstance(Entry, Exception):
            if not from_file:
                self.SGLC_entry_rapidSglComm.setText(
                    f"SYNTAX ERROR: {Entry}\n {txt}"
                )
            return Entry

        # set command ID if given, sorting is done later by "Queue" class
        if at_id:
            Entry.id = id

        GlobalMutex.lock()
        res = du.SCQueue.add(Entry)
        GlobalMutex.unlock()

        if res == ValueError:
            if not from_file:
                self.SGLC_entry_rapidSglComm.setText(f"VALUE ERROR: \n {txt}")
            return ValueError

        if not from_file:
            self.log_entry(
                "ComQ",
                f"single RAPID command added -- "
                f"ID: {Entry.id}  MT: {Entry.mt}  PT: {Entry.pt}"
                f"  --  COOR_1: {Entry.Coor1}  --  COOR_2: {Entry.Coor2}"
                f"  --  SV: {Entry.Speed}  --  SBT: {Entry.sbt}   SC: {Entry.sc}"
                f"  --  Z: {Entry.z}  --  TOOL: {Entry.Tool}",
            )

        # update displays
        self.label_update_on_queue_change()
        return Entry


    def add_SIB(self, num:int, at_end=False) -> bool:
        """add standard instruction block (SIB) to queue"""

        num -= 1
        sib_entry = [
            self.SIB_entry_sib1,
            self.SIB_entry_sib2,
            self.SIB_entry_sib3,
        ]
        txt = sib_entry[num].toPlainText()

        if (len(du.SCQueue) == 0) or not at_end:
            try:
                line_id = du.SCQueue[0].id
            except AttributeError:
                line_id = du.ROBTelem.id + 1
    
        else:
            line_id = du.SCQueue.last_entry().id + 1

        if line_id < 1: line_id = 1
        line_id_start = line_id
        rows = txt.split('\n')

        # interpret rows as either RAPID or GCode, row-wise, handling the
        # entry is unnessecary as its added to queue by the addRapidSgl /
        # addGcodeSgl funcions already
        for row in rows:
            if "Move" in row:
                Entry = self.add_rapid_sgl(
                    at_id=True, id=line_id, from_file=True, file_txt=row
                )

                if not isinstance(Entry, du.QEntry):
                    sib_entry[num].setText(f"COMMAND ERROR, ABORTED\n {txt}")
                    self.log_entry(
                        f"SIB{num + 1}",
                        (
                            f"ERROR: SIB command import aborted ({Entry})! "
                            f"false entry: {txt}"
                        ),
                    )
                    return False
                else:
                    line_id += 1

            else:
                Entry, command = self.add_gcode_sgl(
                    at_id=True, id=line_id, from_file=True, file_txt=row
                )

                if (command == "G1") or (command == "G28"):
                    line_id += 1
                else:
                    sib_entry[num].setText(f"COMMAND ERROR, ABORTED\n {txt}")
                    self.log_entry(
                        f"SIB{num + 1}",
                        (
                            f"ERROR: SIB command import aborted ({command})! "
                            f"false entry: {txt}"
                        ),
                    )
                    return False

        log_txt = f"{line_id - line_id_start} SIB lines added"
        if at_end:
            log_txt += " at end of queue"
        else:
            log_txt += " in front of queue"
        self.log_entry(f"SIB{num + 1}", log_txt)
        return True


    ##########################################################################
    #                               DC COMMANDS                              #
    ##########################################################################

    def home_command(self) -> None:
        """sets up a command to drive back to DC_curr_zero, gives it to the
        actual sendCommand function
        """

        if du.DC_rob_moving:
            return None
        self.switch_rob_moving()

        read_mt = self.DC_drpd_moveType.currentText()
        mt = "L" if (read_mt == "LINEAR") else "J"

        Command = du.QEntry(
            id=du.SC_curr_comm_id,
            mt=mt,
            Coor1=copy.deepcopy(du.DCCurrZero),
            Speed=copy.deepcopy(du.DCSpeed),
            z=0,
        )

        self.log_entry("DCom", "sending DC home command...")
        return self.send_command(Command, dc=True)


    def send_DC_command(self, axis:str, dir:str) -> None:
        """sets up a command accourding to the DC frames input, gives it to
        the actual sendCommand function
        """

        if du.DC_rob_moving:
            return None
        self.switch_rob_moving()

        step_width = self.DC_sld_stepWidth.value()
        step_width = int(10 ** (step_width - 1)) # 1->1, 2->10, 3->100

        if dir != '+' and dir != '-':
            raise ValueError
        if dir == '-':
            step_width = -step_width

        NewPos = copy.deepcopy(du.ROBTelem.Coor)
        match axis:
            case "X":
                NewPos.x += step_width
            case "Y":
                NewPos.y += step_width
            case "Z":
                NewPos.z += step_width
            case "EXT":
                NewPos.ext += step_width
            case _:
                raise ValueError(f"unknown axis {axis}!")

        read_mt = self.DC_drpd_moveType.currentText()
        mt = "L" if (read_mt == "LINEAR") else "J"
        Command = du.QEntry(
            id=du.SC_curr_comm_id,
            mt=mt,
            Coor1=NewPos,
            Speed=copy.deepcopy(du.DCSpeed),
            z=0,
        )

        self.log_entry("DCom", f"sending DC command: ({Command})")
        return self.send_command(Command, dc=True)


    def send_NC_command(self, axis:list) -> None:
        """sets up a command according to NC absolute positioning, gives it
        to the actual sendCommand function
        """

        if du.DC_rob_moving or not isinstance(axis, list):
            return None
        self.switch_rob_moving()

        NewPos = copy.deepcopy(du.ROBTelem.Coor)

        # 7 is a placeholder for Q, which can not be set by hand
        if 1 in axis:
            NewPos.x = float(self.NC_float_x.value())
        if 2 in axis:
            NewPos.y = float(self.NC_float_y.value())
        if 3 in axis:
            NewPos.z = float(self.NC_float_z.value())
        if 4 in axis:
            NewPos.rx = float(self.NC_float_xOrient.value())
        if 5 in axis:
            NewPos.ry = float(self.NC_float_yOrient.value())
        if 6 in axis:
            NewPos.rz = float(self.NC_float_zOrient.value())
        if 8 in axis:
            NewPos.ext = float(self.NC_float_ext.value())

        read_mt = self.DC_drpd_moveType.currentText()
        mt = "L" if (read_mt == "LINEAR") else "J"
        Command = du.QEntry(
            id=du.SC_curr_comm_id,
            mt=mt,
            Coor1=NewPos,
            Speed=copy.deepcopy(du.DCSpeed),
            z=0,
        )

        self.log_entry("DCom", f"sending NC command: ({NewPos})")
        return self.send_command(Command, dc=True)


    def send_gcode_command(self) -> None:
        """send the GCode interpreter line on the TERM panel to robot,
        uses the current position as it is executed directly, otherwise
        DONT do that if no X, Y, Z or EXT position is given
        """

        if du.DC_rob_moving:
            return None
        self.switch_rob_moving()

        # get text
        Speed = copy.deepcopy(du.DCSpeed)
        Pos = copy.deepcopy(du.ROBTelem.Coor)
        txt = self.TERM_entry_gcodeInterp.text()

        # act according to GCode command
        Entry, command = fu.gcode_to_qentry(Pos, Speed, du.IO_zone, txt)

        if command == "G92":
            self.label_update_on_new_zero()

        elif command != "G1" and command != "G28":
            if command == ";":
                pan_txt = f"leading semicolon interpreted as comment:\n{txt}"
            elif Entry is None:
                pan_txt = f"SYNTAX ERROR:\n{txt}"
            else:
                pan_txt = f"{command}\n{txt}"

            self.TERM_entry_gcodeInterp.setText(pan_txt)
            return None

        Entry.id = du.SC_curr_comm_id

        self.log_entry("DCom", f"sending GCode DC command: ({Entry})")
        return self.send_command(Entry, dc=True)


    def send_rapid_command(self) -> None:
        """send the GCode interpreter line on the TERM panel to robot,
        absolute coordinates or relative to "pHome" (DC_currZero)
        """

        if du.DC_rob_moving:
            return None
        self.switch_rob_moving()

        txt = self.TERM_entry_rapidInterp.text()
        Entry = fu.rapid_to_qentry(txt)

        if isinstance(Entry, Exception) or Entry is None:
            self.TERM_entry_rapidInterp.setText(f"SYNTAX ERROR: {Entry}\n" + txt)
            return None

        Entry.id = du.SC_curr_comm_id

        self.log_entry("DCom", f"sending RAPID DC command: ({Entry})")
        return self.send_command(Entry, dc=True)


    def forced_stop_command(self) -> None:
        """send immediate stop to robot (buffer will be lost, but added to
        the queue again), gives command  to the actual sendCommand function
        """

        Command = du.QEntry(id=1, mt="S")

        if self._testrun:
            return self.send_command(Command, dc=True)
        fs_warning = strd_dialog(
            f"WARNING!\n\nRobot will stop after current movement! "
            f"OK to delete buffered commands on robot, "
            f"Cancel to continue queue processing.",
            "FORCED STOP COMMIT",
        )
        fs_warning.exec()

        if fs_warning.result():
            self.stop_SCTRL_queue()
            du.ROBTcp.send(Command) # bypass all queued commands

            GlobalMutex.lock()
            LostBuf = copy.deepcopy(du.ROBCommQueue)
            for Entry in du.ROB_send_list:
                if Entry[0].mt != "S":
                    LostBuf.append(Entry[0])
            du.SC_curr_comm_id = du.ROBTelem.id
            du.SCQueue = LostBuf + du.SCQueue
            du.ROBCommQueue.clear()
            du.ROB_send_list.clear()
            GlobalMutex.unlock()

            self.label_update_on_queue_change()
            self.log_entry("SysC", f"FORCED STOP (user committed).")

        else:
            self.log_entry("SysC", f"user denied FS-Dialog, continuing...")


    def robot_stop_command(self, directly=True) -> None:
        """close connection signal for robot, add it to Queue or gives it to
        the actual sendCommand function
        """

        Command = du.QEntry(id=1, mt="E")

        if directly:
            self.log_entry("SysC", "sending robot stop command directly")
            if du.SC_q_processing:
                self.stop_SCTRL_queue()

            GlobalMutex.lock()
            du.ROB_send_list.clear()
            GlobalMutex.unlock()

            return self.send_command(Command, dc=True)

        else:
            Command.id = 0
            du.SCQueue.add(Command)
            self.log_entry("SysC", "added robot stop command to queue")
            return None


    ##########################################################################
    #                              SEND COMMANDS                             #
    ##########################################################################

    def send_command(self, command:du.QEntry, dc=False) -> None:
        """passing new commands to RoboCommWorker"""

        # error catching for fast-clicking users
        if len(du.ROB_send_list) != 0:
            LastCom, dummy = du.ROB_send_list[len(du.ROB_send_list) - 1]
            if command.id <= LastCom.id:
                command.id = LastCom.id + 1
        
        # pass command to sendList
        GlobalMutex.lock()
        du.ROB_send_list.append((command, dc))
        GlobalMutex.unlock()


    ##########################################################################
    #                              PUMP CONTROL                              #
    ##########################################################################

    def pump_set_speed(self, type="") -> None:
        """handle user inputs regarding pump frequency"""

        GlobalMutex.lock()
        match type:
            case "1":
                du.PMP_speed += 1
            case "-1":
                du.PMP_speed -= 1
            case "10":
                du.PMP_speed += 10
            case "-10":
                du.PMP_speed -= 10
            case "25":
                du.PMP_speed += 25
            case "-25":
                du.PMP_speed -= 25
            case "0":
                du.PMP_speed = 0
            case "r":
                du.PMP_speed *= -1
            case "c1":
                du.PMP1_live_ad = self.SCTRL_num_liveAd_pump1.value() / 100.0
            case "c2":
                du.PMP2_live_ad = self.SCTRL_num_liveAd_pump2.value() / 100.0
            case "s1":
                du.PMP1_user_speed = self.PUMP_num_setSpeedP1.value()
            case "s2":
                du.PMP2_user_speed = self.PUMP_num_setSpeedP2.value()
            case "def":
                if len(du.ROBCommQueue) != 0:
                    du.PMP_speed = PU_def_mode(du.ROBCommQueue[0])
                else:
                    userInfo = strd_dialog(
                        "No current command!",
                        "Action not possible"
                    )
                    userInfo.exec()

            case _:
                du.PMP_speed = self.PUMP_num_setSpeed.value()
        GlobalMutex.unlock()


    def pump_script_overwrite(self) -> None:
        """overwrites every command in SC_queue"""

        # windows vista dialog
        user_dialog = strd_dialog(
            f"You about to overwrite every command in SC_queue to contain the"
            f" 'pMode default' command, are you sure?",
            f"Overwrite warning",
        )
        user_dialog.exec()
        if user_dialog.result() == 0:
            return

        # overwrite
        GlobalMutex.lock()
        for i in range(len(du.SCQueue)):
            du.SCQueue[i].p_mode = 'default'
        GlobalMutex.unlock()
        return


    def pinch_valve_toggle(self) -> None:
        """not implemented yet"""

        usr_info = strd_dialog(
            'Pinch valve not supported, yet!', 'Process does not exist'
        )
        usr_info.exec()


    ##########################################################################
    #                              MIXER CONTROL                             #
    ##########################################################################

    def mixer_set_speed(self, type='') -> None:
        """handle user inputs for 2K mixer"""

        match type:
            case 'sld':
                speed = self.MIX_sld_speed.value()
            case '0':
                speed = 0
            case _:
                speed = self.MIX_num_setSpeed.value()

        self.mutex_setattr(du, 'MIX_speed', speed)


    ##########################################################################
    #                              AMCON CONTROL                             #
    ##########################################################################

    def adc_read_user_input(self, panel) -> du.ToolCommand:
        """short-hand to get user input"""

        group = self.ADC_group if (panel=='ADC') else self.ASC_group
        return du.ToolCommand(
            pnmtc_clamp_yn=self.group[0].isChecked(),
            knife_pos_yn=self.group[1].isChecked(),
            knife_yn=self.group[2].isChecked(),
            pnmtc_fiber_yn=self.group[3].isChecked(),
            pan_steps=self.group[4].value(),
            fib_deliv_steps=self.group[5].value(),
        )


    def adc_user_change(self) -> None:
        """send changes to Amcon, if user commit them"""

        if du.DC_rob_moving:
            return None

        Pos = copy.deepcopy(du.ROBTelem.Coor)
        Tool = self.adc_read_user_input('ADC')

        Command = du.QEntry(
            id=du.SC_curr_comm_id,
            Coor1=Pos,
            Speed=copy.deepcopy(du.DCSpeed),
            z=0,
            Tool=Tool,
        )

        self.log_entry('ACON', f"updating tool status by user: ({Tool})")
        return self.send_command(Command, dc=True)


    def amcon_script_overwrite(self) -> None:
        """override entire/partial SC queue with custom Amcon settings"""

        def overwrite(i:int, tool:du.ToolCommand) -> bool:
            try:
                j = du.SCQueue.id_pos(i + id_start)
            except AttributeError:
                return False

            du.SCQueue[j].Tool.pan_steps = tool.pan_steps
            du.SCQueue[j].Tool.fib_deliv_steps = tool.fib_deliv_steps
            du.SCQueue[j].Tool.pnmtc_clamp_yn= tool.pnmtc_clamp_yn
            du.SCQueue[j].Tool.knife_pos_yn = tool.knife_pos_yn
            du.SCQueue[j].Tool.knife_yn = tool.knife_yn
            du.SCQueue[j].Tool.pnmtc_fiber_yn = tool.pnmtc_fiber_yn
            return True


        id_range = self.ASC_entry_SCLines.text()
        SC_first = 1
        usr_txt = ''

        try:
            start = int(re.findall('\d+', id_range)[0])
            if start < SC_first:
                usr_txt = (
                    f"SC lines value is lower than lowest SC queue ID, "
                    f"nothing was done."
                )
        except IndexError:
            usr_txt = 'Invalid command in SC lines.'

        try:
            SC_first = du.SCQueue[0].id
        except AttributeError:
            usr_txt = 'SC queue contains no commands, nothing was done.'
        
        if usr_txt:
            user_info = strd_dialog(usr_txt, 'Command error')
            user_info.exec()
            return None

        Tool = self.adc_read_user_input('ASC')

        if ".." in id_range:
            ids = re.findall('\d+', id_range)
            if len(ids) != 2:
                user_info = strd_dialog(
                    'Worng syntax used in SC lines value, nothing was done.',
                    'Command error',
                )
                user_info.exec()
                return None
            id_start = int(ids[0])
            id_end = int(ids[1])

            GlobalMutex.lock()
            for i in range(id_end - id_start + 1):
                if not overwrite(i, Tool):
                    break
            GlobalMutex.unlock()

        else:
            ids = re.findall('\d+', id_range)
            if len(ids) != 1:
                user_info = strd_dialog(
                    'Worng syntax used in SC lines value, nothing was done.',
                    'Command error',
                )
                user_info.exec()
                return None
            id_start = int(ids[0])

            GlobalMutex.lock()
            overwrite(id_start, Tool)
            GlobalMutex.unlock()

        check_entry = du.SCQueue.id_pos(id_start)
        Tool = du.SCQueue[check_entry].Tool
        self.log_entry(
            'ACON',
            (
                f"{id_range} SC commands overwritten to new tool "
                f"settings: ({Tool})"
            ),
        )


    ##########################################################################
    #                              CLOSE UI                                  #
    ##########################################################################

    def closeEvent(self, event) -> None:
        """exit all threads and connections clean(ish)"""

        self.log_entry('newline')
        self.log_entry('GNRL', 'closeEvent signal.')
        self.log_entry('GNRL', 'cut connections...')

        # stop pump thread
        if self._PumpCommThread.isRunning():
            self._PumpCommThread.quit()
            self._PumpCommThread.wait()
        
        # stop sensor array
        if self._SensorArrThread.isRunning():
            self._SensorArrThread.quit()
            self._SensorArrThread.wait()

        # disconnect everything
        self.disconnect_tcp('ROB', internal_call=True)
        self.disconnect_tcp('P1', internal_call=True)
        self.disconnect_tcp('P2', internal_call=True)
        self.disconnect_tcp('MIX', internal_call=True)

        # delete threads
        self.log_entry('GNRL', 'stop threading...')
        self._RoboCommThread.deleteLater()
        self._PumpCommThread.deleteLater()
        self._LoadFileThread.deleteLater()

        # bye
        self.log_entry('GNRL', 'exiting GUI.')
        self.Daq.close()
        event.accept()



##################################   MAIN  ###################################

# only do the following if run as main program
if __name__ == '__main__':

    from libs.win_dialogs import strd_dialog
    import libs.data_utilities as du

    # import PyQT UIs (converted from .ui to .py)
    from ui.UI_mainframe_v6 import Ui_MainWindow

    logpath = fu.create_logfile()

    # overwrite ROB_tcpip for testing, delete later
    du.ROBTcp.ip = 'localhost'
    du.ROBTcp.port = 10001

    # start the UI and assign to app
    app = 0  # leave that here so app doesnt include the remnant of a previous QApplication instance
    win = 0
    app = QApplication(sys.argv)
    win = Mainframe(lpath=logpath)
    win.show()

    # start application (uses sys for CMD)
    app.exec()
    # sys.exit(app.exec())
