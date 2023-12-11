# test win_mainframe

############################################# IMPORTS #################################################

import os
import sys
import unittest
import pathlib as pl

from PyQt5.QtWidgets    import QApplication
from PyQt5.QtCore       import QThread
from datetime           import datetime

# appending the parent directory path
current_dir = os.path.dirname( os.path.realpath(__file__) )
parent_dir  = os.path.dirname( current_dir )
sys.path.append( parent_dir )

import libs.data_utilities    as UTIL
import libs.win_mainframe     as MF

from libs.win_daq import DAQWindow as DAQ
from libs.threads import RoboCommWorker, PumpCommWorker




########################################## TEST CLASS ##############################################

class Mainframe_test( unittest.TestCase ):

    def assertIsFile( self, path ):
        """ program file exist error """

        if not pl.Path( path ).resolve().is_file():
            raise AssertionError(f"No such file: {path}")
    


    def test_addGcodeSgl( self ):
        global testFrame

        UTIL.SC_queue.clear()

        # G1
        testFrame.SGLC_entry_gcodeSglComm.setText( 'G1 X1 Y2.2 EXT3 F40' )
        testFrame.addGcodeSgl()
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext=3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort() ] )
        
        testFrame.SGLC_entry_gcodeSglComm.setText( 'G1 X1' )
        UTIL.DC_currZero = UTIL.Coordinate( x= 1, y= 1 )
        testFrame.addGcodeSgl( atID= True, ID= 1 )
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2, y=1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext=3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort() ] )
        
        testFrame.addGcodeSgl( atID= True, ID= 2, fromFile= True, fileText= 'G1 Z1' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2, y= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 2, y= 1, z= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext=3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort() ] )
        
        testFrame.addGcodeSgl( atID= False, ID=0, fromFile= True, fileText= 'G1 X1.2' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2, y= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 2, y= 1, z= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext= 3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort()
                           # here, the external axis is set to 0, as a change in X activates the recalculation of the 
                           # appropriate EXT position in UTIL.gcodeToQEntry using UTIL.SC_extFllwBhvr 
                           ,UTIL.QEntry( id= 4 ,Coor1= UTIL.Coordinate( x= 2.2, y= 2.2, ext= 0 ) ).printShort() ] )
        
        # G28 & G92
        testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= 'G92 Y0 EXT0' )
        self.assertEqual( UTIL.DC_currZero, UTIL.Coordinate( x= 1, y= 2.2 ) )

        testFrame.addGcodeSgl( atID= False, ID=0, fromFile= True, fileText= 'G28 Y0 EXT0' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2, y= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 2, y= 1, z= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext=3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort()
                           ,UTIL.QEntry( id= 4 ,Coor1= UTIL.Coordinate( x= 2.2, y= 2.2, ext= 0 ) ).printShort()
                           ,UTIL.QEntry( id= 5 ,Coor1= UTIL.Coordinate( x= 2.2, y= 2.2, ext= 0 ) ).printShort() ] )
        
        testFrame.addGcodeSgl( atID= True, ID= 3, fromFile= True, fileText= 'G92 X0 Z0' )
        self.assertEqual( UTIL.DC_currZero, UTIL.Coordinate( x= 2, y=2.2, z=1, ext= 0 ) )


        UTIL.DC_currZero = UTIL.Coordinate()
        UTIL.SC_queue.clear()
    


    def test_addRapidSgl( self ):
        global testFrame

        testFrame.SGLC_entry_rapidSglComm.setText( 'MoveL [[1.0,2.2,0.0][0.0,0.0,0.0,0.0]],[4,50,50,50],z10,tool0 EXT:3;' )
        testFrame.addRapidSgl()
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[UTIL.QEntry( id= 1, pt= 'Q', Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext= 3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort() ] )
        
        testFrame.SGLC_entry_rapidSglComm.setText( 'MoveL [[1.0,0.0,0.0][0.0,0.0,0.0,0.0]],[200,50,50,50],z10,tool0 EXT:0.0;' )
        testFrame.addRapidSgl( atID= True, ID= 1 )
        self.assertEqual( UTIL.SC_queue.display() 
                         ,[ UTIL.QEntry( id= 1, pt= 'Q', Coor1= UTIL.Coordinate( x= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, pt= 'Q', Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext= 3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort() ] )
        
        UTIL.DC_currZero = UTIL.Coordinate( z= 1 )
        testFrame.addRapidSgl( atID= True, ID= 2, fromFile= True
                              ,fileText= 'MoveL Offs(pHome,0.0,0.0,1.0),[200,50,50,50],z10,tool0 EXT:0;' )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, pt= 'Q', Coor1= UTIL.Coordinate( x= 1) ).printShort()
                           ,UTIL.QEntry( id= 2, pt= 'E', Coor1= UTIL.Coordinate( z= 2 ) ).printShort()
                           ,UTIL.QEntry( id= 3, pt= 'Q', Coor1= UTIL.Coordinate( x= 1, y= 2.2, ext= 3 ), Speed= UTIL.SpeedVector( ts=4 ) ).printShort( ) ] )

        UTIL.DC_currZero = UTIL.Coordinate()
        UTIL.SC_queue.clear()



    def test_addSIB( self ):
        global testFrame
        self.maxDiff = 2000

        testFrame.SIB_entry_sib1.setText( f"G1 X1.0 Y2.0 Z3.0 F4000 EXT500\n"
                                          f"G1 X6.0 Y7.0 Z8.0 F9000 EXT990" )
        testFrame.SIB_entry_sib2.setText( f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT:600\n"
                                          f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT:160" )
        testFrame.SIB_entry_sib3.setText( f"MoveL [[1.1,2.2,3.3],[4.4,5.5,6.6,7.7],[8,9,10,11],[12,13,14,15,16,17]],[18,19,20,21],z50,tool0  EXT:600\n"
                                          f"MoveJ Offs(pHome,7.0,8.0,9.0),[110,120,130,140],z15,tool0 EXT:160" )

        testFrame.addSIB( number= 1, atEnd= False )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1, y= 2, z= 3, ext= 500 ), Speed= UTIL.SpeedVector( ts= 400 ) ).printShort() 
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 6, y= 7, z= 8, ext= 990 ), Speed= UTIL.SpeedVector( ts= 900 ) ).printShort() ] )
        
        UTIL.DC_currZero = UTIL.Coordinate( x= 1 )
        testFrame.addSIB( number= 2, atEnd= True )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1, y= 2, z= 3, ext= 500 ), Speed= UTIL.SpeedVector( ts= 400 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 6, y= 7, z= 8, ext= 990 ), Speed= UTIL.SpeedVector( ts= 900 ) ).printShort()
                           ,UTIL.QEntry( id= 3, pt= 'Q', Coor1= UTIL.Coordinate( x= 1.1, y= 2.2, z= 3.3, rx= 4.4, ry= 5.5, rz= 6.6, q= 7.7, ext= 600 ), Speed= UTIL.SpeedVector( ts= 18, ors= 19, acr= 20, dcr= 21 ), z= 50 ).printShort() 
                           ,UTIL.QEntry( id= 4, mt= 'J', Coor1= UTIL.Coordinate( x= 8, y= 8, z= 9, ext= 160 ), Speed= UTIL.SpeedVector( ts= 110, ors= 120, acr= 130, dcr= 140 ), z= 15 ).printShort() ] )
        
        UTIL.DC_currZero = UTIL.Coordinate( x= 1 )
        testFrame.addSIB( number= 3, atEnd= False )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, pt= 'Q', Coor1= UTIL.Coordinate( x= 1.1, y= 2.2, z= 3.3, rx= 4.4, ry= 5.5, rz= 6.6, q= 7.7, ext= 600 ), Speed= UTIL.SpeedVector( ts= 18, ors= 19, acr= 20, dcr= 21 ), z= 50 ).printShort()
                           ,UTIL.QEntry( id= 2, mt= 'J', Coor1= UTIL.Coordinate( x= 8, y= 8, z= 9, ext= 160 ), Speed= UTIL.SpeedVector( ts= 110, ors= 120, acr= 130, dcr= 140 ), z= 15 ).printShort()
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 1, y= 2, z= 3, ext= 500 ), Speed= UTIL.SpeedVector( ts= 400 ) ).printShort()
                           ,UTIL.QEntry( id= 4, Coor1= UTIL.Coordinate( x= 6, y= 7, z= 8, ext= 990 ), Speed= UTIL.SpeedVector( ts= 900 ) ).printShort()
                           ,UTIL.QEntry( id= 5, pt= 'Q', Coor1= UTIL.Coordinate( x= 1.1, y= 2.2, z= 3.3, rx= 4.4, ry= 5.5, rz= 6.6, q= 7.7, ext= 600 ), Speed= UTIL.SpeedVector( ts= 18, ors= 19, acr= 20, dcr= 21 ), z= 50 ).printShort()
                           ,UTIL.QEntry( id= 6, mt= 'J', Coor1= UTIL.Coordinate( x= 8, y= 8, z= 9, ext= 160 ), Speed= UTIL.SpeedVector( ts= 110, ors= 120, acr= 130, dcr= 140 ), z= 15 ).printShort() ] )
        
        UTIL.SC_queue.clear()
        UTIL.DC_currZero = UTIL.Coordinate()
    


    def test_amconScriptOverwrite( self ):
        global testFrame

        for i in range( 1, 5, 1 ):
            testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= f"G1 X{i}" )
        testFrame.ASC_num_panning.setValue      ( 1 )
        testFrame.ASC_num_fibDeliv.setValue     ( 2 )
        testFrame.ASC_btt_clamp.setChecked      ( True )
        testFrame.ASC_btt_knifePos.setChecked   ( True )
        testFrame.ASC_btt_knife.setChecked      ( True )
        testFrame.ASC_btt_fiberPnmtc.setChecked ( True )
        

        testFrame.ASC_entry_SCLines.setText( '2..3' )
        testFrame.amconScriptOverwrite()
        self.assertEqual( UTIL.SC_queue.queue
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1 ), Tool= UTIL.ToolCommand( 0, 0, 0, 0, 0, 0, 0, False, 0, False, 0, False, 0, False ) )
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 2 ), Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) )
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 3 ), Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) )
                           ,UTIL.QEntry( id= 4, Coor1= UTIL.Coordinate( x= 4 ), Tool= UTIL.ToolCommand( 0, 0, 0, 0, 0, 0, 0, False, 0, False, 0, False, 0, False ) ) ] )

        testFrame.ASC_entry_SCLines.setText( '4' )
        testFrame.amconScriptOverwrite()
        self.assertEqual( UTIL.SC_queue.queue
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1 ), Tool= UTIL.ToolCommand( 0, 0, 0, 0, 0, 0, 0, False, 0, False, 0, False, 0, False ) )
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 2 ), Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) )
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 3 ), Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) )
                           ,UTIL.QEntry( id= 4, Coor1= UTIL.Coordinate( x= 4 ), Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) ) ] )

        testFrame.clrQueue( partial= False )
        testFrame.ASC_num_panning.setValue      ( UTIL.DEF_AMC_PANNING )
        testFrame.ASC_num_fibDeliv.setValue     ( UTIL.DEF_AMC_FIB_DELIV )
        testFrame.ASC_btt_clamp.setChecked      ( UTIL.DEF_AMC_CLAMP )
        testFrame.ASC_btt_knifePos.setChecked   ( UTIL.DEF_AMC_KNIFE_POS )
        testFrame.ASC_btt_knife.setChecked      ( UTIL.DEF_AMC_KNIFE )
        testFrame.ASC_btt_fiberPnmtc.setChecked ( UTIL.DEF_AMC_FIBER_PNMTC )
    


    def test_adcUserChange( self ):
        global testFrame
        global ACON_btt_group

        testFrame.ADC_num_panning.blockSignals( True )
        testFrame.ADC_num_fibDeliv.blockSignals( True )
        for widget in ACON_btt_group:
            widget.blockSignals( True )

        testFrame.ADC_num_panning.setValue      ( 1 )
        testFrame.ADC_num_fibDeliv.setValue     ( 2 )
        testFrame.ADC_btt_clamp.setChecked      ( True )
        testFrame.ADC_btt_knifePos.setChecked   ( True )
        testFrame.ADC_btt_knife.setChecked      ( True )
        testFrame.ADC_btt_fiberPnmtc.setChecked ( True )

        command = testFrame.adcUserChange()[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, z= 0, Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) ) )

        UTIL.SC_currCommId = 1
        testFrame.ADC_num_panning.setValue      ( UTIL.DEF_AMC_PANNING )
        testFrame.ADC_num_fibDeliv.setValue     ( UTIL.DEF_AMC_FIB_DELIV )
        testFrame.ADC_btt_clamp.setChecked      ( UTIL.DEF_AMC_CLAMP )
        testFrame.ADC_btt_knifePos.setChecked   ( UTIL.DEF_AMC_KNIFE_POS )
        testFrame.ADC_btt_knife.setChecked      ( UTIL.DEF_AMC_KNIFE )
        testFrame.ADC_btt_fiberPnmtc.setChecked ( UTIL.DEF_AMC_FIBER_PNMTC )

        testFrame.ADC_num_panning.blockSignals( False )
        testFrame.ADC_num_fibDeliv.blockSignals( False )
        for widget in ACON_btt_group:
            widget.blockSignals( False )
        
        UTIL.ROB_commQueue.clear()
        UTIL.ROB_sendList.clear()
    


    def test_applySettings( self ):
        """ tests default settings loading in '__init__' and 'updateCommForerun' as well """
        global testFrame

        # check if defaults were loaded
        self.assertEqual( testFrame.TCP_num_commForerun.value(),        UTIL.DEF_ROB_COMM_FR )
        self.assertEqual( testFrame.SET_float_volPerMM.value(),         UTIL.DEF_SC_VOL_PER_M )
        self.assertEqual( testFrame.SET_float_frToMms.value(),          UTIL.DEF_IO_FR_TO_TS )
        self.assertEqual( testFrame.SET_num_zone.value(),               UTIL.DEF_IO_ZONE )
        self.assertEqual( testFrame.SET_num_transSpeed_dc.value(),      UTIL.DEF_DC_SPEED.ts )
        self.assertEqual( testFrame.SET_num_orientSpeed_dc.value(),     UTIL.DEF_DC_SPEED.ors )
        self.assertEqual( testFrame.SET_num_accelRamp_dc.value(),       UTIL.DEF_DC_SPEED.acr )
        self.assertEqual( testFrame.SET_num_decelRamp_dc.value(),       UTIL.DEF_DC_SPEED.dcr )
        self.assertEqual( testFrame.SET_num_transSpeed_print.value(),   UTIL.DEF_PRIN_SPEED.ts )
        self.assertEqual( testFrame.SET_num_orientSpeed_print.value(),  UTIL.DEF_PRIN_SPEED.ors )
        self.assertEqual( testFrame.SET_num_accelRamp_print.value(),    UTIL.DEF_PRIN_SPEED.acr )
        self.assertEqual( testFrame.SET_num_decelRamp_print.value(),    UTIL.DEF_PRIN_SPEED.dcr )
        self.assertEqual( testFrame.SET_TE_num_fllwBhvrInterv.value(),  UTIL.DEF_SC_EXT_FLLW_BHVR [0] )
        self.assertEqual( testFrame.SET_TE_num_fllwBhvrSkip.value(),    UTIL.DEF_SC_EXT_FLLW_BHVR [1] )
        self.assertEqual( testFrame.SET_TE_num_retractSpeed.value(),    UTIL.DEF_PUMP_RETR_SPEED )
        self.assertEqual( testFrame.SET_TE_float_p1VolFlow.value(),     UTIL.DEF_PUMP_LPS )
        self.assertEqual( testFrame.SET_TE_float_p2VolFlow.value(),     UTIL.DEF_PUMP_LPS )

        self.assertEqual( testFrame.ADC_num_panning.value(),            UTIL.DEF_AMC_PANNING )
        self.assertEqual( testFrame.ADC_num_fibDeliv.value(),           UTIL.DEF_AMC_FIB_DELIV )
        self.assertEqual( testFrame.ADC_btt_clamp.isChecked(),          UTIL.DEF_AMC_CLAMP )
        self.assertEqual( testFrame.ADC_btt_knifePos.isChecked(),       UTIL.DEF_AMC_KNIFE_POS )
        self.assertEqual( testFrame.ADC_btt_knife.isChecked(),          UTIL.DEF_AMC_KNIFE )
        self.assertEqual( testFrame.ADC_btt_fiberPnmtc.isChecked(),     UTIL.DEF_AMC_FIBER_PNMTC )
        self.assertEqual( testFrame.ASC_num_panning.value(),            UTIL.DEF_AMC_PANNING )
        self.assertEqual( testFrame.ASC_num_fibDeliv.value(),           UTIL.DEF_AMC_FIB_DELIV )
        self.assertEqual( testFrame.ASC_btt_clamp.isChecked(),          UTIL.DEF_AMC_CLAMP )
        self.assertEqual( testFrame.ASC_btt_knifePos.isChecked(),       UTIL.DEF_AMC_KNIFE_POS )
        self.assertEqual( testFrame.ASC_btt_knife.isChecked(),          UTIL.DEF_AMC_KNIFE )
        self.assertEqual( testFrame.ASC_btt_fiberPnmtc.isChecked(),     UTIL.DEF_AMC_FIBER_PNMTC )

        # test setting by user
        testFrame.TCP_num_commForerun.setValue      ( 1 )
        testFrame.SET_float_volPerMM.setValue       ( 2.2 )
        testFrame.SET_float_frToMms.setValue        ( 3.3 )
        testFrame.SET_num_zone.setValue             ( 4 )
        testFrame.SET_num_transSpeed_dc.setValue    ( 5 )
        testFrame.SET_num_orientSpeed_dc.setValue   ( 6 )
        testFrame.SET_num_accelRamp_dc.setValue     ( 7 )
        testFrame.SET_num_decelRamp_dc.setValue     ( 8 )
        testFrame.SET_num_transSpeed_print.setValue ( 9 )
        testFrame.SET_num_orientSpeed_print.setValue( 10 )
        testFrame.SET_num_accelRamp_print.setValue  ( 11 )
        testFrame.SET_num_decelRamp_print.setValue  ( 12 )
        testFrame.applySettings()
        testFrame.updateCommForerun()

        testFrame.SET_TE_num_fllwBhvrInterv.setValue( 13 )
        testFrame.SET_TE_num_fllwBhvrSkip.setValue  ( 14 )
        testFrame.SET_TE_num_retractSpeed.setValue  ( 15 )
        testFrame.SET_TE_float_p1VolFlow.setValue   ( 16 )
        testFrame.SET_TE_float_p2VolFlow.setValue   ( 17 )
        testFrame.applyTeSettings()

        self.assertEqual( UTIL.ROB_commFr,      1 )
        self.assertEqual( UTIL.SC_volPerM,      2.2 )
        self.assertEqual( UTIL.IO_frToTs,       3.3 )
        self.assertEqual( UTIL.IO_zone,         4 )
        self.assertEqual( UTIL.DC_speed.ts,     5 )
        self.assertEqual( UTIL.DC_speed.ors,    6 )
        self.assertEqual( UTIL.DC_speed.acr,    7 )
        self.assertEqual( UTIL.DC_speed.dcr,    8 )
        self.assertEqual( UTIL.PRIN_speed.ts,   9 )
        self.assertEqual( UTIL.PRIN_speed.ors,  10 )
        self.assertEqual( UTIL.PRIN_speed.acr,  11 )
        self.assertEqual( UTIL.PRIN_speed.dcr,  12 )

        self.assertEqual( UTIL.SC_extFllwBhvr[0], 13 )
        self.assertEqual( UTIL.SC_extFllwBhvr[1], 14 )
        self.assertEqual( UTIL.PUMP_retractSpeed, 15 )
        self.assertEqual( UTIL.PUMP1_literPerS,   16 )
        self.assertEqual( UTIL.PUMP2_literPerS,   17 )

        # test resetting by user
        testFrame.TCP_num_commForerun.setValue( 10 )
        testFrame.loadDefaults()
        testFrame.applySettings()
        testFrame.updateCommForerun()
        testFrame.loadTeDefaults()
        testFrame.applyTeSettings()

        self.assertEqual( testFrame.TCP_num_commForerun.value(),        UTIL.DEF_ROB_COMM_FR )
        self.assertEqual( testFrame.SET_float_volPerMM.value(),         UTIL.DEF_SC_VOL_PER_M )
        self.assertEqual( testFrame.SET_float_frToMms.value(),          UTIL.DEF_IO_FR_TO_TS )
        self.assertEqual( testFrame.SET_num_zone.value(),               UTIL.DEF_IO_ZONE )
        self.assertEqual( testFrame.SET_num_transSpeed_dc.value(),      UTIL.DEF_DC_SPEED.ts )
        self.assertEqual( testFrame.SET_num_orientSpeed_dc.value(),     UTIL.DEF_DC_SPEED.ors )
        self.assertEqual( testFrame.SET_num_accelRamp_dc.value(),       UTIL.DEF_DC_SPEED.acr )
        self.assertEqual( testFrame.SET_num_decelRamp_dc.value(),       UTIL.DEF_DC_SPEED.dcr )
        self.assertEqual( testFrame.SET_num_transSpeed_print.value(),   UTIL.DEF_PRIN_SPEED.ts )
        self.assertEqual( testFrame.SET_num_orientSpeed_print.value(),  UTIL.DEF_PRIN_SPEED.ors )
        self.assertEqual( testFrame.SET_num_accelRamp_print.value(),    UTIL.DEF_PRIN_SPEED.acr )
        self.assertEqual( testFrame.SET_num_decelRamp_print.value(),    UTIL.DEF_PRIN_SPEED.dcr )
        self.assertEqual( testFrame.SET_TE_num_fllwBhvrInterv.value(),  UTIL.DEF_SC_EXT_FLLW_BHVR [0] )
        self.assertEqual( testFrame.SET_TE_num_fllwBhvrSkip.value(),    UTIL.DEF_SC_EXT_FLLW_BHVR [1] )
        self.assertEqual( testFrame.SET_TE_num_retractSpeed.value(),    UTIL.DEF_PUMP_RETR_SPEED )
        self.assertEqual( testFrame.SET_TE_float_p1VolFlow.value(),     UTIL.DEF_PUMP_LPS )
        self.assertEqual( testFrame.SET_TE_float_p2VolFlow.value(),     UTIL.DEF_PUMP_LPS )
    


    def test_clrQueue( self ):
        global testFrame

        for i in range( 1, 7, 1 ):
            testFrame.addGcodeSgl( atID= False, ID= 0, fromFile= True, fileText= f"G1 X{i}" )

        testFrame.SCTRL_entry_clrByID.setText( '2..4' )
        testFrame.clrQueue( partial= True )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 5 ) ).printShort()
                           ,UTIL.QEntry( id= 3, Coor1= UTIL.Coordinate( x= 6 ) ).printShort() ] )

        testFrame.SCTRL_entry_clrByID.setText( '2' )
        testFrame.clrQueue( partial= True )
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1 ) ).printShort()
                           ,UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( x= 6 ) ).printShort() ] )

        testFrame.clrQueue( partial= False )
        self.assertEqual( UTIL.SC_queue.display()
                         ,['Queue is empty!'] )
    


    def test_homeCommand( self ):
        global testFrame
        
        UTIL.DC_currZero = UTIL.Coordinate( x= 1, y= 2.2, z=3, rx=4, ry= 5, rz= 6, q= 7, ext= 8 )
        testFrame.DC_drpd_moveType.setCurrentText( 'LINEAR' )
        command = testFrame.homeCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, z= 0, Coor1= UTIL.Coordinate( x= 1, y= 2.2, z= 3, rx= 4, ry= 5, rz= 6, q= 7, ext= 8 ) ) )
        self.assertTrue( UTIL.DC_robMoving )

        testFrame.roboSend( command, True, 1, True, True )
        UTIL.DC_robMoving  = False
        
        testFrame.DC_drpd_moveType.setCurrentText( 'JOINT' )
        command = testFrame.homeCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 2, z= 0, mt= 'J', Coor1= UTIL.Coordinate( x= 1, y= 2.2, z= 3, rx= 4, ry= 5, rz= 6, q= 7, ext= 8 ) ) )
        
        UTIL.DC_currZero    = UTIL.Coordinate()
        UTIL.SC_currCommId  = 1
        UTIL.DC_robMoving   = False
        UTIL.SC_queue.clear()



    def test_init( self ):
        global testFrame
        global logpath

        # general values
        self.assertEqual     ( testFrame.logpath, logpath )
        self.assertIsInstance( testFrame.DAQ, DAQ )

        # logfile
        self.assertIsFile   ( logpath )
        logfileCheck        = open( logpath, 'r' )
        logfileCheckTxt     = logfileCheck.read()
        logfileCheck.close()
        self.assertIn( 'setup finished.', logfileCheckTxt )

        # defaults test with 'applySettings'
        
        # threads
        self.assertIsInstance( testFrame.roboCommThread, QThread )
        self.assertIsInstance( testFrame.pumpCommThread, QThread )
        self.assertIsInstance( testFrame.roboCommWorker, RoboCommWorker )
        self.assertIsInstance( testFrame.pumpCommWorker, PumpCommWorker )
    


    def test_labelUpdate_onNewZero( self ):
        """ rababer rababer """
        global testFrame

        UTIL.DC_currZero = UTIL.Coordinate( 1.1,2,3,4,5,6,7,8 )
        testFrame.labelUpdate_onNewZero()
        
        self.assertEqual( testFrame.ZERO_disp_x.text(), '1.1' )
        self.assertEqual( testFrame.ZERO_disp_y.text(), '2.0' )
        self.assertEqual( testFrame.ZERO_disp_z.text(), '3.0' )
        self.assertEqual( testFrame.ZERO_disp_xOrient.text(), '4.0' )
        self.assertEqual( testFrame.ZERO_disp_yOrient.text(), '5.0' )
        self.assertEqual( testFrame.ZERO_disp_zOrient.text(), '6.0' )
        self.assertEqual( testFrame.ZERO_disp_ext.text(), '8.0' )

        UTIL.DC_currZero = UTIL.Coordinate()



    def test_labelUpdate_onSend( self ):
        """ test labelUpdate_onQueueChange as well """
        global testFrame
        global ACON_btt_group

        UTIL.DC_currZero = UTIL.Coordinate()

        testFrame.SGLC_entry_gcodeSglComm.setText( 'G1 X2.2 Y1' )
        testFrame.addGcodeSgl()
        testFrame.labelUpdate_onSend( entry= UTIL.QEntry( Tool= UTIL.ToolCommand( 0, 1, 0, 2, 0, 0, 0, True, 0, True, 0, True, 0, True ) ) )

        self.assertEqual( testFrame.SCTRL_disp_elemInQ.text(),  '1' )
        self.assertEqual( testFrame.SCTRL_disp_buffComms.text(),'0' )
        self.assertEqual( testFrame.ADC_num_panning.value(),     1 )
        self.assertEqual( testFrame.ADC_num_fibDeliv.value(),    2 )
        self.assertEqual( testFrame.ASC_num_panning.value(),     1 )
        self.assertEqual( testFrame.ASC_num_fibDeliv.value(),    2 )
        for widget in ACON_btt_group:
            self.assertTrue( widget.isChecked(), True )

        # secondarily calls labelUpdate_onQueueChange
        self.assertEqual( testFrame.SCTRL_arr_queue.item(0).text(), UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2.2, y= 1 ) ).printShort() )
        
        UTIL.SC_queue.clear()
    


    def test_loadFile( self ):
        global testFrame
        
        UTIL.IO_currFilepath = pl.Path( 'test.abc' )
        testFrame.loadFile()
        self.assertEqual( testFrame.IO_lbl_loadFile.text(), "... no valid file, not executed" )
        
        UTIL.IO_currFilepath = pl.Path( 'test.mod' )
        testFrame.loadFile( testrun= True )
        self.assertEqual( testFrame.IO_lbl_loadFile.text(), "... conversion running ..." )

        UTIL.IO_currFilepath = None
    


    def test_loadFileFinished( self ):
        """ no need to test loadFileFailed, skip to loadFileFinished """
        global testFrame

        testFrame.loadFileFinished( lineID= 1, startID= 2, skips= 3 )
        self.assertEqual( testFrame.IO_num_addByID.value(), 1 )
        self.assertEqual( testFrame.IO_lbl_loadFile.text(), "... 3 command(s) skipped (syntax)" )
    


    def test_mixerSetSpeed( self ):
        global testFrame

        testFrame.MIX_num_setSpeed.setValue( 56 )
        testFrame.MIX_sld_speed.setValue( 78 )

        testFrame.mixerSetSpeed()
        self.assertEqual( UTIL.MIXER_speed, 56 )
        testFrame.mixerSetSpeed( 'sld' )
        self.assertEqual( UTIL.MIXER_speed, 78 )
        testFrame.mixerSetSpeed( '0' )
        self.assertEqual( UTIL.MIXER_speed, 0 )



    def test_openFile( self ):
        global testFrame
        global gcodeTestpath
        global rapidTestpath

        currSetting         = UTIL.SC_volPerM
        UTIL.SC_volPerM    = 0.1
        
        testFrame.openFile( testrun= True, testpath= gcodeTestpath )
        self.assertEqual  ( UTIL.IO_currFilepath, gcodeTestpath )
        self.assertEqual  ( testFrame.IO_disp_filename.text(), gcodeTestpath.name )
        self.assertEqual  ( testFrame.IO_disp_commNum.text(),  '2' )
        self.assertEqual  ( testFrame.IO_disp_estimLen.text(), '3.0' )
        self.assertEqual  ( testFrame.IO_disp_estimVol.text(), '0.3' )


        testFrame.openFile( testrun= True, testpath= rapidTestpath )
        self.assertEqual  ( UTIL.IO_currFilepath, rapidTestpath )
        self.assertEqual  ( testFrame.IO_disp_filename.text(), rapidTestpath.name )
        self.assertEqual  ( testFrame.IO_disp_commNum.text(),  '2' )
        self.assertEqual  ( testFrame.IO_disp_estimLen.text(), '3.0' )
        self.assertEqual  ( testFrame.IO_disp_estimVol.text(), '0.3' )

        UTIL.SC_volPerM = currSetting
    


    def test_roboSend( self ):
        """ test overflow control etc. labelUpdate_onSend tested by own function """
        global testFrame

        UTIL.SC_currCommId = 2991

        testFrame.roboSend( UTIL.QEntry( id= 12 ), True, 10, True, True )
        self.assertEqual( UTIL.SC_currCommId, 1 )
        self.assertEqual( testFrame.TCP_ROB_disp_writeBuffer.text()
                         ,f"ID: 12 -- L, E -- COOR_1: X: 0.0   Y: 0.0   Z: 0.0   Rx: 0.0   Ry: 0.0   Rz: 0.0   Q: 0.0   EXT: 0.0 -- SV: TS: 200   OS: 50   ACR: 50   DCR: 50 -- PMODE:  None" )
        self.assertEqual( testFrame.TCP_ROB_disp_bytesWritten.text(), '10' )

        testFrame.roboSend( None, True, ValueError, False, False )
        self.assertEqual( testFrame.TCP_ROB_disp_writeBuffer.text(), 'ValueError' )




    def test_roboRecv( self ):
        """ tests labelUpdate_onReceive as well """
        global testFrame

        # primary function
        UTIL.DC_currZero = UTIL.Coordinate()

        # check first loop switch, Q is not set by roboRecv
        UTIL.ROB_telem = UTIL.RoboTelemetry( 0, 0, UTIL.Coordinate( 1,2,3,4,5,6,7,8.8 ) )
        self.assertEqual    ( UTIL.DC_currZero, UTIL.Coordinate() )
        testFrame.roboRecv  ( rawDataString= 'ABC', telem= UTIL.RoboTelemetry() )
        self.assertEqual    ( UTIL.DC_currZero, UTIL.Coordinate( 1,2,3,4,5,6,0,8.8 ) )

        # check loop run
        UTIL.SC_currCommId = 15
        UTIL.DC_currZero   = UTIL.Coordinate( 0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.1 )
        UTIL.ROB_telem     = UTIL.RoboTelemetry( 9.9, 10, UTIL.Coordinate( 1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8 ) ) 
        testFrame.roboRecv( rawDataString= 'ABC', telem= UTIL.RoboTelemetry() )

        # labelUpdate_onReceive (called from roboRecv)
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
        self.assertEqual( testFrame.NC_disp_xOrient.text(),         '4.4°' )
        self.assertEqual( testFrame.NC_disp_yOrient.text(),         '5.5°' )
        self.assertEqual( testFrame.NC_disp_zOrient.text(),         '6.6°' )
        self.assertEqual( testFrame.NC_disp_ext.text(),             '8.8' )
        
        self.assertEqual( testFrame.TERM_disp_tcpSpeed.text(),      '9.9' )
        self.assertEqual( testFrame.TERM_disp_robCommID.text(),     '10' )
        self.assertEqual( testFrame.TERM_disp_progCommID.text(),    '15' )
        
        self.assertEqual( testFrame.SID_disp_progID.text(),         '15' )
        self.assertEqual( testFrame.SID_disp_robID.text(),          '10' )

        self.assertEqual( testFrame.TRANS_disp_xStart.text(),       '1.0' )
        self.assertEqual( testFrame.TRANS_disp_yStart.text(),       '2.0' )
        self.assertEqual( testFrame.TRANS_disp_zStart.text(),       '3.0' )
        self.assertEqual( testFrame.TRANS_disp_extStart.text(),     '8.8' )
        self.assertEqual( testFrame.TRANS_disp_xEnd.text(),         '1.0' )
        self.assertEqual( testFrame.TRANS_disp_yEnd.text(),         '2.0' )
        self.assertEqual( testFrame.TRANS_disp_zEnd.text(),         '3.0' )
        self.assertEqual( testFrame.TRANS_disp_extEnd.text(),       '8.8' )

        UTIL.DC_currZero        = UTIL.Coordinate()
        UTIL.ROB_telem          = UTIL.RoboTelemetry()
        UTIL.SC_currCommId      = 1
        UTIL.SC_queue.clear()



    def test_pumpSend( self ):
        global testFrame

        testFrame.pumpSend( newSpeed= 1.1, command= 'ABC', ans= 'DEF', source= 'P1' )

        self.assertEqual( UTIL.PUMP1_speed, 1.1 )
        self.assertEqual( testFrame.TCP_PUMP1_disp_writeBuffer.text(),  'ABC' )
        self.assertEqual( testFrame.TCP_PUMP1_disp_bytesWritten.text(), '3' )
        self.assertEqual( testFrame.TCP_PUMP1_disp_readBuffer.text(),   'DEF' )

        testFrame.pumpSend( newSpeed= 1.1, command= 'ABC', ans= 'DEF', source= 'P2' )

        self.assertEqual( UTIL.PUMP1_speed, 1.1)
        self.assertEqual( testFrame.TCP_PUMP2_disp_writeBuffer.text(),  'ABC' )
        self.assertEqual( testFrame.TCP_PUMP2_disp_bytesWritten.text(), '3' )
        self.assertEqual( testFrame.TCP_PUMP2_disp_readBuffer.text(),   'DEF' )



    def test_pumpRecv( self ):
        global testFrame
        
        UTIL.STT_dataBlock.Pump1 = UTIL.PumpTelemetry( 1.1,2.2,3.3,4.4 )
        testFrame.pumpRecv( telem= UTIL.STT_dataBlock.Pump1, source= 'P1' )

        self.assertEqual( testFrame.PUMP_disp_freqP1.text(),    '1.1%' )
        self.assertEqual( testFrame.PUMP_disp_voltP1.text(),    '2.2 V' )
        self.assertEqual( testFrame.PUMP_disp_ampsP1.text(),    '3.3 A' )
        self.assertEqual( testFrame.PUMP_disp_torqP1.text(),    '4.4 Nm' )
        self.assertEqual( testFrame.PUMP_disp_currSpeed.text(), '1.1%')
        
        UTIL.STT_dataBlock.Pump2 = UTIL.PumpTelemetry( 5,6,7,8 )
        UTIL.PUMP1_serial.connected = True
        UTIL.PUMP2_serial.connected = True
        testFrame.pumpRecv( telem= UTIL.STT_dataBlock.Pump2, source= 'P2' )

        self.assertEqual( testFrame.PUMP_disp_freqP2.text(),     '5.0%' )
        self.assertEqual( testFrame.PUMP_disp_voltP2.text(),     '6.0 V' )
        self.assertEqual( testFrame.PUMP_disp_ampsP2.text(),     '7.0 A' )
        self.assertEqual( testFrame.PUMP_disp_torqP2.text(),     '8.0 Nm' )
        self.assertEqual( testFrame.PUMP_disp_currSpeed.text(),  '3.0%')
        self.assertEqual( testFrame.PUMP_disp_outputRatio.text(),'18 / 82' )

        UTIL.STT_dataBlock.Pump1 = UTIL.STT_dataBlock.Pump2 = UTIL.PumpTelemetry()
        UTIL.PUMP1_serial.connected = False
        UTIL.PUMP2_serial.connected = False
    



    def test_sendCommand( self ):
        global testFrame

        UTIL.SC_currCommId = 1
        testFrame.roboSend( command= UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 2.2 ) ), msg= True, numSend= 1, dc= True, noError= True )
        self.assertEqual( UTIL.SC_currCommId, 2 )

        UTIL.SC_currCommId = 1
        UTIL.ROB_sendList.clear()

    

    def test_sendDCCommand( self ):
        global testFrame

        testFrame.DC_sld_stepWidth.setValue( 1 )
        testFrame.DC_drpd_moveType.setCurrentText( 'LINEAR' )
        
        command = testFrame.sendDCCommand( axis= 'X', dir= '+' )[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, z= 0, Coor1= UTIL.Coordinate( x= 1 ) ) )
        
        UTIL.DC_robMoving = False
        testFrame.roboSend( command, True, 1, True, True )
        testFrame.DC_sld_stepWidth.setValue( 2 )
        testFrame.DC_drpd_moveType.setCurrentText( 'JOINT' )

        command = testFrame.sendDCCommand( axis= 'Y', dir= '-' )[1]
        self.assertEqual( command, UTIL.QEntry( id= 2, mt='J',z=0, Coor1= UTIL.Coordinate( y= -10 ) ) )

        UTIL.DC_robMoving = False
        testFrame.roboSend( command, True, 1, True, True )
        testFrame.DC_sld_stepWidth.setValue( 3 )

        command = testFrame.sendDCCommand( axis= 'Z', dir= '+' )[1]
        self.assertEqual( command, UTIL.QEntry( id= 3, mt='J',z=0, Coor1= UTIL.Coordinate( z= 100 ) ) )
        
        UTIL.DC_robMoving = False
        testFrame.roboSend( command, True, 1, True, True )
        self.assertRaises( ValueError, testFrame.sendDCCommand, axis= 'A', dir= '+' )
        
        UTIL.DC_robMoving = False
        self.assertRaises( ValueError, testFrame.sendDCCommand, axis= 'X', dir= '/' )

        UTIL.DC_robMoving   = False
        UTIL.SC_currCommId  = 1
        UTIL.ROB_sendList.clear()
    


    def test_sendGcodeCommand( self ):
        global testFrame

        testFrame.TERM_entry_gcodeInterp.setText( 'G1 Y2.2 TOOL' )
        UTIL.ROB_telem.Coor = UTIL.Coordinate( 1,1,1,1,1,1,1,1 )
        UTIL.DC_currZero    = UTIL.Coordinate( y= 1 )

        command = testFrame.sendGcodeCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, Coor1= UTIL.Coordinate( x= 1, y= 3.2, z= 1, rx= 1, ry= 1, rz= 1, q= 1, ext= 1 ), Tool= UTIL.ToolCommand( fibDeliv_steps= 10, pnmtcFiber_yn= True ) ) )
        
        UTIL.DC_robMoving = False
        testFrame.roboSend( command, True, 1, True, True )
        testFrame.TERM_entry_gcodeInterp.setText( 'G1 X1 Z3' )
        UTIL.ROB_telem.Coor = UTIL.Coordinate( 1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8 )
        UTIL.DC_currZero    = UTIL.Coordinate( 1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8 )

        command = testFrame.sendGcodeCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 2, Coor1= UTIL.Coordinate( 2.1,2.2,6.3,4.4,5.5,6.6,7.7,8.8 ) ) )
        
        UTIL.DC_robMoving = False
        UTIL.ROB_telem.Coor = UTIL.Coordinate()
        UTIL.SC_currCommId = 1
        UTIL.ROB_sendList.clear()
    


    def test_sendNCCommand( self ):
        global testFrame

        testFrame.NC_float_x.setValue( 1 )
        testFrame.NC_float_y.setValue( 2.2 )
        testFrame.NC_float_z.setValue( 3 )
        testFrame.NC_float_xOrient.setValue( 4 )
        testFrame.NC_float_yOrient.setValue( 5 )
        testFrame.NC_float_zOrient.setValue( 6 )
        testFrame.NC_float_ext.setValue( 7 )
        testFrame.DC_drpd_moveType.setCurrentText( 'LINEAR' )
        
        command = testFrame.sendNCCommand( [1,2,3] )[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, z=0, Coor1= UTIL.Coordinate( x= 1, y= 2.2, z= 3 ) ) )
        
        UTIL.DC_robMoving = False
        testFrame.roboSend( command, True, 1, True, True )
        UTIL.ROB_telem.Coor = UTIL.Coordinate( 1,1,1,1,1,1,0,1 )
        testFrame.DC_drpd_moveType.setCurrentText( 'JOINT' )

        command = testFrame.sendNCCommand( [4,5,6,8] )[1]
        self.assertEqual( command, 
                          UTIL.QEntry( id= 2, mt= 'J', z= 0, Coor1= UTIL.Coordinate( x= 1, y= 1, z= 1, rx= 4, ry= 5, rz= 6, ext= 7) ) )
        
        UTIL.DC_robMoving = False
        UTIL.ROB_telem.Coor = UTIL.Coordinate()
        UTIL.SC_currCommId = 1
        UTIL.ROB_sendList.clear()
    


    def test_sendRapidCommand( self ):
        global testFrame

        testFrame.TERM_entry_rapidInterp.setText( 'MoveL [[1.0,2.0,3.0],[4.0,5.0,6.0,7.0]],[200,50,50,50],z50,tool0  EXT:600  TOOL' )
        self.assertEqual( testFrame.sendRapidCommand()[1]
                         ,UTIL.QEntry( id= 1, pt= 'Q', z= 50, Coor1= UTIL.Coordinate( x= 1, y= 2, z= 3, rx= 4, ry= 5, rz= 6, q= 7, ext= 600 ), Tool= UTIL.ToolCommand( fibDeliv_steps= 10, pnmtcFiber_yn= True ) ) )
        
        UTIL.SC_currCommId = 1
        UTIL.ROB_sendList.clear()
    


    def test_pumpSetSpeed( self ):
        global testFrame

        UTIL.PUMP_speed = 10
        testFrame.PUMP_num_setSpeed.setValue( 5 )
        UTIL.ROB_commQueue.add( UTIL.QEntry( Speed= UTIL.SpeedVector( ts=123 ) ) )

        testFrame.pumpSetSpeed  ( type= '1' )
        self.assertEqual        ( UTIL.PUMP_speed, 11 )
        testFrame.pumpSetSpeed  ( type= '0' )
        self.assertEqual        ( UTIL.PUMP_speed, 0 )
        testFrame.pumpSetSpeed  ( type= '-1' )
        self.assertEqual        ( UTIL.PUMP_speed, -1 )
        testFrame.pumpSetSpeed  ( type= 'r' )
        self.assertEqual        ( UTIL.PUMP_speed, 1 )
        testFrame.pumpSetSpeed  ()
        self.assertEqual        ( UTIL.PUMP_speed, 5 )
        testFrame.pumpSetSpeed  ( 'def' )
        self.assertEqual        ( UTIL.PUMP_speed, 9.84 )

        UTIL.PUMP_speed = 0
    


    def test_setZero( self ):
        global testFrame

        UTIL.DC_currZero   = UTIL.Coordinate( 1,2,3,4,5,6,7,8 )
        UTIL.ROB_telem.Coor  = UTIL.Coordinate()
        
        testFrame.setZero( [1,2,3] )
        self.assertEqual ( UTIL.DC_currZero, UTIL.Coordinate( 0,0,0,4,5,6,7,8) )
        
        testFrame.setZero( [4,5,6,8] )
        self.assertEqual ( UTIL.DC_currZero, UTIL.Coordinate( 0,0,0,0,0,0,7,0) )

        testFrame.ZERO_float_x.setValue  ( 1 )
        testFrame.ZERO_float_y.setValue  ( 2 )
        testFrame.ZERO_float_z.setValue  ( 3 )
        testFrame.ZERO_float_rx.setValue ( 4 )
        testFrame.ZERO_float_ry.setValue ( 5 )
        testFrame.ZERO_float_rz.setValue ( 6 )
        testFrame.ZERO_float_ext.setValue( 7 )
        testFrame.setZero( [1,2,3,4,5,6,8], fromSysMonitor= True )
        self.assertEqual ( UTIL.DC_currZero, UTIL.Coordinate( 1,2,3,4,5,6,7,7) )


        UTIL.DC_currZero = UTIL.Coordinate()
    


    def test_systemStopCommands( self ):
        global testFrame

        command = testFrame.forcedStopCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, mt= 'S' ) )

        testFrame.roboSend( command, True, 1, True, True )
        command = testFrame.robotStopCommand()[1]
        self.assertEqual( command, UTIL.QEntry( id= 1, mt= 'E' ) )

        testFrame.roboSend( command, True, 1, True, True )
        testFrame.robotStopCommand( directly= False )

        self.assertEqual( UTIL.SC_queue.display()
                         ,[UTIL.QEntry( id= 3, mt= 'E' ).printShort() ] )
        
        UTIL.SC_currCommId = 1
        UTIL.SC_queue.clear()



    def test_zz_end( self ):
        """ does not test anything, just here to close all sockets/ exit cleanly,
            named '_zz_' to be executed by unittest at last """
        global testFrame

        UTIL.ROB_tcp.connected      = False
        UTIL.PUMP1_serial.connected = False
        UTIL.PUMP2_serial.connected = False
        UTIL.MIXER_tcp.connected    = False
        testFrame.close()

        UTIL.ROB_tcp.close  ( end= True )
        UTIL.PUMP1_tcp.close( end= True )
        UTIL.PUMP2_tcp.close( end= True )
        UTIL.TERM_log.clear()




