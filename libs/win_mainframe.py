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
from pathlib import Path
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# PyQt stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QTimer, QMutex, QThread
from PyQt5.QtWidgets import QApplication, QMainWindow, QShortcut


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_mainframe_v6 import Ui_MainWindow


# import my own libs
from libs.win_daq import daq_window
from libs.win_dialogs import strd_dialog, file_dialog
from libs.pump_utilities import default_mode as PU_def_mode
import libs.threads as workers
import libs.data_utilities as du
import libs.func_utilities as fu

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod



####################### MAINFRAME CLASS  #####################################

class Mainframe(QMainWindow, Ui_MainWindow):
    """main UI of PRINT_py (further details pending)"""

    ##########################################################################
    #                                ATTRIBUTES                              #
    ##########################################################################

    logpath = ""  # reference for logEntry, set by __init__

    _testrun = False  # switch for mainframe_test.py
    _first_pos = True  # one-time switch to get robot home position

    _last_comm_id = 0
    _LastP1Telem = None
    _LastP2Telem = None

    _RoboCommWorker = None
    _PumpCommWorker = None
    _LoadFileWorker = None
    _SensorArrWorker = None
    
    _RobRecvWd = None
    _P1RecvWd = None
    _P2RecvWd = None
    _MixRecvWd = None


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

        super().__init__(parent)

        # UI SETUP
        self.setupUi(self)
        self.setWindowTitle('---   PRINT_py  -  Main Window  ---')
        self.setWindowFlags(
            Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        self.group_gui_elems()
        self._testrun = testrun

        # LOGFILE SETUP
        if lpath is None:
            log_txt = (
                f"No path for logfile!\n\n"
                f"Press OK to continue anyways or Cancel to exit the program."
            )
            log_warning = strd_dialog(log_txt, 'LOGFILE ERROR')
            log_warning.exec()

            if log_warning.result() == 0:
                # suicide after the actual .exec is finished,
                # exit without chrash
                print('no logpath given, user choose to exit after setup...')
                QTimer.singleShot(0, self.close)
            else:
                print('no logpath given, user chose to continue without...')
        else:
            self.logpath = lpath
            self.log_entry('GNRL', 'main GUI running.')

        # DAQ SETUP
        self.Daq = daq_window()
        self.Daq.logEntry.connect(self.log_entry)
        if not testrun:
            self.Daq.show()
        self.log_entry('GNRL', 'DAQ GUI running.')

        # LOAD THREADS, SIGNALS & DEFAULT SETTINGS
        self.log_entry('GNRL', 'connecting signals...')
        self.connect_main_signals()
        self.connect_short_signals()

        self.log_entry('GNRL', 'load default settings...')
        self.load_defaults(setup=True)

        self.log_entry('GNRL', 'init threading...')
        self._RoboCommThread = QThread()
        self._LoadFileThread = QThread()
        self._PumpCommThread = QThread()
        self._SensorArrThread = QThread()
        self.connect_threads('OTHER')

        # TESTRUN OPTION
        if testrun:
            self.log_entry('TEST', 'testrun, skipping robot connection...')
            self.log_entry('GNRL', 'setup finished.')
            self.log_entry('newline')
            return

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
        self._ctrl_S = QShortcut("Ctrl+S", self)
        self._ctrl_T = QShortcut("Ctrl+T", self)
        self._ctrl_U = QShortcut("Ctrl+U", self)
        self._ctrl_Raute = QShortcut("Ctrl+#", self)
        self._ctrl_alt_I = QShortcut("Ctrl+Alt+I", self)

        # SCRIPT CONTROL
        self._ctrl_S.activated.connect(self.start_SCTRL_queue)
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
    

    def group_gui_elems(self) -> None:
        """build groups for enable/disable actions"""

        self.ADC_group = self.ADC_frame.findChildren(
            (QtWidgets.QPushButton, QtWidgets.QSpinBox)
        )

        self.ASC_group = self.ASC_frame.findChildren(
            (QtWidgets.QPushButton, QtWidgets.QSpinBox)
        )

        self.DC_group = [
            self.DC_btt_xPlus,
            self.DC_btt_xMinus,
            self.DC_btt_yPlus,
            self.DC_btt_yMinus,
            self.DC_btt_zPlus,
            self.DC_btt_zMinus,
            self.DC_btt_extPlus,
            self.DC_btt_extMinus,
            self.DC_btt_home,
            self.DC_lbl_x,
            self.DC_lbl_y,
            self.DC_lbl_z,
            self.DC_lbl_ext,
        ]

        self.NC_group = [
            self.NC_btt_xyzSend,
            self.NC_btt_xyzExtSend,
            self.NC_btt_orientSend,
        ]

        self.PMP1_group = [
            self.PUMP_num_setSpeedP1,
            self.PUMP_btt_setSpeedP1,
            self.PUMP_disp_freqP1,
            self.PUMP_disp_voltP1,
            self.PUMP_disp_ampsP1,
            self.PUMP_disp_torqP1,
        ]
        for elem in self.PMP1_group:
            elem.setEnabled(False)

        self.PMP2_group = [
            self.PUMP_num_setSpeedP2,
            self.PUMP_btt_setSpeedP2,
            self.PUMP_disp_freqP2,
            self.PUMP_disp_voltP2,
            self.PUMP_disp_ampsP2,
            self.PUMP_disp_torqP2,
        ]
        for elem in self.PMP2_group:
            elem.setEnabled(False)

        self.ROB_group = [
            self.SGLC_btt_sendFirstQComm,
            self.SCTRL_btt_startQProcessing,
            self.SCTRL_btt_holdQProcessing,
            self.SCTRL_btt_forcedStop,
            self.TERM_btt_gcodeInterp,
            self.TERM_btt_rapidInterp,
            self.ADC_btt_clamp,
            self.ADC_btt_knifePos,
            self.ADC_btt_knife,
            self.ADC_btt_fiberPnmtc,
            self.ADC_num_panning,
            self.ADC_num_fibDeliv,
        ]
        self.ROB_group += self.DC_group
        self.ROB_group += self.NC_group
        for elem in self.ROB_group:
            elem.setEnabled(False)

        self.TERM_group = self.TERM_btt_gcodeInterp, self.TERM_btt_rapidInterp


    def load_defaults(self, setup=False) -> None:
        """load default general settings to user display"""

        self.SET_float_volPerMM.setValue(du.DEF_SC_VOL_PER_M)
        self.SET_float_frToMms.setValue(du.DEF_IO_FR_TO_TS)
        self.SET_num_zone.setValue(du.DEF_IO_ZONE)
        self.SET_num_transSpeed_dc.setValue(du.DEF_DC_SPEED.ts)
        self.SET_num_orientSpeed_dc.setValue(du.DEF_DC_SPEED.ors)
        self.SET_num_accelRamp_dc.setValue(du.DEF_DC_SPEED.acr)
        self.SET_num_decelRamp_dc.setValue(du.DEF_DC_SPEED.dcr)
        self.SET_num_transSpeed_print.setValue(du.DEF_PRIN_SPEED.ts)
        self.SET_num_orientSpeed_print.setValue(du.DEF_PRIN_SPEED.ors)
        self.SET_num_accelRamp_print.setValue(du.DEF_PRIN_SPEED.acr)
        self.SET_num_decelRamp_print.setValue(du.DEF_PRIN_SPEED.dcr)

        if not setup:
            self.log_entry(
                "SETS", "User resetted general properties to default values."
            )
        else:
            self.load_TE_defaults(setup=True)
            self.TCP_num_commForerun.setValue(du.DEF_ROB_COMM_FR)

            self.load_ADC_defaults()
            self.ASC_num_panning.setValue(du.DEF_AMC_PANNING)
            self.ASC_num_fibDeliv.setValue(du.DEF_AMC_FIB_DELIV)
            self.ASC_btt_clamp.setChecked(du.DEF_AMC_CLAMP)
            self.ASC_btt_knifePos.setChecked(du.DEF_AMC_KNIFE_POS)
            self.ASC_btt_knife.setChecked(du.DEF_AMC_KNIFE)
            self.ASC_btt_fiberPnmtc.setChecked(du.DEF_AMC_FIBER_PNMTC)


    def load_TE_defaults(self, setup=False) -> None:
        """load default Tool/External settings to user display"""

        self.SET_TE_num_fllwBhvrInterv.setValue(du.DEF_SC_EXT_FLLW_BHVR[0])
        self.SET_TE_num_fllwBhvrSkip.setValue(du.DEF_SC_EXT_FLLW_BHVR[1])
        self.SET_TE_float_p1VolFlow.setValue(du.DEF_PUMP_LPS)
        self.SET_TE_float_p2VolFlow.setValue(du.DEF_PUMP_LPS)
        self.SET_TE_num_retractSpeed.setValue(int(du.DEF_PUMP_RETR_SPEED))

        if not setup:
            self.log_entry("SETS", "User resetted TE properties to default values.")


    def load_ADC_defaults(self, send_changes=False) -> None:
        """load ADC default values"""

        # stop UI changes to retrigger themselfs
        for widget in self.ADC_group:
            widget.blockSignals(True)

        self.ADC_num_panning.setValue(du.DEF_AMC_PANNING)
        self.ADC_num_fibDeliv.setValue(du.DEF_AMC_FIB_DELIV)
        self.ADC_btt_clamp.setChecked(du.DEF_AMC_CLAMP)
        self.ADC_btt_knifePos.setChecked(du.DEF_AMC_KNIFE_POS)
        self.ADC_btt_knife.setChecked(du.DEF_AMC_KNIFE)
        self.ADC_btt_fiberPnmtc.setChecked(du.DEF_AMC_FIBER_PNMTC)
        if send_changes:
            self.adc_user_change()

        for widget in self.ADC_group:
            widget.blockSignals(False)


    ##########################################################################
    #                             CONNECTIONS                                #
    ##########################################################################

    def connect_tcp(self, slot='') -> bool:
        """slot-wise connection management, mostly to shrink code length,
        maybe more functionality later
        """

        css = "border-radius: 25px; background-color: #00aaff;"
        
        def rob_connect() -> bool:
            res  = du.ROBTcp.connect()

            if isinstance(res, tuple):
                # if successful, start threading and watchdog
                if not self._RoboCommThread.isRunning():
                    # restart if necessary; if so reconnect threads
                    self.connect_threads(slot)
                    self._RoboCommThread.start()

                self.set_watchdog(slot)
                self.log_entry(
                    'CONN',
                    f"connected to {du.ROBTcp.ip} at {du.ROBTcp.port}."
                )
                self.TCP_ROB_indi_connected.setStyleSheet(css)
                for elem in self.ROB_group:
                    elem.setEnabled(True)
                return True
            
            elif res == TimeoutError:
                log_txt = f"timeout connecting {du.ROBTcp.ip}:{du.ROBTcp.port}."
            elif res == ConnectionRefusedError:
                log_txt = f"{du.ROBTcp.ip}:{du.ROBTcp.port} refused connection."
            else:
                log_txt = f"failed to connect {du.ROBTcp.ip}:{du.ROBTcp.port}!"
            
            self.log_entry('CONN', log_txt)
            return False
            
        def pmp_connect(
                serial:MtecMod,
                port:str,
                p_num:str,
                indi,
                elem_group:list
        ) -> bool:
            if 'COM' in port:
                if fu.connect_pump(p_num):
                    if not self._PumpCommThread.isRunning():
                        # restart if necessary; if so reconnect threads
                        self.connect_threads('PMP')
                        self._PumpCommThread.start()
                    
                    self.log_entry(
                        'CONN',
                        f"connected to {p_num} as inverter "
                        f"{serial.settings_inverter_id} at {port}"
                    )
                    self.set_watchdog(p_num)
                    indi.setStyleSheet(css)
                    for elem in elem_group:
                        elem.setEnabled(True)
                    return True
            
                else:
                    self.log_entry('CONN', f"connection to {p_num} failed!")
                    return False
            
            else:
                raise ConnectionError("TCP not supported, yet")

        match slot:
            case 'ROB':
                return rob_connect()
            
            case 'P1':
                return pmp_connect(
                    du.PMP1Serial,
                    du.PMP1Tcp.port,
                    slot,
                    self.TCP_PUMP1_indi_connected,
                    self.PMP1_group
                )

            case 'P2':
                return pmp_connect(
                    du.PMP2Serial,
                    du.PMP2Tcp.port,
                    slot,
                    self.TCP_PUMP2_indi_connected,
                    self.PMP2_group
                )

            case 'MIX':
                pass #to-do

            case _:
                return False

        return False


    def disconnect_tcp(self, slot='', internal_call=False) -> None:
        """disconnect works, reconnect crashes the app, problem probably lies
        here should also send E command to robot on disconnect
        """

        css = "border-radius: 25px; background-color: #4c4a48;"
        if internal_call:
            log_txt = "internal call to disconnect" 
        else:
            log_txt = "user disconnected"
            
        def safe_reset_positions():
            self.log_entry('SAFE', f"Last robot positions:")
            self.log_entry('SAFE', f"zero: {du.DCCurrZero}")
            self.log_entry('SAFE', f"curr: {du.ROBTelem.Coor}")
            self.log_entry('SAFE', f"rel: {du.ROBTelem.Coor - du.DCCurrZero}")
            self.log_entry('SAFE', f"last active ID was: {du.ROBTelem.id}")
            Mutex.lock()
            du.ROBCommQueue.clear()
            du.ROB_send_list.clear()
            Mutex.unlock()
            self.switch_rob_moving(end=True)

        def p_disconnect(
                serial:MtecMod,
                port:str,
                p_num:str,
                indi,
                elem_group:list
        ) -> None:
            if not serial.connected:
                return
            
            if 'COM' in port:
                self.kill_watchdog(p_num)
                serial.disconnect()
                self.log_entry('CONN', f"{log_txt} {p_num}.")
                indi.setStyleSheet(css)
            else:
                raise ConnectionError(
                    "TCP not supported, unable to disconnect"
                )
        
            for elem in elem_group:
                elem.setEnabled(False)

        match slot:
            case 'ROB':
                if not du.ROBTcp.connected:
                    return
                
                # send stop command to robot; stop threading & watchdog
                du.ROBTcp.send(du.QEntry(id=du.SC_curr_comm_id, mt="E"))
                self.kill_watchdog("ROB")
                self._RoboCommThread.quit()
                du.ROBTcp.close()

                # indicate to user
                self.TCP_ROB_indi_connected.setStyleSheet(css)
                for elem in self.ROB_group:
                    elem.setEnabled(False)

                # safe data & wait for Thread:
                self.log_entry("CONN", f"{log_txt} robot.")
                safe_reset_positions()
                self._RoboCommThread.wait()

            case 'P1':
                p_disconnect(
                    du.PMP1Serial,
                    du.PMP1Tcp.port,
                    slot,
                    self.TCP_PUMP1_indi_connected,
                    self.PMP1_group
                )

            case 'P2':
                p_disconnect(
                    du.PMP2Serial,
                    du.PMP2Tcp.port,
                    slot,
                    self.TCP_PUMP2_indi_connected,
                    self.PMP2_group
                )

            case 'MIX':
                pass #to-do

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
            self._RoboCommWorker.dataReceived.connect(lambda: self.reset_watchdog("ROB"))
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
            self._PumpCommWorker.connLost.connect(self.disconnect_tcp)
            self._PumpCommWorker.dataMixerSend.connect(self.mixer_send)
            self._PumpCommWorker.dataMixerRecv.connect(self.mixer_recv)
            self._PumpCommWorker.connActive.connect(self.reset_watchdog)
        
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



    def robo_send(
            self,
            command:du.QEntry,
            no_error:bool,
            num_send:int | Exception,
            dc:bool
    ) -> None:
        """handle UI update after new command was send"""

        write_buffer = command.print_short()
        if no_error:
            du.SC_curr_comm_id += num_send

            if du.SC_curr_comm_id > 3000:
                Mutex.lock()
                du.SC_curr_comm_id -= 3000
                Mutex.unlock()

            log_txt = "DC" if dc else 'SC'
            log_txt = f"{num_send} {log_txt} command(s) send"
            self.label_update_on_send(command)
            self.log_entry("ROBO", log_txt)

        else:
            self.log_entry(
                "CONN",
                (
                    f"TCPIP class 'ROB_tcpip' encountered {num_send} "
                    f"in sendCommand!"
                ),
            )
        self.TCP_ROB_disp_writeBuffer.setText(write_buffer)
        self.TCP_ROB_disp_bytesWritten.setText(str(num_send))


    def robo_recv(self, raw_data_string:str, telem:du.RoboTelemetry) -> None:
        """write robots telemetry to log & user displays, resetting globals
        position variables is done by RobCommWorker"""

        # set the fist given position to zero as this is usually the standard
        # position for Rob2, take current ID
        if self._first_pos:
            du.ROBMovStartP = copy.deepcopy(du.ROBTelem.Coor)
            du.ROBMovEndP = copy.deepcopy(du.ROBTelem.Coor)
            self.set_zero([1, 2, 3, 4, 5, 6, 8])
            self._first_pos = False

        if telem.id != self._last_comm_id:
            log_txt = f"ID {telem.id},   {telem.Coor}   ToolSpeed: {telem.t_speed}"
            
            if du.PMP1Serial.connected:
                log_txt += f"   PMP1: {self._LastP1Telem}"
            if du.PMP2Serial.connected:
                log_txt += f"   PMP1: {self._LastP2Telem}"

            self.log_entry("RTel", log_txt)
            self._last_comm_id = telem.id

        self.label_update_on_receive(raw_data_string)
        self.Daq.data_update()


    def pump_send(
            self,
            new_speed:int,
            command:str,
            ans:int,
            source:str
    ) -> None:
        """display pump communication, global vars are set by
        PumpCommWorker, calc ratios and volume flow
        """

        def p_send(displays:list, speed:int, p_num:int) -> None:
            displays[0].setText(str(command))
            displays[1].setText(str(len(command)))
            displays[2].setText(str(ans))

            self.log_entry(
                f"PMP{p_num}", f"speed set to {speed}, command: {command}"
            )

        match source:
            case 'P1':
                displays = [self.TCP_PUMP1_disp_writeBuffer,
                            self.TCP_PUMP1_disp_bytesWritten,
                            self.TCP_PUMP1_disp_readBuffer]
                p_send(displays, du.PMP1_speed, 1)

            case 'P2':
                displays = [self.TCP_PUMP1_disp_writeBuffer,
                            self.TCP_PUMP1_disp_bytesWritten,
                            self.TCP_PUMP1_disp_readBuffer]
                p_send(displays, du.PMP2_speed, 2)

            case _:
                raise KeyError(
                    f"Pump signal from unspecified source ({source})!"
                )

        # keep track of PUMP_speed in case of user overwrite:
        if du.PMP1Serial.connected and du.PMP2Serial.connected:
            curr_total, p1_ratio = fu.calc_pump_ratio(
                du.PMP1_speed, du.PMP2_speed
            )

            Mutex.lock()
            du.PMP_speed = curr_total
            du.PMP_output_ratio = p1_ratio
            Mutex.unlock()

        else:
            curr_total = new_speed
            p1_ratio = 1.0 if (source == 'P1') else 0.0

        sld = int((1 - p1_ratio) * 100)
        self.PUMP_disp_currSpeed.setText(f"{round(curr_total, 2)}%")
        self.PUMP_disp_outputRatio.setText(f"{int(p1_ratio * 100)} / {sld}")
        if not self.PUMP_sld_outputRatio.isSliderDown():
            self.PUMP_sld_outputRatio.setValue(sld)


    def pump_recv(self, telem:du.PumpTelemetry, source:str)  -> None:
        """display pump telemetry, global vars are set by PumpCommWorker"""

        def p_recv(display:list, stt_data:du.PumpTelemetry, dump:str) -> None:
            # display & log
            display[0].setText(f"{stt_data.freq}%")
            display[1].setText(f"{stt_data.volt} V")
            display[2].setText(f"{stt_data.amps} A")            
            display[3].setText(f"{stt_data.torq} Nm")

            setattr(self, dump, telem)

        match source:
            case 'P1':
                displays = [self.PUMP_disp_freqP1,
                            self.PUMP_disp_voltP1,
                            self.PUMP_disp_ampsP1,
                            self.PUMP_disp_torqP1]
                p_recv(displays, du.STTDataBlock.Pump1, '_LastP1Telem')

            case 'P2':
                displays = [self.PUMP_disp_freqP2,
                            self.PUMP_disp_voltP2,
                            self.PUMP_disp_ampsP2,
                            self.PUMP_disp_torqP2]
                p_recv(displays, du.STTDataBlock.Pump2, '_LastP2Telem')

            case _:
                raise KeyError(
                    f"Received Pump Telem from unspecified source ({source})!"
                )


    def mixer_send(self, mixer_speed:int, res:bool, data_len:bool) -> None:
        """display mixer communication"""

        self.TCP_MIXER_disp_writeBuffer.setText(str(mixer_speed))
        self.TCP_MIXER_disp_bytesWritten.setText(str(data_len))
        self.log_entry("MIXR", f"speed set to {mixer_speed}")


    def mixer_recv(self, mixerSpeed:int) -> None:
        """display mixer communication"""

        self.MIX_disp_currSpeed.setText(f"{mixerSpeed}%")
        self.log_entry("MTel", f"current speed at {mixerSpeed}%")


    ##########################################################################
    #                               WATCHDOGS                                #
    ##########################################################################

    def set_watchdog(self, dog:str) -> None:
        """set Watchdog, check data updates from robot and pump occure at
        least every 10 sec"""

        watchdog = QTimer()
        watchdog.setSingleShot(True)
        watchdog.setInterval(10000)
        watchdog.timeout.connect(lambda: self.watchdog_bite(dog))

        match dog:
            case 'ROB':
                self._RobRecvWd = watchdog
                self._RobRecvWd.start()
            case 'P1':
                self._P1RecvWd = watchdog
                self._P1RecvWd.start()
            case 'P2':
                self._P2RecvWd = watchdog
                self._P2RecvWd.start()
            case 'MIX':
                self._MixRecvWd = watchdog
                self._MixRecvWd.start()
            case _:
                raise ValueError(f"{dog} is invalad as a watchdog!")
        self.log_entry("WDOG", f"Watchdog {dog} started.")


    def reset_watchdog(self, dog:str) -> None:
        """reset the Watchdog on every newly received data block, check
        connection everytime if disconnected inbetween
        """

        match dog:
            case 'ROB':
                if du.ROBTcp.connected:
                    self._RobRecvWd.start()
            case 'P1':
                if du.PMP1Serial.connected:
                    self._P1RecvWd.start()
            case 'P2':
                if du.PMP2Serial.connected:
                    self._P2RecvWd.start()
            case 'MIX':
                if du.MIXTcp.connected:
                    self._MixRecvWd.start()
            case _:
                self.log_entry('WDOG', f"no such WD: {dog}, reset failed!")


    def watchdog_bite(self, dog:str) -> None:
        """infrom user on any biting WD, log info"""

        cancel_operation = False
        match dog:
            case 'ROB':
                result = "Robot offline"
                if du.SC_q_processing:
                    cancel_operation = True

            case 'P1':
                result = "Pump 1 offline"
                if du.SC_q_processing:
                    cancel_operation = True

            case 'P2':
                result = "Pump 2 offline"
                if du.SC_q_processing:
                    cancel_operation = True

            case 'MIX':
                result = "Mixer offline"

            case _:
                result = "Internal error"
                return

        # stop critical operations, build user text
        if cancel_operation:
            self.log_entry(
                'WDOG',
                (
                    f"Watchdog {dog} has bitten! Stopping script control & "
                    f"forwarding forced-stop to robot!"
                ),
            )
            self.forced_stop_command()
            self.stop_SCTRL_queue()

            wd_text = (
                f"Watchdog {dog} has bitten!\n\nScript control was stopped "
                f"and forced-stop command was send to robot!\nPress OK to "
                f"keep PRINT_py running or Cancel to exit and close."
            )

        else:
            self.log_entry('WDOG', f"Watchdog {dog} has bitten!")
            wd_text = (
                (
                    f"Watchdog {dog} has bitten!\n\n{result}.\nPress OK to "
                    f"keep PRINT_py running or Cancel to exit and close."
                )
            )

        # disconnect, also stops watchdog
        self.disconnect_tcp(slot=dog, internal_call=True)

        # ask user to close application
        watchdog_warning = strd_dialog(wd_text, "WATCHDOG ALARM")
        watchdog_warning.exec()

        if watchdog_warning.result():
            self.log_entry('WDOG', f"User chose to return to main screen.")

        else:
            self.log_entry('WDOG', f"User chose to close PRINT_py, exiting...")
            self.close()


    def kill_watchdog(self, dog:str) -> None:
        """put them to sleep (dont do this to real dogs)"""

        match dog:
            case 'ROB':
                self._RobRecvWd.stop()
                self._RobRecvWd.deleteLater()
            case 'P1':
                self._P1RecvWd.stop()
                self._P1RecvWd.deleteLater()
            case 'P2':
                self._P2RecvWd.stop()
                self._P2RecvWd.deleteLater()
            case 'MIX':
                self._MixRecvWd.stop()
                self._MixRecvWd.deleteLater()
            case _:
                pass
            
        self.log_entry('WDOG', f"Watchdog {dog} deleted.")


    ##########################################################################
    #                                SETTINGS                                #
    ##########################################################################

    def mutex_setattr(self, obj, attr, val) -> None:
        """reduce the Mutex lock/unlock game to a single line,
        but makes refactoring a little more tedious
        """

        Mutex.lock()
        setattr(obj, attr, val)
        Mutex.unlock()


    def apply_settings(self) -> None:
        """load default settings to settings display"""

        Mutex.lock()
        du.SC_vol_per_m = self.SET_float_volPerMM.value()
        du.IO_fr_to_ts = self.SET_float_frToMms.value()
        du.IO_zone = self.SET_num_zone.value()
        du.DCSpeed.ts = self.SET_num_transSpeed_dc.value()
        du.DCSpeed.ors = self.SET_num_orientSpeed_dc.value()
        du.DCSpeed.acr = self.SET_num_accelRamp_dc.value()
        du.DCSpeed.dcr = self.SET_num_decelRamp_dc.value()
        du.PRINSpeed.ts = self.SET_num_transSpeed_print.value()
        du.PRINSpeed.ors = self.SET_num_orientSpeed_print.value()
        du.PRINSpeed.acr = self.SET_num_accelRamp_print.value()
        du.PRINSpeed.dcr = self.SET_num_decelRamp_print.value()
        Mutex.unlock()

        self.log_entry(
            'SETS',
            f"General settings updated -- VolPerMM: {du.SC_vol_per_m}"
            f", FR2TS: {du.IO_fr_to_ts}, IOZ: {du.IO_zone}"
            f", PrinTS: {du.PRINSpeed.ts}, PrinOS: {du.PRINSpeed.ors}"
            f", PrinACR: {du.PRINSpeed.acr} PrinDCR: {du.PRINSpeed.dcr}"
            f", DCTS: {du.DCSpeed.ts}, DCOS: {du.DCSpeed.ors}"
            f", DCACR: {du.DCSpeed.acr}, DCDCR: {du.DCSpeed.dcr}",
        )


    def apply_TE_settings(self) -> None:
        """load default settings to settings display"""

        Mutex.lock()
        du.SC_ext_fllw_bhvr = (
            self.SET_TE_num_fllwBhvrInterv.value(),
            self.SET_TE_num_fllwBhvrSkip.value(),
        )
        du.PMP_retract_speed = self.SET_TE_num_retractSpeed.value()
        du.PMP1_liter_per_s = self.SET_TE_float_p1VolFlow.value()
        du.PMP2_liter_per_s = self.SET_TE_float_p2VolFlow.value()
        Mutex.unlock()

        self.log_entry(
            'SETS',
            f"TE settings updated -- FB_inter: {du.SC_ext_fllw_bhvr[0]}, "
            f"FB_skip: {du.SC_ext_fllw_bhvr[1]}, "
            f"PmpRS: {du.PMP_retract_speed}, "
            f"Pmp1LPS: {du.PMP1_liter_per_s}, "
            f"Pmp2LPS: {du.PMP2_liter_per_s}",
        )


    ##########################################################################
    #                              LOG FUNCTION                              #
    ##########################################################################

    def log_entry(self, source="[    ]", text="") -> None:
        """set one-liner for log entries, safes A LOT of repetitive code"""

        if self.logpath == '':
            return None
        text = text.replace('\n', '')
        text = text.replace('\t', '')

        if source == 'newline':
            text = '\n'
        else:
            time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            text = f"{time}    [{source}]:        {text}\n"

        try:
            logfile = open(self.logpath, 'a')
        except FileExistsError:
            pass

        self.SET_disp_logEntry.setText(text)
        logfile.write(text)
        logfile.close()


    ##########################################################################
    #                            QLABEL UPDATES                              #
    ##########################################################################

    def label_update_on_receive(self, data_string:str) -> None:
        """update all QLabels in the UI that may change with newly received
        data from robot
        """

        Pos = du.ROBTelem.Coor
        Zero = du.DCCurrZero
        rob_id = du.ROBTelem.id
        com_id = du.SC_curr_comm_id
        Start = du.ROBMovStartP
        End = du.ROBMovEndP
        try:
            prog_id = du.SCQueue[0].id
        except AttributeError:
            prog_id = com_id

        # SCRIPT  CONTROL
        self.TCP_ROB_disp_readBuffer.setText(data_string)
        self.SCTRL_disp_buffComms.setText(str(prog_id - rob_id))
        self.SCTRL_disp_robCommID.setText(str(rob_id))
        self.SCTRL_disp_progCommID.setText(str(prog_id))
        self.SCTRL_disp_elemInQ.setText(str(len(du.SCQueue)))

        # DIRECT CONTROL
        self.DC_disp_x.setText(str(round(Pos.x - Zero.x, 3)))
        self.DC_disp_y.setText(str(round(Pos.y - Zero.y, 3)))
        self.DC_disp_z.setText(str(round(Pos.z - Zero.z, 3)))
        self.DC_disp_ext.setText(str(round(Pos.ext - Zero.ext, 3)))

        # NUMERIC CONTROL
        self.NC_disp_x.setText(f"{Pos.x}")
        self.NC_disp_y.setText(f"{Pos.y}")
        self.NC_disp_z.setText(f"{Pos.z}")
        self.NC_disp_xOrient.setText(f"{Pos.rx}°")
        self.NC_disp_yOrient.setText(f"{Pos.ry}°")
        self.NC_disp_zOrient.setText(f"{Pos.rz}°")
        self.NC_disp_ext.setText(f"{Pos.ext}")

        # TERMINAL
        self.TERM_disp_tcpSpeed.setText(str(du.ROBTelem.t_speed))
        self.TERM_disp_robCommID.setText(str(rob_id))
        self.TERM_disp_progCommID.setText(str(prog_id))

        # SCRIPT ID
        self.SID_disp_progID.setText(str(prog_id))
        self.SID_disp_robID.setText(str(rob_id))

        # CURRENT TRANSITION
        # more practical to just display relative coordinates
        if Start.rx != End.rx or Start.ry != End.ry or Start.rz != End.rz:
            self.TRANS_indi_newOrient.setStyleSheet(
                "border-radius: 15px; background-color: #4c4a48;"
            )
        else:
            self.TRANS_indi_newOrient.setStyleSheet(
                "border-radius: 15px; background-color: #00aaff;"
            )

        self.TRANS_disp_xStart.setText(str(round(Start.x - Zero.x, 2)))
        self.TRANS_disp_yStart.setText(str(round(Start.y - Zero.y, 2)))
        self.TRANS_disp_zStart.setText(str(round(Start.z - Zero.z, 2)))
        self.TRANS_disp_extStart.setText(str(round(Start.ext - Zero.ext, 2)))
        self.TRANS_disp_xEnd.setText(str(round(End.x - Zero.x, 2)))
        self.TRANS_disp_yEnd.setText(str(round(End.y - Zero.y, 2)))
        self.TRANS_disp_zEnd.setText(str(round(End.z - Zero.z, 2)))
        self.TRANS_disp_extEnd.setText(str(round(End.ext - Zero.ext, 2)))


    def label_update_on_send(self, entry:du.QEntry) -> None:
        """update all UI QLabels that may change when data was send to robot"""

        # update command lists and buffer size displays
        self.label_update_on_queue_change()
        self.label_update_on_terminal_change()
        self.SCTRL_disp_elemInQ.setText(str(len(du.SCQueue)))

        try:
            rob_id = du.ROBTelem.id if (du.ROBTelem.id != -1) else 0
            self.SCTRL_disp_buffComms.setText(
                str(du.SCQueue[0].id - rob_id - 1)
            )
        except AttributeError:
            pass

        # update Amcon & Pump tab
        for widget in self.ADC_group: widget.blockSignals(True)
        for widget in self.ASC_group: widget.blockSignals(True)

        self.ADC_num_panning.setValue(entry.Tool.pan_steps)
        self.ASC_num_panning.setValue(entry.Tool.pan_steps)
        self.ADC_num_fibDeliv.setValue(entry.Tool.fib_deliv_steps)
        self.ASC_num_fibDeliv.setValue(entry.Tool.fib_deliv_steps)
        self.ADC_btt_clamp.setChecked(entry.Tool.pnmtc_clamp_yn)
        self.ASC_btt_clamp.setChecked(entry.Tool.pnmtc_clamp_yn)
        self.ADC_btt_knifePos.setChecked(entry.Tool.knife_pos_yn)
        self.ASC_btt_knifePos.setChecked(entry.Tool.knife_pos_yn)
        self.ADC_btt_knife.setChecked(entry.Tool.knife_yn)
        self.ASC_btt_knife.setChecked(entry.Tool.knife_yn)
        self.ADC_btt_fiberPnmtc.setChecked(entry.Tool.pnmtc_fiber_yn)
        self.ASC_btt_fiberPnmtc.setChecked(entry.Tool.pnmtc_fiber_yn)

        for widget in self.ADC_group: widget.blockSignals(False)
        for widget in self.ASC_group: widget.blockSignals(False)


    def label_update_on_queue_change(self) -> None:
        """show when new entries have been successfully placed in or taken
        from Queue
        """

        list_to_display = du.SCQueue.display()
        max_len = du.DEF_SC_MAX_LINES
        length = len(list_to_display)
        overlen = length - max_len

        if length > max_len:
            list_to_display = list_to_display[0:max_len]
            list_to_display[max_len - 1] = (
                f"{overlen + 1} further command are not display..."
            )

        self.SCTRL_arr_queue.clear()
        self.SCTRL_arr_queue.addItems(list_to_display)
        if self.SCTRL_chk_autoScroll.isChecked():
            self.SCTRL_arr_queue.scrollToBottom()


    def label_update_on_terminal_change(self) -> None:
        """show when data was send or received, update ICQ"""

        self.TERM_arr_terminal.clear()
        self.TERM_arr_terminal.addItems(du.TERM_log)
        if self.TERM_chk_autoScroll.isChecked():
            self.TERM_arr_terminal.scrollToBottom()

        list_to_display = du.ROBCommQueue.display()
        max_len = du.DEF_ICQ_MAX_LINES
        length = len(list_to_display)
        overlen = length - max_len

        if length > max_len:
            list_to_display = list_to_display[0:max_len]
            list_to_display[max_len - 1] = (
                f"{overlen} further command are not display..."
            )

        self.ICQ_arr_terminal.clear()
        self.ICQ_arr_terminal.addItems(list_to_display)
        if self.ICQ_chk_autoScroll.isChecked():
            self.ICQ_arr_terminal.scrollToBottom()


    def label_update_on_new_zero(self) -> None:
        """show when DC_zero has changed"""

        self.ZERO_disp_x.setText(str(du.DCCurrZero.x))
        self.ZERO_disp_y.setText(str(du.DCCurrZero.y))
        self.ZERO_disp_z.setText(str(du.DCCurrZero.z))
        self.ZERO_disp_xOrient.setText(str(du.DCCurrZero.rx))
        self.ZERO_disp_yOrient.setText(str(du.DCCurrZero.ry))
        self.ZERO_disp_zOrient.setText(str(du.DCCurrZero.rz))
        self.ZERO_disp_ext.setText(str(du.DCCurrZero.ext))

        self.ZERO_float_x.setValue(du.DCCurrZero.x)
        self.ZERO_float_y.setValue(du.DCCurrZero.y)
        self.ZERO_float_z.setValue(du.DCCurrZero.z)
        self.ZERO_float_rx.setValue(du.DCCurrZero.rx)
        self.ZERO_float_ry.setValue(du.DCCurrZero.ry)
        self.ZERO_float_rz.setValue(du.DCCurrZero.rz)
        self.ZERO_float_ext.setValue(du.DCCurrZero.ext)


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
        Mutex.lock()
        workers.lfw_file_path = fpath
        workers.lfw_line_id = start_id
        workers.lfw_p_ctrl = p_ctrl
        Mutex.unlock()

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
        Mutex.lock()
        workers.lfw_file_path = None
        workers.lfw_line_id = 0
        workers.lfw_p_ctrl = False
        Mutex.unlock()

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
        Mutex.lock()
        workers.lfw_file_path = None
        workers.lfw_line_id = 0
        workers.lfw_p_ctrl = False
        Mutex.unlock()

        self.IO_btt_loadFile.setStyleSheet("font-size: 16pt;")
        self._LoadFileThread.exit()


    ##########################################################################
    #                             COMMAND QUEUE                              #
    ##########################################################################

    def reset_SC_id(self) -> None:
        """synchronize SC and ROB ID with this, if program falls out of sync
        with the robot, should happen only with on-the-fly restarts,
        theoretically
        """
        
        if du.DC_rob_moving:
            return
        id_dist = (du.ROBTelem.id + 1) - du.SC_curr_comm_id
        
        Mutex.lock()
        du.SC_curr_comm_id = du.ROBTelem.id + 1
        du.SCQueue.increment(id_dist)
        Mutex.unlock()

        self.label_update_on_receive(
            data_string=self.TCP_ROB_disp_readBuffer.text()
        )
        self.log_entry('GNRL', f"User overwrote current comm ID to {du.SC_curr_comm_id}.")


    def start_SCTRL_queue(self) -> None:
        """set UI indicators, send the boring work of timing the command to
        our trusty threads
        """

        # set parameters
        Mutex.lock()
        du.SC_q_processing = True
        du.SC_q_prep_end = False
        Mutex.unlock()
        self.log_entry("ComQ", "queue processing started")

        # update GUI
        css = "border-radius: 20px; background-color: #00aaff;"
        self.SCTRL_indi_qProcessing.setStyleSheet(css)
        self.TCP_indi_qProcessing.setStyleSheet(css)
        self.ASC_indi_qProcessing.setStyleSheet(css)

        for widget in self.ASC_group:
            widget.setEnabled(False)
        self.switch_rob_moving()

        self.label_update_on_queue_change()


    def stop_SCTRL_queue(self, prep_end=False) -> None:
        """set UI indicators, turn off threads"""

        if prep_end:
            css = "border-radius: 20px; background-color: #ffda1e;"
            du.SC_q_prep_end = True

        else:
            Mutex.lock()
            du.PMP_speed = 0
            du.SC_q_prep_end = False
            du.SC_q_processing = False
            Mutex.unlock()
            self.log_entry("ComQ", "queue processing stopped")

            self.label_update_on_queue_change()
            self.switch_rob_moving(end=True)
            css = "border-radius: 20px; background-color: #4c4a48;"

            for widget in self.ASC_group:
                widget.setEnabled(True)

        # update GUI
        self.SCTRL_indi_qProcessing.setStyleSheet(css)
        self.TCP_indi_qProcessing.setStyleSheet(css)
        self.ASC_indi_qProcessing.setStyleSheet(css)


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

        Mutex.lock()
        res = du.SCQueue.add(Entry)
        Mutex.unlock()

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

        Mutex.lock()
        res = du.SCQueue.add(Entry)
        Mutex.unlock()

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
    

    def clr_queue(self, partial=False) -> None:
        """delete specific or all items from queue"""

        Mutex.lock()
        if partial:
            du.SCQueue.clear(all=False, id=self.SCTRL_entry_clrByID.text())
        else:
            du.SCQueue.clear(all=True)
        Mutex.unlock()

        if not partial:
            self.log_entry("ComQ", "queue emptied by user")
        else:
            self.log_entry(
                "ComQ",
                f"queue IDs cleared: {self.SCTRL_entry_clrByID.text()}"
            )
        self.label_update_on_queue_change()


    ##########################################################################
    #                               DC COMMANDS                              #
    ##########################################################################

    def values_to_DC_spinbox(self) -> None:
        """button function to help the user adjust a postion via numeric
        control, copys the current position to the set coordinates
        spinboxes
        """

        self.NC_float_x.setValue(du.ROBTelem.Coor.x)
        self.NC_float_y.setValue(du.ROBTelem.Coor.y)
        self.NC_float_z.setValue(du.ROBTelem.Coor.z)
        self.NC_float_xOrient.setValue(du.ROBTelem.Coor.rx)
        self.NC_float_yOrient.setValue(du.ROBTelem.Coor.ry)
        self.NC_float_zOrient.setValue(du.ROBTelem.Coor.rz)
        self.NC_float_ext.setValue(du.ROBTelem.Coor.ext)


    def switch_rob_moving(self, end=False) -> None:
        """change UTIL.DC_robMoving"""

        Mutex.lock()
        if end:
            du.DC_rob_moving = False
            button_toggle = True
            self.DC_indi_robotMoving.setStyleSheet(
                "border-radius: 25px; background-color: #4c4a48;"
            )
            self.ADC_indi_robotMoving.setStyleSheet(
                "border-radius: 20px; background-color: #4c4a48;"
            )
        else:
            du.DC_rob_moving = True
            button_toggle = False
            self.DC_indi_robotMoving.setStyleSheet(
                "border-radius: 25px; background-color: #00aaff;"
            )
            self.ADC_indi_robotMoving.setStyleSheet(
                "border-radius: 20px; background-color: #00aaff;"
            )

        for widget in self.ADC_group: widget.setEnabled(button_toggle)
        for widget in self.DC_group: widget.setEnabled(button_toggle)
        for widget in self.NC_group: widget.setEnabled(button_toggle)
        for widget in self.TERM_group: widget.setEnabled(button_toggle)
        Mutex.unlock()


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

            Mutex.lock()
            LostBuf = copy.deepcopy(du.ROBCommQueue)
            for Entry in du.ROB_send_list:
                if Entry[0].mt != "S":
                    LostBuf.append(Entry[0])
            du.SC_curr_comm_id = du.ROBTelem.id
            du.SCQueue = LostBuf + du.SCQueue
            du.ROBCommQueue.clear()
            du.ROB_send_list.clear()
            Mutex.unlock()

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

            Mutex.lock()
            du.ROB_send_list.clear()
            Mutex.unlock()

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
        Mutex.lock()
        du.ROB_send_list.append((command, dc))
        Mutex.unlock()


    def set_zero(self, axis:list, from_sys_monitor=False) -> None:
        """overwrite DC_curr_zero, uses deepcopy to avoid large mutual
        exclusion blocks
        """

        NewZero = copy.deepcopy(du.DCCurrZero)
        if from_sys_monitor:
            CurrPos = du.Coordinate(
                x=self.ZERO_float_x.value(),
                y=self.ZERO_float_y.value(),
                z=self.ZERO_float_z.value(),
                rx=self.ZERO_float_rx.value(),
                ry=self.ZERO_float_ry.value(),
                rz=self.ZERO_float_rz.value(),
                ext=self.ZERO_float_ext.value(),
            )
        else:
            CurrPos = copy.deepcopy(du.ROBTelem.Coor)

        if axis:
            # 7 is a placeholder for Q, which can not be set by hand
            if 1 in axis:
                NewZero.x = CurrPos.x
            if 2 in axis:
                NewZero.y = CurrPos.y
            if 3 in axis:
                NewZero.z = CurrPos.z
            if 4 in axis:
                NewZero.rx = CurrPos.rx
            if 5 in axis:
                NewZero.ry = CurrPos.ry
            if 6 in axis:
                NewZero.rz = CurrPos.rz
            if 8 in axis:
                NewZero.ext = CurrPos.ext

            self.mutex_setattr(du, 'DCCurrZero', NewZero)

        self.label_update_on_new_zero()
        self.log_entry(
            "ZERO",
            f"current zero position updated: ({du.DCCurrZero})"
        )


    ##########################################################################
    #                              PUMP CONTROL                              #
    ##########################################################################

    def pump_set_speed(self, type="") -> None:
        """handle user inputs regarding pump frequency"""

        Mutex.lock()
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
        Mutex.unlock()


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
        Mutex.lock()
        for i in range(len(du.SCQueue)):
            du.SCQueue[i].p_mode = "default"
        Mutex.unlock()
        return


    def pinch_valve_toggle(self) -> None:
        """not implemented yet"""

        usr_info = strd_dialog(
            "Pinch valve not supported, yet!", "Process does not exist"
        )
        usr_info.exec()


    ##########################################################################
    #                              MIXER CONTROL                             #
    ##########################################################################

    def mixer_set_speed(self, type="") -> None:
        """handle user inputs for 2K mixer"""

        match type:
            case "sld":
                speed = self.MIX_sld_speed.value()
            case "0":
                speed = 0
            case _:
                speed = self.MIX_num_setSpeed.value()

        self.mutex_setattr(du, 'MIX_speed', speed)


    ##########################################################################
    #                              AMCON CONTROL                             #
    ##########################################################################

    def amcon_script_overwrite(self) -> None:
        """override entire/partial SC queue with custom Amcon settings"""

        # actual overwrite
        id_range = self.ASC_entry_SCLines.text()
        SC_first = 1
        usr_txt = ''

        try:
            start = int(re.findall("\d+", id_range)[0])
            if start < SC_first:
                usr_txt = (
                    f"SC lines value is lower than lowest SC queue ID, "
                    f"nothing was done."
                )
        except IndexError:
            usr_txt = "Invalid command in SC lines."

        try:
            SC_first = du.SCQueue[0].id
        except AttributeError:
            usr_txt = "SC queue contains no commands, nothing was done."
        
        if usr_txt:
            user_info = strd_dialog(usr_txt, "Command error")
            user_info.exec()
            return None

        pan_val = self.ASC_num_panning.value()
        fib_deliv = self.ASC_num_fibDeliv.value()
        clamp = self.ASC_btt_clamp.isChecked()
        knife_pos = self.ASC_btt_knifePos.isChecked()
        knife = self.ASC_btt_knife.isChecked()
        fiber_pnmtc = self.ASC_btt_fiberPnmtc.isChecked()

        if ".." in id_range:
            ids = re.findall("\d+", id_range)
            if len(ids) != 2:
                user_info = strd_dialog(
                    "Worng syntax used in SC lines value, nothing was done.",
                    "Command error",
                )
                user_info.exec()
                return None

            id_start = int(ids[0])
            id_end = int(ids[1])

            Mutex.lock()
            for i in range(id_end - id_start + 1):

                try:
                    j = du.SCQueue.id_pos(i + id_start)
                except AttributeError:
                    break

                du.SCQueue[j].Tool.pan_steps = int(pan_val)
                du.SCQueue[j].Tool.fib_deliv_steps = int(fib_deliv)
                du.SCQueue[j].Tool.pnmtc_clamp_yn= bool(clamp)
                du.SCQueue[j].Tool.knife_pos_yn = bool(knife_pos)
                du.SCQueue[j].Tool.knife_yn = bool(knife)
                du.SCQueue[j].Tool.pnmtc_fiber_yn = bool(fiber_pnmtc)
            Mutex.unlock()

        else:
            ids = re.findall("\d+", id_range)
            if len(ids) != 1:
                user_info = strd_dialog(
                    "Worng syntax used in SC lines value, nothing was done.",
                    "Command error",
                )
                user_info.exec()
                return None

            id_start = int(ids[0])

            Mutex.lock()
            try:
                j = du.SCQueue.id_pos(id_start)
            except AttributeError:
                return

            du.SCQueue[j].Tool.pan_steps = int(pan_val)
            du.SCQueue[j].Tool.fib_deliv_steps = int(fib_deliv)
            du.SCQueue[j].Tool.pnmtc_clamp_yn = bool(clamp)
            du.SCQueue[j].Tool.knife_pos_yn = bool(knife_pos)
            du.SCQueue[j].Tool.knife_yn = bool(knife)
            du.SCQueue[j].Tool.pnmtc_fiber_yn = bool(fiber_pnmtc)
            Mutex.unlock()

        check_entry = du.SCQueue.id_pos(id_start)
        Tool = du.SCQueue[check_entry].Tool
        self.log_entry(
            "ACON",
            (
                f"{ id_range } SC commands overwritten to new tool "
                f"settings: ({ Tool })"
            ),
        )


    def adc_user_change(self) -> None:
        """send changes to Amcon, if user commit them"""

        if du.DC_rob_moving:
            return None

        Pos = copy.deepcopy(du.ROBTelem.Coor)
        Tool = du.ToolCommand(
            pan_steps=self.ADC_num_panning.value(),
            fib_deliv_steps=self.ADC_num_fibDeliv.value(),
            pnmtc_clamp_yn=self.ADC_btt_clamp.isChecked(),
            knife_pos_yn=self.ADC_btt_knifePos.isChecked(),
            knife_yn=self.ADC_btt_knife.isChecked(),
            pnmtc_fiber_yn=self.ADC_btt_fiberPnmtc.isChecked(),
        )

        Command = du.QEntry(
            id=du.SC_curr_comm_id,
            Coor1=Pos,
            Speed=copy.deepcopy(du.DCSpeed),
            z=0,
            Tool=Tool,
        )

        self.log_entry("ACON", f"updating tool status by user: ({ Tool })")
        return self.send_command(Command, dc=True)


    ##########################################################################
    #                              CLOSE UI                                  #
    ##########################################################################

    def closeEvent(self, event) -> None:
        """exit all threads and connections clean(ish)"""

        self.log_entry("newline")
        self.log_entry("GNRL", "closeEvent signal.")
        self.log_entry("GNRL", "cut connections...")

        # stop pump thread
        if self._PumpCommThread.isRunning():
            self._PumpCommThread.quit()
            self._PumpCommThread.wait()
        
        # stop sensor array
        if self._SensorArrThread.isRunning():
            self._SensorArrThread.quit()
            self._SensorArrThread.wait()

        # disconnect everything
        self.disconnect_tcp("ROB", internal_call=True)
        self.disconnect_tcp("P1", internal_call=True)
        self.disconnect_tcp("P2", internal_call=True)
        self.disconnect_tcp("MIX", internal_call=True)

        # delete threads
        self.log_entry("GNRL", "stop threading...")
        self._RoboCommThread.deleteLater()
        self._PumpCommThread.deleteLater()
        self._LoadFileThread.deleteLater()

        # bye
        self.log_entry("GNRL", "exiting GUI.")
        self.Daq.close()
        event.accept()



##################################   MAIN  ###################################

# mutual exclusion object, used to manage global data exchange
Mutex = QMutex()

# only do the following if run as main program
if __name__ == "__main__":

    from libs.win_dialogs import strd_dialog
    import libs.data_utilities as du

    # import PyQT UIs (converted from .ui to .py)
    from ui.UI_mainframe_v6 import Ui_MainWindow

    logpath = fu.create_logfile()

    # overwrite ROB_tcpip for testing, delete later
    du.ROBTcp.ip = "localhost"
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
