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

import libs.data_utilities as du
import libs.threads as T


################################### TESTS ####################################


class ThreadsTest(unittest.TestCase):

    def test_loadFileWorker(self):
        global LFWorker
        global gcode_test_path
        global rapid_test_path

        self.maxDiff = 3000
        du.SC_curr_comm_id = 1
        du.DCCurrZero = du.Coordinate()
        du.SCQueue.clear()

        # GCode
        T.lfw_file_path = gcode_test_path
        T.lfw_line_id = 0
        LFWorker.run(testrun=True)
        TestCoor1 = du.Coordinate(y=2000, z=0)
        TestCoor2 = du.Coordinate(y=2000, z=1000)

        self.assertEqual(
            du.SCQueue.display(),
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
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor2).print_short(),
            ],
        )

        # RAPID
        du.SCQueue.clear()
        du.SC_curr_comm_id = 1
        TestCoor1.ext = 11.0
        TestCoor2.ext = 11.0

        T.lfw_file_path = rapid_test_path
        T.lfw_line_id = 0
        LFWorker.run(testrun=True)
        self.assertEqual(
            du.SCQueue.display(),
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
            du.SCQueue.display(),
            [
                du.QEntry(id=1, Coor1=TestCoor1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor2).print_short(),
            ],
        )

        du.SCQueue.clear()
        du.SC_curr_comm_id = 1


    def test_RoboCommWorker(self):
        global RCWorker

        # send
        du.SCQueue.clear()
        du.ROBCommQueue.clear()
        du.ROB_send_list.clear()
        du.SCQueue.add(du.QEntry(id=1, Coor1=du.Coordinate(y=1.1)))

        du.ROB_send_list.append((du.QEntry(id=3001, mt="A"), True))
        RCWorker.send(testrun=True)
        self.assertEqual(
            du.ROBCommQueue.display(),
            [du.QEntry(id=1, mt="A").print_short()],
        )
        self.assertEqual(
            du.SCQueue.display(),
            [du.QEntry(id=2, Coor1=du.Coordinate(y=1.1)).print_short()],
        )
        du.ROBCommQueue.clear()
        du.SCQueue.clear()

        # checkRobCommZeroDist
        du.ROBCommQueue.clear()
        self.assertIsNone(RCWorker._check_zero_dist())

        TestCoor3 = du.Coordinate(x=1, y=1, z=1, ext=1)
        du.ROBCommQueue.add(du.QEntry(Coor1=TestCoor3))
        du.ROBTelem.Coor = du.Coordinate()
        self.assertEqual(RCWorker._check_zero_dist(), 2)


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
