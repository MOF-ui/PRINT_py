# test data_utilities

############################################# IMPORTS #################################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du
import libs.func_utilities as fu


############################################# TESTS #################################################

class FuncLibTest(unittest.TestCase):

    def test_pre_check_gcode_file_function(self):
        """checks preCheckGcodeFiles function, should count the number of commands in a file"""

        testTxt = ";comment\nG1 X0 Y0 Z0\nG1 X2000 Y0 Z0.0\nG1 X2000 Y1500 Z0"
        self.assertEqual(fu.pre_check_gcode_file(''), (0, 0, "empty"))
        self.assertEqual(fu.pre_check_gcode_file(testTxt), (3, 3.5, ""))


    def test_pre_check_rapid_file_function(self):
        """checks preCheckGcodeFiles function, should count the number of commands in a file"""

        testTxt = "!comment\nMoveL [[0.0,0.0,0.0],...,v50,z10,tool0\nMoveL [[2000.0,0.0,0.0],...,v50,z10,tool0\nMoveL [[2000.0,1500.0,0.0],...,v50,z10,tool0"
        self.assertEqual(fu.pre_check_rapid_file(''), (0, 0, "empty"))
        self.assertEqual(fu.pre_check_rapid_file(testTxt), (3, 3.5, ""))


    def test_re_short_function(self):
        """see reShort in libs/PRINT_data_utilities"""

        TestCoor = du.Coordinate(1,2,3,4,5,6,7,8)
        self.assertIsNone(fu.re_short(['\d+.\d+', '\d+'], 'ABC', None))
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'ABC', TestCoor), TestCoor)
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB1C', TestCoor), '1')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB1.2C', None), '1.2')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB3C', None, 'B'), '3')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB-3C', None, 'B'), '-3')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB3.4C', None, 'B'), '3.4')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB-3.4C', None, 'AB'), '-3.4')
        self.assertEqual(fu.re_short(['\d+.\d+', '\d+'], 'AB-3.4C5.6', None, 'C'), '5.6')
        self.assertEqual(fu.re_short([],'A8B', None, 'A'), '8')
        self.assertEqual(fu.re_short(None,'A8B', None, 'A'), '8')


    def test_gcode_to_qentry_function(self):
        """see gcodeToQEntry in libs/PRINT_data_utilities"""

        testPos = du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)
        testSpeed = du.SpeedVector(2, 2, 2, 2)
        testZone = 3
        du.DCCurrZero = du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)

        testTxt = "G1 X5.5 Y6 EXT7 F80 TOOL"
        self.assertEqual(
            fu.gcode_to_qentry(
                mut_pos=testPos, mut_speed=testSpeed, zone=testZone, txt=testTxt
            ),
            (
                du.QEntry(
                    Coor1=du.Coordinate(9.5, 10, 1, 1, 1, 1, 1, 11),
                    Speed=du.SpeedVector(2, 2, 8, 2),
                    z=3,
                    Tool=du.ToolCommand(fib_deliv_steps=10, pnmtc_fiber_yn=True),
                ),
                "G1",
            ),
        )

        testTxt = "G28 X0 Y0"
        self.assertEqual(
            fu.gcode_to_qentry(
                mut_pos=testPos, mut_speed=testSpeed, zone=testZone, txt=testTxt
            ),
            (
                du.QEntry(
                    Coor1=du.Coordinate(4, 4, 1, 1, 1, 1, 1, 1),
                    Speed=du.SpeedVector(2, 2, 2, 2),
                    z=3,
                ),
                "G28",
            ),
        )

        testTxt = "G92 X0 Y0"
        fu.gcode_to_qentry(
            mut_pos=testPos, mut_speed=testSpeed, zone=testZone, txt=testTxt
        )
        self.assertEqual(du.DCCurrZero, du.Coordinate(1, 1, 4, 4, 4, 4, 4, 4))


    def test_rapid_to_qentry_function(self):
        """see gcodeToQEntry in libs/PRINT_data_utilities"""

        du.DCCurrZero = du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)

        testTxt = "MoveJ [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[0,0,0,0],[0,0,0,0,0,0]],[8,9,10,11],z12,tool0 EXT13 TOOL"
        self.assertEqual(
            fu.rapid_to_qentry(txt=testTxt),
            (
                du.QEntry(
                    Coor1=du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 13),
                    mt="J",
                    pt="Q",
                    Speed=du.SpeedVector(10, 11, 8, 9),
                    z=12,
                    Tool=du.ToolCommand(fib_deliv_steps=10, pnmtc_fiber_yn=True),
                )
            ),
        )

        testTxt = "MoveL Offs(pHome,1.1,2.2,3.3),[8,9,10,11],z12,tool0 EXT13"
        self.assertEqual(
            fu.rapid_to_qentry(txt=testTxt),
            (
                du.QEntry(
                    Coor1=du.Coordinate(5.1, 6.2, 7.3, 4, 4, 4, 4, 17),
                    pt="E",
                    Speed=du.SpeedVector(10, 11, 8, 9),
                    z=12,
                )
            ),
        )


    def test_show_on_terminal_function(self):
        """see showOnTerminal in libs/PRINT_data_utilities"""

        du.DEF_TERM_MAX_LINES = 1
        fu.add_to_comm_protocol("1")
        self.assertEqual(du.TERM_log, ["1"])

        fu.add_to_comm_protocol("2")
        self.assertEqual(du.TERM_log, ["2"])


#############################################  MAIN  ##################################################

if __name__ == "__main__":
    unittest.main()
