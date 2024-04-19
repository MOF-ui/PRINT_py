#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as  
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

# python standard libraries
import os
import sys

# appending the parent directory path
current_dir = os.path.dirname( os.path.realpath(__file__) )
parent_dir  = os.path.dirname( current_dir )
sys.path.append( parent_dir )


# PyQt stuff
from PyQt5.QtCore       import QMutex
from PyQt5.QtWidgets    import QApplication


# import PyQT UIs (converted from .ui to .py using Qt-Designer und pyuic5)
from libs.win_mainframe   import Mainframe


# import my own libs
import libs.data_utilities    as du




####################################### MAINFRAME CLASS  #####################################################

class GUI( Mainframe ):
    """ test """

    
    







####################################################   MAIN  ####################################################

# mutual exclusion object, used to manage global data exchange
mutex = QMutex()




# only do the following if run as main program
if __name__ == '__main__':

    from libs.win_dialogs import strd_dialog
    import libs.data_utilities as du

    # import PyQT UIs (converted from .ui to .py)
    from ui.UI_mainframe_v6 import Ui_MainWindow



    logpath = du.create_logfile()

    # overwrite ROB_tcpip for testing, delete later
    du.ROBTcp.ip   = 'localhost'
    du.ROBTcp.port = 10001

    # start the UI and assign to app
    app = 0                             # leave that here so app doesnt include the remnant of a previous QApplication instance
    win = 0
    app = QApplication( sys.argv )
    win = GUI()
    win.show()

    # start application (uses sys for CMD)
    app.exec()
    # sys.exit(app.exec())