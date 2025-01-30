##############################################################################
#
#   PRINT_py main
#   Release: 1.0
#
#   author:     Max Ole Frohmüller
#   instituion: TU Berlin,
#               Department Baustoffe und Bauchemie
#               (Material Science and Technology)
#   email:      m.frohmue@web.de
#   date:       2023-06-21
#
#   LICENSE
#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 
#   International (CC BY-SA 4.0) 
#   (https://creativecommons.org/licenses/by-sa/4.0/). 
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same 
#   license.
#
##############################################################################
# to-do:
#   work with reconnects in automatic modes (open cell inbetween)
#   test automatic pump control
#   debug mixer protocoll 
#   integrate pinch valve
#   check if PRH WD has to be critical
#   debug temperature readout at printhead
#   new EE protocol
#   wait times in EE protocol
#   implement new 'S' behaviour (movement finished, list emptied, stop pumping, pinch)
#   rework UI

###############################    IMPORTS    ################################

# python standard libraries
import sys


# PyQt stuff
from PyQt5.QtWidgets import QApplication


# import my own libs and UIs
from libs.win_dialogs import strd_dialog, conn_dialog
from libs.win_mainframe import Mainframe
import libs.data_utilities as du
import libs.func_utilities as fu


#######################    COMMAND LINE ARGUMENTS    #########################

test_arg = False
arg_len = len(sys.argv)
arg1 = ''

if arg_len == 2:
    arg1 = sys.argv[1]
    
    match arg1:
        case 'test': test_arg = True
        case 'local':
            du.ROBTcp.ip = 'localhost'
            p_connect = (None, None)
        case 'overwrite':
            du.ROBTcp.ip = '192.168.125.1'
            p_connect = (None, None)
        case _: 
            raise KeyError(f"{arg1} is not a valid argument for PRINT.py!")

elif arg_len > 2:
    raise KeyError(f"PRINT.py got too many arguments!")


################################    SETUP    #################################

if arg1 != 'local' and arg1 != 'overwrite':
    # ask user if default TCP (or USB) connection parameters are to be used,
    # otherwise set new ones
    cd_ret = conn_dialog(
        du.DEF_ROB_TCP,
        du.DEF_PUMP_TCP,
        du.DEF_PUMP_TCP,
        title="Welcome to PRINT_py  --  Connection setup",
        standalone=True,
    )

    if not cd_ret['result']:
        print(f"User choose to abort setup! Exiting..")
        exit()
    else:
        du.ROBTcp.set_params(cd_ret['rob_tcp'])
        du.PMP1Tcp.set_params(cd_ret['p1_tcp'])
        du.PMP2Tcp.set_params(cd_ret['p2_tcp'])
        p_connect = (cd_ret['p1_connect'], cd_ret['p2_connect'])


    # get the go from user
    welc_text = (
        f"STARTING PRINT APP...\n\nYou're about to establish "
        f"a TCP connection with the robot at {du.ROBTcp.ip}.\n"
        f"This can take up to {du.ROBTcp.c_tout} s. You may begin.\n\n"
    )

    welc_choice = strd_dialog(
        welc_text,
        "Welcome to PRINT_py",
        standalone=True
    )
    if not welc_choice:
        print(f"User choose to abort setup! Exiting..")
        exit()


##############################    MAINFRAME    ###############################

# create logfile and get path
logpath = fu.create_logfile()

print(
    f"PRINT_py started.\n"
    f"Writing log at {logpath}.\n"
    f"Got command line arguments: {sys.argv}"
)

# start the UI and show the window to user
# leave following 2 lines here so app doesnt include the remnant of a
# previous QApplication instance
app = 0  
win = 0
app = QApplication(sys.argv)
win = Mainframe(lpath=logpath, p_conn=p_connect, testrun=test_arg)
win.show()
app.exec()
# sys.exit(app.exec())
