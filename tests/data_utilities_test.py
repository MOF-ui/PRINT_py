# test data_utilities

################################## IMPORTS ###################################

import os
import sys
import time
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du
import libs.func_utilities as fu

from datetime import timedelta


################################### TESTS ####################################
# TO DO: add tests for __iter__, __next__, __ne__

class DataLibTest(unittest.TestCase):

    def test_Coor_class(self):
        """test Coor class, used to store positional data from robot"""

        # __init__ & __str__
        TestCoor = du.Coordinate(
            x=1.2, y=3.4, z=5.6, rx=7.8, ry=9.11, rz=22.33, q=44.55, ext=66.77
        )
        self.assertEqual(
            str(TestCoor),
            f"X: 1.2   Y: 3.4   Z: 5.6   RX: 7.8   "
            f"RY: 9.11   RZ: 22.33   Q: 44.55   EXT: 66.77",
        )
        self.assertEqual(
            str(du.Coordinate()),
            f"X: 0.0   Y: 0.0   Z: 0.0   RX: 0.0   "
            f"RY: 0.0   RZ: 0.0   Q: 0.0   EXT: 0.0",
        )

        # __eq__ & __ne__
        self.assertFalse(TestCoor == du.Coordinate())
        self.assertFalse(TestCoor == None)
        self.assertTrue(TestCoor == TestCoor)
        with self.assertRaises(TypeError):
            TestCoor == 5
        self.assertTrue(TestCoor != du.Coordinate())
        self.assertTrue(TestCoor != None)
        self.assertFalse(TestCoor != TestCoor)
        with self.assertRaises(TypeError):
            TestCoor != 5

        # __add__
        TestCoor = du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
        ResCoor = du.Coordinate(2.2, 4.4, 6.6, 8.8, 11.0, 13.2, 15.4, 17.6)
        self.assertEqual(TestCoor + TestCoor, ResCoor)
        ResCoor = du.Coordinate(12.2, 13.3, 14.4, 15.5, 16.6, 17.7, 18.8, 19.9)
        self.assertEqual(TestCoor + 11.1, ResCoor)

        # __sub__
        self.assertEqual(TestCoor - TestCoor, du.Coordinate())
        ResCoor = du.Coordinate(0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7)
        self.assertEqual(TestCoor - 1.1, ResCoor)

        # __round__
        TestCoor = du.Coordinate(
            1.111,
            2.222,
            3.333,
            4.444,
            5.555,
            6.666,
            7.777,
            8.888
        )
        ResCoor = du.Coordinate(1.1, 2.2, 3.3, 4.4, 5.6, 6.7, 7.8, 8.9)
        self.assertEqual(round(TestCoor, 1), ResCoor)


    def test_Speed_class(self):
        """test Speed class, used to store acceleration and travel speed 
        settings"""

        # __init__ & __str__
        TestVector = du.SpeedVector(acr=1.2, dcr=3.4, ts=5.6, ors=7.8)
        self.assertEqual(str(TestVector), f"TS: 6   OS: 8   ACR: 1   DCR: 3")
        self.assertEqual(
            str(du.SpeedVector()),
            f"TS: 200   OS: 50   ACR: 50   DCR: 50"
        )

        # __eq__ & __ne__
        self.assertFalse(TestVector == du.SpeedVector())
        self.assertFalse(TestVector == None)
        self.assertTrue(TestVector == TestVector)
        with self.assertRaises(TypeError):
            TestVector == 5
        self.assertTrue(TestVector != du.SpeedVector())
        self.assertTrue(TestVector != None)
        self.assertFalse(TestVector != TestVector)
        with self.assertRaises(TypeError):
            TestVector != 5

        # __mul__ & __rmul__
        TestVector = du.SpeedVector(22, 44, 6, 8)
        ResVector = du.SpeedVector(24, 48, 7, 9)
        self.assertEqual(TestVector * 1.1, ResVector)
        self.assertEqual(TestVector * 1.1, 1.1 * TestVector)


    def test_ToolCommand_class(self):
        """test ToolCommand class, used to store AmConEE data"""

        # __init__ & __str__
        TestTool = du.ToolCommand(1, True, False, True, False, 2)
        self.assertEqual(
            str(TestTool),
            f"TRL: 1   PS: True   LS: False   CUT: False   CL: True   W: 2"
        )
        self.assertEqual(
            str(du.ToolCommand()),
            f"TRL: 0   PS: False   LS: False   CUT: False   CL: False   W: 0",
        )

        # __eq__ & __ne__
        self.assertFalse(TestTool == du.ToolCommand())
        self.assertFalse(TestTool == None)
        self.assertTrue(TestTool == TestTool)
        with self.assertRaises(TypeError):
            TestTool == 5
        self.assertTrue(TestTool != du.ToolCommand())
        self.assertTrue(TestTool != None)
        self.assertFalse(TestTool != TestTool)
        with self.assertRaises(TypeError):
            TestTool != 5


    def test_QEntry_class(self):
        """test QEntry class, build 159-bytes commands"""

        self.maxDiff = 2000

        # __init__ & __str__
        TestCoor1 = du.Coordinate(4, 4, 4, 4, 4, 4, 4, 4)
        TestCoor2 = du.Coordinate(5, 5, 5, 5, 5, 5, 5, 5)
        TestVector = du.SpeedVector(6, 6, 6, 6)
        TestTool = du.ToolCommand(9, 1, 1, 1, 1, 9)
        TestEntry = du.QEntry(
            1, 'A', 'B', TestCoor1, TestCoor2, TestVector, 7, 'C', 8, TestTool
        )
        self.assertEqual(
            str(TestEntry),
            f"ID: 1  MT: A  PT: B \n  || COOR_1: {TestCoor1}"
            f"\n  || COOR_2: {TestCoor2}"
            f"\n  || SV:     {TestVector}   || SBT: 7   SC: C   Z: 8"
            f"\n  || TOOL:   {TestTool}"
            f"\n  || PM/PR:  -1001/1.0   PIN: False",
        )
        self.assertEqual(
            str(du.QEntry()),
            f"ID: 0  MT: L  PT: E \n  || COOR_1: {du.Coordinate()}"
            f"\n  || COOR_2: {du.Coordinate()}"
            f"\n  || SV:     {du.SpeedVector()}   || SBT: 0   SC: V   Z: 10"
            f"\n  || TOOL:   {du.ToolCommand()}"
            f"\n  || PM/PR:  -1001/1.0   PIN: False",
        )

        # __eq__ & __ne__
        self.assertFalse(TestEntry == du.QEntry())
        self.assertFalse(TestEntry == None)
        self.assertTrue(TestEntry == TestEntry)
        with self.assertRaises(TypeError):
            TestEntry == 5
        self.assertTrue(TestEntry != du.QEntry())
        self.assertTrue(TestEntry != None)
        self.assertFalse(TestEntry != TestEntry)
        with self.assertRaises(TypeError):
            TestEntry != 5

        # print_short
        TestEntry.p_mode = 1001
        TestEntry.p_ratio = 0.2
        TestEntry.pinch = True
        self.assertEqual(
            TestEntry.print_short(),
            f"ID: 1 -- A, B -- "
            f"COOR_1: {TestCoor1} -- SV: {TestVector} -- "
            f"PM/PR,PIN:  1001/0.2, True",
        )


    def test_Queue_class(self):
        """test Queue class, organizes QEntry list"""

        self.maxDiff = 2000

        EmptyQueue = du.Queue()
        TestCoor = du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
        TestQueue = du.Queue()
        TestQueue.add(du.QEntry())
        TestQueue.add(du.QEntry(id=10, Coor1=TestCoor))
        TestQueue.add(du.QEntry(id=2, Coor1=TestCoor+1))
        TestStrs = [
            f"{du.QEntry(id=1)}\n",
            f"{du.QEntry(id=2, Coor1=TestCoor+1)}\n",
            f"{du.QEntry(id=3, Coor1=TestCoor)}\n",
        ]

        # __init__ & __str__
        self.assertEqual(str(du.Queue()), 'Queue is empty!')
        self.assertEqual(
            str(TestQueue),
            f"{TestStrs[0]}{TestStrs[1]}{TestStrs[2]}"
        )

        # __getitem__
        self.assertIsNone(EmptyQueue[1])
        self.assertEqual(TestQueue[1], du.QEntry(id=2, Coor1=TestCoor+1))

        # __iter__ & __next__
        i = 0
        for Entry in TestQueue:
            self.assertEqual(f"{Entry}\n", TestStrs[i])
            i += 1

        # __len__
        self.assertEqual(len(TestQueue), 3)

        # __eq__ & __ne__
        self.assertFalse(TestQueue == du.Queue())
        self.assertFalse(TestQueue == None)
        self.assertTrue(TestQueue == TestQueue)
        with self.assertRaises(TypeError):
            TestQueue == 5
        self.assertTrue(TestQueue != du.Queue())
        self.assertTrue(TestQueue != None)
        self.assertFalse(TestQueue != TestQueue)
        with self.assertRaises(TypeError):
            TestQueue != 5

        # last_entry
        self.assertIsNone(EmptyQueue.last_entry())
        self.assertEqual(
            TestQueue.last_entry(),
            du.QEntry(id=3, Coor1=TestCoor),
        )

        # entry_before_id
        self.assertRaises(AttributeError, EmptyQueue.entry_before_id, 1)
        self.assertRaises(AttributeError, TestQueue.entry_before_id, 1)
        self.assertRaises(AttributeError, TestQueue.entry_before_id, 4)
        self.assertEqual(TestQueue.entry_before_id(2), du.QEntry(id=1))

        # display
        self.assertEqual(EmptyQueue.display(), ['Queue is empty!'])
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=1).print_short(),
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor).print_short(),
            ],
        )

        # increment
        TestQueue.increment()
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=4, Coor1=TestCoor).print_short(),
            ],
        )
        TestQueue.increment(6)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=8).print_short(),
                du.QEntry(id=9, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=10, Coor1=TestCoor).print_short(),
            ],
        )
        TestQueue.increment(-6)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=4, Coor1=TestCoor).print_short(),
            ],
        )

        # add
        self.assertEqual(TestQueue.add(du.QEntry(id=-1)), ValueError)
        TestQueue.add(du.QEntry(id=0, Coor1=TestCoor+2))
        TestQueue.add(du.QEntry(id=9, Coor1=TestCoor+3))
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=4, Coor1=TestCoor).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=6, Coor1=TestCoor+3).print_short(),
            ],
        )
        TestQueue.add(du.QEntry(id=1, Coor1=TestCoor+4))
        TestQueue.add(du.QEntry(id=4, Coor1=TestCoor+5))
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=3).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+5).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=6, Coor1=TestCoor).print_short(),
                du.QEntry(id=7, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=8, Coor1=TestCoor+3).print_short(),
            ],
        )

        # id_pos
        self.assertEqual(TestQueue.id_pos(4), 2)
        self.assertIsNone(TestQueue.id_pos(1))
        self.assertIsNone(TestQueue.id_pos(10))
        self.assertIsNone(EmptyQueue.id_pos(10))

        # clear
        unchanged_disp = TestQueue.display()
        TestQueue.clear(all=False, id='')
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="3..4.5")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="9")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="1")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="1..3")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="5..9")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="5..3")
        self.assertEqual(TestQueue.display(), unchanged_disp)
        TestQueue.clear(all=False, id="3,,5")
        self.assertEqual(TestQueue.display(), unchanged_disp)

        TestQueue.clear(all=False, id="4")
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=3).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=5, Coor1=TestCoor).print_short(),
                du.QEntry(id=6, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=7, Coor1=TestCoor+3).print_short(),
            ],
        )
        TestQueue.clear(all=False, id="3..5")
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+3).print_short(),
            ],
        )
        TestQueue.clear()
        self.assertEqual(TestQueue.display(), ['Queue is empty!'])

        # pop_first_item
        self.assertIsInstance(EmptyQueue.pop_first_item(), BufferError)
        TestQueue.add(du.QEntry())
        TestQueue.add(du.QEntry(id=3, Coor1=TestCoor))
        self.assertEqual(TestQueue.pop_first_item(), du.QEntry(id=1))
        self.assertEqual(
            TestQueue.display(),
            [du.QEntry(id=2, Coor1=TestCoor).print_short()],
        )

        # add_queue
        AddQueue = du.Queue()
        AddQueue.add(du.QEntry(id=1, Coor1=TestCoor+1), thread_call=True)
        AddQueue.add(du.QEntry(id=2, Coor1=TestCoor+2), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor).print_short(),
            ],
        )
        AddQueue.clear()
        AddQueue.add(du.QEntry(id=4, Coor1=TestCoor+4), thread_call=True)
        AddQueue.add(du.QEntry(id=5, Coor1=TestCoor+5), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor+2).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+5).print_short(),
                du.QEntry(id=6, Coor1=TestCoor).print_short(),
            ],
        )
        TestQueue.clear(all=False, id='3..5')
        AddQueue.clear()
        AddQueue.add(du.QEntry(id=4, Coor1=TestCoor+4), thread_call=True)
        AddQueue.add(du.QEntry(id=5, Coor1=TestCoor+5), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+5).print_short(),
            ],
        )
        TestQueue.clear(all=False, id='4..5')
        AddQueue.clear()
        AddQueue.add(du.QEntry(id=0, Coor1=TestCoor+4), thread_call=True)
        AddQueue.add(du.QEntry(id=1, Coor1=TestCoor+5), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+5).print_short(),
            ],
        )
        TestQueue.clear(all=False, id='4..5')
        AddQueue.clear()
        AddQueue.add(du.QEntry(id=10, Coor1=TestCoor+4), thread_call=True)
        AddQueue.add(du.QEntry(id=11, Coor1=TestCoor+5), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=2, Coor1=TestCoor+1).print_short(),
                du.QEntry(id=3, Coor1=TestCoor).print_short(),
                du.QEntry(id=4, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=5, Coor1=TestCoor+5).print_short(),
            ],
        )
        TestQueue.clear(all=True)
        AddQueue.clear()
        du.SC_curr_comm_id = 8
        AddQueue.add(du.QEntry(id=10, Coor1=TestCoor+4), thread_call=True)
        AddQueue.add(du.QEntry(id=11, Coor1=TestCoor+5), thread_call=True)
        TestQueue.add_queue(AddQueue)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=8, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=9, Coor1=TestCoor+5).print_short(),
            ],
        )
        self.assertIsInstance(TestQueue.add_queue(du.Queue()), AttributeError)
        self.assertIsInstance(TestQueue.add_queue(None), ValueError)

        # append
        TestEntry = du.QEntry(id=2, Coor1=TestCoor+6)
        TestQueue.append(TestEntry)
        self.assertEqual(
            TestQueue.display(),
            [
                du.QEntry(id=8, Coor1=TestCoor+4).print_short(),
                du.QEntry(id=9, Coor1=TestCoor+5).print_short(),
                du.QEntry(id=2, Coor1=TestCoor+6).print_short(),
            ],
        )

        du.SC_curr_comm_id = 1


    def test_RoboTelemetry_class(self):
        """test RoboTelemetry class, used to store 36 TCP-response from robot"""

        # __init__ & __str__
        TestCoor = du.Coordinate(3, 3, 3, 3, 3, 3, 3, 3)
        TestTelem = du.RoboTelemetry(t_speed=1.1, id=2, Coor=TestCoor)
        self.assertEqual(
            str(TestTelem),
            f"ID: 2   COOR: X: 3.0   Y: 3.0   Z: 3.0   RX: 3.0   RY: 3.0   "
            f"RZ: 3.0   Q: 3.0   EXT: 3.0   TOOL_SPEED: 1.1",
        )
        self.assertEqual(
            str(du.RoboTelemetry()),
            f"ID: -1   COOR: X: 0.0   Y: 0.0   Z: 0.0   RX: 0.0   RY: 0.0   "
            f"RZ: 0.0   Q: 0.0   EXT: 0.0   TOOL_SPEED: 0.0",
        )

        # __eq__ & __ne__
        self.assertFalse(TestTelem == du.RoboTelemetry())
        self.assertFalse(TestTelem == None)
        self.assertTrue(TestTelem == TestTelem)
        with self.assertRaises(TypeError):
            TestTelem == 5
        self.assertTrue(TestTelem != du.RoboTelemetry())
        self.assertTrue(TestTelem != None)
        self.assertFalse(TestTelem != TestTelem)
        with self.assertRaises(TypeError):
            TestTelem != 5

        # __round__ (and automatic ID conversion to int)
        RoundCoor = du.Coordinate(
            3.333, 3.333, 3.333, 3.333, 3.333, 3.333, 3.333, 3.333
        )
        RoundTelem = du.RoboTelemetry(t_speed=1.111, id=2.222, Coor=RoundCoor)
        RoundedCoor = du.Coordinate(3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3, 3.3)
        self.assertEqual(
            round(RoundTelem, 1),
            du.RoboTelemetry(t_speed=1.1, id=2, Coor=RoundedCoor),
        )


    def test_PumpTelemetry_class(self):
        """test RoboTelemetry class, used to store 36 TCP-response from robot"""

        # __init__ & __str__
        TestTelem = du.PumpTelemetry(freq=1.1, volt=2.2, amps=3.3, torq=4.4)
        self.assertEqual(
            str(TestTelem),
            f"FREQ: 1.1   VOLT: 2.2   AMPS: 3.3   TORQ: 4.4",
        )
        self.assertEqual(
            str(du.PumpTelemetry()),
            f"FREQ: 0.0   VOLT: 0.0   AMPS: 0.0   TORQ: 0.0",
        )

        # __eq__ & __ne__
        self.assertFalse(TestTelem == du.PumpTelemetry())
        self.assertFalse(TestTelem == None)
        self.assertTrue(TestTelem == TestTelem)
        with self.assertRaises(TypeError):
            TestTelem == 5
        self.assertTrue(TestTelem != du.PumpTelemetry())
        self.assertTrue(TestTelem != None)
        self.assertFalse(TestTelem != TestTelem)
        with self.assertRaises(TypeError):
            TestTelem != 5

        # __round__
        RoundTelem = du.PumpTelemetry(
            freq=1.111, volt=2.222, amps=3.333, torq=4.444
        )
        self.assertEqual(
            round(RoundTelem, 1),
            du.PumpTelemetry(freq=1.1, volt=2.2, amps=3.3, torq=4.4),
        )


    def test_TSData_class(self):
        """test TSData class, a decriptor used in DataBlock class"""

        # descriptor needs to be a metaclass to have __set__ invoked
        # on expressions like 'Class.attribute = 2', where 'attribute'
        # has to be an instance of the descriptor class
        # 'Descriptor() = 2' will just overwrite
        class TestClass():
            ts_val = du.TSData()
            def __init__(self, val):
                self.ts_val = du.TSData(val)
                self.valid_time = timedelta(seconds=60)

        # __init__, __str__ & __get__ (valid case)
        TestC = TestClass(4.5)
        self.assertEqual(TestC.ts_val, 4.5)
        self.assertEqual(str(TestC.ts_val), '4.5')

        # __set__
        TestC.ts_val = 5
        self.assertEqual(TestC.ts_val, 5.0)
        TestC.ts_val = du.TSData(4.3)
        self.assertEqual(TestC.ts_val, 4.3)
        TestC.ts_val = 6.7
        self.assertEqual(TestC.ts_val, 6.7)
        with self.assertRaises(TypeError):
            TestC.ts_val = 'A'

        # __eq__ & __ne__
        self.assertFalse(TestC.ts_val == du.TSData())
        self.assertFalse(TestC.ts_val == None)
        self.assertFalse(TestC.ts_val == 5)
        self.assertTrue(TestC.ts_val == du.TSData(6.7))
        self.assertTrue(TestC.ts_val == TestC.ts_val)
        self.assertTrue(TestC.ts_val == 6.7)
        self.assertTrue(TestC.ts_val != du.TSData())
        self.assertTrue(TestC.ts_val != None)
        self.assertTrue(TestC.ts_val != 5)
        self.assertFalse(TestC.ts_val != TestC.ts_val)
        self.assertFalse(TestC.ts_val != 6.7)

        # change valid_time & __get__ (invalid case)
        TestC.ts_val = 8.9
        TestC.valid_time = timedelta(seconds=1) # [s]
        self.assertEqual(TestC.valid_time, timedelta(seconds=1))
        self.assertEqual(TestC.ts_val, 8.9)
        time.sleep(2)
        self.assertIsNone(TestC.ts_val)


    def test_DataBlock_class(self):
        """test DataBlock class, used to sort data for InfluxDB"""
        self.maxDiff = 2000

        # __init__ & __str__
        TestCoor = du.Coordinate(14.14, 15, 16, 17, 18, 19, 20, 21)
        TestDqB = du.DaqBlock(
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
            Robo = du.RoboTelemetry(12.12, 13, TestCoor),
            Pump1 = du.PumpTelemetry(23, 24, 25, 26),
            Pump2 = du.PumpTelemetry(27, 28, 29, 30),
            phc_aircon = 31.31,
            phc_fdist = 32.32,
            phc_edist = 33.33,
            )
        self.assertEqual(
            str(TestDqB),
            f"Amb. temp.: 1.1    Amb. humid.: 2.2    RB temp.: 3.3    "
            f"MSP temp.: 4.4    MSP press.: 5.5    APS freq.: 6.6    "
            f"APS amp.: 7.7    IMP temp.: 8.8    IMP press.: 9.9    "
            f"IMP freq.: 10.1    IMP amp.: 11.11    "
            f"ROB: {du.RoboTelemetry(12.12, 13, TestCoor)}    "
            f"PUMP1: {du.PumpTelemetry(23, 24, 25, 26)}    "
            f"PUMP2: {du.PumpTelemetry(27, 28, 29, 30)}    "
            f"PHC air cont.: 31.31    PHC front dist.: 32.32    "
            f"PHC end dist.: 33.33",
        )
        self.assertEqual(
            str(du.DaqBlock()),
            f"Amb. temp.: 0.0    Amb. humid.: 0.0    RB temp.: 0.0    "
            f"MSP temp.: 0.0    MSP press.: 0.0    APS freq.: 0.0    "
            f"APS amp.: 0.0    IMP temp.: 0.0    IMP press.: 0.0    "
            f"IMP freq.: 0.0    IMP amp.: 0.0    ROB: {du.RoboTelemetry()}    "
            f"PUMP1: {du.PumpTelemetry()}    PUMP2: {du.PumpTelemetry()}    "
            f"PHC air cont.: 0.0    PHC front dist.: 0.0    "
            f"PHC end dist.: 0.0",
        )

        # __eq__ & __ne__
        self.assertFalse(TestDqB == du.DaqBlock())
        self.assertFalse(TestDqB == None)
        self.assertTrue(TestDqB == TestDqB)
        with self.assertRaises(TypeError):
            TestDqB == 5
        self.assertTrue(TestDqB != du.DaqBlock())
        self.assertTrue(TestDqB != None)
        self.assertFalse(TestDqB != TestDqB)
        with self.assertRaises(TypeError):
            TestDqB != 5
        
        # store
        invalid_time = du.DEF_STT_VALID_TIME + 1
        self.assertIsNone(TestDqB.store((1, invalid_time), '', ''))
        with self.assertRaises(KeyError):
            TestDqB.store((0, 0), 'wrong', 'wrong')
        with self.assertRaises(KeyError):
            TestDqB.store((0, 0), 'amb', 'wrong')
        # just try one overwrite for example
        TestDqB.store((-1.1, 0), 'amb', 'temp')
        self.assertEqual(TestDqB.amb_temp, -1.1)

        # valid_time setter
        TestDqB.valid_time = 6.54
        self.assertEqual(TestDqB.valid_time, timedelta(seconds=7))


    def test_TCPIP_class(self):
        """test TCPIP class, handles connection data und functions"""

        # __init__ & __str__
        TestTCPIP = du.TCPIP()
        InitTestTCPIP = du.TCPIP(
            ip="1.1.1.1",
            port=2222,
            c_tout=3.3,
            rw_tout=4.4,
            r_bl=5.5,
            w_bl=6.6
        )
        self.assertEqual(
            str(InitTestTCPIP),
            f"IP: 1.1.1.1   PORT: 2222   C_TOUT: 3.3   RW_TOUT: 4.4   "
            f"R_BL: 5   W_BL: 6",
        )
        self.assertEqual(
            str(TestTCPIP),
            f"IP:    PORT: 0   C_TOUT: 1.0   RW_TOUT: 1.0   "
            f"R_BL: 0   W_BL: 0",
        )
        InitTestTCPIP.close(end=True)

        # setParams
        TestTCPIP.set_params({
            'ip': "1.1.1.1",
            'port': 2222,
            'c_tout': 0.003,
            'rw_tout': 0.004,
            'r_bl': 5.5,
            'w_bl': 6.6,
        })
        self.assertEqual(
            str(TestTCPIP),
            f"IP: 1.1.1.1   PORT: 2222   C_TOUT: 0.003   RW_TOUT: 0.004   "
            f"R_BL: 5   W_BL: 6",
        )
        TestTCPIP.connected = True
        self.assertRaises(PermissionError, TestTCPIP.set_params, None)
        TestTCPIP.connected = False

        # connect
        ans0 = TestTCPIP.connect()
        self.assertIsInstance(ans0, (TimeoutError, OSError))
        TestTCPIP.port = "ABC"
        self.assertRaises(ConnectionError, TestTCPIP.connect)

        # send
        ans0, ans1 = TestTCPIP.send([True,True])
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ConnectionError)
        TestTCPIP.connected = True
        ans0, ans1 = TestTCPIP.send([True, True])
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ValueError)

        # receive
        ans0, ans1 = TestTCPIP.receive()
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, TimeoutError)

        # close
        TestTCPIP.close(end=True)
        self.assertFalse(TestTCPIP.connected)


    def test_RobConnection_class(self):
        """test RobConnection class, handles connection data und functions"""

        # send
        TestRobCon = du.RoboConnection()
    
        ans0, ans1 = TestRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ConnectionError)

        TestRobCon.connected = True
        ans0, ans1 = TestRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, ValueError)

        TestRobCon.w_bl = du.DEF_ROB_TCP['w_bl']
        ans0, ans1 = TestRobCon.send(du.QEntry(id=1))
        self.assertFalse(ans0)
        self.assertIsInstance(ans1, OSError)

        # received (to do)

        TestRobCon.close(end=True)


#################################  MAIN  #####################################

if __name__ == "__main__":
    unittest.main()
