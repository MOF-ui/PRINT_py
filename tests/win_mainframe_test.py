# test win_mainframe

############################################# IMPORTS #################################################

import os
import sys
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



########################################## TEST CLASS ##############################################

class MainframeWinTest(unittest.TestCase):


    def assert_is_file(self, path):
        """program file exist error"""

        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"No such file: {path}")


    def test_add_gcode_sgl(self):
        global test_frame

        du.SCQueue.clear()
        du.DCCurrZero = du.Coordinate()

        # G1
        test_frame.SGLC_entry_gcodeSglComm.setText("G1 X1 Y2.2 EXT3 F40")
        test_frame.add_gcode_sgl()
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(
                    id=1,
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short()
            ],
        )

        test_frame.SGLC_entry_gcodeSglComm.setText("G1 X1")
        du.DCCurrZero = du.Coordinate(x=1, y=1)
        test_frame.add_gcode_sgl(at_id=True, id=1)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=2, y=1)).print_short(),
                du.QEntry(
                    id=2,
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short(),
            ],
        )

        test_frame.add_gcode_sgl(at_id=True, id=2, from_file=True, file_txt="G1 Z1")
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=2, y=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=2, y=1, z=1)).print_short(),
                du.QEntry(
                    id=3,
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short(),
            ],
        )

        test_frame.add_gcode_sgl(at_id=False, id=0, from_file=True, file_txt="G1 X1.2")
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=2, y=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=2, y=1, z=1)).print_short(),
                du.QEntry(
                    id=3,
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short()
                # here, the external axis is set to 0, as a change in X activates the recalculation of the
                # appropriate EXT position in UTIL.gcodeToQEntry using UTIL.SC_extFllwBhvr
                ,
                du.QEntry(id=4, Coor1=du.Coordinate(x=2.2, y=2.2, ext=0)).print_short(),
            ],
        )

        # G28 & G92
        test_frame.add_gcode_sgl(
            at_id=False, id=0, from_file=True, file_txt="G92 Y0 EXT0"
        )
        self.assertEqual(du.DCCurrZero, du.Coordinate(x=1, y=2.2))

        test_frame.add_gcode_sgl(
            at_id=False, id=0, from_file=True, file_txt="G28 Y0 EXT0"
        )
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=2, y=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=2, y=1, z=1)).print_short(),
                du.QEntry(
                    id=3,
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short(),
                du.QEntry(id=4, Coor1=du.Coordinate(x=2.2, y=2.2, ext=0)).print_short(),
                du.QEntry(id=5, Coor1=du.Coordinate(x=2.2, y=2.2, ext=0)).print_short(),
            ],
        )

        test_frame.add_gcode_sgl(at_id=True, id=3, from_file=True, file_txt="G92 X0 Z0")
        self.assertEqual(du.DCCurrZero, du.Coordinate(x=2, y=2.2, z=1, ext=0))

        du.DCCurrZero = du.Coordinate()
        du.SCQueue.clear()


    def test_add_rapid_sgl(self):
        global test_frame

        du.DCCurrZero = du.Coordinate()
        test_frame.SGLC_entry_rapidSglComm.setText(
            "MoveL [[1.0,2.2,0.0][0.0,0.0,0.0,0.0]],[4,50,50,50],z10,tool0 EXT3;"
        )
        test_frame.add_rapid_sgl()
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(
                    id=1,
                    pt="Q",
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short()
            ],
        )

        test_frame.SGLC_entry_rapidSglComm.setText(
            "MoveL [[1.0,0.0,0.0][0.0,0.0,0.0,0.0]],[200,50,50,50],z10,tool0 EXT0.0;"
        )
        test_frame.add_rapid_sgl(at_id=True, id=1)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, pt="Q", Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(
                    id=2,
                    pt="Q",
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate(z=1)
        test_frame.add_rapid_sgl(
            at_id=True,
            id=2,
            from_file=True,
            file_txt="MoveL Offs(pHome,0.0,0.0,1.0),[200,50,50,50],z10,tool0 EXT0;",
        )
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, pt="Q", Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(id=2, pt="E", Coor1=du.Coordinate(z=2)).print_short(),
                du.QEntry(
                    id=3,
                    pt="Q",
                    Coor1=du.Coordinate(x=1, y=2.2, ext=3),
                    Speed=du.SpeedVector(ts=4),
                ).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate()
        du.SCQueue.clear()


    def test_add_SIB(self):
        global test_frame
        self.maxDiff = 2000

        test_frame.SIB_entry_sib1.setText(
            f"G1 X1.0 Y2.0 Z3.0 F4000 EXT500\n" f"G1 X6.0 Y7.0 Z8.0 F9000 EXT990"
        )
        test_frame.SIB_entry_sib2.setText(
            f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT600\n"
            f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT160"
        )
        test_frame.SIB_entry_sib3.setText(
            f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT600\n"
            f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT160"
        )

        test_frame.add_SIB(num=1, at_end=False)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(
                    id=1,
                    Coor1=du.Coordinate(x=1, y=2, z=3, ext=500),
                    Speed=du.SpeedVector(ts=400),
                ).print_short(),
                du.QEntry(
                    id=2,
                    Coor1=du.Coordinate(x=6, y=7, z=8, ext=990),
                    Speed=du.SpeedVector(ts=900),
                ).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate(x=1)
        test_frame.add_SIB(num=2, at_end=True)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(
                    id=1,
                    Coor1=du.Coordinate(x=1, y=2, z=3, ext=500),
                    Speed=du.SpeedVector(ts=400),
                ).print_short(),
                du.QEntry(
                    id=2,
                    Coor1=du.Coordinate(x=6, y=7, z=8, ext=990),
                    Speed=du.SpeedVector(ts=900),
                ).print_short(),
                du.QEntry(
                    id=3,
                    pt="Q",
                    Coor1=du.Coordinate(
                        x=1.1, y=2.2, z=3.3, rx=4.4, ry=5.5, rz=6.6, q=7.7, ext=600
                    ),
                    Speed=du.SpeedVector(ts=18, ors=19, acr=20, dcr=21),
                    z=50,
                ).print_short(),
                du.QEntry(
                    id=4,
                    mt="J",
                    Coor1=du.Coordinate(x=8, y=8, z=9, ext=160),
                    Speed=du.SpeedVector(ts=110, ors=120, acr=130, dcr=140),
                    z=15,
                ).print_short(),
            ],
        )

        du.DCCurrZero = du.Coordinate(x=1)
        test_frame.add_SIB(num=3, at_end=False)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(
                    id=1,
                    pt="Q",
                    Coor1=du.Coordinate(
                        x=1.1, y=2.2, z=3.3, rx=4.4, ry=5.5, rz=6.6, q=7.7, ext=600
                    ),
                    Speed=du.SpeedVector(ts=18, ors=19, acr=20, dcr=21),
                    z=50,
                ).print_short(),
                du.QEntry(
                    id=2,
                    mt="J",
                    Coor1=du.Coordinate(x=8, y=8, z=9, ext=160),
                    Speed=du.SpeedVector(ts=110, ors=120, acr=130, dcr=140),
                    z=15,
                ).print_short(),
                du.QEntry(
                    id=3,
                    Coor1=du.Coordinate(x=1, y=2, z=3, ext=500),
                    Speed=du.SpeedVector(ts=400),
                ).print_short(),
                du.QEntry(
                    id=4,
                    Coor1=du.Coordinate(x=6, y=7, z=8, ext=990),
                    Speed=du.SpeedVector(ts=900),
                ).print_short(),
                du.QEntry(
                    id=5,
                    pt="Q",
                    Coor1=du.Coordinate(
                        x=1.1, y=2.2, z=3.3, rx=4.4, ry=5.5, rz=6.6, q=7.7, ext=600
                    ),
                    Speed=du.SpeedVector(ts=18, ors=19, acr=20, dcr=21),
                    z=50,
                ).print_short(),
                du.QEntry(
                    id=6,
                    mt="J",
                    Coor1=du.Coordinate(x=8, y=8, z=9, ext=160),
                    Speed=du.SpeedVector(ts=110, ors=120, acr=130, dcr=140),
                    z=15,
                ).print_short(),
            ],
        )

        du.SCQueue.clear()
        du.DCCurrZero = du.Coordinate()


    def test_amcon_script_overwrite(self):
        global test_frame
        self.maxDiff = 3000

        du.SCQueue.clear()
        for i in range(1, 5, 1):
            test_frame.add_gcode_sgl(
                at_id=False, id=0, from_file=True, file_txt=f"G1 X{i}"
            )
        test_frame.ASC_num_panning.setValue(1)
        test_frame.ASC_num_fibDeliv.setValue(2)
        test_frame.ASC_btt_clamp.setChecked(True)
        test_frame.ASC_btt_knifePos.setChecked(True)
        test_frame.ASC_btt_knife.setChecked(True)
        test_frame.ASC_btt_fiberPnmtc.setChecked(True)

        test_frame.ASC_entry_SCLines.setText("2..3")
        test_frame.amcon_script_overwrite()

        ToolOff = du.ToolCommand(
            0, 0, 0, 0, 0, 0, 0, False, 0, False, 0, False, 0, False
        )
        ToolOn = du.ToolCommand(
            0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True
        )
        self.assertEqual(
            f"{du.SCQueue}",
            f"{du.QEntry(id=1, Coor1=du.Coordinate(x=1), Tool=ToolOff)}\n"\
            f"{du.QEntry(id=2, Coor1=du.Coordinate(x=2), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=3, Coor1=du.Coordinate(x=3), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=4, Coor1=du.Coordinate(x=4), Tool=ToolOff)}\n"
        )

        test_frame.ASC_entry_SCLines.setText("4")
        test_frame.amcon_script_overwrite()
        self.assertEqual(
            f"{du.SCQueue}",
            f"{du.QEntry(id=1, Coor1=du.Coordinate(x=1), Tool=ToolOff)}\n"\
            f"{du.QEntry(id=2, Coor1=du.Coordinate(x=2), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=3, Coor1=du.Coordinate(x=3), Tool=ToolOn)}\n"\
            f"{du.QEntry(id=4, Coor1=du.Coordinate(x=4), Tool=ToolOn)}\n"
        )

        test_frame.clr_queue(partial=False)
        test_frame.ASC_num_panning.setValue(du.DEF_AMC_PANNING)
        test_frame.ASC_num_fibDeliv.setValue(du.DEF_AMC_FIB_DELIV)
        test_frame.ASC_btt_clamp.setChecked(du.DEF_AMC_CLAMP)
        test_frame.ASC_btt_knifePos.setChecked(du.DEF_AMC_KNIFE_POS)
        test_frame.ASC_btt_knife.setChecked(du.DEF_AMC_KNIFE)
        test_frame.ASC_btt_fiberPnmtc.setChecked(du.DEF_AMC_FIBER_PNMTC)


    def test_adc_user_change(self):
        global test_frame
        global ACON_btt_group

        test_frame.ADC_num_panning.blockSignals(True)
        test_frame.ADC_num_fibDeliv.blockSignals(True)
        for widget in ACON_btt_group:
            widget.blockSignals(True)

        test_frame.ADC_num_panning.setValue(1)
        test_frame.ADC_num_fibDeliv.setValue(2)
        test_frame.ADC_btt_clamp.setChecked(True)
        test_frame.ADC_btt_knifePos.setChecked(True)
        test_frame.ADC_btt_knife.setChecked(True)
        test_frame.ADC_btt_fiberPnmtc.setChecked(True)

        test_frame.adc_user_change()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=1,
                z=0,
                Tool=du.ToolCommand(
                    0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True
                ),
            ),
        )

        du.SC_curr_comm_id = 1
        test_frame.ADC_num_panning.setValue(du.DEF_AMC_PANNING)
        test_frame.ADC_num_fibDeliv.setValue(du.DEF_AMC_FIB_DELIV)
        test_frame.ADC_btt_clamp.setChecked(du.DEF_AMC_CLAMP)
        test_frame.ADC_btt_knifePos.setChecked(du.DEF_AMC_KNIFE_POS)
        test_frame.ADC_btt_knife.setChecked(du.DEF_AMC_KNIFE)
        test_frame.ADC_btt_fiberPnmtc.setChecked(du.DEF_AMC_FIBER_PNMTC)

        test_frame.ADC_num_panning.blockSignals(False)
        test_frame.ADC_num_fibDeliv.blockSignals(False)
        for widget in ACON_btt_group:
            widget.blockSignals(False)

        du.ROBCommQueue.clear()
        du.ROB_send_list.clear()


    def test_apply_settings(self):
        """tests default settings loading in '__init__' and 'updateCommForerun' as well"""
        global test_frame

        # check if defaults were loaded
        self.assertEqual(test_frame.TCP_num_commForerun.value(), du.DEF_ROB_COMM_FR)
        self.assertEqual(test_frame.SET_float_volPerMM.value(), du.DEF_SC_VOL_PER_M)
        self.assertEqual(test_frame.SET_float_frToMms.value(), du.DEF_IO_FR_TO_TS)
        self.assertEqual(test_frame.SET_num_zone.value(), du.DEF_IO_ZONE)
        self.assertEqual(test_frame.SET_num_transSpeed_dc.value(), du.DEF_DC_SPEED.ts)
        self.assertEqual(test_frame.SET_num_orientSpeed_dc.value(), du.DEF_DC_SPEED.ors)
        self.assertEqual(test_frame.SET_num_accelRamp_dc.value(), du.DEF_DC_SPEED.acr)
        self.assertEqual(test_frame.SET_num_decelRamp_dc.value(), du.DEF_DC_SPEED.dcr)
        self.assertEqual(
            test_frame.SET_num_transSpeed_print.value(), du.DEF_PRIN_SPEED.ts
        )
        self.assertEqual(
            test_frame.SET_num_orientSpeed_print.value(), du.DEF_PRIN_SPEED.ors
        )
        self.assertEqual(
            test_frame.SET_num_accelRamp_print.value(), du.DEF_PRIN_SPEED.acr
        )
        self.assertEqual(
            test_frame.SET_num_decelRamp_print.value(), du.DEF_PRIN_SPEED.dcr
        )
        self.assertEqual(
            test_frame.SET_TE_num_fllwBhvrInterv.value(), du.DEF_SC_EXT_FLLW_BHVR[0]
        )
        self.assertEqual(
            test_frame.SET_TE_num_fllwBhvrSkip.value(), du.DEF_SC_EXT_FLLW_BHVR[1]
        )
        self.assertEqual(
            test_frame.SET_TE_num_retractSpeed.value(), du.DEF_PUMP_RETR_SPEED
        )
        self.assertEqual(test_frame.SET_TE_float_p1VolFlow.value(), du.DEF_PUMP_LPS)
        self.assertEqual(test_frame.SET_TE_float_p2VolFlow.value(), du.DEF_PUMP_LPS)

        self.assertEqual(test_frame.ADC_num_panning.value(), du.DEF_AMC_PANNING)
        self.assertEqual(test_frame.ADC_num_fibDeliv.value(), du.DEF_AMC_FIB_DELIV)
        self.assertEqual(test_frame.ADC_btt_clamp.isChecked(), du.DEF_AMC_CLAMP)
        self.assertEqual(test_frame.ADC_btt_knifePos.isChecked(), du.DEF_AMC_KNIFE_POS)
        self.assertEqual(test_frame.ADC_btt_knife.isChecked(), du.DEF_AMC_KNIFE)
        self.assertEqual(
            test_frame.ADC_btt_fiberPnmtc.isChecked(), du.DEF_AMC_FIBER_PNMTC
        )
        self.assertEqual(test_frame.ASC_num_panning.value(), du.DEF_AMC_PANNING)
        self.assertEqual(test_frame.ASC_num_fibDeliv.value(), du.DEF_AMC_FIB_DELIV)
        self.assertEqual(test_frame.ASC_btt_clamp.isChecked(), du.DEF_AMC_CLAMP)
        self.assertEqual(test_frame.ASC_btt_knifePos.isChecked(), du.DEF_AMC_KNIFE_POS)
        self.assertEqual(test_frame.ASC_btt_knife.isChecked(), du.DEF_AMC_KNIFE)
        self.assertEqual(
            test_frame.ASC_btt_fiberPnmtc.isChecked(), du.DEF_AMC_FIBER_PNMTC
        )

        # test setting by user
        test_frame.TCP_num_commForerun.setValue(1)
        test_frame.SET_float_volPerMM.setValue(2.2)
        test_frame.SET_float_frToMms.setValue(3.3)
        test_frame.SET_num_zone.setValue(4)
        test_frame.SET_num_transSpeed_dc.setValue(5)
        test_frame.SET_num_orientSpeed_dc.setValue(6)
        test_frame.SET_num_accelRamp_dc.setValue(7)
        test_frame.SET_num_decelRamp_dc.setValue(8)
        test_frame.SET_num_transSpeed_print.setValue(9)
        test_frame.SET_num_orientSpeed_print.setValue(10)
        test_frame.SET_num_accelRamp_print.setValue(11)
        test_frame.SET_num_decelRamp_print.setValue(12)
        test_frame.apply_settings()

        test_frame.SET_TE_num_fllwBhvrInterv.setValue(13)
        test_frame.SET_TE_num_fllwBhvrSkip.setValue(14)
        test_frame.SET_TE_num_retractSpeed.setValue(15)
        test_frame.SET_TE_float_p1VolFlow.setValue(16)
        test_frame.SET_TE_float_p2VolFlow.setValue(17)
        test_frame.apply_TE_settings()

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

        self.assertEqual(du.SC_ext_fllw_bhvr[0], 13)
        self.assertEqual(du.SC_ext_fllw_bhvr[1], 14)
        self.assertEqual(du.PMP_retract_speed, 15)
        self.assertEqual(du.PMP1_liter_per_s, 16)
        self.assertEqual(du.PMP2_liter_per_s, 17)

        # test resetting by user
        test_frame.TCP_num_commForerun.setValue(10)
        test_frame.load_defaults()
        test_frame.apply_settings()
        test_frame.load_TE_defaults()
        test_frame.apply_TE_settings()

        self.assertEqual(test_frame.TCP_num_commForerun.value(), du.DEF_ROB_COMM_FR)
        self.assertEqual(test_frame.SET_float_volPerMM.value(), du.DEF_SC_VOL_PER_M)
        self.assertEqual(test_frame.SET_float_frToMms.value(), du.DEF_IO_FR_TO_TS)
        self.assertEqual(test_frame.SET_num_zone.value(), du.DEF_IO_ZONE)
        self.assertEqual(test_frame.SET_num_transSpeed_dc.value(), du.DEF_DC_SPEED.ts)
        self.assertEqual(test_frame.SET_num_orientSpeed_dc.value(), du.DEF_DC_SPEED.ors)
        self.assertEqual(test_frame.SET_num_accelRamp_dc.value(), du.DEF_DC_SPEED.acr)
        self.assertEqual(test_frame.SET_num_decelRamp_dc.value(), du.DEF_DC_SPEED.dcr)
        self.assertEqual(
            test_frame.SET_num_transSpeed_print.value(), du.DEF_PRIN_SPEED.ts
        )
        self.assertEqual(
            test_frame.SET_num_orientSpeed_print.value(), du.DEF_PRIN_SPEED.ors
        )
        self.assertEqual(
            test_frame.SET_num_accelRamp_print.value(), du.DEF_PRIN_SPEED.acr
        )
        self.assertEqual(
            test_frame.SET_num_decelRamp_print.value(), du.DEF_PRIN_SPEED.dcr
        )
        self.assertEqual(
            test_frame.SET_TE_num_fllwBhvrInterv.value(), du.DEF_SC_EXT_FLLW_BHVR[0]
        )
        self.assertEqual(
            test_frame.SET_TE_num_fllwBhvrSkip.value(), du.DEF_SC_EXT_FLLW_BHVR[1]
        )
        self.assertEqual(
            test_frame.SET_TE_num_retractSpeed.value(), du.DEF_PUMP_RETR_SPEED
        )
        self.assertEqual(test_frame.SET_TE_float_p1VolFlow.value(), du.DEF_PUMP_LPS)
        self.assertEqual(test_frame.SET_TE_float_p2VolFlow.value(), du.DEF_PUMP_LPS)


    def test_clr_queue(self):
        global test_frame
        self.maxDiff = 2000

        du.SCQueue.clear()
        du.SC_ext_fllw_bhvr = (500, 200)

        for i in range(1, 7, 1):
            test_frame.add_gcode_sgl(
                at_id=False, id=0, from_file=True, file_txt=f"G1 X{i}"
            )

        test_frame.SCTRL_entry_clrByID.setText("2..4")
        test_frame.clr_queue(partial=True)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=5)).print_short(),
                du.QEntry(id=3, Coor1=du.Coordinate(x=6)).print_short(),
            ],
        )

        test_frame.SCTRL_entry_clrByID.setText("2")
        test_frame.clr_queue(partial=True)
        self.assertEqual(
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=du.Coordinate(x=1)).print_short(),
                du.QEntry(id=2, Coor1=du.Coordinate(x=6)).print_short(),
            ],
        )

        test_frame.clr_queue(partial=False)
        self.assertEqual(du.SCQueue.display(), ["Queue is empty!"])

        du.SC_ext_fllw_bhvr = du.DEF_SC_EXT_FLLW_BHVR


    def test_home_command(self):
        global test_frame

        du.DCCurrZero = du.Coordinate(x=1, y=2.2, z=3, rx=4, ry=5, rz=6, q=7, ext=8)
        test_frame.DC_drpd_moveType.setCurrentText("LINEAR")
        test_frame.home_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=1,
                z=0,
                Coor1=du.Coordinate(x=1, y=2.2, z=3, rx=4, ry=5, rz=6, q=7, ext=8),
            ),
        )
        self.assertTrue(du.DC_rob_moving)

        test_frame.robo_send(command[0], True, 1, True)
        du.DC_rob_moving = False

        test_frame.DC_drpd_moveType.setCurrentText("JOINT")
        test_frame.home_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=2,
                z=0,
                mt="J",
                Coor1=du.Coordinate(x=1, y=2.2, z=3, rx=4, ry=5, rz=6, q=7, ext=8),
            ),
        )

        du.DCCurrZero = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.DC_rob_moving = False
        du.SCQueue.clear()


    def test_init(self):
        global test_frame
        global logpath

        # general values
        self.assertEqual(test_frame._logpath, logpath)
        self.assertIsInstance(test_frame.Daq, DAQ)

        # logfile
        self.assert_is_file(logpath)
        logfileCheck = open(logpath, "r")
        logfileCheckTxt = logfileCheck.read()
        logfileCheck.close()
        self.assertIn("setup finished.", logfileCheckTxt)

        # defaults test with 'applySettings'

        # threads -- R
        self.assertIsInstance(test_frame._RoboCommThread, QThread)
        self.assertIsInstance(test_frame._PumpCommThread, QThread)
        self.assertIsInstance(test_frame._LoadFileThread, QThread)
        self.assertIsInstance(test_frame._SensorArrThread, QThread)
        self.assertIsInstance(test_frame._RoboCommWorker, RoboCommWorker)
        self.assertIsInstance(test_frame._PumpCommWorker, PumpCommWorker)
        self.assertIsInstance(test_frame._LoadFileWorker, LoadFileWorker)
        self.assertIsInstance(test_frame._SensorArrWorker, SensorCommWorker)


    def test_label_update_on_new_zero(self):
        """rababer rababer"""
        global test_frame

        du.DCCurrZero = du.Coordinate(1.1, 2, 3, 4, 5, 6, 7, 8)
        test_frame.label_update_on_new_zero()

        self.assertEqual(test_frame.ZERO_disp_x.text(), "1.1")
        self.assertEqual(test_frame.ZERO_disp_y.text(), "2.0")
        self.assertEqual(test_frame.ZERO_disp_z.text(), "3.0")
        self.assertEqual(test_frame.ZERO_disp_xOrient.text(), "4.0")
        self.assertEqual(test_frame.ZERO_disp_yOrient.text(), "5.0")
        self.assertEqual(test_frame.ZERO_disp_zOrient.text(), "6.0")
        self.assertEqual(test_frame.ZERO_disp_ext.text(), "8.0")

        du.DCCurrZero = du.Coordinate()


    def test_label_update_on_send(self):
        """test labelUpdate_onQueueChange as well"""
        global test_frame
        global ACON_btt_group

        du.DCCurrZero = du.Coordinate()

        test_frame.SGLC_entry_gcodeSglComm.setText("G1 X2.2 Y1")
        test_frame.add_gcode_sgl()
        test_frame.label_update_on_send(
            entry=du.QEntry(
                Tool=du.ToolCommand(
                    0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True
                )
            )
        )

        self.assertEqual(test_frame.SCTRL_disp_elemInQ.text(), "1")
        self.assertEqual(test_frame.SCTRL_disp_buffComms.text(), "0")
        self.assertEqual(test_frame.ADC_num_panning.value(), 1)
        self.assertEqual(test_frame.ADC_num_fibDeliv.value(), 2)
        self.assertEqual(test_frame.ASC_num_panning.value(), 1)
        self.assertEqual(test_frame.ASC_num_fibDeliv.value(), 2)
        for widget in ACON_btt_group:
            self.assertTrue(widget.isChecked(), True)

        # secondarily calls labelUpdate_onQueueChange
        self.assertEqual(
            test_frame.SCTRL_arr_queue.item(0).text(),
            du.QEntry(id=1, Coor1=du.Coordinate(x=2.2, y=1)).print_short(),
        )

        du.SCQueue.clear()


    def test_load_file(self):
        global test_frame

        du.IO_curr_filepath = pl.Path("test.abc")
        test_frame.load_file()
        self.assertEqual(
            test_frame.IO_lbl_loadFile.text(), "... no valid file, not executed"
        )

        du.IO_curr_filepath = pl.Path("test.mod")
        test_frame.load_file(testrun=True)
        self.assertEqual(test_frame.IO_lbl_loadFile.text(), "... conversion running ...")

        du.IO_curr_filepath = None


    def test_load_file_finished(self):
        """no need to test loadFileFailed, skip to loadFileFinished"""
        global test_frame

        test_frame.load_file_finished(line_id=1, start_id=2, skips=3)
        self.assertEqual(test_frame.IO_num_addByID.value(), 1)
        self.assertEqual(
            test_frame.IO_lbl_loadFile.text(), "... 3 command(s) skipped (syntax)"
        )


    def test_mixer_set_speed(self):
        global test_frame

        test_frame.MIX_num_setSpeed.setValue(56)
        test_frame.MIX_sld_speed.setValue(78)

        test_frame.mixer_set_speed()
        self.assertEqual(du.MIX_speed, 56)
        test_frame.mixer_set_speed("sld")
        self.assertEqual(du.MIX_speed, 78)
        test_frame.mixer_set_speed("0")
        self.assertEqual(du.MIX_speed, 0)


    def test_open_file(self):
        global test_frame
        global gcode_test_path
        global rapid_test_path

        currSetting = du.SC_vol_per_m
        du.SC_vol_per_m = 0.1

        test_frame.open_file(testrun=True, testpath=gcode_test_path)
        self.assertEqual(du.IO_curr_filepath, gcode_test_path)
        self.assertEqual(test_frame.IO_disp_filename.text(), gcode_test_path.name)
        self.assertEqual(test_frame.IO_disp_commNum.text(), "2")
        self.assertEqual(test_frame.IO_disp_estimLen.text(), "3.0")
        self.assertEqual(test_frame.IO_disp_estimVol.text(), "0.3")

        test_frame.open_file(testrun=True, testpath=rapid_test_path)
        self.assertEqual(du.IO_curr_filepath, rapid_test_path)
        self.assertEqual(test_frame.IO_disp_filename.text(), rapid_test_path.name)
        self.assertEqual(test_frame.IO_disp_commNum.text(), "2")
        self.assertEqual(test_frame.IO_disp_estimLen.text(), "3.0")
        self.assertEqual(test_frame.IO_disp_estimVol.text(), "0.3")

        du.SC_vol_per_m = currSetting


    def test_pump_recv(self):
        global test_frame

        du.STTDataBlock.Pump1 = du.PumpTelemetry(1.1, 2.2, 3.3, 4.4)
        test_frame.pump_recv(telem=du.STTDataBlock.Pump1, source="P1")

        self.assertEqual(test_frame.PUMP_disp_freqP1.text(), "1.1%")
        self.assertEqual(test_frame.PUMP_disp_voltP1.text(), "2.2 V")
        self.assertEqual(test_frame.PUMP_disp_ampsP1.text(), "3.3 A")
        self.assertEqual(test_frame.PUMP_disp_torqP1.text(), "4.4 Nm")

        du.STTDataBlock.Pump2 = du.PumpTelemetry(5, 6, 7, 8)
        du.PMP1Serial.connected = True
        du.PMP2Serial.connected = True
        test_frame.pump_recv(telem=du.STTDataBlock.Pump2, source="P2")

        self.assertEqual(test_frame.PUMP_disp_freqP2.text(), "5.0%")
        self.assertEqual(test_frame.PUMP_disp_voltP2.text(), "6.0 V")
        self.assertEqual(test_frame.PUMP_disp_ampsP2.text(), "7.0 A")
        self.assertEqual(test_frame.PUMP_disp_torqP2.text(), "8.0 Nm")

        du.STTDataBlock.Pump1 = du.STTDataBlock.Pump2 = du.PumpTelemetry()
        du.PMP1Serial.connected = False
        du.PMP2Serial.connected = False



    def test_pump_send(self):
        global test_frame

        test_frame.pump_send(new_speed=1.1, command="ABC", ans="DEF", source="P1")

        self.assertEqual(test_frame.TCP_PUMP1_disp_writeBuffer.text(), "ABC")
        self.assertEqual(test_frame.TCP_PUMP1_disp_bytesWritten.text(), "3")
        self.assertEqual(test_frame.TCP_PUMP1_disp_readBuffer.text(), "DEF")

        test_frame.pump_send(new_speed=1.1, command="ABC", ans="DEF", source="P2")

        self.assertEqual(test_frame.TCP_PUMP2_disp_writeBuffer.text(), "ABC")
        self.assertEqual(test_frame.TCP_PUMP2_disp_bytesWritten.text(), "3")
        self.assertEqual(test_frame.TCP_PUMP2_disp_readBuffer.text(), "DEF")

        # TO DO:
        # test test_frame.PUMP_disp_currSpeed.text()
        # test test_frame.PUMP_disp_outputRatio.text()


    def test_pump_set_speed(self):
        global test_frame

        du.PMP_speed = 10
        test_frame.PUMP_num_setSpeed.setValue(5)
        du.ROBCommQueue.add(du.QEntry(Speed=du.SpeedVector(ts=123)))

        test_frame.pump_set_speed(type="1")
        self.assertEqual(du.PMP_speed, 11)
        test_frame.pump_set_speed(type="0")
        self.assertEqual(du.PMP_speed, 0)
        test_frame.pump_set_speed(type="-1")
        self.assertEqual(du.PMP_speed, -1)
        test_frame.pump_set_speed(type="r")
        self.assertEqual(du.PMP_speed, 1)
        test_frame.pump_set_speed()
        self.assertEqual(du.PMP_speed, 5)
        test_frame.pump_set_speed("def")
        self.assertEqual(du.PMP_speed, 9.84)

        du.PMP_speed = 0


    def test_robo_send(self):
        """test overflow control etc. labelUpdate_onSend tested by own function"""
        global test_frame
        self.maxDiff = 2000

        du.SC_curr_comm_id = 2991

        test_frame.robo_send(du.QEntry(id=12), True, 10, True)
        self.assertEqual(du.SC_curr_comm_id, 1)
        self.assertEqual(
            test_frame.TCP_ROB_disp_writeBuffer.text(),
            f"ID: 12 -- L, E -- COOR_1: X: 0.0   Y: 0.0   Z: 0.0   "
            f"Rx: 0.0   Ry: 0.0   Rz: 0.0   Q: 0.0   EXT: 0.0 -- "
            f"SV: TS: 200   OS: 50   ACR: 50   DCR: 50 -- PM/PR:  None/1.0",
        )
        self.assertEqual(test_frame.TCP_ROB_disp_bytesWritten.text(), "10")

        test_frame.robo_send(
            None,
            False,
            ValueError(f"None is not an instance of QEntry!"),
            False
        )
        self.assertEqual(
            test_frame.TCP_ROB_disp_writeBuffer.text(),
            "None is not an instance of QEntry!"
        )

        du.ROB_send_list.clear()


    def test_robo_recv(self):
        """tests labelUpdate_onReceive as well"""
        global test_frame

        # primary function
        du.DCCurrZero = du.Coordinate()

        # check first loop switch, Q is not set by roboRecv
        du.ROBTelem = du.RoboTelemetry(0, 0, du.Coordinate(1, 2, 3, 4, 5, 6, 7, 8.8))
        self.assertEqual(du.DCCurrZero, du.Coordinate())
        test_frame.robo_recv(raw_data_string="ABC", telem=du.RoboTelemetry())
        self.assertEqual(du.DCCurrZero, du.Coordinate(1, 2, 3, 4, 5, 6, 0, 8.8))

        # check loop run
        du.SC_curr_comm_id = 15
        du.DCCurrZero = du.Coordinate(0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1)
        du.ROBTelem = du.RoboTelemetry(
            9.9, 10, du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
        )
        test_frame.robo_recv(raw_data_string="ABC", telem=du.RoboTelemetry())

        # labelUpdate_onReceive (called from roboRecv)
        self.assertEqual(test_frame.TCP_ROB_disp_readBuffer.text(), "ABC")
        self.assertEqual(test_frame.SCTRL_disp_buffComms.text(), "5")
        self.assertEqual(test_frame.SCTRL_disp_robCommID.text(), "10")
        self.assertEqual(test_frame.SCTRL_disp_progCommID.text(), "15")
        self.assertEqual(test_frame.SCTRL_disp_elemInQ.text(), "0")

        self.assertEqual(test_frame.DC_disp_x.text(), "1.0")
        self.assertEqual(test_frame.DC_disp_y.text(), "2.1")
        self.assertEqual(test_frame.DC_disp_z.text(), "3.2")
        self.assertEqual(test_frame.DC_disp_ext.text(), "8.7")

        self.assertEqual(test_frame.NC_disp_x.text(), "1.1")
        self.assertEqual(test_frame.NC_disp_y.text(), "2.2")
        self.assertEqual(test_frame.NC_disp_z.text(), "3.3")
        self.assertEqual(test_frame.NC_disp_xOrient.text(), "4.4°")
        self.assertEqual(test_frame.NC_disp_yOrient.text(), "5.5°")
        self.assertEqual(test_frame.NC_disp_zOrient.text(), "6.6°")
        self.assertEqual(test_frame.NC_disp_ext.text(), "8.8")

        self.assertEqual(test_frame.TERM_disp_tcpSpeed.text(), "9.9")
        self.assertEqual(test_frame.TERM_disp_robCommID.text(), "10")
        self.assertEqual(test_frame.TERM_disp_progCommID.text(), "15")

        self.assertEqual(test_frame.SID_disp_progID.text(), "15")
        self.assertEqual(test_frame.SID_disp_robID.text(), "10")

        self.assertEqual(test_frame.TRANS_disp_xStart.text(), "0.9")
        self.assertEqual(test_frame.TRANS_disp_yStart.text(), "1.9")
        self.assertEqual(test_frame.TRANS_disp_zStart.text(), "2.9")
        self.assertEqual(test_frame.TRANS_disp_extStart.text(), "8.7")
        self.assertEqual(test_frame.TRANS_disp_xEnd.text(), "0.9")
        self.assertEqual(test_frame.TRANS_disp_yEnd.text(), "1.9")
        self.assertEqual(test_frame.TRANS_disp_zEnd.text(), "2.9")
        self.assertEqual(test_frame.TRANS_disp_extEnd.text(), "8.7")

        du.DCCurrZero = du.Coordinate()
        du.ROBTelem = du.RoboTelemetry()
        du.SC_curr_comm_id = 1
        du.SCQueue.clear()


    def test_send_DC_command(self):
        global test_frame

        test_frame.DC_sld_stepWidth.setValue(1)
        test_frame.DC_drpd_moveType.setCurrentText("LINEAR")

        test_frame.send_DC_command(axis="X", dir="+")
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(id=1, z=0, Coor1=du.Coordinate(x=1))
        )

        du.DC_rob_moving = False
        test_frame.robo_send(command[0], True, 1, True)
        test_frame.DC_sld_stepWidth.setValue(2)
        test_frame.DC_drpd_moveType.setCurrentText("JOINT")

        test_frame.send_DC_command(axis="Y", dir="-")
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(id=2, mt="J", z=0, Coor1=du.Coordinate(y=-10))
        )

        du.DC_rob_moving = False
        test_frame.robo_send(command[0], True, 1, True)
        test_frame.DC_sld_stepWidth.setValue(3)

        test_frame.send_DC_command(axis="Z", dir="+")
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(id=3, mt="J", z=0, Coor1=du.Coordinate(z=100))
        )

        du.DC_rob_moving = False
        test_frame.robo_send(command[0], True, 1, True)
        self.assertRaises(ValueError, test_frame.send_DC_command, axis="A", dir="+")

        du.DC_rob_moving = False
        self.assertRaises(ValueError, test_frame.send_DC_command, axis="X", dir="/")

        du.DC_rob_moving = False
        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_command(self):
        global test_frame

        du.SC_curr_comm_id = 1
        test_frame.robo_send(
            command=du.QEntry(id=1, Coor1=du.Coordinate(x=2.2)),
            no_error=True,
            num_send=1,
            dc=True,
        )
        self.assertEqual(du.SC_curr_comm_id, 2)

        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_gcode_command(self):
        global test_frame

        test_frame.TERM_entry_gcodeInterp.setText("G1 Y2.2 TOOL")
        du.ROBTelem.Coor = du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)
        du.DCCurrZero = du.Coordinate(y=1)
        TCoor = du.Coordinate(x=1, y=3.2, z=1, rx=1, ry=1, rz=1, q=1, ext=1)

        test_frame.send_gcode_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=1,
                Coor1=TCoor,
                Tool=du.ToolCommand(fib_deliv_steps=10, pnmtc_fiber_yn=True),
            ),
        )

        du.DC_rob_moving = False
        test_frame.robo_send(command[0], True, 1, True)
        test_frame.TERM_entry_gcodeInterp.setText("G1 X1 Z3")
        du.ROBTelem.Coor = du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
        du.DCCurrZero = du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)

        test_frame.send_gcode_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=2, Coor1=du.Coordinate(2.1, 2.2, 6.3, 4.4, 5.5, 6.6, 7.7, 8.8)
            ),
        )

        du.DC_rob_moving = False
        du.ROBTelem.Coor = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_NC_command(self):
        global test_frame
        self.maxDiff = 2000
        
        test_frame.NC_float_x.setValue(1)
        test_frame.NC_float_y.setValue(2.2)
        test_frame.NC_float_z.setValue(3)
        test_frame.NC_float_xOrient.setValue(4)
        test_frame.NC_float_yOrient.setValue(5)
        test_frame.NC_float_zOrient.setValue(6)
        test_frame.NC_float_ext.setValue(7)
        test_frame.DC_drpd_moveType.setCurrentText("LINEAR")

        du.ROB_send_list.clear()
        du.SC_curr_comm_id = 1
        test_frame.send_NC_command([1, 2, 3])
        command, dc_dummy = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            f"{command}",
            f"{du.QEntry(id=1, z=0, Coor1=du.Coordinate(x=1, y=2.2, z=3))}"
        )

        du.DC_rob_moving = False
        test_frame.robo_send(command, True, 1, True)
        du.ROBTelem.Coor = du.Coordinate(1, 1, 1, 1, 1, 1, 0, 1)
        test_frame.DC_drpd_moveType.setCurrentText("JOINT")

        test_frame.send_NC_command([4, 5, 6, 8])
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=2,
                mt="J",
                z=0,
                Coor1=du.Coordinate(x=1, y=1, z=1, rx=4, ry=5, rz=6, ext=7),
            ),
        )

        du.DC_rob_moving = False
        du.ROBTelem.Coor = du.Coordinate()
        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_send_rapid_command(self):
        global test_frame

        test_frame.TERM_entry_rapidInterp.setText(
            "MoveL [[1.0,2.0,3.0],[4.0,5.0,6.0,7.0]],[200,50,50,50],z50,tool0  EXT600  TOOL"
        )
        test_frame.send_rapid_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(
            command[0],
            du.QEntry(
                id=1,
                pt="Q",
                z=50,
                Coor1=du.Coordinate(x=1, y=2, z=3, rx=4, ry=5, rz=6, q=7, ext=600),
                Tool=du.ToolCommand(fib_deliv_steps=10, pnmtc_fiber_yn=True),
            ),
        )

        du.SC_curr_comm_id = 1
        du.ROB_send_list.clear()


    def test_set_zero(self):
        global test_frame

        du.DCCurrZero = du.Coordinate(1, 2, 3, 4, 5, 6, 7, 8)
        du.ROBTelem.Coor = du.Coordinate()

        test_frame.set_zero([1, 2, 3])
        self.assertEqual(du.DCCurrZero, du.Coordinate(0, 0, 0, 4, 5, 6, 7, 8))

        test_frame.set_zero([4, 5, 6, 8])
        self.assertEqual(du.DCCurrZero, du.Coordinate(0, 0, 0, 0, 0, 0, 7, 0))

        test_frame.ZERO_float_x.setValue(1)
        test_frame.ZERO_float_y.setValue(2)
        test_frame.ZERO_float_z.setValue(3)
        test_frame.ZERO_float_rx.setValue(4)
        test_frame.ZERO_float_ry.setValue(5)
        test_frame.ZERO_float_rz.setValue(6)
        test_frame.ZERO_float_ext.setValue(7)
        test_frame.set_zero([1, 2, 3, 4, 5, 6, 8], from_sys_monitor=True)
        self.assertEqual(du.DCCurrZero, du.Coordinate(1, 2, 3, 4, 5, 6, 7, 7))

        du.DCCurrZero = du.Coordinate()


    def test_system_stop_commands(self):
        global test_frame

        test_frame.forced_stop_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command[0], du.QEntry(id=1, mt="S"))

        test_frame.robo_send(command[0], True, 1, True)
        test_frame.robot_stop_command()
        command = du.ROB_send_list[len(du.ROB_send_list) - 1]
        self.assertEqual(command[0], du.QEntry(id=1, mt="E"))

        test_frame.robo_send(command[0], True, 1, True)
        test_frame.robot_stop_command(directly=False)

        self.assertEqual(du.SCQueue.display(), [du.QEntry(id=3, mt="E").print_short()])

        du.SC_curr_comm_id = 1
        du.SCQueue.clear()


    def test_zz_end(self):
        """does not test anything, just here to close all sockets/ exit cleanly,
        named '_zz_' to be executed by unittest at last"""
        global test_frame

        du.ROBTcp.connected = False
        du.PMP1Serial.connected = False
        du.PMP2Serial.connected = False
        du.MIX_connected = False
        test_frame.close()

        du.ROBTcp.close(end=True)
        du.PMP1Tcp.close(end=True)
        du.PMP2Tcp.close(end=True)
        du.TERM_log.clear()


