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
# TO DO: add tests for __iter__, __next__, __ne__

class UTIL_test(unittest.TestCase):


    def test_Coor_class(self):
        """test Coor class, used to store positional data from robot"""

        # __init__ & __str__
        self.assertEqual(
            str(
                du.Coordinate(
                    x=1.2, y=3.4, z=5.6, rx=7.8, ry=9.11, rz=22.33, q=44.55, ext=66.77
                )
            ),
            f"X: {1.2}   Y: {3.4}   Z: {5.6}   Rx: {7.8}   Ry: {9.11}   Rz: {22.33}   Q: {44.55}   EXT: {66.77}",
        )
        self.assertEqual(
            str(du.Coordinate()),
            f"X: {0.0}   Y: {0.0}   Z: {0.0}   Rx: {0.0}   Ry: {0.0}   Rz: {0.0}   Q: {0.0}   EXT: {0.0}",
        )

        # __add__
        self.assertEqual(
            du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
            + du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8),
            du.Coordinate(2.2, 4.4, 6.6, 8.8, 11.0, 13.2, 15.4, 17.6),
        )
        self.assertEqual(
            du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8) + 11.1,
            du.Coordinate(12.2, 13.3, 14.4, 15.5, 16.6, 17.7, 18.8, 19.9),
        )

        # __sub__
        self.assertEqual(
            du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
            - du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8),
            du.Coordinate(),
        )
        self.assertEqual(
            du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8) - 1.1,
            du.Coordinate(0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7),
        )

        # __round__
        self.assertEqual(
            round(
                du.Coordinate(1.111, 2.222, 3.333, 4.444, 5.555, 6.666, 7.777, 8.888), 1
            ),
            du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.6, 6.7, 7.8, 8.9),
        )


    def test_Speed_class(self):
        """test Speed class, used to store acceleration and travel speed settings"""

        # __init__ & __str__
        self.assertEqual(
            str(du.SpeedVector(acr=1.2, dcr=3.4, ts=5.6, ors=7.8)),
            f"TS: {6}   OS: {8}   ACR: {1}   DCR: {3}",
        )
        self.assertEqual(
            str(du.SpeedVector()), f"TS: {200}   OS: {50}   ACR: {50}   DCR: {50}"
        )

        # __mul__ & __rmul__
        self.assertEqual(
            du.SpeedVector(22, 44, 6, 8) * 1.1, du.SpeedVector(24, 48, 7, 9)
        )
        self.assertEqual(
            du.SpeedVector(22, 44, 6, 8) * 1.1, 1.1 * du.SpeedVector(22, 44, 6, 8)
        )


    def test_ToolCommand_class(self):
        """test ToolCommand class, used to store AmConEE data"""

        # __init__ & __str__
        self.assertEqual(
            str(
                du.ToolCommand(
                    1, 2, 3, 4, 5, 6, 7, True, 8, False, 9, False, 10, True, 11, 12
                )
            ),
            f"PAN: {1}, {2}   FB: {3}, {4}   MP: {5}, {6}   PC: {7}, {True}   KP: {8}, {False}   K: {9}, {False}   PF: {10}, {True}   TIME: {11}, {12}",
        )

        self.assertEqual(
            str(du.ToolCommand()),
            f"PAN: {0}, {0}   FB: {0}, {0}   MP: {0}, {0}   PC: {0}, {False}   KP: {0}, {False}   K: {0}, {False}   PF: {0}, {False}   TIME: {0}, {0}",
        )


    def test_QEntry_class(self):
        """test QEntry class, build 159-bytes commands"""

        self.maxDiff = 2000

        # __init__ & __str__
        self.assertEqual(
            str(
                du.QEntry(
                    id=1,
                    mt=2,
                    pt=3,
                    Coor1=du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4),
                    Coor2=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5),
                    Speed=du.SpeedVector(6, 6, 6, 6),
                    sbt=7,
                    sc="A",
                    z=8,
                    Tool=du.ToolCommand(9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9),
                )
            ),
            f"ID: {1}  MT: {2}  PT: {3} \t|| COOR_1: {du.Coordinate( 4,4,4,4,4,4,4,4 )}"
            f"\n\t\t|| COOR_2: {du.Coordinate( 5,5,5,5,5,5,5,5 )}"
            f"\n\t\t|| SV:     {du.SpeedVector( 6,6,6,6 )} \t|| SBT: {7}   SC: A   Z: {8}"
            f"\n\t\t|| TOOL:   {du.ToolCommand( 9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9)}"
            f"\n\t\t|| PMODE:  None",
        )

        self.assertEqual(
            str(du.QEntry()),
            f"ID: {0}  MT: L  PT: E \t|| COOR_1: {du.Coordinate()}"
            f"\n\t\t|| COOR_2: {du.Coordinate()}"
            f"\n\t\t|| SV:     {du.SpeedVector()} \t|| SBT: {0}   SC: V   Z: {10}"
            f"\n\t\t|| TOOL:   {du.ToolCommand()}"
            f"\n\t\t|| PMODE:  None",
        )


    def test_Queue_class(self):
        """test Queue class, organizes QEntry list"""

        self.maxDiff = 2000

        emptyQueue = du.Queue()
        testQueue = du.Queue()
        testQueue.add(du.QEntry())
        testQueue.add(du.QEntry(id=3, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)))

        # __init__ & __str__
        self.assertEqual(
            str(testQueue),
            f"Element 1: {du.QEntry( id= 1 ) }\n"
            f"Element 2: {du.QEntry( id= 2, Coor1= du.Coordinate( 3,3,3,3,3,3,3,3 ) )}\n",
        )

        self.assertEqual(str(du.Queue()), f"Queue is empty!")

        # __getitem__
        self.assertIsNone(emptyQueue[1])
        self.assertEqual(
            testQueue[1], du.QEntry(id=2, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3))
        )

        # __len__
        self.assertEqual(len(testQueue), 2)

        # __eq__
        self.assertFalse(testQueue == du.Queue())
        self.assertTrue(testQueue == testQueue)

        # lastEntry
        self.assertIsNone(emptyQueue.last_entry())
        self.assertEqual(
            testQueue.last_entry(),
            du.QEntry(id=2, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)),
        )

        # entryBeforeID
        self.assertRaises(AttributeError, emptyQueue.entry_before_id, 1)
        self.assertRaises(AttributeError, testQueue.entry_before_id, 1)
        self.assertRaises(AttributeError, testQueue.entry_before_id, 3)
        self.assertEqual(testQueue.entry_before_id(2), du.QEntry(id=1))

        # display
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(id=1).print_short(),
                du.QEntry(
                    id=2, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short(),
            ],
        )

        self.assertEqual(emptyQueue.display(), ["Queue is empty!"])

        # increment
        testQueue.increment()
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(id=2).print_short(),
                du.QEntry(
                    id=3, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short(),
            ],
        )

        # add
        self.assertEqual(testQueue.add(du.QEntry(id=-1)), ValueError)

        testQueue.add(du.QEntry(id=0, Coor1=du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)))
        testQueue.add(du.QEntry(id=9, Coor1=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)))
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(id=2).print_short(),
                du.QEntry(
                    id=3, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short(),
                du.QEntry(
                    id=4, Coor1=du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)
                ).print_short(),
                du.QEntry(
                    id=5, Coor1=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)
                ).print_short(),
            ],
        )

        testQueue.add(du.QEntry(id=1, Coor1=du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)))
        testQueue.add(du.QEntry(id=4, Coor1=du.Coordinate(6, 6, 6, 6, 6, 6, 6, 6)))
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(
                    id=2, Coor1=du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)
                ).print_short(),
                du.QEntry(id=3).print_short(),
                du.QEntry(
                    id=4, Coor1=du.Coordinate(6, 6, 6, 6, 6, 6, 6, 6)
                ).print_short(),
                du.QEntry(
                    id=5, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short(),
                du.QEntry(
                    id=6, Coor1=du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)
                ).print_short(),
                du.QEntry(
                    id=7, Coor1=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)
                ).print_short(),
            ],
        )

        # clear
        self.assertEqual(testQueue.clear(all=False, id=""), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="3..4.5"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="8"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="1"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="1..3"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="5..8"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="5..3"), ValueError)
        self.assertEqual(testQueue.clear(all=False, id="3,,5"), ValueError)

        testQueue.clear(all=False, id="4")
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(
                    id=2, Coor1=du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)
                ).print_short(),
                du.QEntry(id=3).print_short(),
                du.QEntry(
                    id=4, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short(),
                du.QEntry(
                    id=5, Coor1=du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)
                ).print_short(),
                du.QEntry(
                    id=6, Coor1=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)
                ).print_short(),
            ],
        )

        testQueue.clear(all=False, id="3..5")
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(
                    id=2, Coor1=du.Coordinate(1, 1, 1, 1, 1, 1, 1, 1)
                ).print_short(),
                du.QEntry(
                    id=3, Coor1=du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)
                ).print_short(),
            ],
        )

        testQueue.clear()
        self.assertEqual(testQueue.display(), ["Queue is empty!"])

        # popFirstItem
        self.assertEqual(emptyQueue.pop_first_item(), IndexError)

        testQueue.add(du.QEntry())
        testQueue.add(du.QEntry(id=3, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)))
        self.assertEqual(testQueue.pop_first_item(), du.QEntry(id=1))
        self.assertEqual(
            testQueue.display(),
            [
                du.QEntry(
                    id=2, Coor1=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                ).print_short()
            ],
        )


    def test_RoboTelemetry_class(self):
        """test RoboTelemetry class, used to store 36 TCP-response from robot"""

        # __init__ & __str__
        self.assertEqual(
            str(
                du.RoboTelemetry(
                    t_speed=1.1, id=2, Coor=du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
                )
            ),
            f"ID: {2}   X: {3.0}   Y: {3.0}   Z: {3.0}   Rx: {3.0}   Ry: {3.0}   Rz: {3.0}   EXT:   {3.0}   TOOL_SPEED: {1.1}",
        )
        self.assertEqual(
            str(du.RoboTelemetry()),
            f"ID: {-1}   X: {0.0}   Y: {0.0}   Z: {0.0}   Rx: {0.0}   Ry: {0.0}   Rz: {0.0}   EXT:   {0.0}   TOOL_SPEED: {0.0}",
        )

        # __round__
        self.assertEqual(
            round(
                du.RoboTelemetry(
                    t_speed=1.111,
                    id=2.222,
                    Coor=du.Coordinate(
                        3.333, 3.333, 3.333, 3.333, 3.333, 3.333, 3.333, 3.333
                    ),
                ),
                1,
            ),
            du.RoboTelemetry(
                t_speed=1.1,
                id=2,
                Coor=du.Coordinate(3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3),
            ),
        )


    def test_PumpTelemetry_class(self):
        """test RoboTelemetry class, used to store 36 TCP-response from robot"""

        # __init__ & __str__
        self.assertEqual(
            str(du.PumpTelemetry(freq=1.1, volt=2.2, amps=3.3, torq=4.4)),
            f"FREQ: {1.1}   VOLT: {2.2}   AMPS: {3.3}   TORQ: {4.4}",
        )
        self.assertEqual(
            str(du.PumpTelemetry()),
            f"FREQ: {0.0}   VOLT: {0.0}   AMPS: {0.0}   TORQ: {0.0}",
        )

        # __round__
        self.assertEqual(
            round(du.PumpTelemetry(freq=1.111, volt=2.222, amps=3.333, torq=4.444), 1),
            du.PumpTelemetry(freq=1.1, volt=2.2, amps=3.3, torq=4.4),
        )


    def test_DataBlock_class(self):
        """test DataBlock class, used to sort data for InfluxDB"""
        self.maxDiff = 2000

        # __init__ & __str__
        self.assertEqual(
            str(
                du.DaqBlock(
                    amb_temp = 1.1,
                    amb_humidity = 2.2,
                    rb_temp = 3.3,
                    msp_temp = 4.4,
                    msp_press = 5.5,
                    asp_freq = 6.6,
                    asp_amps = 7.7,
                    imp_temp = 8.8,
                    imp_press = 9.9,
                    imp_freq = 10.1,
                    imp_amps = 11.11,
                    Robo = du.RoboTelemetry(
                        12.12, 13, du.Coordinate(14.14, 15, 16, 17, 18, 19, 20, 21)
                    ),
                    Pump1 = du.PumpTelemetry(23, 24, 25, 26),
                    Pump2 = du.PumpTelemetry(27, 28, 29, 30),
                    phc_aircon = 31.31,
                    phc_fdist = 32.32,
                    phc_edist = 33.33,
                )
            ),
            f"Amb. temp.: {1.1}    Amb. humid.: {2.2}    RB temp.: {3.3}    MSP temp.: {4.4}    "
            f"MSP press.: {5.5}    APS freq.: {6.6}    APS amp.: {7.7}    IMP temp.: {8.8}    "
            f"IMP press.: {9.9}    IMP freq.: {10.10}    IMP amp.: {11.11}    "
            f"ROB: {du.RoboTelemetry(12.12, 13, du.Coordinate(14.14, 15, 16, 17, 18, 19, 20, 21))}    "
            f"PUMP1: {du.PumpTelemetry(23, 24, 25, 26)}    PUMP2: {du.PumpTelemetry(27, 28, 29, 30)}    "
            f"PHC air cont.: {31.31}    PHC front dist.: {32.32}    PHC end dist.: {33.33}",
        )

        self.assertEqual(
            str(du.DaqBlock()),
            f"Amb. temp.: {0.0}    Amb. humid.: {0.0}    RB temp.: {0.0}    MSP temp.: {0.0}    "
            f"MSP press.: {0.0}    APS freq.: {0.0}    APS amp.: {0.0}    IMP temp.: {0.0}    "
            f"IMP press.: {0.0}    IMP freq.: {0.0}    IMP amp.: {0.0}    "
            f"ROB: {du.RoboTelemetry()}    PUMP1: {du.PumpTelemetry()}    "
            f"PUMP2: {du.PumpTelemetry()}    "
            f"PHC air cont.: {0.0}    PHC front dist.: {0.0}    PHC end dist.: {0.0}",
        )


    def test_TCPIP_class(self):
        """test TCPIP class, handles connection data und functions"""

        testTCPIP = du.TCPIP()

        # __init__ & __str__
        initTestTCPIP = du.TCPIP(
            ip="1.1.1.1", PORT=2222, C_TOUT=3.3, RW_TOUT=4.4, R_BL=5.5, W_BL=6.6
        )

        self.assertEqual(
            str(initTestTCPIP),
            f"IP: 1.1.1.1   PORT: {2222}   C_TOUT: {3.3}   RW_TOUT: {4.4}   R_BL: {5}   W_BL: {6}",
        )
        self.assertEqual(
            str(testTCPIP),
            f"IP:    PORT: {0}   C_TOUT: {1.0}   RW_TOUT: {1.0}   R_BL: {0}   W_BL: {0}",
        )

        initTestTCPIP.close(end=True)

        # setParams
        testTCPIP.set_params(
            {
                "IP": "1.1.1.1",
                "PORT": 2222,
                "C_TOUT": 0.003,
                "RW_TOUT": 0.004,
                "R_BL": 5.5,
                "W_BL": 6.6,
            }
        )
        self.assertEqual(
            str(testTCPIP),
            f"IP: 1.1.1.1   PORT: {2222}   C_TOUT: {0.003}   RW_TOUT: {0.004}   R_BL: {5}   W_BL: {6}",
        )

        testTCPIP.connected = True
        self.assertRaises(PermissionError, testTCPIP.set_params, param_dict=None)
        testTCPIP.connected = False

        # connect
        ans0, ans1 = testTCPIP.connect()
        ans11, ans12 = ans1
        self.assertIsInstance(ans0, TimeoutError)
        self.assertEqual(ans11, "1.1.1.1")
        self.assertEqual(ans12, 2222)

        testTCPIP.port = "ABC"
        self.assertRaises(ConnectionError, testTCPIP.connect)

        # send
        ans0, ans1 = testTCPIP.send([True,True])
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ConnectionError)

        testTCPIP.connected = True
        ans0, ans1 = testTCPIP.send([True, True])
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ValueError)

        # receive
        ans0, ans1 = testTCPIP.receive()
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, TimeoutError)

        # close
        testTCPIP.close(end=True)
        self.assertFalse(testTCPIP.connected)


    def test_RobConnection_class(self):
        """test RobConnection class, handles connection data und functions"""

        testRobCon = du.RobConnection()

        # send
        
        ans0, ans1 = testRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ConnectionError)

        testRobCon.connected = True
        ans0, ans1 = testRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ValueError)

        testRobCon.w_bl = 159
        ans0, ans1 = testRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, OSError)

        # received (to add)

        testRobCon.close(end=True)


    def test_pre_check_gcode_file_function(self):
        """checks preCheckGcodeFiles function, should count the number of commands in a file"""

        testTxt = ";comment\nG1 X0 Y0 Z0\nG1 X2000 Y0 Z0.0\nG1 X2000 Y1500 Z0"
        self.assertEqual(fu.pre_check_ccode_file(''), (0, 0, "empty"))
        self.assertEqual(fu.pre_check_ccode_file(testTxt), (3, 3.5, ""))


    def test_pre_check_rapid_file_function(self):
        """checks preCheckGcodeFiles function, should count the number of commands in a file"""

        testTxt = "!comment\nMoveL [[0.0,0.0,0.0],...,v50,z10,tool0\nMoveL [[2000.0,0.0,0.0],...,v50,z10,tool0\nMoveL [[2000.0,1500.0,0.0],...,v50,z10,tool0"
        self.assertEqual(fu.pre_check_rapid_file(''), (0, 0, "empty"))
        self.assertEqual(fu.pre_check_rapid_file(testTxt), (3, 3.5, ""))


    def test_re_short_function(self):
        """see reShort in libs/PRINT_data_utilities"""

        self.assertEqual(fu.re_short("\d+\.\d+", "A12B", "0", "\d+"), "12")
        self.assertEqual(fu.re_short("\d+\.\d+", "A12.3B", "0", "\d+"), "12.3")
        self.assertEqual(fu.re_short("\d+\.\d+", "ABC", "0", "\d+"), "0")
        self.assertEqual(fu.re_short("\d+\.\d+", "A12B", "0"), "0")


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

        testTxt = "MoveJ [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[0,0,0,0],[0,0,0,0,0,0]],[8,9,10,11],z12,tool0 EXT:13 TOOL"
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
                ),
                None,
            ),
        )

        testTxt = "MoveL Offs(pHome,1.1,2.2,3.3),[8,9,10,11],z12,tool0 EXT:13"
        self.assertEqual(
            fu.rapid_to_qentry(txt=testTxt),
            (
                du.QEntry(
                    Coor1=du.Coordinate(5.1, 6.2, 7.3, 4, 4, 4, 4, 17),
                    pt="E",
                    Speed=du.SpeedVector(10, 11, 8, 9),
                    z=12,
                ),
                None,
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