#############################################  MAIN  ##################################################

# create test logfile and 0_BT_testfiles
desk    = os.environ[ 'USERPROFILE' ]
dirpath = desk / pl.Path( 'Desktop/PRINT_py_testrun' )
dirpath.mkdir( parents=True, exist_ok=True )

logpath = dirpath / pl.Path( f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.txt" )
text    = f"{datetime.now().strftime('%Y-%m-%d_%H%M%S')}:   test running..\n\n"

logfile = open( logpath, 'w' )
logfile.write( text )
logfile.close()

gcodeTestpath = dirpath / pl.Path( '0_UT_testfile.gcode' )
rapidTestpath = dirpath / pl.Path( '0_UT_testfile.mod' )
gcodeText     = ';comment\nG1 Y2000\nG1 Z1000'
rapidText     = '!comment\nMoveJ pHome,v200,fine,tool0;\n\n\
                    ! start printjob relative to pStart\n\
                    MoveL Offs(pHome,0.0,2000.0,0.0),[200,50,50,50],z10,tool0 EXT:11;\n\
                    MoveL Offs(pHome,0.0,2000.0,1000.0),[200,50,50,50],z10,tool0 EXT:11;'

gcodeTestfile = open( gcodeTestpath, 'w' )
rapidTestfile = open( rapidTestpath, 'w' )
gcodeTestfile.write( gcodeText )
rapidTestfile.write( rapidText )
gcodeTestfile.close()
rapidTestfile.close()

# create application
app = 0
win = 0
app         = QApplication( sys.argv )
testFrame   = MF.Mainframe( lpath= logpath, connDef= (False, False), testrun= True )
rapidTestfile.close()

# grouping
ACON_btt_group = testFrame.ADC_btt_clamp, testFrame.ADC_btt_knifePos,\
                 testFrame.ADC_btt_knife, testFrame.ADC_btt_fiberPnmtc,\
                 testFrame.ASC_btt_clamp, testFrame.ASC_btt_knifePos,\
                 testFrame.ASC_btt_knife, testFrame.ASC_btt_fiberPnmtc



# run test immediatly only if called alone
if __name__ == '__main__':
    unittest.main()