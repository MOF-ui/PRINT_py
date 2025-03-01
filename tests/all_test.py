
# one test to rule them all

############################     IMPORTS      ################################

import os
import sys
import unittest

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# comment out tests you dont want to run he<re
from tests.data_utilities_test import DataLibTest
from tests.func_utilities_test import FuncLibTest
from tests.win_mainframe_test import MainframeWinTest
from tests.pump_utilities_test import PumpLibTest
from tests.threads_test import ThreadsTest


#############################     MAIN      #################################

# see if all of the libs can be run without errors
import libs.data_utilities
import libs.func_utilities
import libs.pump_utilities
import libs.threads
import libs.win_daq
import libs.win_dialogs
import libs.win_mainframe

if __name__ == '__main__':
    # run unittests
    unittest.main()