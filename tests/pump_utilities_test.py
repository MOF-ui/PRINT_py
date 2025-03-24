# test pump_utilities

################################## IMPORTS ###################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du
import libs.pump_utilities as pu

################################### TESTS ####################################



class PumpLibTest(unittest.TestCase):


    def test_get_pmp_speeds(self):
        """"""

        du.SC_q_processing = False
        preset_speed = du.PMP_speed
        preset_pmp_out_ratio = du.PMP_output_ratio
        du.PMP_speed = 10
        du.PMP_output_ratio = 0.5
        self.assertEqual(pu.get_pmp_speeds(), (5, 5, None))

        du.PMP1_user_speed = 12
        du.PMP2_user_speed = 34
        self.assertEqual(pu.get_pmp_speeds(), (12, 34, None))
        self.assertEqual(du.PMP1_user_speed, -999)
        self.assertEqual(du.PMP2_user_speed, -999)

        du.PMP_speed = preset_speed
        du.PMP_output_ratio = preset_pmp_out_ratio


    def test_look_ahead(self):
        """ """

        du.PMP_look_ahead_prerun = 1.0
        du.PMP_look_ahead_retract = 1.0
        # if no valid command comming up, return input
        du.ROBCommQueue.add(du.QEntry(Coor1=du.Coordinate(x=10), p_mode=10))
        du.ROBTelem = du.RoboTelemetry(Coor=du.Coordinate(x=8))
        preset_look_ahead_dist = du.PMP_look_ahead_dist
        du.PMP_look_ahead_dist = 5.0
        self.assertEqual(pu.look_ahead(10,0), (10, 0))

        # if so and we're closer than PMP_look_ahead_dist, return retract
        # for running pump and prerun for upcomming pump
        du.ROBCommQueue.add(du.QEntry(
            Coor1=du.Coordinate(x=20),
            p_mode=10,
            p_ratio=0.0,
        ))
        self.assertEqual(pu.look_ahead(10,0), (-10, 10))

        # check if look ahead works over multiple entries by placing
        # some inbetween with p_ratio=1
        du.ROBCommQueue.add(du.QEntry(
            id=2,
            Coor1=du.Coordinate(x=11),
            p_mode=10,
            p_ratio=1.0,
        ))
        du.ROBCommQueue.add(du.QEntry(
            id=3,
            Coor1=du.Coordinate(x=12),
            p_mode=10,
            p_ratio=1.0,
        ))
        self.assertEqual(pu.look_ahead(10,0), (-10, 10))

        # test factorization
        du.PMP_look_ahead_prerun = 2.0
        du.PMP_look_ahead_retract = 2.0
        self.assertEqual(pu.look_ahead(10,0), (-20, 20))
        du.PMP_look_ahead_prerun = 1.0
        du.PMP_look_ahead_retract = 1.0

        # if we're further away, return input
        du.ROBTelem = du.RoboTelemetry(Coor=du.Coordinate(x=2))
        self.assertEqual(pu.look_ahead(10,0), (10, 0))

        du.ROBCommQueue.clear()
        du.ROBTelem = du.RoboTelemetry()
        du.PMP_look_ahead_dist = preset_look_ahead_dist



    def test_calcSpeed(self):
        """cases 'default', 'start' and 'end' are tested seperately"""

        du.PMP_speed = 89
        du.ROBCommQueue.clear()
        testEntry = du.QEntry(
            Speed=du.SpeedVector(ts=2000),
            p_mode=1001, # = default mode
            p_ratio=0.345
        )

        # domain control
        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), (100, 100, False))
        du.ROBCommQueue[0].Speed.ts = -2000
        self.assertEqual(pu.calc_speed(), (-100, -100, False))

        # test empty ROB_commQueue
        du.ROBCommQueue.clear()
        du.PMP1Serial.connected = True
        du.PMP2Serial.connected = False
        self.assertEqual(pu.calc_speed(), (89, 89, False))
        du.PMP1Serial.connected = True
        du.PMP2Serial.connected = True
        self.assertEqual(pu.calc_speed(), (89, 0, False))

        # mode: None
        testEntry = du.QEntry(Speed=du.SpeedVector(ts=123))
        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), (89, 0, False))

        # mode: default
        testEntry = du.QEntry(
            id=1,
            Speed=du.SpeedVector(ts=234),
            p_mode=1001,
            p_ratio=0.765
        )
        du.ROBCommQueue.add(testEntry)
        self.assertEqual(pu.calc_speed(), (14, 4, False))

        du.ROBCommQueue.clear()


    def test_defaultMode(self):
        """  """

        du.PMP1_liter_per_s = 1.0
        du.PMP_output_ratio = 1.0
        du.SC_vol_per_m = 100.0
        # None
        self.assertIsNone(pu.default_mode(None))

        # newCommand ( default Speed.ts for QEntry is 200 )
        testEntry = du.QEntry(Speed=du.SpeedVector(ts=1))
        self.assertEqual(pu.default_mode(testEntry), 10)


    def test_getBaseSpeed(self):
        """ """

        self.assertEqual(pu.get_base_speed("zero", 12), 0)
        self.assertEqual(pu.get_base_speed("max", 12), 100)
        self.assertEqual(pu.get_base_speed("min", 12), -100)
        self.assertEqual(pu.get_base_speed("default", 12), 12)
        self.assertEqual(pu.get_base_speed("retract", 12), -50)
        self.assertEqual(pu.get_base_speed("conn", 12), 12)

        TestCoor= du.Coordinate(10)
        TestVector=du.SpeedVector(ts=1)
        du.ROBCommQueue.append(
            du.QEntry(id=2, Coor1=TestCoor, Speed=TestVector)
        )
        du.ROBCommQueue.append(
            du.QEntry(id=3, Coor1=TestCoor+10, Speed=TestVector)
        )
        self.assertEqual(pu.get_base_speed("conn", 12), 10)
        du.ROBCommQueue.clear()


    def test_profileMode(self):
        """ """

        du.PMP_retract_speed = -50.0
        du.ROBMovStartP = du.Coordinate()
        TestCoor= du.Coordinate(10)
        TestVector=du.SpeedVector(ts=1)
        TestEntry = du.QEntry(Coor1=TestCoor, Speed=TestVector)
        du.ROBCommQueue.append(
            du.QEntry(id=2, Coor1=TestCoor, Speed=TestVector)
        )
        du.ROBCommQueue.append(
            du.QEntry(id=3, Coor1=TestCoor+10, Speed=TestVector)
        )
        pu.START_SUPP_PTS = [
            {'until': 5.0, 'base': 'zero', 'mode': 'instant'},
            {'until': 1.0, 'base': 'max', 'mode': 'instant'},
            {'until': 0.0, 'base': 'conn', 'mode': 'linear'},
        ]

        pu.END_SUPP_PTS = [
            {'until': 5.0, 'base': 'default', 'mode': 'instant'},
            {'until': 1.0, 'base': 'retract', 'mode': 'smoothstep'},
            {'until': 0.0, 'base': 'zero', 'mode': 'instant'},
        ]

        # START_SUPP_PTS
        expected_ans = [0, 0, 0, 0, 0, 0, 100.0, 100.0, 100.0, 100.0, 10.0]
        for i in range(0, 11):
            du.ROBTelem.Coor = du.Coordinate(x=i)
            self.assertEqual(
                pu.profile_mode(TestEntry, pu.START_SUPP_PTS),
                expected_ans[i],
            )

        du.ROBTelem.Coor = du.Coordinate(x=9.5)
        self.assertEqual(pu.profile_mode(TestEntry, pu.START_SUPP_PTS), 55.0)

        # END_SUPP_PTS
        expected_ans = [10, 10, 10, 10, 10, 10, 0.625, -20, -40.625, -50.0, 0]
        for i in range(0, 11):
            du.ROBTelem.Coor = du.Coordinate(x=i)
            self.assertEqual(
                pu.profile_mode(TestEntry, pu.END_SUPP_PTS),
                expected_ans[i],
            )

        du.ROBCommQueue.clear()
        du.PMP1_liter_per_s = du.DEF_PUMP_LPS
        du.PMP_output_ratio = 1.0
        du.SC_vol_per_m = du.DEF_SC_VOL_PER_M
        du.PMP_retract_speed = du.DEF_PUMP_RETR_SPEED


#################################  MAIN  #####################################

if __name__ == "__main__":
    unittest.main()
