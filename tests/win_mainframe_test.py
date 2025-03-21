# test win_mainframe

################################## IMPORTS ###################################

import os
import sys
import copy
import unittest
import pathlib as pl

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du
import libs.win_mainframe as mf

from libs.win_daq import DAQWindow as DAQ
from libs.threads import (
    RoboCommWorker, PumpCommWorker, LoadFileWorker, SensorCommWorker
)



################################### TESTS ####################################

class MainframeWinTest(unittest.TestCase):


    def assert_is_file(self, path):
        """program file exist error"""

        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"No such file: {path}")


    def test_adc_user_change(self):
        global TestFrame
        global ACON_btt_group

        TestFrame.ADC_num_trolley.blockSignals(True)
        for widget in ACON_btt_group:
            widget.blockSignals(True)

        TestFrame.ADC_num_trolley.setValue(11)
        TestFrame.ADC_btt_clamp.setChecked(True)
        TestFrame.ADC_btt_cut.setChecked(True)
        TestFrame.ADC_btt_placeSpring.setChecked(False)

        TestFrame.adc_user_change()
        TestTool = du.ToolCommand(11, True, True, False, False, 0)
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=1, z=0, Tool=TestTool))

        du.SC_curr_comm_id = 1
        TestFrame.ADC_num_trolley.setValue(du.DEF_PRH_TROLLEY)
        TestFrame.ADC_btt_clamp.setChecked(du.DEF_PRH_CLAMP)
        TestFrame.ADC_btt_cut.setChecked(du.DEF_PRH_CUT)
        TestFrame.ADC_btt_placeSpring.setChecked(du.DEF_PRH_PLACE_SPR)

        TestFrame.ADC_num_trolley.blockSignals(False)
        for widget in ACON_btt_group:
            widget.blockSignals(False)

        du.ROBCommQueue.clear()
        du.ROB_send_list.clear()


    def test_add_gcode_sgl(self):
        global TestFrame

        du.SCQueue.clear()
        du.DCCurrZero = du.Coordinate()

        # G1
        TestCoor1 = du.Coordinate(x=1, y=2.2, ext=3)
        TestVec = du.SpeedVector(ts=4)
        TestFrame.SGLC_entry_gcodeSglComm.setText('G1 X1 Y2.2 EXT3 F40')
        TestFrame.add_gcode_sgl()
        self.assertEqual(
            du.SCQueue.display(),
            [du.QEntry(id=1, Coor1=TestCoor1, Speed=TestVec).print_short()],
        )

        TestFrame.SGLC_entry_gcodeSglComm.setText('G1 X1')
        du.DCCurrZero = du.Coordinate(x=1, y=1)
        TestFrame.add_gcode_sgl(at_id=True, id=1)
        TestCoor2 = du.Coordinate(x=2, y=1)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor2).print_short(),
                du.QEntry(id=2, Coor1=TestCoor1, Speed=TestVec).print_short(),
            ],
        )

        TestFrame.add_gcode_sgl(
            at_id=True,
            id=2,
            from_file=True,
            file_txt='G1 Z1'
        )
        TestCoor3 = du.Coordinate(x=2, y=1, z=1)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor2).print_short(),
                du.QEntry(id=2, Coor1=TestCoor3).print_short(),
                du.QEntry(id=3, Coor1=TestCoor1, Speed=TestVec).print_short(),
            ],
        )

        TestFrame.add_gcode_sgl(
            at_id=False,
            id=0,
            from_file=True,
            file_txt='G1 X1.2'
        )
        TestCoor4 = du.Coordinate(x=2.2, y=2.2, ext=0)
        self.assertEqual(
            du.SCQueue.display(),
            [
                
                du.QEntry(id=1, Coor1=TestCoor2).print_short(),
                du.QEntry(id=2, Coor1=TestCoor3).print_short(),
                du.QEntry(id=3, Coor1=TestCoor1, Speed=TestVec).print_short(),
                du.QEntry(id=4, Coor1=TestCoor4).print_short(),
                # here, the external axis is set to 0, as a change in X 
                # activates the recalculation of the appropriate EXT position 
                # in UTIL.gcodeToQEntry using UTIL.SC_extFllwBhvr
            ],
        )

        # G28 & G92
        TestFrame.add_gcode_sgl(
            at_id=False,
            id=0,
            from_file=True,
            file_txt='G92 Y0 EXT0'
        )
        self.assertEqual(du.DCCurrZero, du.Coordinate(x=1, y=2.2))

        TestFrame.add_gcode_sgl(
            at_id=False,
            id=0,
            from_file=True,
            file_txt='G28 Y0 EXT0'
        )
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor2).print_short(),
                du.QEntry(id=2, Coor1=TestCoor3).print_short(),
                du.QEntry(id=3, Coor1=TestCoor1, Speed=TestVec).print_short(),
                du.QEntry(id=4, Coor1=TestCoor4).print_short(),
                du.QEntry(id=5, Coor1=TestCoor4).print_short(),
            ],
        )

        TestFrame.add_gcode_sgl(
            at_id=True,
            id=3,
            from_file=True,
            file_txt='G92 X0 Z0'
        )
        self.assertEqual(du.DCCurrZero, du.Coordinate(x=2, y=2.2, z=1, ext=0))

        du.DCCurrZero = du.Coordinate()
        du.SCQueue.clear()


    def test_add_rapid_sgl(self):
        global TestFrame

        du.DCCurrZero = du.Coordinate()
        TestFrame.SGLC_entry_rapidSglComm.setText(
            f"MoveL [[1.0,2.2,0.0][0.0,0.0,0.0,0.0]],"
            f"[4,50,50,50],z10,tool0 EXT3;"
        )
        TestFrame.add_rapid_sgl()
        TCoor1 = du.Coordinate(x=1, y=2.2, ext=3)
        Sp = du.SpeedVector(ts=4)
        self.assertEqual(
            du.SCQueue.display(),
            [du.QEntry(id=1, pt="Q", Coor1=TCoor1, Speed=Sp).print_short()],
        )

        TestFrame.SGLC_entry_rapidSglComm.setText(
            f"MoveL [[1.0,0.0,0.0][0.0,0.0,0.0,0.0]],[200,50,50,50],"
            f"z10,tool0 EXT0.0;"
        )
        TestFrame.add_rapid_sgl(at_id=True, id=1)
        TCoor2 = du.Coordinate(x=1)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, pt="Q", Coor1=TCoor2).print_short(),
                du.QEntry(id=2, pt="Q", Coor1=TCoor1, Speed=Sp).print_short()
            ],
        )

        du.DCCurrZero = du.Coordinate(z=1)
        TestFrame.add_rapid_sgl(
            at_id=True,
            id=2,
            from_file=True,
            file_txt=(
                f"MoveL Offs(pHome,0.0,0.0,1.0),[200,50,50,50],"
                f"z10,tool0 EXT0;"
            )
        )
        TestCoor3 = du.Coordinate(z=2)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, pt="Q", Coor1=TCoor2).print_short(),
                du.QEntry(id=2, pt="E", Coor1=TestCoor3).print_short(),
                du.QEntry(id=3, pt="Q", Coor1=TCoor1, Speed=Sp).print_short()
            ],
        )

        du.DCCurrZero = du.Coordinate()
        du.SCQueue.clear()


    def test_add_SIB(self):
        global TestFrame
        self.maxDiff = 2000

        TestFrame.SIB_entry_sib1.setText(
            f"G1 X1.0 Y2.0 Z3.0 F4000 EXT500\n"
            f"G1 X6.0 Y7.0 Z8.0 F9000 EXT990"
        )
        TestFrame.SIB_entry_sib2.setText(
            f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],"
            f"[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT600\n"
            f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT160"
        )
        TestFrame.SIB_entry_sib3.setText(
            f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],"
            f"[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT600\n"
            f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT160"
        )

        TestFrame.add_SIB(num=1, at_end=False)
        TCoor1 = du.Coordinate(x=1, y=2, z=3, ext=500)
        TCoor2 = du.Coordinate(x=6, y=7, z=8, ext=990)
        Sp1 = du.SpeedVector(ts=400)
        Sp2 = du.SpeedVector(ts=900)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TCoor1, Speed=Sp1).print_short(),
                du.QEntry(id=2, Coor1=TCoor2, Speed=Sp2).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate(x=1)
        TestFrame.add_SIB(num=2, at_end=True)
        TCoor3 = du.Coordinate(
            x=1.1,y=2.2, z=3.3, rx=4.4, ry=5.5, rz=6.6, q=7.7, ext=600
        )
        TCoor4 = du.Coordinate(x=8, y=8, z=9, ext=160)
        Sp3 = du.SpeedVector(ts=18, ors=19, acr=20, dcr=21)
        Sp4 = du.SpeedVector(ts=110, ors=120, acr=130, dcr=140)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TCoor1, Speed=Sp1).print_short(),
                du.QEntry(id=2, Coor1=TCoor2, Speed=Sp2).print_short(),
                du.QEntry(id=3, pt='Q', Coor1=TCoor3, Speed=Sp3).print_short(),
                du.QEntry(id=4, mt='J', Coor1=TCoor4, Speed=Sp4).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate(x=1)
        TestFrame.add_SIB(num=3, at_end=False)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, pt='Q', Coor1=TCoor3, Speed=Sp3).print_short(),
                du.QEntry(id=2, mt='J', Coor1=TCoor4, Speed=Sp4).print_short(),
                du.QEntry(id=3, Coor1=TCoor1, Speed=Sp1).print_short(),
                du.QEntry(id=4, Coor1=TCoor2, Speed=Sp2).print_short(),
                du.QEntry(id=5, pt='Q', Coor1=TCoor3, Speed=Sp3).print_short(),
                du.QEntry(id=6, mt='J', Coor1=TCoor4, Speed=Sp4).print_short(),
            ],
        )

        du.SCQueue.clear()
        du.DCCurrZero = du.Coordinate()


    def test_amcon_script_overwrite(self):
        global TestFrame
        self.maxDiff = 3000

        du.SCQueue.clear()
        for i in range(1, 5, 1):
            TestFrame.add_gcode_sgl(
                at_id=False, id=0, from_file=True, file_txt=f"G1 X{i}"
            )
        TestFrame.ASC_num_trolley.setValue(11)
        TestFrame.ASC_btt_clamp.setChecked(True)
        TestFrame.ASC_btt_cut.setChecked(True)
        TestFrame.ASC_btt_placeSpring.setChecked(True)
        TestFrame.ASC_entry_SCLines.setText('2..3')
        TestFrame.amcon_script_overwrite()

        ToolOff = du.ToolCommand()
        ToolOn = du.ToolCommand(11, True, True, True, False, 0)
        self.assertEqual(
            f"{du.SCQueue}",
            f"{du.QEntry(id=1, Coor1=du.Coordinate(x=1), Tool=ToolOff)}\n"\
            f"{du.QEntry(id=2, Coor1=du.Coordinate(x=2), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=3, Coor1=du.Coordinate(x=3), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=4, Coor1=du.Coordinate(x=4), Tool=ToolOff)}\n"
        )

        TestFrame.ASC_entry_SCLines.setText('4')
        TestFrame.amcon_script_overwrite()
        self.assertEqual(
            f"{du.SCQueue}",
            f"{du.QEntry(id=1, Coor1=du.Coordinate(x=1), Tool=ToolOff)}\n"\
            f"{du.QEntry(id=2, Coor1=du.Coordinate(x=2), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=3, Coor1=du.Coordinate(x=3), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=4, Coor1=du.Coordinate(x=4), Tool=ToolOn)}\n"
        )

        TestFrame.clr_queue(partial=False)
        TestFrame.ASC_num_trolley.setValue(du.DEF_PRH_TROLLEY)
        TestFrame.ASC_btt_clamp.setChecked(du.DEF_PRH_CLAMP)
        TestFrame.ASC_btt_cut.setChecked(du.DEF_PRH_CUT)
        TestFrame.ASC_btt_placeSpring.setChecked(du.DEF_PRH_PLACE_SPR)


    def test_apply_settings(self):
        """tests default settings loading in '__init__' and 'updateCommForerun' as well"""
        global TestFrame

        # check if defaults were loaded
        self.assertEqual(TestFrame.SET_num_zone.value(), du.DEF_IO_ZONE)
        self.assertEqual(
            TestFrame.CONN_num_commForerun.value(), du.DEF_ROB_COMM_FR
        )
        self.assertEqual(
            TestFrame.SET_float_volPerMM.value(), du.DEF_SC_VOL_PER_M
        )
        self.assertEqual(
            TestFrame.SET_float_frToMms.value(), du.DEF_IO_FR_TO_TS
        )
        self.assertEqual(
            TestFrame.SET_num_transSpeed_dc.value(), du.DEF_DC_SPEED.ts
        )
        self.assertEqual(
            TestFrame.SET_num_orientSpeed_dc.value(), du.DEF_DC_SPEED.ors
        )
        self.assertEqual(
            TestFrame.SET_num_accelRamp_dc.value(), du.DEF_DC_SPEED.acr
        )
        self.assertEqual(
            TestFrame.SET_num_decelRamp_dc.value(), du.DEF_DC_SPEED.dcr
        )
        self.assertEqual(
            TestFrame.SET_num_transSpeed_print.value(), du.DEF_PRIN_SPEED.ts
        )
        self.assertEqual(
            TestFrame.SET_num_orientSpeed_print.value(), du.DEF_PRIN_SPEED.ors
        )
        self.assertEqual(
            TestFrame.SET_num_accelRamp_print.value(), du.DEF_PRIN_SPEED.acr
        )
        self.assertEqual(
            TestFrame.SET_num_decelRamp_print.value(), du.DEF_PRIN_SPEED.dcr
        )
        self.assertEqual(
            TestFrame.SET_num_followInterv.value(),
            du.DEF_SC_EXT_TRAIL[0],
        )
        self.assertEqual(
            TestFrame.SET_num_followSkip.value(),
            du.DEF_SC_EXT_TRAIL[1],
        )
        self.assertEqual(
            TestFrame.SET_num_retractSpeed.value(), du.DEF_PUMP_RETR_SPEED
        )
        self.assertEqual(
            TestFrame.SET_float_p1Flow.value(), du.DEF_PUMP_LPS
        )
        self.assertEqual(
            TestFrame.SET_float_p2Flow.value(), du.DEF_PUMP_LPS
        )
        self.assertEqual(
            TestFrame.ADC_num_trolley.value(), du.DEF_PRH_TROLLEY
        )
        self.assertEqual(
            TestFrame.ADC_btt_clamp.isChecked(), du.DEF_PRH_CLAMP
        )
        self.assertEqual(
            TestFrame.ADC_btt_cut.isChecked(), du.DEF_PRH_CUT
        )
        self.assertEqual(
            TestFrame.ADC_btt_placeSpring.isChecked(), du.DEF_PRH_PLACE_SPR
        )
        self.assertEqual(
            TestFrame.ASC_num_trolley.value(), du.DEF_PRH_TROLLEY
        )
        self.assertEqual(
            TestFrame.ASC_btt_clamp.isChecked(), du.DEF_PRH_CLAMP
        )
        self.assertEqual(
            TestFrame.ASC_btt_cut.isChecked(), du.DEF_PRH_CUT
        )
        self.assertEqual(
            TestFrame.ASC_btt_placeSpring.isChecked(), du.DEF_PRH_PLACE_SPR
        )

        # test setting by user
        TestFrame.CONN_num_commForerun.setValue(1)
        TestFrame.SET_float_volPerMM.setValue(2.2)
        TestFrame.SET_float_frToMms.setValue(3.3)
        TestFrame.SET_num_zone.setValue(4)
        TestFrame.SET_num_transSpeed_dc.setValue(5)
        TestFrame.SET_num_orientSpeed_dc.setValue(6)
        TestFrame.SET_num_accelRamp_dc.setValue(7)
        TestFrame.SET_num_decelRamp_dc.setValue(8)
        TestFrame.SET_num_transSpeed_print.setValue(9)
        TestFrame.SET_num_orientSpeed_print.setValue(10)
        TestFrame.SET_num_accelRamp_print.setValue(11)
        TestFrame.SET_num_decelRamp_print.setValue(12)
        TestFrame.SET_num_followInterv.setValue(13)
        TestFrame.SET_num_followSkip.setValue(14)
        TestFrame.SET_num_retractSpeed.setValue(15)
        TestFrame.SET_float_p1Flow.setValue(16)
        TestFrame.SET_float_p2Flow.setValue(17)
        TestFrame.apply_settings()

        self.assertEqual(du.ROB_comm_fr, 1)
        self.assertEqual(du.SC_vol_per_m, 2.2)
        self.assertEqual(du.IO_fr_to_ts, 3.3)
        self.assertEqual(du.IO_zone, 4)
        self.assertEqual(du.DCSpeed.ts, 5)
        self.assertEqual(du.DCSpeed.ors, 6)
        self.assertEqual(du.DCSpeed.acr, 7)
        self.assertEqual(du.DCSpeed.dcr, 8)
        self.assertEqual(du.PRINSpeed.ts, 9)
        self.assertEqual(du.PRINSpeed.ors, 10)
        self.assertEqual(du.PRINSpeed.acr, 11)
        self.assertEqual(du.PRINSpeed.dcr, 12)
        self.assertEqual(du.SC_ext_trail[0], 13)
        self.assertEqual(du.SC_ext_trail[1], 14)
        self.assertEqual(du.PMP_retract_speed, 15)
        self.assertEqual(du.PMP1_liter_per_s, 16)
        self.assertEqual(du.PMP2_liter_per_s, 17)

        # test resetting by user
        TestFrame.CONN_num_commForerun.setValue(10)
        TestFrame.load_defaults()
        TestFrame.apply_settings()

        self.assertEqual(TestFrame.SET_num_zone.value(), du.DEF_IO_ZONE)
        self.assertEqual(
            TestFrame.CONN_num_commForerun.value(), du.DEF_ROB_COMM_FR
        )
        self.assertEqual(
            TestFrame.SET_float_volPerMM.value(), du.DEF_SC_VOL_PER_M
        )
        self.assertEqual(
            TestFrame.SET_float_frToMms.value(), du.DEF_IO_FR_TO_TS
        )
        self.assertEqual(
            TestFrame.SET_num_transSpeed_dc.value(), du.DEF_DC_SPEED.ts
        )
        self.assertEqual(
            TestFrame.SET_num_orientSpeed_dc.value(), du.DEF_DC_SPEED.ors
        )
        self.assertEqual(
            TestFrame.SET_num_accelRamp_dc.value(), du.DEF_DC_SPEED.acr
        )
        self.assertEqual(
            TestFrame.SET_num_decelRamp_dc.value(), du.DEF_DC_SPEED.dcr
        )
        self.assertEqual(
            TestFrame.SET_num_transSpeed_print.value(), du.DEF_PRIN_SPEED.ts
        )
        self.assertEqual(
            TestFrame.SET_num_orientSpeed_print.value(), du.DEF_PRIN_SPEED.ors
        )
        self.assertEqual(
            TestFrame.SET_num_accelRamp_print.value(), du.DEF_PRIN_SPEED.acr
        )
        self.assertEqual(
            TestFrame.SET_num_decelRamp_print.value(), du.DEF_PRIN_SPEED.dcr
        )
        self.assertEqual(
            TestFrame.SET_num_followInterv.value(),
            du.DEF_SC_EXT_TRAIL[0],
        )
        self.assertEqual(
            TestFrame.SET_num_followSkip.value(),
            du.DEF_SC_EXT_TRAIL[1],
        )
        self.assertEqual(
            TestFrame.SET_num_retractSpeed.value(), du.DEF_PUMP_RETR_SPEED
        )
        self.assertEqual(
            TestFrame.SET_float_p1Flow.value(), du.DEF_PUMP_LPS
        )
        self.assertEqual(
            TestFrame.SET_float_p2Flow.value(), du.DEF_PUMP_LPS
        )


    def test_clr_queue(self):
        global TestFrame
        self.maxDiff = 2000

        du.SCQueue.clear()
        du.SC_ext_trail = (500, 200)

        for i in range(1, 7, 1):
            TestFrame.add_gcode_sgl(
                at_id=False, id=0, from_file=True, file_txt=f"G1 X{i}"
            )

        TestFrame.SCTRL_entry_clrByID.setText('2..4')
        TestFrame.clr_queue(partial=True)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=5)).print_short(),
                du.QEntry(id=3, Coor1=du.Coordinate(x=6)).print_short(),
            ],
        )

        TestFrame.SCTRL_entry_clrByID.setText('2')
        TestFrame.clr_queue(partial=True)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=6)).print_short(),
            ],
        )

        TestFrame.clr_queue(partial=False)
        self.assertEqual(du.SCQueue.display(), ['Queue is empty!'])

        du.SC_ext_trail = du.DEF_SC_EXT_TRAIL


    def test_home_command(self):
        global TestFrame

        TestHome = du.Coordinate(
            x=1, y=2000, z=0, rx=4, ry=5, rz=6, q=0.5, ext=100
        )
        du.DCCurrZero = copy.deepcopy(TestHome)
        TestFrame.DC_drpd_moveType.setCurrentText('LINEAR')
        TestFrame.home_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command[0], du.QEntry(id=1, z=0, Coor1=TestHome))
        self.assertTrue(du.DC_rob_moving)

        TestFrame.robo_send(command[0], True, 1, True)
        du.DC_rob_moving = False

        TestFrame.DC_drpd_moveType.setCurrentText("JOINT")
        TestFrame.home_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(id=2, z=0, mt="J", Coor1=TestHome),
        )

        du.DCCurrZero = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.DC_rob_moving = False
        du.SCQueue.clear()


    def test_init(self):
        global TestFrame
        global logpath

        # general values
        self.assertEqual(TestFrame._logpath, logpath)
        self.assertIsInstance(TestFrame.Daq, DAQ)

        # logfile
        self.assert_is_file(logpath)
        logfileCheck = open(logpath, 'r')
        logfileCheckTxt = logfileCheck.read()
        logfileCheck.close()
        self.assertIn('setup finished.', logfileCheckTxt)

        # defaults test with 'applySettings'

        # threads -- R
        self.assertIsInstance(TestFrame._RoboCommThread, QThread)
        self.assertIsInstance(TestFrame._PumpCommThread, QThread)
        self.assertIsInstance(TestFrame._LoadFileThread, QThread)
        self.assertIsInstance(TestFrame._SensorArrThread, QThread)
        self.assertIsInstance(TestFrame._RoboCommWorker, RoboCommWorker)
        self.assertIsInstance(TestFrame._PumpCommWorker, PumpCommWorker)
        self.assertIsInstance(TestFrame._LoadFileWorker, LoadFileWorker)
        self.assertIsInstance(TestFrame._SensorArrWorker, SensorCommWorker)


    def test_label_update_on_new_zero(self):
        """rababer rababer"""
        global TestFrame

        du.DCCurrZero = du.Coordinate(1.1, 2, 3, 4, 5, 6, 7, 8)
        TestFrame.label_update_on_new_zero()

        self.assertEqual(TestFrame.ZERO_disp_x.text(), '1.1')
        self.assertEqual(TestFrame.ZERO_disp_y.text(), '2.0')
        self.assertEqual(TestFrame.ZERO_disp_z.text(), '3.0')
        self.assertEqual(TestFrame.ZERO_disp_rx.text(), '4.0')
        self.assertEqual(TestFrame.ZERO_disp_ry.text(), '5.0')
        self.assertEqual(TestFrame.ZERO_disp_rz.text(), '6.0')
        self.assertEqual(TestFrame.ZERO_disp_ext.text(), '8.0')

        du.DCCurrZero = du.Coordinate()


    def test_label_update_on_send(self):
        """test labelUpdate_onQueueChange as well"""
        global TestFrame
        global ACON_btt_group

        du.DCCurrZero = du.Coordinate()

        TestFrame.SGLC_entry_gcodeSglComm.setText('G1 X2.2 Y1')
        TestTool = du.ToolCommand(1, True, True, False, True, 0)
        TestFrame.add_gcode_sgl()
        TestFrame.label_update_on_send(entry=du.QEntry(Tool=TestTool))

        self.assertEqual(TestFrame.SCTRL_disp_elemInQ.text(), '1')
        self.assertEqual(TestFrame.SCTRL_disp_buffComms.text(), '0')
        self.assertEqual(TestFrame.ADC_num_trolley.value(), 1)
        self.assertEqual(TestFrame.ADC_btt_clamp.isChecked(), True)
        self.assertEqual(TestFrame.ADC_btt_cut.isChecked(), True)
        self.assertEqual(TestFrame.ADC_btt_placeSpring.isChecked(), False)
        self.assertEqual(TestFrame.ASC_num_trolley.value(), 1)
        self.assertEqual(TestFrame.ASC_btt_clamp.isChecked(), True)
        self.assertEqual(TestFrame.ASC_btt_cut.isChecked(), True)
        self.assertEqual(TestFrame.ASC_btt_placeSpring.isChecked(), False)

        # secondarily calls label_update_on_queue_change
        self.assertEqual(
            TestFrame.SCTRL_arr_queue.item(0).text(),
            du.QEntry(id=1, Coor1=du.Coordinate(x=2.2, y=1)).print_short(),
        )
        du.SCQueue.clear()


    def test_load_file(self):
        global TestFrame

        du.IO_curr_filepath = pl.Path("test.abc")
        TestFrame.load_file()
        self.assertEqual(
            TestFrame.IO_lbl_loadFile.text(),
            '... no valid file, not executed',
        )

        du.IO_curr_filepath = pl.Path("test.mod")
        TestFrame.load_file(testrun=True)
        self.assertEqual(
            TestFrame.IO_lbl_loadFile.text(),
            '... conversion running ...',
        )

        du.IO_curr_filepath = None


    def test_load_file_finished(self):
        """no need to test loadFileFailed, skip to loadFileFinished"""
        global TestFrame

        TestFrame.load_file_finished(line_id=1, start_id=2, skips=3)
        self.assertEqual(TestFrame.IO_num_addByID.value(), 1)
        self.assertEqual(
            TestFrame.IO_lbl_loadFile.text(),
            '... conversion successful',
        )


    def test_mixer_set_speed(self):
        global TestFrame

        TestFrame.PRH_num_setSpeed.setValue(56)
        TestFrame.PRH_sld_speed.setValue(78)

        TestFrame.mixer_set_speed()
        self.assertEqual(du.MIX_speed, 56)
        TestFrame.mixer_set_speed('sld')
        self.assertEqual(du.MIX_speed, 78)
        TestFrame.mixer_set_speed('0')
        self.assertEqual(du.MIX_speed, 0)


    def test_open_file(self):
        global TestFrame
        global gcode_test_path
        global rapid_test_path

        currSetting = du.SC_vol_per_m
        du.SC_vol_per_m = 0.1

        TestFrame.open_file(testrun=True, testpath=gcode_test_path)
        self.assertEqual(du.IO_curr_filepath, gcode_test_path)
        self.assertEqual(
            TestFrame.IO_disp_filename.text(), gcode_test_path.name
        )
        self.assertEqual(TestFrame.IO_disp_commNum.text(), '2')
        self.assertEqual(TestFrame.IO_disp_estimLen.text(), '3.0 m')
        self.assertEqual(TestFrame.IO_disp_estimVol.text(), '0.3 L')

        TestFrame.open_file(testrun=True, testpath=rapid_test_path)
        self.assertEqual(du.IO_curr_filepath, rapid_test_path)
        self.assertEqual(
            TestFrame.IO_disp_filename.text(), rapid_test_path.name
        )
        self.assertEqual(TestFrame.IO_disp_commNum.text(), '2')
        self.assertEqual(TestFrame.IO_disp_estimLen.text(), '3.0 m')
        self.assertEqual(TestFrame.IO_disp_estimVol.text(), '0.3 L')

        du.SC_vol_per_m = currSetting


    def test_pump_recv(self):
        global TestFrame

        du.STTDataBlock.Pump1 = du.PumpTelemetry(1.1, 2.2, 3.3, 4.4)
        TestFrame.pump_recv(telem=du.STTDataBlock.Pump1, source='P1')

        self.assertEqual(TestFrame.PUMP_disp_freqP1.text(), '1.1%')
        self.assertEqual(TestFrame.PUMP_disp_voltP1.text(), '2.2 V')
        self.assertEqual(TestFrame.PUMP_disp_ampsP1.text(), '3.3 A')
        self.assertEqual(TestFrame.PUMP_disp_torqP1.text(), '4.4 Nm')

        du.STTDataBlock.Pump2 = du.PumpTelemetry(5, 6, 7, 8)
        du.PMP1Serial.connected = True
        du.PMP2Serial.connected = True
        TestFrame.pump_recv(telem=du.STTDataBlock.Pump2, source='P2')

        self.assertEqual(TestFrame.PUMP_disp_freqP2.text(), '5.0%')
        self.assertEqual(TestFrame.PUMP_disp_voltP2.text(), '6.0 V')
        self.assertEqual(TestFrame.PUMP_disp_ampsP2.text(), '7.0 A')
        self.assertEqual(TestFrame.PUMP_disp_torqP2.text(), '8.0 Nm')

        du.STTDataBlock.Pump1 = du.STTDataBlock.Pump2 = du.PumpTelemetry()
        du.PMP1Serial.connected = False
        du.PMP2Serial.connected = False



    def test_pump_send(self):
        global TestFrame

        TestFrame.pump_send(
            new_speed=1.1, command='ABC', ans='DEF', source='P1'
        )
        self.assertEqual(TestFrame.CONN_PUMP1_disp_writeBuffer.text(), 'ABC')
        self.assertEqual(TestFrame.CONN_PUMP1_disp_bytesWritten.text(), '3')
        self.assertEqual(TestFrame.CONN_PUMP1_disp_readBuffer.text(), 'DEF')

        TestFrame.pump_send(
            new_speed=1.1, command='ABC', ans='DEF', source='P2'
        )
        self.assertEqual(TestFrame.CONN_PUMP2_disp_writeBuffer.text(), 'ABC')
        self.assertEqual(TestFrame.CONN_PUMP2_disp_bytesWritten.text(), '3')
        self.assertEqual(TestFrame.CONN_PUMP2_disp_readBuffer.text(), 'DEF')

        # TO DO:
        # test test_frame.PUMP_disp_currSpeed.text()
        # test test_frame.PUMP_disp_outputRatio.text()


    def test_pump_set_speed(self):
        global TestFrame

        du.PMP_speed = 10
        TestFrame.PUMP_num_setSpeed.setValue(5)
        du.ROBCommQueue.add(du.QEntry(Speed=du.SpeedVector(ts=123)))

        TestFrame.pump_set_speed(flag='1')
        self.assertEqual(du.PMP_speed, 11)
        TestFrame.pump_set_speed(flag='0')
        self.assertEqual(du.PMP_speed, 0)
        TestFrame.pump_set_speed(flag='-1')
        self.assertEqual(du.PMP_speed, -1)
        TestFrame.pump_set_speed(flag='r')
        self.assertEqual(du.PMP_speed, 1)
        TestFrame.pump_set_speed()
        self.assertEqual(du.PMP_speed, 5)
        TestFrame.pump_set_speed('def')
        self.assertEqual(du.PMP_speed, 9.84)

        du.PMP_speed = 0


    def test_robo_send(self):
        """test overflow control etc. labelUpdate_onSend tested by
        own function
        """
        global TestFrame
        self.maxDiff = 2000

        du.SC_curr_comm_id = 2991
        TestFrame.robo_send(du.QEntry(id=12), True, 10, True)
        self.assertEqual(du.SC_curr_comm_id, 1)
        self.assertEqual(
            TestFrame.CONN_ROB_disp_writeBuffer.text(),
            f"ID: 12 -- L, E -- COOR_1: X: 0.0   Y: 0.0   Z: 0.0   "
            f"RX: 0.0   RY: 0.0   RZ: 0.0   Q: 0.0   EXT: 0.0 -- "
            f"SV: TS: 200   OS: 50   ACR: 50   DCR: 50 -- "
            f"PM/PR,PIN:  -1001/1.0, False",
        )
        self.assertEqual(TestFrame.CONN_ROB_disp_bytesWritten.text(), '10')

        TestFrame.robo_send(
            None,
            False,
            ValueError('None is not an instance of QEntry!'),
            False
        )
        self.assertEqual(
            TestFrame.CONN_ROB_disp_writeBuffer.text(),
            'None is not an instance of QEntry!',
        )

        du.ROB_send_list.clear()


    def test_robo_recv(self):
        """tests labelUpdate_onReceive as well"""
        global TestFrame

        # prep
        du.DCCurrZero = du.Coordinate()
        TestCoor = du.Coordinate(1, 2, 3, 4, 5, 6, 7, 8.8)
        du.ROBTelem = du.RoboTelemetry(0, 0, TestCoor)
        TestFrame.robo_recv(raw_data_string='ABC', telem=du.RoboTelemetry())

        # check loop run
        du.SC_curr_comm_id = 15
        du.DCCurrZero = du.Coordinate(0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1)
        du.ROBTelem = du.RoboTelemetry(
            9.9, 10, du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
        )
        TestFrame.robo_recv(raw_data_string='ABC', telem=du.RoboTelemetry())

        # labelUpdate_onReceive (called from roboRecv)
        self.assertEqual(TestFrame.CONN_ROB_disp_readBuffer.text(), 'ABC')
        self.assertEqual(TestFrame.SCTRL_disp_buffComms.text(), '5')
        self.assertEqual(TestFrame.SCTRL_disp_robCommID.text(), '10')
        self.assertEqual(TestFrame.SCTRL_disp_progCommID.text(), '15')
        self.assertEqual(TestFrame.SCTRL_disp_elemInQ.text(), '0')

        self.assertEqual(TestFrame.DC_disp_x.text(), '1.0')
        self.assertEqual(TestFrame.DC_disp_y.text(), '2.1')
        self.assertEqual(TestFrame.DC_disp_z.text(), '3.2')
        self.assertEqual(TestFrame.DC_disp_ext.text(), '8.7')

        self.assertEqual(TestFrame.NC_disp_x.text(), '1.1')
        self.assertEqual(TestFrame.NC_disp_y.text(), '2.2')
        self.assertEqual(TestFrame.NC_disp_z.text(), '3.3')
        self.assertEqual(TestFrame.NC_disp_rx.text(), '4.4°')
        self.assertEqual(TestFrame.NC_disp_ry.text(), '5.5°')
        self.assertEqual(TestFrame.NC_disp_rz.text(), '6.6°')
        self.assertEqual(TestFrame.NC_disp_ext.text(), '8.8')

        self.assertEqual(TestFrame.TERM_disp_tcpSpeed.text(), '9.9')
        self.assertEqual(TestFrame.TERM_disp_robCommID.text(), '10')
        self.assertEqual(TestFrame.TERM_disp_progCommID.text(), '15')

        self.assertEqual(TestFrame.SID_disp_progID.text(), '15')
        self.assertEqual(TestFrame.SID_disp_robID.text(), '10')

        self.assertEqual(TestFrame.TRANS_disp_xStart.text(), '0.9')
        self.assertEqual(TestFrame.TRANS_disp_yStart.text(), '1.9')
        self.assertEqual(TestFrame.TRANS_disp_zStart.text(), '2.9')
        self.assertEqual(TestFrame.TRANS_disp_extStart.text(), '8.7')
        self.assertEqual(TestFrame.TRANS_disp_xEnd.text(), '0.9')
        self.assertEqual(TestFrame.TRANS_disp_yEnd.text(), '1.9')
        self.assertEqual(TestFrame.TRANS_disp_zEnd.text(), '2.9')
        self.assertEqual(TestFrame.TRANS_disp_extEnd.text(), '8.7')

        du.DCCurrZero = du.Coordinate()
        du.ROBTelem = du.RoboTelemetry()
        du.SC_curr_comm_id = 1
        du.SCQueue.clear()


    def test_send_DC_command(self):
        global TestFrame

        TestFrame.DC_sld_stepWidth.setValue(1)
        TestFrame.DC_drpd_moveType.setCurrentText('LINEAR')

        du.ROBTelem.Coor = du.Coordinate(1, 2000, 0, 4, 5, 6, 0.5, 100)
        TCoor = du.Coordinate(2, 2000, 0, 4, 5, 6, 0.5, 100)
        TestFrame.send_DC_command(axis='X', dir='+')
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=1, z=0, Coor1=TCoor))

        du.DC_rob_moving = False
        TestFrame.robo_send(command, True, 1, True)
        TestFrame.DC_sld_stepWidth.setValue(2)
        TestFrame.DC_drpd_moveType.setCurrentText('JOINT')
        TCoor = du.Coordinate(1, 1990, 0, 4, 5, 6, 0.5, 100)
        TestFrame.send_DC_command(axis='Y', dir='-')
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=2, mt='J', z=0, Coor1=TCoor))

        du.DC_rob_moving = False
        TestFrame.robo_send(command, True, 1, True)
        TestFrame.DC_sld_stepWidth.setValue(3)
        TCoor = du.Coordinate(1, 2000, 100, 4, 5, 6, 0.5, 100)
        TestFrame.send_DC_command(axis='Z', dir='+')
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=3, mt='J', z=0, Coor1=TCoor))

        du.DC_rob_moving = False
        TestFrame.robo_send(command, True, 1, True)
        self.assertRaises(
            ValueError,
            TestFrame.send_DC_command,
            axis='A',
            dir='+',
        )
        du.DC_rob_moving = False
        self.assertRaises(
            ValueError,
            TestFrame.send_DC_command,
            axis='X',
            dir='/',
        )

        du.DC_rob_moving = False
        du.SC_curr_comm_id = 1
        du.ROBTelem.Coor = du.Coordinate()
        du.ROB_send_list.clear()


    def test_send_command(self):
        global TestFrame

        du.SC_curr_comm_id = 1
        TestFrame.robo_send(
            command=du.QEntry(id=1, Coor1=du.Coordinate(x=2.2)),
            no_error=True,
            num_send=1,
            dc=True,
        )
        self.assertEqual(du.SC_curr_comm_id, 2)

        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_gcode_command(self):
        global TestFrame

        TestFrame.TERM_entry_gcodeInterp.setText('G1 Y2.2 EXT100 TRL0.1 TCL1 TCU1')
        du.ROBTelem.Coor = du.Coordinate(1, 1900, 1, 1, 1, 1, 1, 100)
        du.DCCurrZero = du.Coordinate(y=2000, ext=100)
        TCoor = du.Coordinate(x=1, y=2002.2, z=1, rx=1, ry=1, rz=1, q=1, ext=200)
        TestTool = du.ToolCommand(
            0.1 * du.DEF_TOOL_TROL_RATIO,
            True,
            True,
            False,
            False,
            0,
        )

        TestFrame.send_gcode_command()
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=1, Coor1=TCoor, Tool=TestTool))

        du.DC_rob_moving = False
        TestFrame.robo_send(command, True, 1, True)
        TestFrame.TERM_entry_gcodeInterp.setText('G1 X1 Z3')
        TCoor = du.Coordinate(1.1, 2002.2, 3.3, 4.4, 5.5, 6.6, 0.7, 108.8)
        du.ROBTelem.Coor = du.DCCurrZero = TCoor

        TestFrame.send_gcode_command()
        TCoor = du.Coordinate(2.1, 2002.2, 6.3, 4.4, 5.5, 6.6, 0.7, 108.8)
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=2, Coor1=TCoor))

        du.DC_rob_moving = False
        du.ROBTelem.Coor = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_NC_command(self):
        global TestFrame
        self.maxDiff = 2000
        
        TestFrame.NC_float_x.setValue(1)
        TestFrame.NC_float_y.setValue(2000)
        TestFrame.NC_float_z.setValue(0)
        TestFrame.NC_float_rx.setValue(4)
        TestFrame.NC_float_ry.setValue(5)
        TestFrame.NC_float_rz.setValue(6)
        TestFrame.NC_float_ext.setValue(102)
        TestFrame.DC_drpd_moveType.setCurrentText('LINEAR')

        du.ROB_send_list.clear()
        du.SC_curr_comm_id = 1
        du.DC_rob_moving = False
        du.ROBTelem.Coor = du.Coordinate(1, 1, 1, 0, 0, 0, 0, 100)
        TestFrame.send_NC_command([1, 2, 3])
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command,
            du.QEntry(id=1, z=0, Coor1=du.Coordinate(x=1, y=2000, z=0, ext=100))
        )

        du.DC_rob_moving = False
        TestFrame.robo_send(command, True, 1, True)
        du.ROBTelem.Coor = du.Coordinate(1, 2000, 1, 1, 1, 1, 0, 1)
        TestFrame.DC_drpd_moveType.setCurrentText('JOINT')

        TCoor = du.Coordinate(x=1, y=2000, z=1, rx=4, ry=5, rz=6, ext=102)
        TestFrame.send_NC_command([4, 5, 6, 8])
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command, du.QEntry(id=2, mt='J', z=0, Coor1=TCoor))

        du.DC_rob_moving = False
        du.ROBTelem.Coor = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_rapid_command(self):
        global TestFrame

        TestFrame.TERM_entry_rapidInterp.setText(
            f"MoveL [[1.0,2000.0,3.0],[4.0,5.0,6.0,1.0]],[200,50,50,50],"
            f"z50,tool0  EXT600  TPS1 TLS1"
        )
        TCoor = du.Coordinate(x=1, y=2000, z=3, rx=4, ry=5, rz=6, q=1, ext=600)
        TestTool = du.ToolCommand(0, False, False, True, True, 0)
        TestFrame.send_rapid_command()
        command,_ = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command,
            du.QEntry(id=1, pt='Q', z=50, Coor1=TCoor, Tool=TestTool),
        )

        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_set_zero(self):
        global TestFrame

        du.DCCurrZero = du.Coordinate(1, 2, 3, 4, 5, 6, 7, 8)
        du.ROBTelem.Coor = du.Coordinate()

        TestFrame.set_zero([1, 2, 3])
        self.assertEqual(du.DCCurrZero, du.Coordinate(0, 0, 0, 4, 5, 6, 7, 8))

        TestFrame.set_zero([4, 5, 6, 8])
        self.assertEqual(du.DCCurrZero, du.Coordinate(0, 0, 0, 0, 0, 0, 7, 0))

        TestFrame.ZERO_float_x.setValue(1)
        TestFrame.ZERO_float_y.setValue(2)
        TestFrame.ZERO_float_z.setValue(3)
        TestFrame.ZERO_float_rx.setValue(4)
        TestFrame.ZERO_float_ry.setValue(5)
        TestFrame.ZERO_float_rz.setValue(6)
        TestFrame.ZERO_float_ext.setValue(7)
        TestFrame.set_zero([1, 2, 3, 4, 5, 6, 8], source='user')
        self.assertEqual(du.DCCurrZero, du.Coordinate(1, 2, 3, 4, 5, 6, 7, 7))

        du.DCCurrZero = du.Coordinate()


    def test_system_stop_commands(self):
        global TestFrame

        TestFrame.forced_stop_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command[0], du.QEntry(id=1, mt='S'))

        TestFrame.robo_send(command[0], True, 1, True)
        TestFrame.robot_stop_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command[0], du.QEntry(id=1, mt='E'))

        TestFrame.robo_send(command[0], True, 1, True)
        TestFrame.robot_stop_command(directly=False)

        self.assertEqual(
            du.SCQueue.display(),
            [du.QEntry(id=3, mt='E').print_short()],
        )

        du.SC_curr_comm_id = 1
        du.SCQueue.clear()


    def test_zz_end(self):
        """does not test anything, just here to close all sockets/ exit cleanly,
        named '_zz_' to be executed by unittest at last"""
        global TestFrame

        du.ROBTcp.connected = False
        du.PMP1Serial.connected = False
        du.PMP2Serial.connected = False
        du.PRH_connected = False
        TestFrame.close()

        du.ROBTcp.close(end=True)
        du.TERM_log.clear()