#############################################  MAIN  ##################################################

# create test logfile and 0_BT_testfiles
desk = os.environ["USERPROFILE"]
dir_path = desk / pl.Path("Desktop/PRINT_py_testrun")
dir_path.mkdir(parents=True, exist_ok=True)

logpath = dir_path / pl.Path(f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt")
txt = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}:   test running..\n\n"

logfile = open(logpath, "w")
logfile.write(txt)
logfile.close()

gcode_test_path = dir_path / pl.Path("0_UT_testfile.gcode")
rapid_test_path = dir_path / pl.Path("0_UT_testfile.mod")
gcode_txt = ";comment\nG1 Y2000\nG1 Z1000"
rapid_txt = "!comment\nMoveJ pHome,v200,fine,tool0;\n\n\
             ! start printjob relative to pStart\n\
             MoveL Offs(pHome,0.0,2000.0,0.0),[200,50,50,50],z10,tool0 EXT:11;\n\
             MoveL Offs(pHome,0.0,2000.0,1000.0),[200,50,50,50],z10,tool0 EXT:11;"

gcode_test_file = open(gcode_test_path, "w")
rapid_test_file = open(rapid_test_path, "w")
gcode_test_file.write(gcode_txt)
rapid_test_file.write(rapid_txt)
gcode_test_file.close()
rapid_test_file.close()

# create application
app = 0
win = 0
app = QApplication(sys.argv)
test_frame = mf.Mainframe(lpath=logpath, p_conn=(False, False), testrun=True)
rapid_test_file.close()

# grouping
ACON_btt_group = (
    test_frame.ADC_btt_clamp,
    test_frame.ADC_btt_knifePos,
    test_frame.ADC_btt_knife,
    test_frame.ADC_btt_fiberPnmtc,
    test_frame.ASC_btt_clamp,
    test_frame.ASC_btt_knifePos,
    test_frame.ASC_btt_knife,
    test_frame.ASC_btt_fiberPnmtc,
)


# run test immediatly only if called alone
if __name__ == "__main__":
    unittest.main()
