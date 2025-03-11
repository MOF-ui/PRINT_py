#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# python standard libraries
import os
import sys
from datetime import datetime
from copy import deepcopy as dcpy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


# PyQt stuff
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtCore import QObject, QTimer, QMutex, QMutexLocker, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from ui.UI_mainframe_v6 import Ui_MainWindow


# import my own libs
from libs.win_daq import daq_window
from libs.win_cam_cap import cam_cap_window
from libs.win_dialogs import strd_dialog
import libs.data_utilities as du
import libs.func_utilities as fu



####################### MAINFRAME CLASS  #####################################

class PreMainframe(QMainWindow, Ui_MainWindow):
    """Panel element grouping, log_entry function, UI setup;
    everything prearrange to use and reduce code lines in win_mainframe
    """

    ##########################################################################
    #                                ATTRIBUTES                              #
    ##########################################################################

    _logpath = ''  # reference for logEntry, set by __init__
    _testrun = False

    _last_comm_id = 0
    _LastP1Telem = None
    _LastP2Telem = None

    _IPCamWorker = None
    _LoadFileWorker = None
    _PumpCommWorker = None
    _RoboCommWorker = None
    _SensorArrWorker = None

    _RobRecvWd = None
    _P1RecvWd = None
    _P2RecvWd = None
    _PRHRecvWd = None

    #########################################################################
    #                                  SETUP                                #
    #########################################################################

    def __init__(self, lpath, testrun=False, parent=None) -> None:

        super().__init__(parent)
        self._testrun = testrun

        # UI SETUP
        self.setupUi(self)
        self.setWindowTitle('---   PRINT_py  -  Main Window  ---')
        self.setWindowFlags(
            Qt.WindowMaximizeButtonHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # INIT THREADS
        self._IPCamThread = QThread()
        self._LoadFileThread = QThread()
        self._PumpCommThread = QThread()
        self._RoboCommThread = QThread()
        self._SensorArrThread = QThread()

        # INIT WATCHDOGS
        self._RobRecvWd = Watchdog(True, 'Robot', 'ROBTcp', 'ROB')
        self._P1RecvWd = Watchdog(True, 'Pump 1', 'PMP1Serial', 'P1')
        self._P2RecvWd = Watchdog(True, 'Pump 2', 'PMP2Serial', 'P2')
        self._PRHRecvWd = Watchdog(False, 'Printhead', 'PRH_connected', 'PRH')

        # GROUP PANEL ELEMENTS
        self.group_elems()

        # LOGFILE SETUP
        if lpath is None:
            log_txt = (
                f"No path for logfile ({lpath})!\n\n"
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
            self._logpath = lpath
            self.log_entry('GNRL', 'main GUI running.')

        # SIDE WINDOW SETUP
        self.Daq = daq_window()
        self.CamCap = cam_cap_window()
        for side_win in [self.Daq, self.CamCap]:
            side_win.logEntry.connect(self.log_entry)
            if not testrun:
                side_win.show()
        self.log_entry('GNRL', 'side windows running.')

    

    def group_elems(self) -> None:
        """build groups for enable/disable actions"""

        self.ADC_group = [
            self.ADC_num_trolley,
            self.ADC_btt_clamp,
            self.ADC_btt_cut,
            self.ADC_btt_placeSpring,
        ]

        self.ASC_group = [
            self.ASC_num_trolley,
            self.ASC_btt_clamp,
            self.ASC_btt_cut,
            self.ASC_btt_placeSpring,
        ]

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

        self.PRH_group = [
            self.PRH_btt_actWithPump,
            self.PRH_btt_setSpeed,
            self.PRH_disp_currSpeed,
            self.PRH_num_setSpeed,
            self.PRH_sld_speed,
            self.PRH_btt_pinchValve
        ]
        for elem in self.PRH_group:
            elem.setEnabled(False)

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
            self.ADC_btt_cut,
            self.ADC_btt_placeSpring,
            self.ADC_num_trolley,
        ]
        self.ROB_group += self.DC_group
        self.ROB_group += self.NC_group
        for elem in self.ROB_group:
            elem.setEnabled(False)

        self.TERM_group = self.TERM_btt_gcodeInterp, self.TERM_btt_rapidInterp
        
        self.WD_group = [
            self._RobRecvWd,
            self._P1RecvWd,
            self._P2RecvWd,
            self._PRHRecvWd
        ]


    
    ##########################################################################
    #                              LOG FUNCTION                              #
    ##########################################################################

    def log_entry(self, source='[    ]', text='') -> None:
        """set one-liner for log entries, safes A LOT of repetitive code"""

        if self._logpath == '':
            return None
        text = text.replace('\n', '')
        text = text.replace('\t', '')

        if source == 'newline':
            text = '\n'
        else:
            time = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            text = f"{time}    [{source}]:        {text}\n"

        try:
            with open(self._logpath, 'a') as log_file:
                log_file.write(text)
            self.SET_disp_logEntry.setText(text)
        except:
            self.SET_disp_logEntry.setText('LOG FILE ERROR!')



    ##########################################################################
    #                                SETTINGS                                #
    ##########################################################################

    def mutex_setattr(self, flag:str) -> None:
        """reduce the Mutex lock/unlock game to a single line,
        but makes refactoring a little more tedious
        """

        with QMutexLocker(GlobalMutex):
            match flag:
                case 'robot_live_ad':
                    new_val = self.SCTRL_num_liveAd_robot.value() / 100.0
                    du.ROB_live_ad = new_val
                case 'robot_comm_fr':
                    du.ROB_comm_fr = self.CONN_num_commForerun.value()
                case 'mixer_act_w_pump':
                    new_val = not self.PRH_btt_actWithPump.isChecked()
                    du.PRH_act_with_pump = new_val
                case 'pmp_out_ratio':
                    new_val = 1 - (self.PUMP_sld_outputRatio.value() / 100.0)
                    du.PMP_output_ratio = new_val
                case 'mms_overwrite':
                    if self.SCTRL_btt_mmsOverwrite.isChecked():
                        new_val = self.SCTRL_num_mmsOverwrite.value()
                    else:
                        new_val = -1
                    du.ROB_speed_overwrite = new_val
                case 'pump_look_ahead':
                    new_val = self.LAH_btt_active.isChecked()
                    du.PMP_look_ahead = new_val
                case 'pmp_look_ahead_dist':
                    new_val = self.LAH_num_distance.value()
                    du.PMP_look_ahead_dist = new_val
                case _:
                    raise KeyError(f"'{flag}' is not a defined flag")


    def apply_settings(self) -> None:
        """load default settings to settings display"""

        with QMutexLocker(GlobalMutex):
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

        with QMutexLocker(GlobalMutex):
            du.SC_ext_fllw_bhvr = (
                self.SET_TE_num_fllwBhvrInterv.value(),
                self.SET_TE_num_fllwBhvrSkip.value(),
            )
            du.PMP_retract_speed = self.SET_TE_num_retractSpeed.value()
            du.PMP1_liter_per_s = self.SET_TE_float_p1VolFlow.value()
            du.PMP2_liter_per_s = self.SET_TE_float_p2VolFlow.value()

        self.log_entry(
            'SETS',
            f"TE settings updated -- FB_inter: {du.SC_ext_fllw_bhvr[0]}, "
            f"FB_skip: {du.SC_ext_fllw_bhvr[1]}, "
            f"PmpRS: {du.PMP_retract_speed}, "
            f"Pmp1LPS: {du.PMP1_liter_per_s}, "
            f"Pmp2LPS: {du.PMP2_liter_per_s}",
        )


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
            self.CONN_num_commForerun.setValue(du.DEF_ROB_COMM_FR)

            self.load_ADC_defaults()
            self.ASC_num_trolley.setValue(du.DEF_PRH_TROLLEY)
            self.ASC_btt_clamp.setChecked(du.DEF_PRH_CLAMP)
            self.ASC_btt_cut.setChecked(du.DEF_PRH_CUT)
            self.ASC_btt_placeSpring.setChecked(du.DEF_PRH_PLACE_SPR)


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

        self.ADC_num_trolley.setValue(du.DEF_PRH_TROLLEY)
        self.ADC_btt_clamp.setChecked(du.DEF_PRH_CLAMP)
        self.ADC_btt_cut.setChecked(du.DEF_PRH_CUT)
        self.ADC_btt_placeSpring.setChecked(du.DEF_PRH_PLACE_SPR)
        if send_changes:
            self.adc_user_change()

        for widget in self.ADC_group:
            widget.blockSignals(False)
    

    def adc_user_change(self):
        raise NotImplementedError(
            f"This method was not overwritten by child class, "
            f"but overwite is mandatory!"
        )
    

    def init_connection_settings(self):
        """load connection settings once from data_utilities for the
        user to see, should not change during runtime"""

        # ROBOT
        self.CONN_ROB_disp_ip.setText(du.ROBTcp.ip)
        self.CONN_ROB_disp_port.setText(str(du.ROBTcp.port))
        self.CONN_ROB_disp_rwTo.setText(str(du.ROBTcp.rw_tout))
        self.CONN_ROB_disp_connTo.setText(str(du.ROBTcp.c_tout))
        self.CONN_ROB_disp_bytesToRead.setText(str(du.ROBTcp.r_bl))
        # P1
        self.CONN_PUMP1_disp_port.setText(du.PMP_port)
        self.CONN_PUMP1_disp_modbId.setText(du.PMP1_modbus_id)
        # P2
        self.CONN_PUMP2_disp_port.setText(du.PMP_port)
        self.CONN_PUMP2_disp_modbId.setText(du.PMP2_modbus_id)
        # PRH
        _, ip, port = du.PRH_url.split(':')
        self.CONN_PRH_disp_ip.setText(ip)
        self.CONN_PRH_disp_port.setText(port)




    ##########################################################################
    #                       THREADS HELP FUNCTIONS                           #d
    ##########################################################################

    def robo_send(
            self,
            command:du.QEntry,
            no_error:bool,
            num_send:int | Exception,
            dc:bool
    ) -> None:
        """handle UI update after new command was send"""

        if no_error:
            write_buffer = command.print_short()
            du.SC_curr_comm_id += num_send

            if du.SC_curr_comm_id > du.DEF_ROB_BUFF_SIZE:
                with QMutexLocker(GlobalMutex):
                    du.SC_curr_comm_id -= du.DEF_ROB_BUFF_SIZE

            log_txt = 'DC' if dc else 'SC'
            log_txt = f"{num_send} {log_txt} command(s) send"
            self.label_update_on_send(command)
            self.log_entry('ROBO', log_txt)

        else:
            write_buffer = f"{num_send}"
            self.log_entry(
                'CONN',
                (
                    f"TCPIP class 'ROB_tcpip' encountered {num_send} "
                    f"in sendCommand!"
                ),
            )
        self.CONN_ROB_disp_writeBuffer.setText(write_buffer)
        self.CONN_ROB_disp_bytesWritten.setText(str(num_send))


    def robo_recv(self, raw_data_string:str, telem:du.RoboTelemetry) -> None:
        """write robots telemetry to log & user displays, resetting globals
        position variables is done by RobCommWorker"""

        # set the fist given position to zero as this is usually the standard
        # position for Rob2, take current ID
        if self._first_pos:
            du.ROBMovStartP = dcpy(du.ROBTelem.Coor)
            du.ROBMovEndP = dcpy(du.ROBTelem.Coor)
            self.set_zero([1, 2, 3, 4, 5, 6, 8])
            self._first_pos = False

        if telem.id != self._last_comm_id:
            log_txt = f"ID {telem.id},   {telem.Coor}   ToolSpeed: {telem.t_speed}"
            
            if du.PMP1Serial.connected:
                log_txt += f"   PMP1: {self._LastP1Telem}"
            if du.PMP2Serial.connected:
                log_txt += f"   PMP2: {self._LastP2Telem}"

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
            ans_len = 4 if isinstance(ans, int) else 0
            # sys.getsizeof(int) returns 28, because of python and objects 
            # and stuff so I will just hard code it
            displays[3].setText(str(ans_len))

            self.log_entry(
                f"PMP{p_num}", f"speed set to {speed}, command: {command}"
            )

        match source:
            case 'P1':
                displays = [
                    self.CONN_PUMP1_disp_writeBuffer,
                    self.CONN_PUMP1_disp_bytesWritten,
                    self.CONN_PUMP1_disp_readBuffer,
                    self.CONN_PUMP1_disp_bytesToRead,
                ]
                p_send(displays, du.PMP1_speed, 1)

            case 'P2':
                displays = [
                    self.CONN_PUMP2_disp_writeBuffer,
                    self.CONN_PUMP2_disp_bytesWritten,
                    self.CONN_PUMP2_disp_readBuffer,
                    self.CONN_PUMP2_disp_bytesToRead,
                ]
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
            with QMutexLocker(GlobalMutex):
                du.PMP_speed = curr_total
                du.PMP_output_ratio = p1_ratio

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
            # to-do: display recv and recv length
            display[0].setText(f"{stt_data.freq}%")
            display[1].setText(f"{stt_data.volt} V")
            display[2].setText(f"{stt_data.amps} A")            
            display[3].setText(f"{stt_data.torq} Nm")
            setattr(self, dump, telem)

        match source:
            case 'P1':
                displays = [
                    self.PUMP_disp_freqP1,
                    self.PUMP_disp_voltP1,
                    self.PUMP_disp_ampsP1,
                    self.PUMP_disp_torqP1
                ]
                p_recv(displays, du.STTDataBlock.Pump1, '_LastP1Telem')

            case 'P2':
                displays = [
                    self.PUMP_disp_freqP2,
                    self.PUMP_disp_voltP2,
                    self.PUMP_disp_ampsP2,
                    self.PUMP_disp_torqP2
                ]
                p_recv(displays, du.STTDataBlock.Pump2, '_LastP2Telem')

            case _:
                raise KeyError(
                    f"Received Pump Telem from unspecified source ({source})!"
                )


    def prh_send(self, mixer_speed:float) -> None:
        """display printhead communication"""

        self.CONN_PRH_disp_writeBuffer.setText(str(mixer_speed))
        self.CONN_PRH_disp_bytesWritten.setText("length of float")
        self.log_entry('PRTH', f"speed set to {mixer_speed}")


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
        self.CONN_ROB_disp_readBuffer.setText(data_string)
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

        self.ADC_num_trolley.setValue(entry.Tool.trolley_steps)
        self.ASC_num_trolley.setValue(entry.Tool.trolley_steps)
        self.ADC_btt_clamp.setChecked(entry.Tool.clamp)
        self.ASC_btt_clamp.setChecked(entry.Tool.clamp)
        self.ADC_btt_cut.setChecked(entry.Tool.cut)
        self.ASC_btt_cut.setChecked(entry.Tool.cut)
        self.ADC_btt_placeSpring.setChecked(entry.Tool.place_spring)
        self.ASC_btt_placeSpring.setChecked(entry.Tool.place_spring)

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
    #                      COMMAND QUEUE HELP FUNCTIONS                      #
    ##########################################################################

    def sc_id_overwrite(self) -> None:
        """synchronize SC and ROB ID with this, if program falls out of sync
        with the robot, should happen only with on-the-fly restarts,
        theoretically
        """
        
        if du.DC_rob_moving:
            return
        
        new_sc_id = self.SID_num_overwrite.value()
        with QMutexLocker(GlobalMutex):
            id_dist = new_sc_id - du.SC_curr_comm_id
            du.SC_curr_comm_id = new_sc_id
            du.SCQueue.increment(id_dist)
            last_rob_update = self.CONN_ROB_disp_readBuffer.text()

        self.label_update_on_receive(data_string=last_rob_update)
        self.log_entry('GNRL', f"User overwrote current comm ID to {du.SC_curr_comm_id}.")


    def start_SCTRL_queue(self) -> None:
        """set UI indicators, send the boring work of timing the command to
        our trusty threads
        """

        # set parameters
        with QMutexLocker(GlobalMutex):
            du.SC_q_processing = True
            du.SC_q_prep_end = False
        self.log_entry("ComQ", "queue processing started")

        # update GUI
        css = "border-radius: 20px; background-color: #00aaff;"
        self.SCTRL_indi_qProcessing.setStyleSheet(css)
        self.CONN_indi_qProcessing.setStyleSheet(css)
        self.ASC_indi_qProcessing.setStyleSheet(css)

        for widget in self.ASC_group:
            widget.setEnabled(False)
        self.switch_rob_moving()

        self.label_update_on_queue_change()


    def stop_SCTRL_queue(self, prep_end=False) -> None:
        """set UI indicators, turn off threads"""
        # to-do: stop pumps

        if prep_end:
            css = "border-radius: 20px; background-color: #ffda1e;"
            du.SC_q_prep_end = True

        else:
            with QMutexLocker(GlobalMutex):
                du.PMP_speed = 0
                du.SC_q_prep_end = False
                du.SC_q_processing = False
            self.log_entry("ComQ", "queue processing stopped")

            self.label_update_on_queue_change()
            self.switch_rob_moving(end=True)
            css = "border-radius: 20px; background-color: #4c4a48;"

            for widget in self.ASC_group:
                widget.setEnabled(True)

        # update GUI
        self.SCTRL_indi_qProcessing.setStyleSheet(css)
        self.CONN_indi_qProcessing.setStyleSheet(css)
        self.ASC_indi_qProcessing.setStyleSheet(css)
    

    def clr_queue(self, partial=False) -> None:
        """delete specific or all items from queue"""

        with QMutexLocker(GlobalMutex):
            if partial:
                du.SCQueue.clear(all=False, id=self.SCTRL_entry_clrByID.text())
            else:
                du.SCQueue.clear(all=True)

        if not partial:
            self.log_entry("ComQ", "queue emptied by user")
        else:
            self.log_entry(
                "ComQ",
                f"queue IDs cleared: {self.SCTRL_entry_clrByID.text()}"
            )
        self.label_update_on_queue_change()


    ##########################################################################
    #                            DC HELP COMMANDS                            #
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

        with QMutexLocker(GlobalMutex):
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


    ##########################################################################
    #                                SET ZERO                                #
    ##########################################################################


    def set_zero(self, axis:list, source='') -> None:
        """overwrite DC_curr_zero, uses deepcopy to avoid large mutual
        exclusion blocks
        """

        NewZero = dcpy(du.DCCurrZero)
        if source == 'sys_monitor':
            ZeroOverwrite = du.Coordinate(
                x=self.ZERO_float_x.value(),
                y=self.ZERO_float_y.value(),
                z=self.ZERO_float_z.value(),
                rx=self.ZERO_float_rx.value(),
                ry=self.ZERO_float_ry.value(),
                rz=self.ZERO_float_rz.value(),
                ext=self.ZERO_float_ext.value(),
            )
        elif source == 'file':
            try:
                with open(du.LOG_safe_path, 'r') as save_file:
                    zero_vals = save_file.read().split('_')
                    ZeroOverwrite = du.Coordinate(zero_vals)
            except Exception as e:
                self.log_entry(
                    'ZERO',
                    f"failed to load ZERO data from {du.LOG_safe_path} due to {e}!"
                )
                return
        else:
            ZeroOverwrite = dcpy(du.ROBTelem.Coor)

        if axis:
            # 7 is a placeholder for Q, which can not be set by hand
            if 1 in axis:
                NewZero.x = ZeroOverwrite.x
            if 2 in axis:
                NewZero.y = ZeroOverwrite.y
            if 3 in axis:
                NewZero.z = ZeroOverwrite.z
            if 4 in axis:
                NewZero.rx = ZeroOverwrite.rx
            if 5 in axis:
                NewZero.ry = ZeroOverwrite.ry
            if 6 in axis:
                NewZero.rz = ZeroOverwrite.rz
            if 8 in axis:
                NewZero.ext = ZeroOverwrite.ext

            with QMutexLocker(GlobalMutex):
                du.DCCurrZero = NewZero

        self.label_update_on_new_zero()
        self.log_entry(
            'ZERO',
            f"current zero position updated: ({du.DCCurrZero})"
        )




class Watchdog(QObject):
    
    logEntry = pyqtSignal(str, str)
    criticalBite = pyqtSignal()
    disconnectDevice = pyqtSignal(str, bool)
    closeMainframe = pyqtSignal()

    def __init__(
            self,
            operation_critical:bool,
            name:str,
            device:str,
            token:str
    ) -> None:
        """setup and validate input"""

        super().__init__()
        self._name = name
        self._device = device
        if not hasattr(du, device):
            raise AttributeError(f"{device} doesn't exist in data_utilities!")
        self._token = token
        self._critical = operation_critical
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.setInterval(du.DEF_WD_TIMEOUT) 
        self._timer.timeout.connect(self.bite)


    def start(self) -> None:
        """set Watchdog, check data updates from device occure at
        least every 10 sec
        """
        
        self._timer.start()
        self.logEntry.emit('WDOG', f"Watchdog {self.name} started.")

    def reset(self) -> None:
        """reset the Watchdog on every newly received data block, check
        connection everytime if disconnected inbetween
        """

        Connection = getattr(du, self._device)
        try:
            if Connection.connected:
                self._timer.start()
        except AttributeError:
            if getattr(du, self._device):
                self._timer.start()


    def bite(self) -> None:
        """infrom user on any biting WD, log info"""

        # stop critical operations, build user text
        if du.SC_q_processing and self._critical:
            wd_txt = (
                f"Watchdog {self.name} has bitten! Stopping script control & "
                f"forwarding forced-stop to robot!"
            )
            self.logEntry.emit('WDOG', wd_txt)
            self.criticalBite.emit()
        else:
            wd_txt = f"Watchdog {self.name} has bitten!"
            self.logEntry.emit('WDOG', wd_txt)
            
        # disconnect, also stops watchdog
        self.disconnectDevice.emit(self._token, True)

        # ask user to close application
        usr_txt = f"{wd_txt}\nOK to continue or Cancel to exit and close."
        warning = strd_dialog(usr_txt, "WATCHDOG ALARM")
        warning.exec()

        if warning.result():
            self.logEntry.emit('WDOG', f"User chose to return to main screen.")
        else:
            self.logEntry.emit(
                'WDOG',
                f"User chose to close PRINT_py, exiting..."
            )
            self.closeMainframe.emit()


    def kill(self) -> None:
        """put them to sleep (dont do this to real dogs)"""

        self._timer.stop()
        self.logEntry.emit('WDOG', f"Watchdog {self.name} stopped.")


    @property
    def name(self):
        return self._name

    @property
    def device(self):
        return self._device

    @property
    def token(self):
        return self._token



##################################   MAIN  ###################################

# mutual exclusion object, used to manage global data exchange
GlobalMutex = QMutex()

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
    win = PreMainframe(lpath=logpath)
    win.show()

    # start application (uses sys for CMD)
    app.exec()
    # sys.exit(app.exec())