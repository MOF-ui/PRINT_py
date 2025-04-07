# test threads

################################## IMPORTS ###################################

import os
import sys
import unittest
import pathlib as pl

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.global_var as g
import libs.data_utilities as du
import libs.threads as T


################################### TESTS ####################################


class ThreadsTest(unittest.TestCase):

    def test_loadFileWorker(self):
        global LFWorker
        global gcode_test_path
        global rapid_test_path

        self.maxDiff = 3000
        g.SC_curr_comm_id = 1
        g.ROBCurrZero = du.Coordinate()
        g.SCQueue.clear()

        # GCode
        T.lfw_file_path = gcode_test_path
        T.lfw_line_id = 0
        LFWorker.run(testrun=True)
        TestCoor1 = du.Coordinate(y=2000, z=0)
        TestCoor2 = du.Coordinate(y=2000, z=1000)

        self.assertEqual(
            g.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor2).print_short(),
            ],
        )

        # GCode at ID
        T.lfw_file_path = gcode_test_path
        T.lfw_line_id = 2
        LFWorker.run(testrun=True)

        self.assertEqual(
            g.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor2).print_short(),
            ],
        )

        # RAPID
        g.SCQueue.clear()
        g.SC_curr_comm_id = 1
        TestCoor1.ext = 11.0
        TestCoor2.ext = 11.0

        T.lfw_file_path = rapid_test_path
        T.lfw_line_id = 0
        LFWorker.run(testrun=True)
        self.assertEqual(
            g.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor2).print_short(),
            ],
        )

        # RAPID at ID
        T.lfw_file_path = rapid_test_path
        T.lfw_line_id = 2
        LFWorker.run(testrun=True)
        self.assertEqual(
            g.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor2).print_short(),
            ],
        )

        g.SCQueue.clear()
        g.SC_curr_comm_id = 1


    def test_RoboCommWorker(self):
        global RCWorker

        # send
        g.SCQueue.clear()
        g.ROBCommQueue.clear()
        g.ROB_send_list.clear()
        g.SCQueue.add(
            du.QEntry(id=1, Coor1=du.Coordinate(y=1.1)),
            g.SC_curr_comm_id,
        )

        g.ROB_send_list.append((du.QEntry(id=3001, mt="A"), True))
        RCWorker.send(testrun=True)
        self.assertEqual(
            g.ROBCommQueue.display(),
            [du.QEntry(id=1, mt="A").print_short()],
        )
        self.assertEqual(
            g.SCQueue.display(),
            [du.QEntry(id=2, Coor1=du.Coordinate(y=1.1)).print_short()],
        )
        g.ROBCommQueue.clear()
        g.SCQueue.clear()

        # checkRobCommZeroDist
        g.ROBCommQueue.clear()
        self.assertTrue(RCWorker._check_target_reached())

        TestCoor3 = du.Coordinate(x=1, y=1, z=1, ext=1)
        g.ROBCommQueue.add(du.QEntry(Coor1=TestCoor3), g.SC_curr_comm_id)
        g.ROBTelem.Coor = du.Coordinate()
        g.ROB_min_target_dist = 3
        self.assertTrue(RCWorker._check_target_reached())
        g.ROB_min_target_dist = 1
        self.assertFalse(RCWorker._check_target_reached())


#################################  MAIN  #####################################

# create 0_BT_testfiles
desk = os.environ["USERPROFILE"]
dir_path = desk / pl.Path("Desktop/PRINT_py_testrun")
dir_path.mkdir(parents=True, exist_ok=True)

gcode_test_path = dir_path / pl.Path("0_UT_testfile.gcode")
rapid_test_path = dir_path / pl.Path("0_UT_testfile.mod")
gcode_txt = ";comment\nG1 Y2000\nG1 Z1000"
rapid_txt = "!comment\nMoveJ pHome,v200,fine,tool0;\n\n\
             ! start printjob relative to pStart\n\
             MoveL Offs(pHome,0.0,2000.0,0.0),[200,50,50,50],z10,tool0 EXT11;\n\
             MoveL Offs(pHome,0.0,2000.0,1000.0),[200,50,50,50],z10,tool0 EXT11;"

gcode_test_file = open(gcode_test_path, "w")
rapid_test_file = open(rapid_test_path, "w")
gcode_test_file.write(gcode_txt)
rapid_test_file.write(rapid_txt)
gcode_test_file.close()
rapid_test_file.close()

LFWorker = T.LoadFileWorker()
RCWorker = T.RoboCommWorker()

if __name__ == "__main__":
    unittest.main()
