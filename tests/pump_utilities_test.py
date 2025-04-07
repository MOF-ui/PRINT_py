# test pump_utilities

################################## IMPORTS ###################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.global_var as g
import libs.data_utilities as du
import libs.pump_utilities as pu

################################### TESTS ####################################



class PumpLibTest(unittest.TestCase):


    def test_get_pmp_speeds(self):
        """"""

        g.SC_q_processing = False
        preset_speed = g.PMP_speed
        preset_pmp_out_ratio = g.PMP_output_ratio
        g.PMP_speed = 10
        g.PMP_output_ratio = 0.5
        g.PMP1Serial.connected = True
        g.PMP2Serial.connected = True
        self.assertEqual(pu.get_pmp_speeds(), (5, 5, None))

        g.PMP1_user_speed = 12
        g.PMP2_user_speed = 34
        self.assertEqual(pu.get_pmp_speeds(), (12, 34, None))
        self.assertEqual(g.PMP1_user_speed, -999)
        self.assertEqual(g.PMP2_user_speed, -999)

        g.PMP_speed = preset_speed
        g.PMP_output_ratio = preset_pmp_out_ratio
        g.PMP1Serial.connected = False
        g.PMP2Serial.connected = False


    def test_look_ahead(self):
        """ """

        g.PMP_look_ahead_prerun = 1.0
        g.PMP_look_ahead_retract = 1.0
        # if no valid command comming up, return input
        g.ROBCommQueue.add(
            du.QEntry(Coor1=du.Coordinate(x=10), p_mode=10),
            g.SC_curr_comm_id
        )
        g.ROBTelem = du.RoboTelemetry(Coor=du.Coordinate(x=8))
        preset_look_ahead_dist = g.PMP_look_ahead_dist
        g.PMP_look_ahead_dist = 5.0
        self.assertEqual(pu.look_ahead(10,0), (10, 0))

        # if so and we're closer than PMP_look_ahead_dist, return retract
        # for running pump and prerun for upcomming pump
        g.ROBCommQueue.add(
            du.QEntry(
                Coor1=du.Coordinate(x=20),
                p_mode=10,
                p_ratio=0.0,
            ),
            g.SC_curr_comm_id,
        )
        self.assertEqual(pu.look_ahead(10,0), (-10, 10))

        # check if look ahead works over multiple entries by placing
        # some inbetween with p_ratio=1
        g.ROBCommQueue.add(
            du.QEntry(
                id=2,
                Coor1=du.Coordinate(x=11),
                p_mode=10,
                p_ratio=1.0,
            ),
            g.SC_curr_comm_id,
        )
        g.ROBCommQueue.add(
            du.QEntry(
                id=3,
                Coor1=du.Coordinate(x=12),
                p_mode=10,
                p_ratio=1.0,
            ),
            g.SC_curr_comm_id,
        )
        self.assertEqual(pu.look_ahead(10,0), (-10, 10))

        # test factorization
        g.PMP_look_ahead_prerun = 2.0
        g.PMP_look_ahead_retract = 2.0
        self.assertEqual(pu.look_ahead(10,0), (-20, 20))
        g.PMP_look_ahead_prerun = 1.0
        g.PMP_look_ahead_retract = 1.0

        # if we're further away, return input
        g.ROBTelem = du.RoboTelemetry(Coor=du.Coordinate(x=2))
        self.assertEqual(pu.look_ahead(10,0), (10, 0))

        g.ROBCommQueue.clear()
        g.ROBTelem = du.RoboTelemetry()
        g.PMP_look_ahead_dist = preset_look_ahead_dist



    def test_calcSpeed(self):
        """cases 'default', 'start' and 'end' are tested seperately"""

        g.PMP_speed = 89
        g.ROBCommQueue.clear()
        testEntry = du.QEntry(
            Speed=du.SpeedVector(ts=2000),
            p_mode=1001, # = default mode
            p_ratio=0.345
        )

        # domain control
        g.ROBCommQueue.add(testEntry, g.SC_curr_comm_id)
        self.assertEqual(pu.calc_speed(), (100, 100, False))
        g.ROBCommQueue[0].Speed.ts = -2000
        self.assertEqual(pu.calc_speed(), (-100, -100, False))

        # test empty ROB_commQueue
        g.ROBCommQueue.clear()
        g.PMP1Serial.connected = True
        g.PMP2Serial.connected = False
        self.assertEqual(pu.calc_speed(), (89, 89, False))
        g.PMP1Serial.connected = True
        g.PMP2Serial.connected = True
        self.assertEqual(pu.calc_speed(), (89, 0, False))

        # mode: None
        testEntry = du.QEntry(Speed=du.SpeedVector(ts=123))
        g.ROBCommQueue.add(testEntry, g.SC_curr_comm_id)
        self.assertEqual(pu.calc_speed(), (89, 0, False))

        # mode: default
        testEntry = du.QEntry(
            id=1,
            Speed=du.SpeedVector(ts=234),
            p_mode=1001,
            p_ratio=0.765
        )
        g.ROBCommQueue.add(testEntry, g.SC_curr_comm_id)
        self.assertEqual(pu.calc_speed(), (14, 4, False))

        g.ROBCommQueue.clear()


    def test_defaultMode(self):
        """  """

        g.PMP1_liter_per_s = 1.0
        g.PMP_output_ratio = 1.0
        g.SC_vol_per_m = 100.0
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
        g.ROBCommQueue.append(
            du.QEntry(id=2, Coor1=TestCoor, Speed=TestVector)
        )
        g.ROBCommQueue.append(
            du.QEntry(id=3, Coor1=TestCoor+10, Speed=TestVector)
        )
        self.assertEqual(pu.get_base_speed("conn", 12), 10)
        g.ROBCommQueue.clear()


    def test_profileMode(self):
        """ """

        g.PMP_retract_speed = -50.0
        g.ROBMovStartP = du.Coordinate()
        TestCoor= du.Coordinate(10)
        TestVector=du.SpeedVector(ts=1)
        TestEntry = du.QEntry(Coor1=TestCoor, Speed=TestVector)
        g.ROBCommQueue.append(
            du.QEntry(id=2, Coor1=TestCoor, Speed=TestVector)
        )
        g.ROBCommQueue.append(
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
            g.ROBTelem.Coor = du.Coordinate(x=i)
            self.assertEqual(
                pu.profile_mode(TestEntry, pu.START_SUPP_PTS),
                expected_ans[i],
            )

        g.ROBTelem.Coor = du.Coordinate(x=9.5)
        self.assertEqual(pu.profile_mode(TestEntry, pu.START_SUPP_PTS), 55.0)

        # END_SUPP_PTS
        expected_ans = [10, 10, 10, 10, 10, 10, 0.625, -20, -40.625, -50.0, 0]
        for i in range(0, 11):
            g.ROBTelem.Coor = du.Coordinate(x=i)
            self.assertEqual(
                pu.profile_mode(TestEntry, pu.END_SUPP_PTS),
                expected_ans[i],
            )

        g.ROBCommQueue.clear()
        g.PMP1_liter_per_s = g.PMP_LPS
        g.PMP_output_ratio = 1.0
        g.SC_vol_per_m = g.SC_VOL_PER_M
        g.PMP_retract_speed = g.PMP_RETR_SPEED


#################################  MAIN  #####################################

if __name__ == "__main__":
    unittest.main()
