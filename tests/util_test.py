
import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.PRINT_data_utilities as UTIL



class UTIL_test(unittest.TestCase):


    def test_CoorClass (self):
        """ test Coor class, used to store positional data from robot """
        
        # __init__ & __str__
        self.assertEqual( str( UTIL.Coor( X= 1.2, Y= 3.4, Z= 5.6
                                         ,X_ori= 7.8, Y_ori= 9.11, Z_ori= 22.33
                                         ,Q= 44.55, EXT= 66.77) )
                         ,f"X: {1.2}   Y: {3.4}   Z: {5.6}   " \
                          f"Rx: {7.8}   Ry: {9.11}   Rz: {22.33}   " \
                          f"Q: {44.55}   EXT: {66.77}")
        self.assertEqual( str( UTIL.Coor() )
                         ,f"X: {0.0}   Y: {0.0}   Z: {0.0}   " \
                          f"Rx: {0.0}   Ry: {0.0}   Rz: {0.0}   " \
                          f"Q: {0.0}   EXT: {0.0}")
        
        # __add__
        self.assertEqual( UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                          + UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                          ,UTIL.Coor( 2.2, 4.4, 6.6, 8.8, 11.0, 13.2, 15.4, 17.6) )                          
        self.assertEqual( UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                          + 11.1
                          ,UTIL.Coor( 12.2, 13.3, 14.4, 15.5, 16.6, 17.7, 18.8, 19.9) )
        
        # __sub__
        self.assertEqual( UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                          - UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                         ,UTIL.Coor() )
        self.assertEqual( UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7, 8.8)
                          - 1.1
                         ,UTIL.Coor( 0.0, 1.1, 2.2, 3.3, 4.4, 5.5, 6.6, 7.7) )
        
        #__round__
        self.assertEqual( round(UTIL.Coor( 1.111, 2.222, 3.333, 4.444, 5.555, 6.666, 7.777, 8.888), 1)
                         ,UTIL.Coor( 1.1, 2.2, 3.3, 4.4, 5.6, 6.7, 7.8, 8.9) )
        

    def test_SpeedClass(self):
        """ test Speed class, used to store acceleration and travel speed settings """
        
        # __init__ & __str__
        self.assertEqual( str( UTIL.Speed( ACR= 1.2, DCR= 3.4, TS= 5.6, OS= 7.8) )
                         ,f"TS: {6}   OS: {8}   ACR: {1}   DCR: {3}")
        self.assertEqual( str( UTIL.Speed() )
                         ,f"TS: {200}   OS: {50}   ACR: {50}   DCR: {50}")
        
        #__mul__ & __rmul__
        self.assertEqual( UTIL.Speed( 22, 44, 6, 8) * 1.1
                         ,UTIL.Speed( 24, 48, 7, 9))
        self.assertEqual( UTIL.Speed( 22, 44, 6, 8) * 1.1
                         ,1.1 * UTIL.Speed( 22, 44, 6, 8))
        


    def test_ToolCommandClass(self):
        """ test ToolCommand class, used to store AmConEE data """

        # __init__ & __str__
        self.assertEqual( str( UTIL.ToolCommand( M1_ID= 1, M1_STEPS= 2, M2_ID= 3, M2_STEPS= 4
                                                ,M3_ID= 5, M3_STEPS= 6, PNMTC_CLAMP_ID= 7
                                                ,PNMTC_CLAMP_YN= True ,KNIFE_ID= 8
                                                ,KNIFE_YN= False, M4_ID= 9, M4_STEPS= False
                                                ,PNMTC_FIBER_ID= 10, PNMTC_FIBER_YN= True
                                                ,TIME_ID= 11, TIME_TIME= 12) )
                         ,f"M1: {1}, {2}   M2: {3}, {4}   M3: {5}, {6}   "\
                          f"P_C: {7}, {True}   KN: {8}, {False}   "\
                          f"M4: {9}, {False}   P_F: {10}, {True}   TIME: {11}, {12}")

        self.assertEqual( str( UTIL.ToolCommand() )
                         ,f"M1: {0}, {0}   M2: {0}, {0}   M3: {0}, {0}   "\
                          f"P_C: {0}, {False}   KN: {0}, {False}   "\
                          f"M4: {0}, {False}   P_F: {0}, {False}   TIME: {0}, {0}")
        


    def test_QEntryClass (self):
        """ test QEntry class, build 159-bytes commands """

        self.maxDiff = 2000

        # __init__ & __str__
        self.assertEqual( str( UTIL.QEntry( ID= 1, MT= 2, PT= 3, COOR_1= UTIL.Coor(4,4,4,4,4,4,4,4)
                                           ,COOR_2= UTIL.Coor(5,5,5,5,5,5,5,5), SV= UTIL.Speed(6,6,6,6)
                                           ,SBT= 7 ,SC= "A" ,Z= 8
                                           ,TOOL= UTIL.ToolCommand(9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9)) )
                         ,f"ID: {1}  MT: {2}  PT: {3} \t|| COOR_1: {UTIL.Coor(4,4,4,4,4,4,4,4)}"\
                          f"\n\t\t|| COOR_2: {UTIL.Coor(5,5,5,5,5,5,5,5)}"\
                          f"\n\t\t|| SV:     {UTIL.Speed(6,6,6,6)} \t|| SBT: {7}   SC: A   Z: {8}"\
                          f"\n\t\t|| TOOL:   {UTIL.ToolCommand(9,9,9,9,9,9,9,9,9,9,9,9,9,9,9,9)}")

        self.assertEqual( str( UTIL.QEntry() )
                         ,f"ID: {0}  MT: L  PT: E \t|| COOR_1: {UTIL.Coor()}"\
                          f"\n\t\t|| COOR_2: {UTIL.Coor()}"\
                          f"\n\t\t|| SV:     {UTIL.Speed()} \t|| SBT: {0}   SC: V   Z: {10}"\
                          f"\n\t\t|| TOOL:   {UTIL.ToolCommand()}")
        


    def test_QueueClass (self):
        """ test Queue class, organizes QEntry list """

        self.maxDiff = 2000

        emptyQueue = UTIL.Queue()
        testQueue  = UTIL.Queue()
        testQueue.add( UTIL.QEntry() )
        testQueue.add( UTIL.QEntry(ID= 3, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)) )

        # __init__ & __str__
        self.assertEqual( str( testQueue )
                         ,f"Element 1: { UTIL.QEntry(ID= 1) }\n"\
                          f"Element 2: { UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3))}\n")

        self.assertEqual( str( UTIL.Queue() )
                         ,f"Queue is empty!")
        
        # __getitem__
        self.assertIsNone( emptyQueue[1] )
        self.assertEqual ( testQueue[1]
                          ,UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)) )
        
        # __len__
        self.assertEqual( len(testQueue), 2)
        
        # __eq__
        self.assertFalse( testQueue == UTIL.Queue() )
        self.assertTrue ( testQueue == testQueue )
        
        # lastEntry
        self.assertIsNone( emptyQueue.lastEntry() )
        self.assertEqual ( testQueue.lastEntry()
                          ,UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)) )
        
        # entryBeforeID
        self.assertIsNone( emptyQueue.entryBeforeID(1) )
        self.assertIsNone( testQueue.entryBeforeID(1) )
        self.assertIsNone( testQueue.entryBeforeID(3) )
        self.assertEqual ( testQueue.entryBeforeID(2)
                          ,UTIL.QEntry(ID= 1) )
        
        # display
        self.assertEqual( testQueue.display() ,
                          [ str( UTIL.QEntry(ID= 1) )
                           ,str( UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3))) ] )

        self.assertEqual( emptyQueue.display()
                         ,["Queue is empty!"])
        
        # increment
        testQueue.increment()
        self.assertEqual( testQueue.display() ,
                          [ str( UTIL.QEntry(ID= 2) )
                           ,str( UTIL.QEntry(ID= 3, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3))) ] )
        
        # add
        self.assertEqual( testQueue.add( UTIL.QEntry( ID= -1 ) )
                         ,ValueError )
        
        testQueue.add( UTIL.QEntry( ID= 0, COOR_1= UTIL.Coor(4,4,4,4,4,4,4,4)) )
        testQueue.add( UTIL.QEntry( ID= 9, COOR_1= UTIL.Coor(5,5,5,5,5,5,5,5)) )
        self.assertEqual( testQueue.display() 
                         ,[ str( UTIL.QEntry(ID= 2) )
                           ,str( UTIL.QEntry(ID= 3, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)))
                           ,str( UTIL.QEntry(ID= 4, COOR_1= UTIL.Coor(4,4,4,4,4,4,4,4)))
                           ,str( UTIL.QEntry(ID= 5, COOR_1= UTIL.Coor(5,5,5,5,5,5,5,5))) ] )
        
        testQueue.add( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(1,1,1,1,1,1,1,1)))
        testQueue.add( UTIL.QEntry( ID= 4, COOR_1= UTIL.Coor(6,6,6,6,6,6,6,6)))
        self.assertEqual( testQueue.display() ,
                          [ str( UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(1,1,1,1,1,1,1,1)))
                           ,str( UTIL.QEntry(ID= 3) )
                           ,str( UTIL.QEntry(ID= 4, COOR_1= UTIL.Coor(6,6,6,6,6,6,6,6)))
                           ,str( UTIL.QEntry(ID= 5, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)))
                           ,str( UTIL.QEntry(ID= 6, COOR_1= UTIL.Coor(4,4,4,4,4,4,4,4)))
                           ,str( UTIL.QEntry(ID= 7, COOR_1= UTIL.Coor(5,5,5,5,5,5,5,5))) ] )
        
        # clear
        self.assertEqual( testQueue.clear(all= False, ID= ''),      ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '3..4.5'),ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '8'),     ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '1'),     ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '1..3'),  ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '5..8'),  ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '5..3'),  ValueError )
        self.assertEqual( testQueue.clear(all= False, ID= '3,,5'),  ValueError )

        testQueue.clear(all= False, ID = '4')
        self.assertEqual( testQueue.display()
                         ,[ str( UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(1,1,1,1,1,1,1,1)))
                           ,str( UTIL.QEntry(ID= 3) )
                           ,str( UTIL.QEntry(ID= 4, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)))
                           ,str( UTIL.QEntry(ID= 5, COOR_1= UTIL.Coor(4,4,4,4,4,4,4,4)))
                           ,str( UTIL.QEntry(ID= 6, COOR_1= UTIL.Coor(5,5,5,5,5,5,5,5))) ] )
        
        testQueue.clear(all= False, ID = '3..5')
        self.assertEqual( testQueue.display()
                         ,[ str( UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(1,1,1,1,1,1,1,1)))
                           ,str( UTIL.QEntry(ID= 3, COOR_1= UTIL.Coor(5,5,5,5,5,5,5,5))) ] )
        
        testQueue.clear()
        self.assertEqual( testQueue.display()
                         ,['Queue is empty!'] )
        
        # popFirstItem
        self.assertEqual( emptyQueue.popFirstItem(), IndexError )

        testQueue.add( UTIL.QEntry() )
        testQueue.add( UTIL.QEntry(ID= 3, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3)) )
        self.assertEqual( testQueue.popFirstItem()
                         ,UTIL.QEntry(ID= 1) )
        self.assertEqual( testQueue.display()
                         ,[ str( UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(3,3,3,3,3,3,3,3))) ] )
        


    def test_RoboTelemetryClass (self):
        """ test RoboTelemetry class, used to store 36 TCP-response from robot """
        
        # __init__ & __str__
        self.assertEqual( str( UTIL.RoboTelemetry( TOOL_SPEED= 1.1, ID= 2
                                                  ,POS= UTIL.Coor(3,3,3,3,3,3,3,3)) )
                         ,f"ID: {2}   X: {3.0}   Y: {3.0}   Z: {3.0}   Rx: {3.0}   Ry: {3.0}   Rz: {3.0}   "\
                          f"EXT:   {3.0}   TOOL_SPEED: {1.1}" )
        self.assertEqual( str( UTIL.RoboTelemetry() )
                         ,f"ID: {-1}   X: {0.0}   Y: {0.0}   Z: {0.0}   Rx: {0.0}   Ry: {0.0}   Rz: {0.0}   "\
                          f"EXT:   {0.0}   TOOL_SPEED: {0.0}" )
        
        #__round__
        self.assertEqual( round( UTIL.RoboTelemetry( TOOL_SPEED= 1.111, ID= 2.222
                                                    ,POS= UTIL.Coor(3.333,3.333,3.333,3.333,3.333,3.333,3.333,3.333))
                                ,1)
                         ,UTIL.RoboTelemetry( TOOL_SPEED= 1.1, ID= 2
                                             ,POS= UTIL.Coor(3.3,3.3,3.3,3.3,3.3,3.3,3.3,3.3)) )
        


    def test_PumpTelemetryClass (self):
        """ test RoboTelemetry class, used to store 36 TCP-response from robot """
        
        # __init__ & __str__
        self.assertEqual( str( UTIL.PumpTelemetry( FREQ= 1.1, VOLT= 2.2, AMPS= 3.3, TORQ= 4.4) )
                         ,f"FREQ: {1.1}   VOLT: {2.2}   AMPS: {3.3}   TORQ: {4.4}" )
        self.assertEqual( str( UTIL.PumpTelemetry() )
                         ,f"FREQ: {0.0}   VOLT: {0.0}   AMPS: {0.0}   TORQ: {0.0}" )
        
        #__round__
        self.assertEqual( round( UTIL.PumpTelemetry( FREQ= 1.111, VOLT= 2.222, AMPS= 3.333, TORQ= 4.444)
                                ,1 )
                         ,UTIL.PumpTelemetry( FREQ= 1.1, VOLT= 2.2, AMPS= 3.3, TORQ= 4.4))



    def test_DataBlockClass (self):
        """ test DataBlock class, used to sort data for InfluxDB """

        # __init__ & __str__
        self.assertEqual( str( UTIL.DataBlock( ambTemp= 1.1, ambHum= 2.2, delivPumpTemp= 3.3
                                              ,robBaseTemp= 4.4, kPumpTemp= 5.5, delivPumpPress= 6.6
                                              ,kPumpPress= 7.7, PUMP1= UTIL.PumpTelemetry(8,9,10,11)
                                              ,PUMP2= UTIL.PumpTelemetry(12,13,14,15), admPumpFreq= 16.16
                                              ,admPumpAmps= 17.17, kPumpFreq= 18.18, kPumpAmps= 19.19
                                              ,id= 20.2, toolSpeed= 21.21, POS= UTIL.Coor(22,23,24,25,26,27,28,29)
                                              ,porosAnalysis= 30.30, distanceFront= 31.31, distanceEnd= 32.32) )
                         ,f"ambTemp: {1.1}    ambHum: {2.2}    delivPumpTemp: {3.3}    robBaseTemp: {4.4}    "\
                          f"kPumpTemp: {5.5}    delivPumpPress: {6.6}    kPumpPress: {7.7}    "\
                          f"PUMP1: {UTIL.PumpTelemetry(8,9,10,11)}    PUMP2: {UTIL.PumpTelemetry(12,13,14,15)}    "\
                          f"admPumpFreq: {16.16}    admPumpAmps: {17.17}    kPumpFreq: {18.18}    "\
                          f"kPumpAmps: {19.19}    id: {20}    toolspeed: {21.21}    "\
                          f"POS: {UTIL.Coor(22,23,24,25,26,27,28,29)}    porosAnalysis: {30.30}    "\
                          f"distanceFront: {31.31}    distanceEnd: {32.32}")
        
        self.assertEqual( str( UTIL.DataBlock() )
                         ,f"ambTemp: {0.0}    ambHum: {0.0}    delivPumpTemp: {0.0}    robBaseTemp: {0.0}    "\
                          f"kPumpTemp: {0.0}    delivPumpPress: {0.0}    kPumpPress: {0.0}    "\
                          f"PUMP1: {UTIL.PumpTelemetry()}    PUMP2: {UTIL.PumpTelemetry()}    "\
                          f"admPumpFreq: {0.0}    admPumpAmps: {0.0}    kPumpFreq: {0.0}    "\
                          f"kPumpAmps: {0.0}    id: {0}    toolspeed: {0.0}    "\
                          f"POS: {UTIL.Coor()}    porosAnalysis: {0.0}    "\
                          f"distanceFront: {0.0}    distanceEnd: {0.0}")



    def test_TCPIPClass (self):
        """ test TCPIP class, handles connection data und functions """

        testTCPIP = UTIL.TCPIP()

        # __init__ & __str__
        self.assertEqual( str( UTIL.TCPIP( IP= '1.1.1.1', PORT= 2222, C_TOUT= 3.3, RW_TOUT= 4.4
                                          ,R_BL= 5.5, W_BL= 6.6) )
                         ,f"IP: 1.1.1.1   PORT: {2222}   C_TOUT: {3.3}   RW_TOUT: {4.4}   "\
                          f"R_BL: {5}   W_BL: {6}" )
        
        self.assertEqual( str( testTCPIP )
                         ,f"IP:    PORT: {0}   C_TOUT: {1.0}   RW_TOUT: {1.0}   "\
                          f"R_BL: {0}   W_BL: {0}" )
        
        # setParams
        testTCPIP.setParams( { 'IP':'1.1.1.1', 'PORT': '2222', 'CTOUT': 3.3
                              ,'RWTOUT': 4.4, 'R_BL': 5.5, 'W_BL': 6.6} )
        self.assertEqual( str( testTCPIP) 
                         ,f"IP: 1.1.1.1   PORT: {2222}   C_TOUT: {3.3}   RW_TOUT: {4.4}   "\
                          f"R_BL: {5}   W_BL: {6}" )
        
        testTCPIP.connected = 1
        self.assertRaises( expected_exception= PermissionError
                          ,callable= testTCPIP.setParams( None ))





if __name__ == '__main__':
    unittest.main()