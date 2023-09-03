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
        UTIL.SC_volPerMm     = 0.01
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
        self.assertEqual( PUTIL.calcSpeed(), 23.4 )

        UTIL.SC_volPerMm = 1 




############################################  MAIN  ##################################################

if __name__ == '__main__':
    unittest.main()