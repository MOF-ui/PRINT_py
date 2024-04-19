# test pump_utilities

############################################# IMPORTS #################################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du
import libs.pump_utilities as pu

############################################  CLASS  ##################################################



class PUTIL_test(unittest.TestCase):


    def test_calcSpeed(self):
        """cases 'default', 'start' and 'end' are tested seperately"""

        du.PMP_speed = 89

        # domain control
        du.ROBCommQueue.clear()
        testEntry = du.QEntry(Speed=du.SpeedVector(ts=2000), p_mode="default")

        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), 100.0)

        du.ROBCommQueue[0].Speed.ts = -2000
        self.assertEqual(pu.calc_speed(), -100.0)

        # test empty ROB_commQueue
        du.ROBCommQueue.clear()
        self.assertEqual(pu.calc_speed(), 89)

        # mode: None
        testEntry = du.QEntry(Speed=du.SpeedVector(ts=123))
        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), 89)

        # mode: default
        testEntry = du.QEntry(id=1, Speed=du.SpeedVector(ts=234), p_mode="default")
        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), 19)

        du.ROBCommQueue.clear()


    def test_defaultMode(self):
        """ """

        # None
        self.assertIsNone(pu.default_mode(None))

        # lastDefCommand
        testEntry = du.QEntry(Coor1=du.Coordinate(x=10))
        pu.last_def_command = du.QEntry(Coor1=du.Coordinate(x=10))
        pu.last_speed = 45

        self.assertEqual(pu.default_mode(testEntry), 45)

        # newCommand ( default Speed.ts for QEntry is 200 )
        testEntry = du.QEntry(Coor1=du.Coordinate(x=11))

        self.assertEqual(pu.default_mode(testEntry), 16)


    def test_profileMode(self):
        """ """

        du.ROBCommQueue.add(du.QEntry())
        du.ROBCommQueue.add(du.QEntry())
        du.ROBTelem.Coor = du.Coordinate()
        pu.START_SUPP_PTS = [
            {"until": 3.0, "base": "zero", "mode": "instant"},
            {"until": 1.0, "base": "max", "mode": "instant"},
            {"until": 0.0, "base": "conn", "mode": "linear"},
        ]

        pu.END_SUPP_PTS = [
            {"until": 5.0, "base": "default", "mode": "instant"},
            {"until": 1.0, "base": "retract", "mode": "smoothstep"},
            {"until": 0.0, "base": "zero", "mode": "instant"},
        ]

        # START_SUPP_PTS
        testEntry = du.QEntry(Coor1=du.Coordinate(x=10), Speed=du.SpeedVector(ts=1))
        self.assertEqual(pu.profile_mode(testEntry, pu.START_SUPP_PTS), 0)

        du.ROBTelem.Coor = du.Coordinate(x=5)
        self.assertEqual(pu.profile_mode(testEntry, pu.START_SUPP_PTS), 0)

        du.ROBTelem.Coor = du.Coordinate(x=8)
        self.assertEqual(pu.profile_mode(testEntry, pu.START_SUPP_PTS), 100.0)

        du.ROBTelem.Coor = du.Coordinate(x=9.5)
        self.assertEqual(pu.profile_mode(testEntry, pu.START_SUPP_PTS), 58.0)

        du.ROBTelem.Coor = du.Coordinate(x=10)
        self.assertEqual(pu.profile_mode(testEntry, pu.START_SUPP_PTS), 16.0)

        # END_SUPP_PTS
        du.ROBTelem.Coor = du.Coordinate(x=4)
        self.assertEqual(pu.profile_mode(testEntry, pu.END_SUPP_PTS), 0.08)

        du.ROBTelem.Coor = du.Coordinate(x=7)
        self.assertEqual(pu.profile_mode(testEntry, pu.END_SUPP_PTS), -24.96)

        du.ROBTelem.Coor = du.Coordinate(x=10)
        self.assertEqual(pu.profile_mode(testEntry, pu.END_SUPP_PTS), 0)

        du.ROBCommQueue.clear()


    def test_getBaseSpeed(self):
        """ """

        self.assertEqual(pu.get_base_speed("zero", 12), 0)
        self.assertEqual(pu.get_base_speed("max", 12), 100)
        self.assertEqual(pu.get_base_speed("min", 12), -100)
        self.assertEqual(pu.get_base_speed("default", 12), 12)
        self.assertEqual(pu.get_base_speed("retract", 12), -50)
        self.assertEqual(pu.get_base_speed("conn", 12), 12)

        du.ROBCommQueue.add(du.QEntry())
        du.ROBCommQueue.add(du.QEntry())
        self.assertEqual(pu.get_base_speed("conn", 12), 16)


############################################  MAIN  ##################################################

if __name__ == "__main__":
    unittest.main()
