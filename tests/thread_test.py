# test threads

############################################# IMPORTS #################################################

import os
import sys
import unittest
import pathlib as pl

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.PRINT_data_utilities    as UTIL
import libs.PRINT_threads           as T
    



########################################## TEST CLASS ##############################################

class Thread_test(unittest.TestCase):
    
    def test_loadFileWorker (self):
        global LFW
        global gcodeTestpath
        global rapidTestpath

        self.maxDiff        = 3000    
        UTIL.SC_currCommId  = 1
        UTIL.DC_currZero    = UTIL.Coordinate()

        # GCode
        T.LFW_filePath  = gcodeTestpath
        T.LFW_lineID    = 0
        LFW.start()

        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( id=1, Coor1= UTIL.Coordinate(y= 2, z= 0) ) )
                           ,str( UTIL.QEntry( id=2, Coor1= UTIL.Coordinate(y= 2, z= 1) ) )])

        # GCode at ID
        T.LFW_filePath  = gcodeTestpath
        T.LFW_lineID    = 2
        LFW.start()
        
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( id=1, Coor1= UTIL.Coordinate(y= 2, z= 0) ) )
                           ,str( UTIL.QEntry( id=2, Coor1= UTIL.Coordinate(y= 2, z= 0) ) )
                           ,str( UTIL.QEntry( id=3, Coor1= UTIL.Coordinate(y= 2, z= 1) ) )
                           ,str( UTIL.QEntry( id=4, Coor1= UTIL.Coordinate(y= 2, z= 1) ) )])

        # RAPID
        UTIL.SC_queue.clear()
        UTIL.SC_currCommId = 1

        T.LFW_filePath  = rapidTestpath
        T.LFW_lineID    = 0
        LFW.start()
        
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( id=1, Coor1= UTIL.Coordinate(y= 2, z= 0, ext= 11) ) )
                           ,str( UTIL.QEntry( id=2, Coor1= UTIL.Coordinate(y= 2, z= 1, ext= 11) ) )])

        # RAPID at ID
        T.LFW_filePath  = rapidTestpath
        T.LFW_lineID    = 2
        LFW.start()
        
        self.assertEqual( UTIL.SC_queue.display()
                         ,[ str( UTIL.QEntry( id=1, Coor1= UTIL.Coordinate(y= 2, z= 0, ext= 11) ) )
                           ,str( UTIL.QEntry( id=2, Coor1= UTIL.Coordinate(y= 2, z= 0, ext= 11) ) )
                           ,str( UTIL.QEntry( id=3, Coor1= UTIL.Coordinate(y= 2, z= 1, ext= 11) ) )
                           ,str( UTIL.QEntry( id=4, Coor1= UTIL.Coordinate(y= 2, z= 1, ext= 11) ) )])
        
        UTIL.SC_queue.clear()
        UTIL.SC_currCommId = 1
    


    def test_RoboCommWorker (self):
        global RCW

        UTIL.ROB_commQueue.clear()
        self.assertIsNone( RCW.checkRobCommZeroDist() )

        UTIL.ROB_commQueue.add( UTIL.QEntry( Coor1= UTIL.Coordinate(x=1, y= 1, z= 1, ext= 1) ) )
        UTIL.ROB_telem.Coor = UTIL.Coordinate()
        self.assertEqual( RCW.checkRobCommZeroDist(), 2 )
        




########################################## MAIN ##############################################

# create 0_BT_testfiles
desk    = os.environ['USERPROFILE']
dirpath = desk / pl.Path("Desktop/PRINT_py_testrun")
dirpath.mkdir( parents=True, exist_ok=True )

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

LFW = T.LoadFileWorker()
RCW = T.RoboCommWorker()

if __name__ == '__main__':
    unittest.main()