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
import time
import serial
import requests
from pathlib import Path
from copy import deepcopy as dcpy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# PyQt stuff
from PyQt5.QtCore import QMutexLocker
from PyQt5.QtWidgets import QApplication, QShortcut


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from libs.win_mainframe_prearrange import PreMainframe, Watchdog
from libs.win_mainframe_prearrange import GlobalMutex, PmpMutex


# import my own libs
from libs.win_dialogs import strd_dialog, file_dialog
from libs.pump_utilities import default_mode as PU_def_mode
import libs.threads as workers
import libs.global_var as g
import libs.data_utilities as du
import libs.func_utilities as fu

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod



########################## MAINFRAME CLASS ###################################
# to-do: 
# - ID after restart/reconnect to 1 (maybe do that on the robot side)
# - load saved ZERO
# - NC pos ID wrong? (check ROB.CommQueue for plausibility as well)
# - faster SIB

class Mainframe(PreMainframe):
    """main UI of PRINT_py (further details pending)"""

    ##########################################################################
    #                                ATTRIBUTES                              #
    ##########################################################################

    _first_pos = True  # one-time switch to get robot home position


    #########################################################################
    #                                  SETUP                                #
    #########################################################################

    def __init__(
            self,
            lpath=None,
            dev_avail=False,
            testrun=False,
            parent=None
        ) -> None:
        """setup main and daq UI, start subsystems & threads"""

        # getting all prearranged UI functions from PreMainframe
        super().__init__(lpath, testrun, parent)

        # LOAD THREADS, SIGNALS & DEFAULT SETTINGS
        self.log_entry('GNRL', 'connecting signals...')
        self.connect_main_signals()
        self.connect_short_signals()

        self.log_entry('GNRL', 'load default settings...')
        self.load_defaults(setup=True)
        self.set_zero([1,2,3,4,5,6,8], 'default')
        self.set_range()

        self.log_entry('GNRL', 'init threading...')
        if self._testrun:
            # TESTRUN OPTION WITH RETURN
            self.connect_threads('ALL')
            self.log_entry('TEST', 'testrun, skipping robot connection...')
            self.log_entry('GNRL', 'setup finished.')
            self.log_entry('newline')
            return
        self.connect_threads('CAM')
        self.connect_threads('OTHER')

        # INIT WATCHDOGS
        self.log_entry('GNRL', 'init watchdog...')
        self.connect_watchdogs()

        # CONNECTIONS SETUP
        self.init_connection_settings()
        self.log_entry('GNRL', f"connection setup is {bin(dev_avail)}")
        for bit, dev in [
            (4, 'ROB'),
            (3, 'P1'),
            (2, 'P2'),
            (1, 'PRH'),
        ]:
            if (dev_avail>>bit)&1:
                self.log_entry('GNRL', f"connect to {dev}...")
                self.connect_device(dev)

        # SENSOR & CAM ARRAY START-UP
        self._SensorArrThread.start()
        # self._IPCamThread.start()

        # FINISH SETUP
        self.log_entry('GNRL', 'setup finished.')
        self.log_entry('newline')


    def connect_main_signals(self) -> None:
        """create signal-slot-links for UI buttons"""

        # AMCON CONTROL
        self.ADC_btt_resetAll.pressed.connect(lambda: self.load_ADC_defaults(send_changes=True))
        for elem in self.ADC_group:
            try:
                elem.released.connect(self.adc_user_change)
            except AttributeError:
                elem.valueChanged.connect(self.adc_user_change)
        self.ASC_btt_overwrSC.released.connect(self.amcon_script_overwrite)

        # DIRECT CONTROL
        self.DC_btt_xPlus.pressed.connect(lambda: self.send_DC_command('X', '+'))
        self.DC_btt_xMinus.pressed.connect(lambda: self.send_DC_command('X', '-'))
        self.DC_btt_yPlus.pressed.connect(lambda: self.send_DC_command('Y', '+'))
        self.DC_btt_yMinus.pressed.connect(lambda: self.send_DC_command('Y', '-'))
        self.DC_btt_zPlus.pressed.connect(lambda: self.send_DC_command('Z', '+'))
        self.DC_btt_zMinus.pressed.connect(lambda: self.send_DC_command('Z', '-'))
        self.DC_btt_extPlus.pressed.connect(lambda: self.send_DC_command('EXT', '+'))
        self.DC_btt_extMinus.pressed.connect(lambda: self.send_DC_command('EXT', '-'))
        self.DC_btt_xyzZero.pressed.connect(lambda: self.set_zero([1, 2, 3]))
        self.DC_btt_extZero.pressed.connect(lambda: self.set_zero([8]))
        self.DC_btt_home.pressed.connect(self.home_command)

        # FILE IO
        self.IO_btt_newFile.pressed.connect(self.open_file)
        self.IO_btt_loadFile.pressed.connect(self.load_file)
        self.IO_btt_addByID.pressed.connect(lambda: self.load_file(lf_atID=True))
        self.IO_btt_xyzextZero.pressed.connect(lambda: self.set_zero([1, 2, 3, 8]))
        self.IO_btt_rZero.pressed.connect(lambda: self.set_zero([4, 5, 6]))

        # LOOK AHEAD
        self.LAH_btt_active.pressed.connect(lambda: self.mutex_setattr('pmp_look_ahead'))
        self.LAH_num_distance.valueChanged.connect(lambda: self.mutex_setattr('pmp_look_ahead_dist'))
        self.LAH_float_prerunFactor.valueChanged.connect(lambda: self.mutex_setattr('pmp_look_ahead_prerun'))
        self.LAH_float_retractFactor.valueChanged.connect(lambda: self.mutex_setattr('pmp_look_ahead_retract'))

        # MIXER CONTROL
        self.PRH_btt_actWithPump.pressed.connect(lambda: self.mutex_setattr('mixer_act_w_pump'))
        self.PRH_btt_pinchValve.pressed.connect(self.pinch_valve_toggle)
        self.PRH_btt_setSpeed.pressed.connect(self.mixer_set_speed)
        self.PRH_btt_stop.pressed.connect(lambda: self.mixer_set_speed('0'))
        self.PRH_sld_speed.sliderMoved.connect(lambda: self.mixer_set_speed('sld'))

        # NUMERIC CONTROL
        self.NC_btt_getValues.pressed.connect(self.values_to_DC_spinbox)
        self.NC_btt_xyzSend.pressed.connect(lambda: self.send_NC_command([1, 2, 3]))
        self.NC_btt_xyzextSend.pressed.connect(lambda: self.send_NC_command([1, 2, 3, 8]))
        self.NC_btt_rSend.pressed.connect(lambda: self.send_NC_command([4, 5, 6]))
        self.NC_btt_rZero.pressed.connect(lambda: self.set_zero([4, 5, 6]))

        # PUMP CONTROL
        self.PUMP_sld_outputRatio.sliderMoved.connect(lambda: self.mutex_setattr('pmp_out_ratio'))
        self.SCTRL_num_liveAd_pump1.valueChanged.connect(lambda: self.pump_set_speed('c1'))
        self.SCTRL_num_liveAd_pump2.valueChanged.connect(lambda: self.pump_set_speed('c2'))
        self.PUMP_btt_setSpeedP1.pressed.connect(lambda: self.pump_set_speed('s1'))
        self.PUMP_btt_setSpeedP2.pressed.connect(lambda: self.pump_set_speed('s2'))
        self.PUMP_btt_plus1.pressed.connect(lambda: self.pump_set_speed('1'))
        self.PUMP_btt_minus1.pressed.connect(lambda: self.pump_set_speed('-1'))
        self.PUMP_btt_plus10.pressed.connect(lambda: self.pump_set_speed('10'))
        self.PUMP_btt_minus10.pressed.connect(lambda: self.pump_set_speed('-10'))
        self.PUMP_btt_plus25.pressed.connect(lambda: self.pump_set_speed('25'))
        self.PUMP_btt_minus25.pressed.connect(lambda: self.pump_set_speed('-25'))
        self.PUMP_btt_stop.pressed.connect(lambda: self.pump_set_speed('0'))
        self.PUMP_btt_reverse.pressed.connect(lambda: self.pump_set_speed('r'))
        self.PUMP_btt_ccToDefault.pressed.connect(lambda: self.pump_set_speed('def'))
        self.PUMP_btt_setSpeed.pressed.connect(self.pump_set_speed)
        self.PUMP_btt_scToDefault.pressed.connect(self.pump_script_overwrite)

        # SCRIPT CONTROL
        self.SCTRL_num_liveAd_robot.valueChanged.connect(lambda: self.mutex_setattr('robot_live_ad'))
        self.SCTRL_btt_mmsOverwrite.pressed.connect(lambda: self.mutex_setattr('mms_overwrite'))
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
        self.CONN_num_commForerun.valueChanged.connect(lambda: self.mutex_setattr('robot_comm_fr'))
        self.SET_btt_apply.pressed.connect(self.apply_settings)
        self.SET_btt_default.pressed.connect(self.load_defaults)
        self.CHKR_btt_default.pressed.connect(self.set_range)
        self.CHKR_btt_overwrite.pressed.connect(lambda: self.set_range('user'))
        self.SID_btt_overwrite.pressed.connect(self.sc_id_overwrite)

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
            lambda: self.send_command(g.SCQueue.pop_first_item())
        )
        self.SGLC_btt_gcodeSglComm.pressed.connect(self.add_gcode_sgl)
        self.SGLC_btt_rapidSglComm.pressed.connect(self.add_rapid_sgl)

        # CONNECTIONS
        self.CONN_ROB_btt_reconn.pressed.connect(lambda: self.connect_device('ROB'))
        self.CONN_PUMP1_btt_reconn.pressed.connect(lambda: self.connect_device('P1'))
        self.CONN_PUMP2_btt_reconn.pressed.connect(lambda: self.connect_device('P2'))
        self.CONN_PRH_btt_reconn.pressed.connect(lambda: self.connect_device('PRH'))
        self.CONN_ROB_btt_discon.pressed.connect(lambda: self.disconnect_device('ROB'))
        self.CONN_PUMP1_btt_discon.pressed.connect(lambda: self.disconnect_device('P1'))
        self.CONN_PUMP2_btt_discon.pressed.connect(lambda: self.disconnect_device('P2'))
        self.CONN_PRH_btt_discon.pressed.connect(lambda: self.disconnect_device('PRH'))

        # TERMINAL
        self.TERM_btt_gcodeInterp.pressed.connect(self.send_gcode_command)
        self.TERM_btt_rapidInterp.pressed.connect(self.send_rapid_command)

        # ZERO
        self.ZERO_btt_newZero.pressed.connect(
            lambda: self.set_zero(axis=[1, 2, 3, 4, 5, 6, 8], source='user')
        )
        self.ZERO_btt_loadZeroFile.pressed.connect(
            lambda: self.set_zero(axis=[1, 2, 3, 4, 5, 6, 8], source='file')
        )
        self.ZERO_btt_loadDefault.pressed.connect(
            lambda: self.set_zero(axis=[1,2,3,4,5,6,8], source='default')
        )


    def connect_short_signals(self) -> None:
        """create shortcuts and connect them to slots"""

        # CREATE SIGNALS
        self._ctrl_A = QShortcut('Ctrl+A', self)
        self._ctrl_E = QShortcut('Ctrl+E', self)
        self._ctrl_F = QShortcut('Ctrl+F', self)
        self._ctrl_I = QShortcut('Ctrl+I', self)
        self._ctrl_J = QShortcut('Ctrl+J', self)
        self._ctrl_K = QShortcut('Ctrl+K', self)
        self._ctrl_L = QShortcut('Ctrl+L', self)
        self._ctrl_M = QShortcut('Ctrl+M', self)
        self._ctrl_N = QShortcut('Ctrl+N', self)
        self._ctrl_O = QShortcut('Ctrl+O', self)
        self._ctrl_OE = QShortcut('Ctrl+Ö', self)
        self._ctrl_P = QShortcut('Ctrl+P', self)
        self._ctrl_Q = QShortcut('Ctrl+Q', self)
        self._ctrl_R = QShortcut('Ctrl+R', self)
        self._ctrl_alt_S = QShortcut('Ctrl+Alt+S', self)
        self._ctrl_T = QShortcut('Ctrl+T', self)
        self._ctrl_U = QShortcut('Ctrl+U', self)
        self._ctrl_Raute = QShortcut('Ctrl+#', self)
        self._ctrl_alt_I = QShortcut('Ctrl+Alt+I', self)

        # SCRIPT CONTROL
        self._ctrl_alt_S.activated.connect(self.start_SCTRL_queue)
        self._ctrl_A.activated.connect(lambda: self.stop_SCTRL_queue(prep_end=True))
        self._ctrl_F.activated.connect(lambda: self.send_command(g.SCQueue.pop_first_item()))
        self._ctrl_Raute.activated.connect(lambda: self.clr_queue(partial=False))
        self._ctrl_Q.activated.connect(self.forced_stop_command)
        self._ctrl_alt_I.activated.connect(self.sc_id_overwrite)

        # DIRECT CONTROL
        self._ctrl_U.activated.connect(lambda: self.send_DC_command('X', '+'))
        self._ctrl_J.activated.connect(lambda: self.send_DC_command('X', '-'))
        self._ctrl_I.activated.connect(lambda: self.send_DC_command('Y', '+'))
        self._ctrl_K.activated.connect(lambda: self.send_DC_command('Y', '-'))
        self._ctrl_O.activated.connect(lambda: self.send_DC_command('Z', '+'))
        self._ctrl_L.activated.connect(lambda: self.send_DC_command('Z', '-'))
        self._ctrl_P.activated.connect(lambda: self.send_DC_command('EXT', '+'))
        self._ctrl_OE.activated.connect(lambda: self.send_DC_command('EXT', '-'))

        # NUMERIC CONTROL
        self._ctrl_T.activated.connect(self.values_to_DC_spinbox)

        # FILE IO
        self._ctrl_N.activated.connect(self.open_file)
        self._ctrl_M.activated.connect(self.load_file)

        # PUMP CONTROL
        self._ctrl_E.activated.connect(lambda: self.pump_set_speed('0'))
        self._ctrl_R.activated.connect(lambda: self.pump_set_speed('-1'))


    ##########################################################################
    #                             CONNECTIONS                                #
    ##########################################################################

    def connect_device(self, slot='') -> bool:
        """slot-wise connection management, mostly to shrink code length,
        maybe more functionality later
        """

        def _action_on_success(
                wd:Watchdog,
                indi:object,
                elem_group:list,
                log_txt=''
        ) -> None:
            wd.start()
            self.log_entry('CONN', log_txt)
            css = 'border-radius: 25px; background-color: #00aaff;'
            indi.setStyleSheet(css)
            for elem in elem_group:
                elem.setEnabled(True)

        # ROBOT CONNECTION
        def rob_connect() -> bool:
            ip = g.ROBTcp.ip
            port = g.ROBTcp.port
            res = g.ROBTcp.connect()

            if isinstance(res, tuple):
                # if successful, reset SC ID, update command ids
                with QMutexLocker(GlobalMutex):
                    g.SC_curr_comm_id = 1
                    for idx, entry in enumerate(g.SCQueue):
                        # reset all IDs to [1, 2, ..]
                        entry.id = idx + 1
                self.label_update_on_receive('Sucessful reconnect.')
                self.label_update_on_queue_change()
                # start threading and watchdog
                if not self._RoboCommThread.isRunning():
                    # restart if necessary; if so reconnect threads
                    self.connect_threads(slot)
                    self._RoboCommThread.start()

                _action_on_success(
                    self._RobRecvWd,
                    self.CONN_ROB_indi_connected,
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
                wd:Watchdog,
                indi,
                elem_group:list
        ) -> bool:
            if not 'COM' in g.PMP_port:
                raise ConnectionError('TCP not supported, yet')

            else:
                with QMutexLocker(PmpMutex):
                    result = fu.connect_pump(slot)
                if result:
                    if not self._PumpCommThread.isRunning():
                        # restart if necessary; if so reconnect threads
                        self.connect_threads('PMP')
                        self._PumpCommThread.start()

                    wd.start()
                    _action_on_success(
                        wd,
                        indi,
                        elem_group,
                        f"connected to {slot} as inverter "
                        f"{serial.settings_inverter_id} at {g.PMP_port}",
                    )
                    return True

                else:
                    self.log_entry('CONN', f"connection to {slot} failed!")
                    return False

        # PRINTHEAD CONNECTION
        def prh_connect() -> bool:
            # mixer running as a http server for now, just ping to see
            # if the microcontroller is running
            # if request is valid, consider it "connected"
            try:
                ping_resp = requests.get(f"{g.PRH_url}/ping", timeout=3)
                if not ping_resp.ok or ping_resp.text != 'ack':
                    raise ValueError
            except (requests.Timeout, ValueError) as err:
                log_txt = f"printhead controller not present at {g.PRH_url}!"
                self.log_entry('CONN', log_txt)
                print(log_txt)
                return False
            
            with QMutexLocker(GlobalMutex):
                g.PRH_connected = True
            if not self._PumpCommThread.isRunning():
                # restart if necessary; if so reconnect threads
                self.connect_threads('PMP')
                self._PumpCommThread.start()

            _action_on_success(
                self._PRHRecvWd,
                self.CONN_PRH_indi_connected,
                self.PRH_group,
                f"mixer controller found at {g.PRH_url}",
            )
            return True

        # FUNCTION CALLS
        match slot:
            case 'ROB':
                return rob_connect()
            case 'P1':
                return pmp_connect(
                    g.PMP1Serial,
                    self._P1RecvWd,
                    self.CONN_PUMP1_indi_connected,
                    self.PMP1_group
                )
            case 'P2':
                return pmp_connect(
                    g.PMP2Serial,
                    self._P2RecvWd,
                    self.CONN_PUMP2_indi_connected,
                    self.PMP2_group
                )
            case 'PRH':
                return prh_connect()                    
            case _:
                return False


    def disconnect_device(self, slot='', internal_call=False) -> None:
        """disconnect works, reconnect crashes the app, problem probably lies
        here should also send E command to robot on disconnect
        """

        if internal_call:
            log_txt = 'internal call to disconnect' 
        else:
            log_txt = 'user disconnected'

        # save current settings to file
        def _save_reset_positions() -> None:
            Zero = dcpy(g.ROBCurrZero)
            self.log_entry('SAFE', f"Last robot positions:")
            self.log_entry('SAFE', f"zero: {Zero}")
            self.log_entry('SAFE', f"curr: {g.ROBTelem.Coor}")
            self.log_entry('SAFE', f"rel: {g.ROBTelem.Coor - g.ROBCurrZero}")
            self.log_entry('SAFE', f"last active ID was: {g.ROBTelem.id}")
            with QMutexLocker(GlobalMutex):
                g.ROBCommQueue.clear()
                g.ROB_send_list.clear()
            self.switch_rob_moving(end=True)
            try:
                with open(g.CTRL_log_path, 'x') as save_file:
                    save_file.write(
                        f"{Zero.x}_{Zero.y}_{Zero.z}_{Zero.rx}_{Zero.ry}_"
                        f"{Zero.rz}_{Zero.q}_{Zero.ext}"
                    )
            except:
                pass

        # shut down watchdogs, log, indicate to user
        def _action_on_success(wd:Watchdog, indi:object, elem_group:list) -> None:
            wd.kill()
            self.log_entry('CONN', f"{log_txt} {slot}.")
            css = 'border-radius: 25px; background-color: #4c4a48;'
            indi.setStyleSheet(css)
            for elem in elem_group:
                elem.setEnabled(False)
        
        # ROBOT DISCONNECT
        def rob_disconnect() -> None:
            if not g.ROBTcp.connected:
                return

            # send stop command to robot; stop threading & watchdog
            g.ROBTcp.send(du.QEntry(id=g.SC_curr_comm_id, mt='E'))
            _action_on_success(
                self._RobRecvWd,
                self.CONN_ROB_indi_connected,
                self.ROB_group
            )
            self._RoboCommThread.quit()
            g.ROBTcp.close()

            # safe data & wait for thread:
            _save_reset_positions()
            self._RoboCommThread.wait()

        # PUMP DISCONNECT
        def pmp_disconnect(
                interface:MtecMod,
                wd:Watchdog,
                indi,
                elem_group:list
        ) -> None:
            if not interface.connected:
                return
            if not 'COM' in g.PMP_port:
                raise ConnectionError('TCP not supported yet')
            with QMutexLocker(PmpMutex):
                interface.stop()
                interface.disconnect()
                _action_on_success(wd, indi, elem_group)
            # close serial bus if both pumps are disconnect
            if not g.PMP1Serial.connected and not g.PMP2Serial.connected:
                if isinstance(g.PMPSerialDefBus, serial.Serial):
                    g.PMPSerialDefBus.close()
                    g.PMPSerialDefBus = None
        
        # PRH DISCONNECT
        def prh_disconnect() -> None:
            if not g.PRH_connected:
                return
            
            # no need to inform the server, just switch global toggle
            with QMutexLocker(GlobalMutex):
                g.PRH_connected = False
            _action_on_success(
                self._PRHRecvWd,
                self.CONN_PRH_indi_connected,
                self.PRH_group
            )

        # FUNCTION CALLS
        match slot:
            case 'ROB':
                rob_disconnect()
            case 'P1':
                pmp_disconnect(
                    g.PMP1Serial,
                    self._P1RecvWd,
                    self.CONN_PUMP1_indi_connected,
                    self.PMP1_group
                )
            case 'P2':
                pmp_disconnect(
                    g.PMP2Serial,
                    self._P2RecvWd,
                    self.CONN_PUMP2_indi_connected,
                    self.PMP2_group
                )
            case 'PRH':
                prh_disconnect()
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
            self._PumpCommWorker.dataMixerSend.connect(self.prh_send)
            self._PumpCommWorker.prhActive.connect(self._PRHRecvWd.reset)
            self._PumpCommWorker.p1Active.connect(self._P1RecvWd.reset)
            self._PumpCommWorker.p2Active.connect(self._P2RecvWd.reset)
        
        def cam_thread_connector():
            # thread for cam image capture
            self.log_entry('THRT', 'initializing IPCam thread..')
            self._IPCamWorker = workers.IPCamWorker()
            self._IPCamWorker.moveToThread(self._IPCamThread)
            self._IPCamThread.started.connect(self._IPCamWorker.run)
            self._IPCamThread.finished.connect(self._IPCamWorker.stop)
            self._IPCamThread.destroyed.connect(self._IPCamWorker.deleteLater)
            self._IPCamWorker.logEntry.connect(self.log_entry)
            self._IPCamWorker.imageCaptured.connect(self.CamCap.new_img)


        def other_threads_connector():
            # thread for file loading
            self.log_entry('THRT', 'initializing LoadFile thread..')
            self._LoadFileWorker = workers.LoadFileWorker()
            self._LoadFileWorker.moveToThread(self._LoadFileThread)
            self._LoadFileThread.started.connect(self._LoadFileWorker.run)
            self._LoadFileThread.destroyed.connect(self._LoadFileWorker.deleteLater)
            self._LoadFileWorker.convFailed.connect(self.load_file_failed)
            self._LoadFileWorker.convFinished.connect(self.load_file_finished)
            self._LoadFileWorker.rangeChkWarning.connect(self.load_file_range_warning)

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
            case 'CAM':
                cam_thread_connector()
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
            wd.criticalBite.connect(lambda: self.forced_stop_command(True))
            wd.disconnectDevice.connect(self.disconnect_device)
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
            f_dialog = file_dialog('select file to load')
            f_dialog.exec()
            file_path = (
                Path(f_dialog.selectedFiles()[0])
                if (f_dialog.result())
                else None
            )

        if not isinstance(file_path, Path):
            self.IO_disp_filename.setText('no file selected')
            g.IO_curr_filepath = None
            return
        with open(file_path, 'r') as file:
            txt = file.read()
        file.close()

        # get number of commands and filament length
        if file_path.suffix == '.mod':
            comm_num, skips, fil_length, res = fu.pre_check_rapid_file(txt)
        else:
            comm_num, skips, fil_length, res = fu.pre_check_gcode_file(txt)

        if isinstance(comm_num, Exception):
            self.IO_disp_filename.setText('UNREADABLE FILE!')
            self.log_entry(
                'F-IO',
                f"Error while opening {file_path} file: {comm_num}"
            )
            g.IO_curr_filepath = None
            return
        if res == 'empty':
            self.IO_disp_filename.setText('FILE EMPTY!')
            return

        # display data
        fil_vol = round(fil_length * g.SC_vol_per_m, 1)
        self.IO_disp_filename.setText(file_path.name)
        self.IO_disp_commNum.setText(f"{comm_num}")
        self.IO_disp_ignoredLines.setText(f"{skips}")
        self.IO_disp_estimLen.setText(f"{fil_length} m")
        self.IO_disp_estimVol.setText(f"{fil_vol} L")

        self.log_entry(
            'F-IO',
            (
                f"Opened new file at {file_path}:   {comm_num} commands, "
                f"{skips} lines skipted, {fil_length}m filament, {fil_vol}L"
            ),
        )
        g.IO_curr_filepath = file_path


    def load_file(self, lf_at_id=False, testrun=False) -> None:
        """reads the file set in self.openFile, adds all readable commands to
        command queue (at end or at ID) outsourced to loadFileWorker"""

        if workers.lfw_running:
            return

        # get user input
        start_id = self.IO_num_addByID.value() if (lf_at_id) else 0
        ext_trail = self.IO_chk_extTrailing.isChecked()
        p_ctrl = self.IO_chk_autoPCtrl.isChecked()
        range_chk = self.IO_chk_rangeChk.isChecked()
        xy_ext_chk = self.IO_chk_xyextChk.isChecked()
        fpath = g.IO_curr_filepath

        if fpath is None or not (
                fpath.suffix == '.gcode' or fpath.suffix == '.mod'
        ):
            self.IO_lbl_loadFile.setText('... no valid file, not executed')
            return

        self.IO_lbl_loadFile.setText('... conversion running ...')
        self.log_entry(
            'F-IO',
            (
                f"started to load file from {fpath}, task passed to "
                f"loadFileThread..."
            ),
        )

        # set up thread vars and start
        with QMutexLocker(GlobalMutex):
            workers.lfw_file_path = fpath
            workers.lfw_line_id = start_id
            workers.lfw_ext_trail = ext_trail
            workers.lfw_p_ctrl = p_ctrl
            workers.lfw_range_chk = range_chk
            workers.lfw_base_dist_chk = xy_ext_chk

        if not testrun:
            self._LoadFileThread.start()
            self.IO_btt_loadFile.setStyleSheet(
                'font-size: 16pt; background-color: #a28230;'
            )
    

    def load_file_range_warning(self, txt:str) -> None:
        """indicates range warning from loadFileWorker to user"""

        range_warn = strd_dialog(txt, 'Range Warning')
        range_warn.exec()


    def load_file_failed(self, txt:str) -> None:
        """handles convFailed emit from loadFileWorker"""

        self.IO_lbl_loadFile.setText(txt)
        self.log_entry('F-IO', f"ERROR: file IO from aborted! {txt}")

        # reset THREADS vars and exit
        with QMutexLocker(GlobalMutex):
            workers.lfw_file_path = None
            workers.lfw_line_id = 0
            workers.lfw_p_ctrl = False

        self.IO_btt_loadFile.setStyleSheet('font-size: 16pt;')
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
        self.SCTRL_disp_elemInQ.setText(str(len(g.SCQueue)))
        self.IO_num_addByID.setValue(line_id)
        self.IO_lbl_loadFile.setText('... conversion successful')

        log_text = (
            f"File loading finished:   {line_id - start_id} commands added "
            f"({skips} skipped due to syntax),"
        )
        if start_id != 0:
            log_text += f" starting fom {start_id}."
        else:
            log_text += f" at the end."
        self.log_entry('F-IO', log_text)

        # reset THREADS vars and exit
        with QMutexLocker(GlobalMutex):
            workers.lfw_file_path = None
            workers.lfw_line_id = 0
            workers.lfw_p_ctrl = False

        self.IO_btt_loadFile.setStyleSheet('font-size: 16pt;')
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
        try:
            if not at_id:
                LastEntry = dcpy(g.SCQueue.last_entry())
                if LastEntry is None:
                    raise AttributeError
                LastEntry.id = 0
            else:
                LastEntry = dcpy(g.SCQueue.entry_before_id(id))
        except AttributeError:
            LastEntry = du.QEntry(
                id=0,
                Coor1=g.ROBCurrZero,
                Speed=g.SCSpeed,
                z=g.IO_zone
            )

        if not from_file:
            txt = self.SGLC_entry_gcodeSglComm.toPlainText()
        else:
            txt = file_txt

        # act according to GCode command
        Entry, command = fu.gcode_to_qentry(LastEntry, txt, False)
        err_txt = ''
        if command != 'G1' and command != 'G28' and command != 'G92':
            if command == ';':
                err_txt = f"leading semicolon interpreted as comment:\n{txt}"
            elif Entry is None:
                err_txt = f"SYNTAX ERROR:\n{txt}"
            else:
                err_txt = f"{command}\n{txt}"
        elif command == 'G92':
            self.label_update_on_new_zero()
            return Entry, command

        if not self.coor_plausibility_check(Entry):
            err_txt = f"POSITION UNREACHABLE:\n{txt}"
        if err_txt != '':
            if not from_file:
                self.SGLC_entry_gcodeSglComm.setText(err_txt)
            return Entry, command

        # set command ID if given, sorting is done later by 'Queue' class
        if at_id:
            Entry.id = id
        with QMutexLocker(GlobalMutex):
            res = g.SCQueue.add(Entry, g.SC_curr_comm_id)
        if res == ValueError:
            if not from_file:
                self.SGLC_entry_gcodeSglComm.setText(f"VALUE ERROR: \n {txt}")
            return ValueError, ''
        if not from_file:
            self.log_entry(
                'ComQ',
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
        err_txt = ''
        if Entry is None:
            err_txt = (
                f"ERROR: no detectable move-type "
                f"or missing 'EXT' in:\n{txt}"
            )
        if isinstance(Entry, Exception):
            err_txt = f"SYNTAX ERROR: {Entry}\n{txt}"
        if not self.coor_plausibility_check(Entry):
            err_txt = f"COORDINATE ERROR:\n {txt}"
        if err_txt != '':
            if not from_file:
                self.SGLC_entry_rapidSglComm.setText(err_txt)
            return Entry
        
        # set command ID if given, sorting is done later by 'Queue' class
        if at_id:
            Entry.id = id
        with QMutexLocker(GlobalMutex):
            res = g.SCQueue.add(Entry, g.SC_curr_comm_id)
        if res == ValueError:
            if not from_file:
                self.SGLC_entry_rapidSglComm.setText(f"VALUE ERROR: \n {txt}")
            return ValueError

        if not from_file:
            self.log_entry(
                'ComQ',
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

        if (len(g.SCQueue) == 0) or not at_end:
            try:
                line_id = g.SCQueue[0].id
            except AttributeError:
                line_id = g.ROBTelem.id + 1
        else:
            line_id = g.SCQueue.last_entry().id + 1

        if line_id < 1: line_id = 1
        line_id_start = line_id
        rows = txt.split('\n')

        # interpret rows as either RAPID or GCode, row-wise, handling the
        # entry is unnessecary as its added to queue by the addRapidSgl /
        # addGcodeSgl funcions already
        for row in rows:
            if 'Move' in row:
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

                if (command == 'G1') or (command == 'G28'):
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
            log_txt += ' at end of queue'
        else:
            log_txt += ' in front of queue'
        self.log_entry(f"SIB{num + 1}", log_txt)
        return True


    ##########################################################################
    #                               DC COMMANDS                              #
    ##########################################################################

    def coor_plausibility_check(self, entry:du.QEntry) -> bool:
        """checking for a direct command if the coordinates are reachable
        (in theory)"""
        # to-do: check for implausibile coor combinations

        def raise_warn(msg):
            msg += (
                f"\n\nOK\t--> drive to location anyways"
                f"\nCancel\t--> stay at current location"
            )
            imp_warning = strd_dialog(msg, 'IMPLAUSIBILE TARGET')
            imp_warning.exec()
            return imp_warning.result()

        if self._testrun:
            return True
        res, msg = fu.range_check(entry)
        if not res:
            return raise_warn(msg)
        res, msg = fu.base_dist_check(entry)
        if not res:
            return raise_warn(msg)
        return True



    def home_command(self) -> None:
        """sets up a command to drive back to DC_curr_zero, gives it to the
        actual sendCommand function
        """

        if g.DC_rob_moving:
            return None

        read_mt = self.DC_drpd_moveType.currentText()
        mt = 'L' if (read_mt == 'LINEAR') else 'J'
        Command = du.QEntry(
            id=g.SC_curr_comm_id,
            mt=mt,
            Coor1=dcpy(g.ROBCurrZero),
            Speed=dcpy(g.DCSpeed),
            z=0,
        )

        if not self.coor_plausibility_check(Command):
            return
        self.send_command(Command, dc=True)
        self.switch_rob_moving()
        self.log_entry('DCom', 'sending DC home command...')


    def send_DC_command(self, axis:str, dir:str) -> None:
        """sets up a command accourding to the DC frames input, gives it to
        the actual sendCommand function
        """

        if g.DC_rob_moving:
            return None

        NewPos = dcpy(g.ROBTelem.Coor)
        step_width = self.DC_sld_stepWidth.value()
        step_width = int(10 ** (step_width - 1)) # 1->1, 2->10, 3->100
        match dir:
            case '+':
                pass
            case '-':
                step_width = -step_width
            case _:
                raise ValueError
        match axis:
            case 'X':
                NewPos.x += step_width
            case 'Y':
                NewPos.y += step_width
            case 'Z':
                NewPos.z += step_width
            case 'EXT':
                NewPos.ext += step_width
            case _:
                raise ValueError(f"unknown axis {axis}!")

        read_mt = self.DC_drpd_moveType.currentText()
        mt = 'L' if (read_mt == 'LINEAR') else 'J'
        Command = du.QEntry(
            id=g.SC_curr_comm_id,
            mt=mt,
            Coor1=NewPos,
            Speed=dcpy(g.DCSpeed),
            z=0,
        )

        if not self.coor_plausibility_check(Command):
            return
        self.send_command(Command, dc=True)
        self.switch_rob_moving()
        self.log_entry('DCom', f"sending DC command: ({Command})")


    def send_NC_command(self, axis:list) -> None:
        """sets up a command according to NC absolute positioning, gives it
        to the actual sendCommand function
        """

        if g.DC_rob_moving or not isinstance(axis, list):
            return None

        NewPos = dcpy(g.ROBTelem.Coor)
        if 1 in axis:
            NewPos.x = float(self.NC_float_x.value())
        if 2 in axis:
            NewPos.y = float(self.NC_float_y.value())
        if 3 in axis:
            NewPos.z = float(self.NC_float_z.value())
        if 4 in axis:
            NewPos.rx = float(self.NC_float_rx.value())
        if 5 in axis:
            NewPos.ry = float(self.NC_float_ry.value())
        if 6 in axis:
            NewPos.rz = float(self.NC_float_rz.value())
        # 7 is a placeholder for Q, which can not be set by hand
        if 8 in axis:
            NewPos.ext = float(self.NC_float_ext.value())

        read_mt = self.DC_drpd_moveType.currentText()
        mt = 'L' if (read_mt == 'LINEAR') else 'J'
        Command = du.QEntry(
            id=g.SC_curr_comm_id,
            mt=mt,
            Coor1=NewPos,
            Speed=dcpy(g.DCSpeed),
            z=0,
        )

        if not self.coor_plausibility_check(Command):
            return
        self.send_command(Command, dc=True)
        self.switch_rob_moving()
        self.log_entry('DCom', f"sending NC command: ({NewPos})")


    def send_gcode_command(self) -> None:
        """send the GCode interpreter line on the TERM panel to robot,
        uses the current position as it is executed directly, otherwise
        DONT do that if no X, Y, Z or EXT position is given
        """

        if g.DC_rob_moving:
            return None

        # get entry
        CurrEntry = du.QEntry(
            id=g.SC_curr_comm_id,
            Coor1=dcpy(g.ROBTelem.Coor),
            Speed=dcpy(g.DCSpeed),
            z=g.IO_zone,
        )
        txt = self.TERM_entry_gcodeInterp.text()
        Command, com_type = fu.gcode_to_qentry(CurrEntry, txt, False)

        # check for special command types
        if com_type == 'G92':
            self.label_update_on_new_zero()
        elif com_type != 'G1' and com_type != 'G28':
            if com_type == ';':
                pan_txt = f"leading semicolon interpreted as comment:\n{txt}"
            elif Command is None:
                pan_txt = f"SYNTAX ERROR:\n{txt}"
            else:
                pan_txt = f"{com_type}\n{txt}"
            self.TERM_entry_gcodeInterp.setText(pan_txt)
            return None

        # send if standard G1 or G28 command
        if not self.coor_plausibility_check(Command):
            return
        self.send_command(Command, dc=True)
        self.switch_rob_moving()
        self.log_entry('DCom', f"sending GCode DC command: ({Command})")


    def send_rapid_command(self) -> None:
        """send the GCode interpreter line on the TERM panel to robot,
        absolute coordinates or relative to 'pHome' (DC_currZero)
        """

        if g.DC_rob_moving:
            return None

        # get entry
        txt = self.TERM_entry_rapidInterp.text()
        Command = fu.rapid_to_qentry(txt)
        if isinstance(Command, Exception) or Command is None:
            self.TERM_entry_rapidInterp.setText(f"SYNTAX ERROR: {Command}\n" + txt)
            return None

        # send if valid
        Command.id = g.SC_curr_comm_id
        if not self.coor_plausibility_check(Command):
            return
        self.send_command(Command, dc=True)
        self.switch_rob_moving()
        self.log_entry('DCom', f"sending RAPID DC command: ({Command})")


    def forced_stop_command(self, no_dialog=False) -> None:
        """send immediate stop to robot (buffer will be lost, but added to
        the queue again), gives command  to the actual sendCommand function
        """

        res = True
        if not no_dialog:
            Command = du.QEntry(id=1, mt='S')
            if self._testrun:
                return self.send_command(Command, dc=True)
            fs_warning = strd_dialog(
                f"WARNING!\n\nRobot will stop after current movement! "
                f"OK to delete buffered commands on robot, "
                f"Cancel to continue queue processing.",
                'FORCED STOP COMMIT',
            )
            fs_warning.exec()
            res = fs_warning.result()

        if res or no_dialog:
            self.stop_SCTRL_queue()
            g.ROBTcp.send(Command) # bypass all queued commands
            self.pump_set_speed('0')
            self.pinch_valve_toggle(internal=True, val=0)

            # retrieve lost commands, clr buffer lists
            with QMutexLocker(GlobalMutex):
                LostBuf = dcpy(g.ROBCommQueue)
                for Entry in g.ROB_send_list:
                    if Entry[0].mt != 'S':
                        LostBuf.append(Entry[0])
                g.SC_curr_comm_id = g.ROBTelem.id
                g.SCQueue = LostBuf + g.SCQueue
                g.ROBCommQueue.clear()
                g.ROB_send_list.clear()

            self.sc_id_overwrite(internal=True)
            self.log_entry('SysC', f"FORCED STOP (user committed).")
        else:
            self.log_entry('SysC', f"user denied FS-Dialog, continuing...")


    def robot_stop_command(self, directly=True) -> None:
        """close connection signal for robot, add it to Queue or gives it to
        the actual sendCommand function
        """

        Command = du.QEntry(id=1, mt='E')
        if directly:
            self.log_entry('SysC', "sending robot stop command directly")
            if g.SC_q_processing:
                self.stop_SCTRL_queue()
            with QMutexLocker(GlobalMutex):
                g.ROB_send_list.clear()
            return self.send_command(Command, dc=True)
        else:
            Command.id = 0
            g.SCQueue.add(Command, g.SC_curr_comm_id)
            self.log_entry('SysC', 'added robot stop command to queue')
            return None


    ##########################################################################
    #                              SEND COMMANDS                             #
    ##########################################################################

    def send_command(self, command:du.QEntry, dc=False) -> None:
        """passing new commands to RoboCommWorker"""

        # error catching for fast-clicking users
        if len(g.ROB_send_list) != 0:
            LastCom,_ = g.ROB_send_list[len(g.ROB_send_list) - 1]
            if command.id <= LastCom.id:
                command.id = LastCom.id + 1
        
        # error catching for previous function returns
        if isinstance(command, Exception):
            print(f"Command generation failed, caused by {command}")
            return
        
        # pass command to sendList
        with QMutexLocker(GlobalMutex):
            g.ROB_send_list.append((command, dc))


    ##########################################################################
    #                              PUMP CONTROL                              #
    ##########################################################################

    def pump_set_speed(self, flag='') -> None:
        """handle user inputs regarding pump frequency"""

        with QMutexLocker(GlobalMutex):
            match flag:
                case '1':
                    g.PMP_speed += 1
                case '-1':
                    g.PMP_speed -= 1
                case '10':
                    g.PMP_speed += 10
                case '-10':
                    g.PMP_speed -= 10
                case '25':
                    g.PMP_speed += 25
                case '-25':
                    g.PMP_speed -= 25
                case '0':
                    g.PMP_speed = 0
                case 'r':
                    g.PMP_speed *= -1
                case 'c1':
                    g.PMP1_live_ad = (
                        self.SCTRL_num_liveAd_pump1.value() / 100.0
                    )
                case 'c2':
                    g.PMP2_live_ad = (
                        self.SCTRL_num_liveAd_pump2.value() / 100.0
                    )
                case 's1':
                    g.PMP1_user_speed = self.PUMP_num_setSpeedP1.value()
                case 's2':
                    g.PMP2_user_speed = self.PUMP_num_setSpeedP2.value()
                case 'def':
                    if len(g.ROBCommQueue) != 0:
                        g.PMP_speed = PU_def_mode(g.ROBCommQueue[0])
                    else:
                        userInfo = strd_dialog(
                            'No current command!',
                            'Action not possible'
                        )
                        userInfo.exec()

                case _:
                    g.PMP_speed = self.PUMP_num_setSpeed.value()


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
        with QMutexLocker(GlobalMutex):
            for i in range(len(g.SCQueue)):
                g.SCQueue[i].p_mode = 'default'
        return


    def pinch_valve_toggle(self, internal=False, val=0.0) -> None:
        """no docstring yet"""

        if not g.PRH_connected:
            return
        if not internal:
            pinch_state = int(not self.PRH_btt_pinchValve.isChecked())
        else:
            pinch_state = val
        try:
            requests.post(f"{g.PRH_url}/pinch", data={'s': pinch_state}, timeout=1)
        except requests.Timeout as e:
            log_txt = f"post to pinch valve failed! {g.PRH_url} not present!"
            self.log_entry('CONN', log_txt)
            print(log_txt)


    ##########################################################################
    #                              MIXER CONTROL                             #
    ##########################################################################

    def mixer_set_speed(self, type='') -> None:
        """handle user inputs for 2K mixer"""

        match type:
            case 'sld':
                speed = float(self.PRH_sld_speed.value())
            case '0':
                speed = 0.0
            case _:
                speed = float(self.PRH_num_setSpeed.value())

        with QMutexLocker(GlobalMutex):
            g.MIX_speed = speed


    ##########################################################################
    #                              AMCON CONTROL                             #
    ##########################################################################

    def prh_read_user_input(self, panel) -> du.ToolCommand:
        """short-hand to get user input"""
        
        RetTool = du.ToolCommand()
        group = self.ADC_group if (panel=='ADC') else self.ASC_group
        RetTool.trolley_steps = group[0].value()
        RetTool.clamp = bool(group[1].isChecked())
        RetTool.cut = bool(group[2].isChecked())
        RetTool.place_spring = bool(group[3].isChecked())
        RetTool.load_spring = bool(group[4].isChecked())
        if panel == 'ADC':
            if self.ADC_btt_calibrate.isChecked():
                RetTool.trolley_calibrate = g.PRH_TROLL_CALIBRATE
            else:
                RetTool.trolley_calibrate = 0
        return RetTool


    def adc_user_change(self) -> None:
        """send changes to Amcon, if user commits them"""

        if g.DC_rob_moving:
            return None

        Pos = dcpy(g.ROBTelem.Coor)
        Tool = self.prh_read_user_input('ADC')
        Command = du.QEntry(
            id=g.SC_curr_comm_id,
            Coor1=Pos,
            Speed=dcpy(g.DCSpeed),
            z=0,
            Tool=Tool,
        )

        self.log_entry('ACON', f"updating tool status by user: ({Tool})")
        ans = self.send_command(Command, dc=True)
        return ans
            


    def amcon_script_overwrite(self) -> None:
        """override entire/partial SC queue with custom Amcon settings"""

        def overwrite(i:int, tool:du.ToolCommand) -> bool:
            try:
                j = g.SCQueue.id_pos(i + id_start)
            except AttributeError:
                return False
            g.SCQueue[j].Tool.trolley_steps = tool.trolley_steps
            g.SCQueue[j].Tool.clamp = tool.clamp
            g.SCQueue[j].Tool.cut = tool.cut
            g.SCQueue[j].Tool.place_spring = tool.place_spring
            return True


        id_range = self.ASC_entry_SCLines.text()
        SC_first = 1
        usr_txt = ''

        try:
            start = int(re.findall(r'\d+', id_range)[0])
            if start < SC_first:
                usr_txt = (
                    f"SC lines value is lower than lowest SC queue ID, "
                    f"nothing was done."
                )
        except IndexError:
            usr_txt = 'Invalid command in SC lines.'

        try:
            SC_first = g.SCQueue[0].id
        except AttributeError:
            usr_txt = 'SC queue contains no commands, nothing was done.'

        if usr_txt:
            user_info = strd_dialog(usr_txt, 'Command error')
            user_info.exec()
            return None

        Tool = self.prh_read_user_input('ASC')
        if '..' in id_range:
            ids = re.findall(r'\d+', id_range)
            if len(ids) != 2:
                user_info = strd_dialog(
                    'Worng syntax used in SC lines value, nothing was done.',
                    'Command error',
                )
                user_info.exec()
                return None
            id_start = int(ids[0])
            id_end = int(ids[1])

            with QMutexLocker(GlobalMutex):
                for i in range(id_end - id_start + 1):
                    if not overwrite(i, Tool):
                        break

        else:
            ids = re.findall(r'\d+', id_range)
            if len(ids) != 1:
                user_info = strd_dialog(
                    'Worng syntax used in SC lines value, nothing was done.',
                    'Command error',
                )
                user_info.exec()
                return None
            id_start = int(ids[0])

            with QMutexLocker(GlobalMutex):
                overwrite(0, Tool)
            id_range = id_start

        check_entry = g.SCQueue.id_pos(id_start)
        Tool = g.SCQueue[check_entry].Tool
        self.log_entry(
            'ACON',
            f"{id_range} SC commands overwritten; settings: ({Tool})"
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
        
        # stop IP cams
        if self._IPCamThread.isRunning():
            self._IPCamThread.quit()
            self._IPCamThread.wait()

        # disconnect everything
        self.disconnect_device('ROB', internal_call=True)
        self.disconnect_device('P1', internal_call=True)
        self.disconnect_device('P2', internal_call=True)
        self.disconnect_device('PRH', internal_call=True)

        # delete threads
        self.log_entry('GNRL', 'stop threading...')
        self._RoboCommThread.deleteLater()
        self._PumpCommThread.deleteLater()
        self._LoadFileThread.deleteLater()

        # bye
        self.log_entry('GNRL', 'exiting GUI.')
        self.Daq.close()
        self.CamCap.close()
        event.accept()



##################################   MAIN  ###################################

# only do the following if run as main program
if __name__ == '__main__':

    from libs.win_dialogs import strd_dialog
    import libs.data_utilities as du

    # import PyQT UIs (converted from .ui to .py)
    from ui.UI_mainframe_v6 import Ui_MainWindow

    logpath = fu.create_logfile()
    g.PRH_url = f"http://{g.PRH_url}"

    # overwrite ROB_tcpip for testing, delete later
    g.ROBTcp.ip = 'localhost'
    g.ROBTcp.port = 10001

    # start the UI and assign to app
    app = 0  # leave that here so app doesnt include the remnant of a previous QApplication instance
    win = 0
    app = QApplication(sys.argv)
    win = Mainframe(lpath=logpath)
    win.show()

    # start application (uses sys for CMD)
    app.exec()
    # sys.exit(app.exec())
