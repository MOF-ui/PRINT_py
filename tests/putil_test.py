# test pump_utilities

############################################# IMPORTS #################################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.PRINT_data_utilities as UTIL
import libs.PRINT_pump_utilities as PUTIL

############################################  CLASS  ##################################################

class PUTIL_test(unittest.TestCase):

    def test_calcSpeed(self):
        """ cases 'default', 'start' and 'end' are tested seperately """

        UTIL.PUMP1_speed     = 89
        UTIL.SC_volPerM     = 0.01
        UTIL.PUMP1_literPerS = 10

        # domain control
        UTIL.ROB_commQueue.clear()
        testEntry = UTIL.QEntry ( Speed= UTIL.SpeedVector(ts= 2000), pMode= 'default' )
        
        UTIL.ROB_commQueue.add  ( testEntry )
        self.assertEqual        ( PUTIL.calcSpeed(), 100.0) 

        UTIL.ROB_commQueue[0].Speed.ts = -2000
        self.assertEqual        ( PUTIL.calcSpeed(), -100.0)

        # test empty ROB_commQueue
        UTIL.ROB_commQueue.clear()
        self.assertEqual( PUTIL.calcSpeed(), 89 )

        # mode: None
        testEntry = UTIL.QEntry ( Speed= UTIL.SpeedVector(ts= 123) )
        UTIL.ROB_commQueue.add  ( testEntry )
        self.assertEqual        ( PUTIL.calcSpeed(), 89 )

        # mode: default
        testEntry = UTIL.QEntry( id= 1, Speed= UTIL.SpeedVector(ts= 234), pMode= 'default' )
        UTIL.ROB_commQueue.add( testEntry )
        self.assertEqual( PUTIL.calcSpeed(), 23 )


        UTIL.ROB_commQueue.clear()
    

    def test_defaultMode(self):
        """  """

        UTIL.SC_volPerM     = 0.01
        UTIL.PUMP1_literPerS = 10

        # None
        self.assertIsNone( PUTIL.defaultMode( None ) )

        # lastDefCommand
        testEntry               = UTIL.QEntry( Coor1= UTIL.Coordinate(x= 10) )
        PUTIL.lastDefCommand    = UTIL.QEntry( Coor1= UTIL.Coordinate(x= 10) )
        PUTIL.lastSpeed         = 45

        self.assertEqual( PUTIL.defaultMode( testEntry), 45 )

        # newCommand ( default Speed.ts for QEntry is 200 )
        testEntry = UTIL.QEntry( Coor1= UTIL.Coordinate(x= 11) )

        self.assertEqual( PUTIL.defaultMode( testEntry ), 20 )

    

    def test_profileMode(self): 
        """  """
        
        UTIL.ROB_commQueue.add( UTIL.QEntry() )
        UTIL.ROB_commQueue.add( UTIL.QEntry() )
        UTIL.ROB_telem.Coor   = UTIL.Coordinate()
        PUTIL.START_SUPP_PTS  = [   { 'until': 3.0,   'base': 'zero',     'mode': 'instant' },
                                    { 'until': 1.0,   'base': 'max',      'mode': 'instant'    },
                                    { 'until': 0.0,   'base': 'conn',     'mode': 'linear'  } ]

        PUTIL.END_SUPP_PTS    = [   { 'until': 5.0,   'base': 'default',  'mode': 'instant' },
                                    { 'until': 1.0,   'base': 'retract',  'mode': 'smoothstep' },
                                    { 'until': 0.0,   'base': 'zero',     'mode': 'instant' } ]


        # START_SUPP_PTS
        testEntry       = UTIL.QEntry( Coor1= UTIL.Coordinate(x= 10)
                                      ,Speed= UTIL.SpeedVector(ts= 1) )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.START_SUPP_PTS ), 0 )

        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 5 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.START_SUPP_PTS ), 0 )

        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 8 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.START_SUPP_PTS ), 100.0 )

        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 9.5 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.START_SUPP_PTS ), 60.0 )
        
        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 10 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.START_SUPP_PTS ), 20.0 )

        # END_SUPP_PTS
        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 4 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.END_SUPP_PTS ), 0.1 )

        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 7 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.END_SUPP_PTS ), -24.95 )

        UTIL.ROB_telem.Coor = UTIL.Coordinate( x= 10 )
        self.assertEqual( PUTIL.profileMode( testEntry, PUTIL.END_SUPP_PTS ), 0 )


        UTIL.ROB_commQueue.clear()
        
    


    def test_getBaseSpeed(self):
        """  """
        
        self.assertEqual( PUTIL.getBaseSpeed('zero',    12), 0    )
        self.assertEqual( PUTIL.getBaseSpeed('max',     12), 100  )
        self.assertEqual( PUTIL.getBaseSpeed('min',     12), -100 )
        self.assertEqual( PUTIL.getBaseSpeed('default', 12), 12   )
        self.assertEqual( PUTIL.getBaseSpeed('retract', 12), -50   )
        self.assertEqual( PUTIL.getBaseSpeed('conn',    12), 12   )

        UTIL.ROB_commQueue.add( UTIL.QEntry() )
        UTIL.ROB_commQueue.add( UTIL.QEntry() )
        self.assertEqual( PUTIL.getBaseSpeed('conn',    12), 20   )






############################################  MAIN  ##################################################

if __name__ == '__main__':
    unittest.main()