#################################  MAIN  #####################################

# create test logfile and 0_BT_testfiles
desk = os.environ['USERPROFILE']
dir_path = desk / pl.Path("Desktop/PRINT_py_testrun")
dir_path.mkdir(parents=True, exist_ok=True)

logpath = dir_path / pl.Path(
    f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt"
)
txt = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}:   test running..\n\n"

logfile = open(logpath, 'w')
logfile.write(txt)
logfile.close()

gcode_test_path = dir_path / pl.Path("0_UT_testfile.gcode")
rapid_test_path = dir_path / pl.Path("0_UT_testfile.mod")
gcode_txt = ';comment\nG1 Y2000\nG1 Z1000'
rapid_txt = (
    '!comment\nMoveJ pHome,v200,fine,tool0;\n\n\
    ! start printjob relative to pStart\n\
    MoveL Offs(pHome,0.0,2000.0,0.0),[200,50,50,50],z10,tool0 EXT:11;\n\
    MoveL Offs(pHome,0.0,2000.0,1000.0),[200,50,50,50],z10,tool0 EXT:11;'
)

gcode_test_file = open(gcode_test_path, 'w')
rapid_test_file = open(rapid_test_path, 'w')
gcode_test_file.write(gcode_txt)
rapid_test_file.write(rapid_txt)
gcode_test_file.close()
rapid_test_file.close()

# create application
app = 0
win = 0
app = QApplication(sys.argv)
TestFrame = mf.Mainframe(lpath=logpath, testrun=True)
rapid_test_file.close()

# grouping
ACON_btt_group = (
    TestFrame.ADC_btt_clamp,
    TestFrame.ADC_btt_cut,
    TestFrame.ADC_btt_placeSpring,
)


# run test immediatly only if called alone
if __name__ == '__main__':
    unittest.main()
