
# one test to rule them all

############################################# IMPORTS #################################################

import os
import sys
import unittest

# comment out tests you dont want to run here
from mainframe_test            import Mainframe_test
from util_test                  import UTIL_test
from putil_test                 import PUTIL_test

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir  = os.path.dirname(current_dir)
sys.path.append(parent_dir)  




############################################### MAIN ###################################################

# see if all of the libs can be run without errors
import libs.PRINT_data_utilities
import libs.PRINT_threads
import libs.PRINT_win_daq
import libs.PRINT_win_dialogs
import libs.PRINT_win_mainframe

# run unittest
unittest.main()