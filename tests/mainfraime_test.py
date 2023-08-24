
import os
import sys
import unittest
import pathlib as pl

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread
from datetime import datetime

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.PRINT_data_utilities as UTIL
import libs.PRINT_win_mainframe as MF
from libs.PRINT_win_daq import DAQWindow as DAQ
from libs.PRINT_threads import RoboCommWorker, PumpCommWorker



class Mainfraime_test(unittest.TestCase):

    def assertIsFile (self, path):
        """ program file exist error """

        if not pl.Path(path).resolve().is_file():
            raise AssertionError(f"No such file: {path}")



    def test_init (self):
        global testFrame
        global logpath

        # general values
        self.assertEqual     (testFrame.logpath,    logpath)
        self.assertEqual     (testFrame.pump1Conn,  False)
        self.assertEqual     (testFrame.pump2Conn,  False)
        self.assertIsInstance(testFrame.DAQ,        DAQ)

        # logfile
        self.assertIsFile   (logpath)
        logfileCheck        = open(logpath,'r')
        logfileCheckTxt     = logfileCheck.read()
        logfileCheck.close()
        self.assertIn('setup finished.',logfileCheckTxt)

        # defaults test with 'applySettings'
        
        # threads
        self.assertIsInstance( testFrame.roboCommThread, QThread )
        self.assertIsInstance( testFrame.pumpCommThread, QThread )
        self.assertIsInstance( testFrame.roboCommWorker, RoboCommWorker )
        self.assertIsInstance( testFrame.pumpCommWorker, PumpCommWorker )



    def test_posUpdate (self):
        """ tests labelUpdate_onReceive as well """
        global testFrame

        # primary function
        # check first run
        self.assertEqual( UTIL.DC_curr_zero, UTIL.Coor() )
        testFrame.posUpdate( rawDataString= 'ABC'
                            ,pos= UTIL.Coor(1,2,3,4,5,6,7,8.8)
                            ,toolSpeed= 0
                            ,robo_comm_id=0)
        # check first loop switch, Q is not set by posUpdate
        self.assertEqual( UTIL.DC_curr_zero, UTIL.Coor(1,2,3,4,5,6,0,8.8) )

        # check loop run
        UTIL.SC_curr_comm_id = 15
        UTIL.DC_curr_zero    = UTIL.Coor(0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1)
        testFrame.posUpdate( rawDataString= 'ABC'
                            ,pos= UTIL.Coor(1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8)
                            ,toolSpeed= 9.9
                            ,robo_comm_id= 10)
        
        self.assertEqual( UTIL.ROB_pos, UTIL.Coor(1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8) )
        self.assertEqual( UTIL.STT_datablock.POS, UTIL.Coor(1.0,2.1,3.2,4.3,5.4,6.5,7.6,8.7) )
        self.assertEqual( UTIL.ROB_toolSpeed, 9.9 )
        self.assertEqual( UTIL.STT_datablock.toolSpeed, 9.9 )
        self.assertEqual( UTIL.ROB_comm_id, 10 )
        self.assertEqual( UTIL.STT_datablock.id, 10 )

        # labelUpdate_onReceive (called from posUpdate)
        self.assertEqual( testFrame.TCP_ROB_disp_readBuffer.text(), 'ABC' )
        self.assertEqual( testFrame.SCTRL_disp_buffComms.text(),    '5' )
        self.assertEqual( testFrame.SCTRL_disp_robCommID.text(),    '10' )
        self.assertEqual( testFrame.SCTRL_disp_progCommID.text(),   '15' )
        self.assertEqual( testFrame.SCTRL_disp_elemInQ.text(),      '0' )

        self.assertEqual( testFrame.DC_disp_x.text(),               '1.0' )
        self.assertEqual( testFrame.DC_disp_y.text(),               '2.1' )
        self.assertEqual( testFrame.DC_disp_z.text(),               '3.2' )
        self.assertEqual( testFrame.DC_disp_ext.text(),             '8.7' )
        
        self.assertEqual( testFrame.NC_disp_x.text(),               '1.1' )
        self.assertEqual( testFrame.NC_disp_y.text(),               '2.2' )
        self.assertEqual( testFrame.NC_disp_z.text(),               '3.3' )
        self.assertEqual( testFrame.NC_disp_xOrient.text(),         '4.4' )
        self.assertEqual( testFrame.NC_disp_yOrient.text(),         '5.5' )
        self.assertEqual( testFrame.NC_disp_zOrient.text(),         '6.6' )
        self.assertEqual( testFrame.NC_disp_ext.text(),             '8.8' )
        
        self.assertEqual( testFrame.TERM_disp_tcpSpeed.text(),      '9.9' )
        self.assertEqual( testFrame.TERM_disp_robCommID.text(),     '10' )
        self.assertEqual( testFrame.TERM_disp_progCommID.text(),    '15' )

        UTIL.DC_curr_zero = UTIL.Coor()
        UTIL.ROB_pos = UTIL.Coor()
        UTIL.SC_curr_comm_id = 1
        UTIL.ROB_toolSpeed = 0
        UTIL.ROB_comm_id = 0
        UTIL.SC_queue.clear()



    def test_pump1Send (self):
        global testFrame

        testFrame.pump1Send(newSpeed= 1.1, command= 'ABC', ans= 'DEF')

        self.assertEqual( UTIL.PUMP1_speed, 1.1)
        self.assertEqual( testFrame.TCP_PUMP1_disp_writeBuffer.text(),  'ABC')
        self.assertEqual( testFrame.TCP_PUMP1_disp_bytesWritten.text(), '3')
        self.assertEqual( testFrame.TCP_PUMP1_disp_readBuffer.text(),   'DEF')
        self.assertEqual( testFrame.PUMP_disp_currSpeed.text(),         '1.1%')



    def test_pump1Update (self):
        global testFrame
        
        testFrame.pump1Update(UTIL.PumpTelemetry(1.1,2.2,3.3,4.4))

        self.assertEqual( UTIL.STT_datablock.PUMP1
                         ,UTIL.PumpTelemetry(1.1,2.2,3.3,4.4) )
        self.assertEqual( testFrame.PUMP_disp_freq.text(), '1.1' )
        self.assertEqual( testFrame.PUMP_disp_volt.text(), '2.2' )
        self.assertEqual( testFrame.PUMP_disp_amps.text(), '3.3' )
        self.assertEqual( testFrame.PUMP_disp_torq.text(), '4.4' )
    


    def test_applySettings (self):
        """ test default settings loading in '__init__' as well """
        global testFrame

        # check if defaults were loaded
        self.assertEqual( testFrame.TCP_num_commForerun.value()     ,UTIL.DEF_ROB_COMM_FR)
        self.assertEqual( testFrame.SET_float_volPerE.value()       ,UTIL.DEF_SC_VOL_PER_E)
        self.assertEqual( testFrame.SET_float_frToMms.value()       ,UTIL.DEF_IO_FR_TO_TS)
        self.assertEqual( testFrame.SET_num_zone.value()            ,UTIL.DEF_IO_ZONE)
        self.assertEqual( testFrame.SET_num_transSpeed_dc.value()   ,UTIL.DEF_DC_SPEED.TS)
        self.assertEqual( testFrame.SET_num_orientSpeed_dc.value()  ,UTIL.DEF_DC_SPEED.OS)
        self.assertEqual( testFrame.SET_num_accelRamp_dc.value()    ,UTIL.DEF_DC_SPEED.ACR)
        self.assertEqual( testFrame.SET_num_decelRamp_dc.value()    ,UTIL.DEF_DC_SPEED.DCR)
        self.assertEqual( testFrame.SET_num_transSpeed_print.value(),UTIL.DEF_PRIN_SPEED.TS)
        self.assertEqual( testFrame.SET_num_orientSpeed_print.value()
                         ,UTIL.DEF_PRIN_SPEED.OS)
        self.assertEqual( testFrame.SET_num_accelRamp_print.value(),UTIL.DEF_PRIN_SPEED.ACR)
        self.assertEqual( testFrame.SET_num_decelRamp_print.value(),UTIL.DEF_PRIN_SPEED.DCR)

        # test setting by user
        testFrame.TCP_num_commForerun.setValue      (1)
        testFrame.SET_float_volPerE.setValue        (2.2)
        testFrame.SET_float_frToMms.setValue        (3.3)
        testFrame.SET_num_zone.setValue             (4)
        testFrame.SET_num_transSpeed_dc.setValue    (5)
        testFrame.SET_num_orientSpeed_dc.setValue   (6)
        testFrame.SET_num_accelRamp_dc.setValue     (7)
        testFrame.SET_num_decelRamp_dc.setValue     (8)
        testFrame.SET_num_transSpeed_print.setValue (9)
        testFrame.SET_num_orientSpeed_print.setValue(10)
        testFrame.SET_num_accelRamp_print.setValue  (11)
        testFrame.SET_num_decelRamp_print.setValue  (12)
        testFrame.applySettings()

        self.assertEqual( UTIL.ROB_comm_fr,     1 )
        self.assertEqual( UTIL.SC_vol_per_e,    2.2 )
        self.assertEqual( UTIL.IO_fr_to_ts,     3.3 )
        self.assertEqual( UTIL.IO_zone,         4 )
        self.assertEqual( UTIL.DC_speed.TS,     5 )
        self.assertEqual( UTIL.DC_speed.OS,     6 )
        self.assertEqual( UTIL.DC_speed.ACR,    7 )
        self.assertEqual( UTIL.DC_speed.DCR,    8 )
        self.assertEqual( UTIL.PRIN_speed.TS,   9 )
        self.assertEqual( UTIL.PRIN_speed.OS,   10 )
        self.assertEqual( UTIL.PRIN_speed.ACR,  11 )
        self.assertEqual( UTIL.PRIN_speed.DCR,  12 )

        # test resetting by user
        testFrame.loadDefaults()
        testFrame.applySettings()
        self.assertEqual( testFrame.TCP_num_commForerun.value()     ,UTIL.DEF_ROB_COMM_FR)
        self.assertEqual( testFrame.SET_float_volPerE.value()       ,UTIL.DEF_SC_VOL_PER_E)
        self.assertEqual( testFrame.SET_float_frToMms.value()       ,UTIL.DEF_IO_FR_TO_TS)
        self.assertEqual( testFrame.SET_num_zone.value()            ,UTIL.DEF_IO_ZONE)
        self.assertEqual( testFrame.SET_num_transSpeed_dc.value()   ,UTIL.DEF_DC_SPEED.TS)
        self.assertEqual( testFrame.SET_num_orientSpeed_dc.value()  ,UTIL.DEF_DC_SPEED.OS)
        self.assertEqual( testFrame.SET_num_accelRamp_dc.value()    ,UTIL.DEF_DC_SPEED.ACR)
        self.assertEqual( testFrame.SET_num_decelRamp_dc.value()    ,UTIL.DEF_DC_SPEED.DCR)
        self.assertEqual( testFrame.SET_num_transSpeed_print.value(),UTIL.DEF_PRIN_SPEED.TS)
        self.assertEqual( testFrame.SET_num_orientSpeed_print.value()
                         ,UTIL.DEF_PRIN_SPEED.OS)
        self.assertEqual( testFrame.SET_num_accelRamp_print.value(),UTIL.DEF_PRIN_SPEED.ACR)
        self.assertEqual( testFrame.SET_num_decelRamp_print.value(),UTIL.DEF_PRIN_SPEED.DCR)



    def test_labelUpdate_onSend (self):
        """ test labelUpdate_onQueueChange as well """
        global testFrame

        UTIL.DC_curr_zero = UTIL.Coor()

        testFrame.SGLC_entry_gcodeSglComm.setText('G1 X2.2 Y1')
        testFrame.addGcodeSgl()
        testFrame.labelUpdate_onSend(entry= None)

        self.assertEqual( testFrame.SCTRL_disp_elemInQ.text(),  '1' )
        self.assertEqual( testFrame.SCTRL_disp_buffComms.text(),'0' )

        # secondarily calls labelUpdate_onQueueChange
        self.assertEqual( testFrame.SCTRL_arr_queue.item(0).text()
                         ,str(UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 2.2, Y= 1) )) )
        
        UTIL.SC_queue.clear()
        
    

    def test_openFile (self):
        global testFrame
        global gcodeTestpath
        global rapidTestpath

        testFrame.openFile( testrun= True, testpath= gcodeTestpath )
        self.assertEqual  ( UTIL.IO_curr_filepath, gcodeTestpath )
        self.assertEqual  ( testFrame.IO_disp_filename.text(), gcodeTestpath.name )
        self.assertEqual  ( testFrame.IO_disp_commNum.text(),  '2' )
        self.assertEqual  ( testFrame.IO_disp_estimLen.text(), '3.0' )
        self.assertEqual  ( testFrame.IO_disp_estimVol.text(), '3.0' )


        testFrame.openFile(testrun= True, testpath= rapidTestpath)
        self.assertEqual  ( UTIL.IO_curr_filepath, rapidTestpath )
        self.assertEqual  ( testFrame.IO_disp_filename.text(), rapidTestpath.name )
        self.assertEqual  ( testFrame.IO_disp_commNum.text(),  '2' )
        self.assertEqual  ( testFrame.IO_disp_estimLen.text(), '3.0' )
        self.assertEqual  ( testFrame.IO_disp_estimVol.text(), '3.0' )
    


    def test_loadFile (self):
        global testFrame
        
        UTIL.SC_curr_comm_id = 1
        UTIL.DC_curr_zero = UTIL.Coor()

        # GCode
        testFrame.loadFile( lf_atID= False, testrun= True, testpath= gcodeTestpath )
        self.assertEqual( testFrame.IO_lbl_loadFile.text()
                         ,f"... {1} command(s) skipped (syntax)")
        self.assertEqual( testFrame.IO_num_addByID.value(), 2)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID=1, COOR_1= UTIL.Coor(Y= 2, Z= 0) ) )
                           ,str( UTIL.QEntry( ID=2, COOR_1= UTIL.Coor(Y= 2, Z= 1) ) )])

        # GCode at ID
        testFrame.IO_num_addByID.setValue(2)
        testFrame.loadFile( lf_atID= True, testrun= True, testpath= gcodeTestpath )
        self.assertEqual( testFrame.IO_lbl_loadFile.text()
                         ,f"... {1} command(s) skipped (syntax)")
        self.assertEqual( testFrame.IO_num_addByID.value(), 4)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID=1, COOR_1= UTIL.Coor(Y= 2, Z= 0) ) )
                           ,str( UTIL.QEntry( ID=2, COOR_1= UTIL.Coor(Y= 2, Z= 0) ) )
                           ,str( UTIL.QEntry( ID=3, COOR_1= UTIL.Coor(Y= 2, Z= 1) ) )
                           ,str( UTIL.QEntry( ID=4, COOR_1= UTIL.Coor(Y= 2, Z= 1) ) )])

        # RAPID
        UTIL.SC_queue.clear()
        UTIL.SC_curr_comm_id = 1

        testFrame.loadFile( lf_atID= False, testrun= True, testpath= rapidTestpath )
        self.assertEqual( testFrame.IO_lbl_loadFile.text()
                         ,f"... {4} command(s) skipped (syntax)")
        self.assertEqual( testFrame.IO_num_addByID.value(), 2)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID=1, COOR_1= UTIL.Coor(Y= 2, Z= 0, EXT= 11) ) )
                           ,str( UTIL.QEntry( ID=2, COOR_1= UTIL.Coor(Y= 2, Z= 1, EXT= 11) ) )])

        # RAPID at ID
        testFrame.IO_num_addByID.setValue(2)
        testFrame.loadFile( lf_atID= True, testrun= True, testpath= rapidTestpath )
        self.assertEqual( testFrame.IO_lbl_loadFile.text()
                         ,f"... {4} command(s) skipped (syntax)")
        self.assertEqual( testFrame.IO_num_addByID.value(), 4)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID=1, COOR_1= UTIL.Coor(Y= 2, Z= 0, EXT= 11) ) )
                           ,str( UTIL.QEntry( ID=2, COOR_1= UTIL.Coor(Y= 2, Z= 0, EXT= 11) ) )
                           ,str( UTIL.QEntry( ID=3, COOR_1= UTIL.Coor(Y= 2, Z= 1, EXT= 11) ) )
                           ,str( UTIL.QEntry( ID=4, COOR_1= UTIL.Coor(Y= 2, Z= 1, EXT= 11) ) )])
        
        UTIL.SC_queue.clear()
        UTIL.SC_curr_comm_id = 1
    


    def test_addGcodeSgl (self):
        global testFrame

        testFrame.SGLC_entry_gcodeSglComm.setText('G1 X1 Y2.2 EXT3 F40')
        testFrame.addGcodeSgl()
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                            ,SV= UTIL.Speed( TS=4 ) ) )])
        
        testFrame.SGLC_entry_gcodeSglComm.setText('G1 X1')
        UTIL.DC_curr_zero = UTIL.Coor(X=1, Y= 1)
        testFrame.addGcodeSgl( atID= True, ID= 1 )
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 2, Y=1) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                             ,SV= UTIL.Speed( TS=4 ) ) )])
        
        testFrame.addGcodeSgl( atID= True, ID= 2, fromFile= True, fileText= 'G1 Z1' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 2, Y= 1 ) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 2, Y= 1, Z= 1 ) ) )
                           ,str( UTIL.QEntry( ID= 3, COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                             ,SV= UTIL.Speed( TS=4 ) ) )])
        
        testFrame.addGcodeSgl( atID= False, ID=0, fromFile= True, fileText= 'G1 X1.2' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 2, Y= 1 ) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 2, Y= 1, Z= 1 ) ) )
                           ,str( UTIL.QEntry( ID= 3, COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                             ,SV= UTIL.Speed( TS=4 ) ) )
                           ,str( UTIL.QEntry( ID= 4
                                             ,COOR_1= UTIL.Coor(X= 2.2, Y= 2.2, EXT=3 ) ) )])

        UTIL.DC_curr_zero = UTIL.Coor()
        UTIL.SC_queue.clear()
    


    def test_addRapidSgl (self):
        global testFrame

        testFrame.SGLC_entry_rapidSglComm.setText('MoveL [[1.0,2.2,0.0][0.0,0.0,0.0,0.0]],\
                                                  [4,50,50,50],z10,tool0 EXT:3;')
        testFrame.addRapidSgl()
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[str( UTIL.QEntry( ID= 1, PT= 'Q', COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3)
                                            ,SV= UTIL.Speed( TS=4 ) ) )])
        
        testFrame.SGLC_entry_rapidSglComm.setText('MoveL [[1.0,0.0,0.0][0.0,0.0,0.0,0.0]],\
                                                  [200,50,50,50],z10,tool0 EXT:0.0;')
        testFrame.addRapidSgl( atID= True, ID= 1 )
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[ str( UTIL.QEntry( ID= 1, PT= 'Q', COOR_1= UTIL.Coor(X= 1) ) )
                           ,str( UTIL.QEntry( ID= 2, PT= 'Q', COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                             ,SV= UTIL.Speed( TS=4 ) ) )])
        
        UTIL.DC_curr_zero = UTIL.Coor(Z= 1)
        testFrame.addRapidSgl( atID= True, ID= 2, fromFile= True
                              ,fileText= 'MoveL Offs(pHome,0.0,0.0,1.0),[200,50,50,50],z10,\
                                          tool0 EXT:0;')
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, PT= 'Q', COOR_1= UTIL.Coor(X= 1) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(Z= 2 ) ) )
                           ,str( UTIL.QEntry( ID= 3, PT= 'Q', COOR_1= UTIL.Coor(X= 1, Y= 2.2, EXT=3 )
                                             ,SV= UTIL.Speed( TS=4 ) ) )])

        UTIL.DC_curr_zero = UTIL.Coor()
        UTIL.SC_queue.clear()



    def test_addSIB (self):
        global testFrame

        testFrame.addSIB(number= 1, atEnd= False )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 1, Y= 2, Z= 3, EXT= 500)
                                             ,SV= UTIL.Speed(TS= 400) ) ) 
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 6, Y= 7, Z= 8, EXT= 990)
                                             ,SV= UTIL.Speed(TS= 900) ) ) ] )
        
        UTIL.DC_curr_zero = UTIL.Coor(X= 1)
        testFrame.addSIB(number= 2, atEnd=True)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 1, Y= 2, Z= 3, EXT= 500)
                                             ,SV= UTIL.Speed(TS= 400) ) ) 
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 6, Y= 7, Z= 8, EXT= 990)
                                             ,SV= UTIL.Speed(TS= 900) ) )  
                           ,str( UTIL.QEntry( ID= 3, PT= 'Q'
                                             ,COOR_1= UTIL.Coor( X= 1.1, Y= 2.2, Z= 3.3, X_ori= 4.4, Y_ori= 5.5
                                                                ,Z_ori= 6.6, Q=7.7, EXT= 600)
                                             ,SV= UTIL.Speed(TS= 18, OS= 19, ACR= 20, DCR= 21), Z= 50 ) )  
                           ,str( UTIL.QEntry( ID= 4, MT= 'J'
                                             ,COOR_1= UTIL.Coor( X= 8, Y= 8, Z= 9, EXT= 160)
                                             ,SV= UTIL.Speed(TS= 110, OS= 120, ACR= 130, DCR= 140), Z= 15 ) ) ] )
        
        UTIL.DC_curr_zero = UTIL.Coor(X= 1)
        testFrame.addSIB(number= 3, atEnd= False)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, PT= 'Q'
                                             ,COOR_1= UTIL.Coor( X= 1.1, Y= 2.2, Z= 3.3, X_ori= 4.4, Y_ori= 5.5
                                                                ,Z_ori= 6.6, Q=7.7, EXT= 600)
                                             ,SV= UTIL.Speed(TS= 18, OS= 19, ACR= 20, DCR= 21), Z= 50 ) )
                           ,str( UTIL.QEntry( ID= 2, MT= 'J'
                                             ,COOR_1= UTIL.Coor( X= 8, Y= 8, Z= 9, EXT= 160)
                                             ,SV= UTIL.Speed(TS= 110, OS= 120, ACR= 130, DCR= 140), Z= 15 ) )
                           ,str( UTIL.QEntry( ID= 3, COOR_1= UTIL.Coor(X= 1, Y= 2, Z= 3, EXT= 500)
                                             ,SV= UTIL.Speed(TS= 400) ) ) 
                           ,str( UTIL.QEntry( ID= 4, COOR_1= UTIL.Coor(X= 6, Y= 7, Z= 8, EXT= 990)
                                             ,SV= UTIL.Speed(TS= 900) ) )  
                           ,str( UTIL.QEntry( ID= 5, PT= 'Q'
                                             ,COOR_1= UTIL.Coor( X= 1.1, Y= 2.2, Z= 3.3, X_ori= 4.4, Y_ori= 5.5
                                                                ,Z_ori= 6.6, Q=7.7, EXT= 600)
                                             ,SV= UTIL.Speed(TS= 18, OS= 19, ACR= 20, DCR= 21), Z= 50 ) )
                           ,str( UTIL.QEntry( ID= 6, MT= 'J'
                                             ,COOR_1= UTIL.Coor( X= 8, Y= 8, Z= 9, EXT= 160)
                                             ,SV= UTIL.Speed(TS= 110, OS= 120, ACR= 130, DCR= 140), Z= 15 ) ) ] )
        
        UTIL.SC_queue.clear()
        UTIL.DC_curr_zero = UTIL.Coor()
    


    def test_clrQueue (self):
        global testFrame

        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X1' )
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X2' )
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X3' )
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X4' )
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X5' )
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G1 X6' )

        testFrame.SCTRL_entry_clrByID.setText('2..4')
        testFrame.clrQueue(partial= True)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 1) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 5) ) )
                           ,str( UTIL.QEntry( ID= 3, COOR_1= UTIL.Coor(X= 6) ) ) ] )

        testFrame.SCTRL_entry_clrByID.setText('2')
        testFrame.clrQueue(partial= True)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor(X= 1) ) )
                           ,str( UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor(X= 6) ) ) ] )

        testFrame.clrQueue(partial= False)
        self.assertEqual( UTIL.SC_queue.display()
                         ,['Queue is empty!'] )
    


    def test_homeCommand (self):
        global testFrame

        UTIL.DC_curr_zero = UTIL.Coor( X= 1, Y= 2.2, Z=3, X_ori=4, Y_ori= 5, Z_ori= 6, Q= 7, EXT= 8 )
        testFrame.DC_drpd_moveType.setCurrentText('LINEAR')
        self.assertEqual( testFrame.homeCommand()[1]
                         ,UTIL.QEntry( ID= 1, Z= 0, COOR_1= UTIL.Coor( X= 1, Y= 2.2, Z=3, X_ori=4 
                                                                      ,Y_ori= 5, Z_ori= 6, Q= 7, EXT= 8) ) )
        testFrame.DC_drpd_moveType.setCurrentText('JOINT')
        self.assertEqual( testFrame.homeCommand()[1]
                         ,UTIL.QEntry( ID= 2, Z= 0, MT= 'J'
                                          ,COOR_1= UTIL.Coor( X= 1, Y= 2.2, Z=3, X_ori=4 
                                                             ,Y_ori= 5, Z_ori= 6, Q= 7, EXT= 8) ) )
        
        UTIL.DC_curr_zero = UTIL.Coor()
        UTIL.SC_curr_comm_id = 1
        UTIL.SC_queue.clear()

    

    def test_sendDCCommand (self):
        global testFrame

        testFrame.DC_sld_stepWidth.setValue(1)
        testFrame.DC_drpd_moveType.setCurrentText('LINEAR')
        self.assertEqual( str(testFrame.sendDCCommand(axis= 'X', dir= '+')[1])
                         ,str(UTIL.QEntry( ID= 1, Z=0, COOR_1= UTIL.Coor(X=1) ) ))

        testFrame.DC_sld_stepWidth.setValue(2)
        testFrame.DC_drpd_moveType.setCurrentText('JOINT')
        self.assertEqual( testFrame.sendDCCommand(axis= 'Y', dir= '-')[1]
                         ,UTIL.QEntry( ID= 2, MT='J',Z=0, COOR_1= UTIL.Coor(Y= -10) ) )

        testFrame.DC_sld_stepWidth.setValue(3)
        self.assertEqual( testFrame.sendDCCommand(axis= 'Z', dir= '+')[1]
                         ,UTIL.QEntry( ID= 3, MT='J',Z=0, COOR_1= UTIL.Coor(Z= 100) ) )
        
        self.assertRaises( ValueError, testFrame.sendDCCommand, axis= 'A', dir= '+' )
        self.assertRaises( ValueError, testFrame.sendDCCommand, axis= 'X', dir= '/' )

        UTIL.SC_curr_comm_id = 1
    


    def test_sendNCCommand (self):
        global testFrame

        testFrame.NC_float_x.setValue(1)
        testFrame.NC_float_y.setValue(2.2)
        testFrame.NC_float_z.setValue(3)
        testFrame.NC_float_xOrient.setValue(4)
        testFrame.NC_float_yOrient.setValue(5)
        testFrame.NC_float_zOrient.setValue(6)
        testFrame.NC_float_ext.setValue(7)
        testFrame.DC_drpd_moveType.setCurrentText('LINEAR')
        
        self.assertEqual( testFrame.sendNCCommand([1,2,3])[1]
                         ,UTIL.QEntry( ID= 1, Z=0, COOR_1= UTIL.Coor(X= 1, Y= 2.2, Z= 3) ) )
        
        UTIL.ROB_pos = UTIL.Coor( 1,1,1,1,1,1,0,1 )
        testFrame.DC_drpd_moveType.setCurrentText('JOINT')
        self.assertEqual( testFrame.sendNCCommand([4,5,6,8])[1]
                         ,UTIL.QEntry( ID= 2, MT= 'J', Z= 0
                                      ,COOR_1= UTIL.Coor( X= 1, Y= 1, Z= 1, X_ori= 4
                                                         ,Y_ori= 5, Z_ori= 6, EXT= 7) ) )
        
        UTIL.ROB_pos = UTIL.Coor()
        UTIL.SC_curr_comm_id = 1
    


    def test_sendGcodeCommand (self):
        global testFrame

        testFrame.TERM_entry_gcodeInterp.setText('G1 Y2.2')
        UTIL.ROB_pos = UTIL.Coor( 1,1,1,1,1,1,1,1 )
        UTIL.DC_curr_zero = UTIL.Coor( Y= 1 )

        self.assertEqual( testFrame.sendGcodeCommand()[1]
                         ,UTIL.QEntry( ID= 1, COOR_1= UTIL.Coor( X= 1, Y= 3.2, Z= 1, X_ori= 1
                                                                ,Y_ori= 1, Z_ori= 1, Q= 1, EXT= 1 ) ) )
        
        testFrame.TERM_entry_gcodeInterp.setText('G1 X1 Z3')
        UTIL.ROB_pos = UTIL.Coor( 1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8 )
        UTIL.DC_curr_zero = UTIL.Coor( 1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8 )

        self.assertEqual( testFrame.sendGcodeCommand()[1]
                         ,UTIL.QEntry( ID= 2, COOR_1= UTIL.Coor( 2.1,2.2,6.3,4.4,5.5,6.6,7.7,8.8 ) ) )
        
        UTIL.ROB_pos = UTIL.Coor()
        UTIL.SC_curr_comm_id = 1
    


    def test_sendRapidCommand (self):
        global testFrame

        testFrame.TERM_entry_rapidInterp.setText('MoveL [[1.0,2.0,3.0],[4.0,5.0,6.0,7.0]],\
                                                  [200,50,50,50],z50,tool0  EXT:600')
        self.assertEqual( testFrame.sendRapidCommand()[1]
                         ,UTIL.QEntry( ID= 1, PT= 'Q', Z= 50
                                      ,COOR_1= UTIL.Coor( X= 1, Y= 2, Z= 3, X_ori= 4
                                                         ,Y_ori= 5, Z_ori= 6, Q= 7, EXT= 600 ) ))
        
        UTIL.SC_curr_comm_id = 1
    


    def test_systemStopCommands (self):
        global testFrame

        self.assertEqual( testFrame.forcedStopCommand()[1], UTIL.QEntry( ID= 0, MT= 'S' ) )
        self.assertEqual( testFrame.robotStopCommand()[1],  UTIL.QEntry( ID= 0, MT= 'E' ) )
        testFrame.robotStopCommand(directly= False)
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str(UTIL.QEntry( ID= 3, MT= 'E' ))] )
        
        UTIL.SC_curr_comm_id = 1
        UTIL.SC_queue.clear()
    


    def test_sendCommand (self):
        global testFrame

        UTIL.ROB_comm_queue.clear()
        UTIL.SC_queue.add( UTIL.QEntry(ID= 1, COOR_1= UTIL.Coor(Y= 1.1)) )

        testFrame.sendCommand( command= UTIL.QEntry(ID= 1, COOR_1= UTIL.Coor(X= 2.2))
                              ,DC= True )                              
        self.assertEqual( UTIL.ROB_comm_queue.display()
                         ,[str(UTIL.QEntry(ID= 1, COOR_1= UTIL.Coor(X= 2.2)))] )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[str(UTIL.QEntry(ID= 2, COOR_1= UTIL.Coor(Y= 1.1)))] )
        self.assertEqual( UTIL.SC_curr_comm_id, 2 )

        UTIL.ROB_comm_queue.clear()
        UTIL.SC_curr_comm_id = 1
        UTIL.SC_queue.clear()
    


    def test_setZero (self):
        global testFrame

        UTIL.DC_curr_zero   = UTIL.Coor( 1,2,3,4,5,6,7,8 )
        UTIL.ROB_pos        = UTIL.Coor()
        
        testFrame.setZero([1,2,3])
        self.assertEqual( UTIL.DC_curr_zero, UTIL.Coor( 0,0,0,4,5,6,7,8) )
        
        testFrame.setZero([4,5,6,8])
        self.assertEqual( UTIL.DC_curr_zero, UTIL.Coor( 0,0,0,0,0,0,7,0) )

        UTIL.DC_curr_zero = UTIL.Coor()
    


    def test_setSpeed (self):
        global testFrame

        UTIL.PUMP1_speed = 10

        testFrame.setSpeed( type= '1' )
        self.assertEqual  ( UTIL.PUMP1_speed, 11 )
        testFrame.setSpeed( type= '0' )
        self.assertEqual  ( UTIL.PUMP1_speed, 0 )
        testFrame.setSpeed( type= '-1' )
        self.assertEqual  ( UTIL.PUMP1_speed, -1 )
        testFrame.setSpeed( type= 'r' )
        self.assertEqual  ( UTIL.PUMP1_speed, 1 )
        testFrame.PUMP_num_setSpeed.setValue(5)
        testFrame.setSpeed()
        self.assertEqual  ( UTIL.PUMP1_speed, 5 )

        UTIL.PUMP1_speed = 0



    def test_zz_end (self):
        """ does not test anything, just here to close all sockets/ exit cleanly,
            named '_zz_' to be executed bei unittest at last """
        global testFrame

        testFrame.close()

        UTIL.ROB_tcpip.close  (end= True)
        UTIL.PUMP1_tcpip.close(end= True)
        UTIL.PUMP2_tcpip.close(end= True)
        UTIL.TERM_log.clear()




# create test logfile and 0_BT_testfiles
desk    = os.environ['USERPROFILE']
dirpath = desk / pl.Path("Desktop/PRINT_py_testrun")
dirpath.mkdir( parents=True, exist_ok=True )

logpath = dirpath / pl.Path(str(datetime.now().strftime('%Y-%m-%d_%H%M%S')) + ".txt")
text    = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}:   test running..\n\n"

logfile = open(logpath,'x')
logfile.write(text)
logfile.close()

gcodeTestpath = dirpath / pl.Path('0_UT_testfile.gcode')
rapidTestpath = dirpath / pl.Path('0_UT_testfile.mod')
gcodeText     = ';comment\nG1 Y2\nG1 Z1'
rapidText     = '!comment\nMoveJ pHome,v200,fine,tool0;\n\n\
                    ! start printjob relative to pStart\n\
                    MoveL Offs(pHome,0.0,2.0,0.0),[200,50,50,50],z10,tool0 EXT:11;\n\
                    MoveL Offs(pHome,0.0,2.0,1.0),[200,50,50,50],z10,tool0 EXT:11;'

gcodeTestfile = open(gcodeTestpath,'w')
rapidTestfile = open(rapidTestpath,'w')
gcodeTestfile.write(gcodeText)
rapidTestfile.write(rapidText)
gcodeTestfile.close()
rapidTestfile.close()

# create application
app = 0
win = 0
app         = QApplication(sys.argv)
testFrame   = MF.Mainframe(lpath= logpath, connDef= (False, False), testrun= True)



# run test immediatly only if called alone
if __name__ == '__main__':
    unittest.main()