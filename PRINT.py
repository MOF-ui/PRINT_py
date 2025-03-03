##############################################################################
#
#   PRINT_py main
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
#   debug mixer protocoll
#   check if PRH WD has to be critical
#   debug temperature readout at printhead
#   new EE protocol
#   wait times in EE protocol
#   implement new 'S' behaviour
#   (movement finished, list emptied, stop pumping, pinch)
#   rework UI
#   implement pre-checked driving

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

arg_len = len(sys.argv)
arg1 = ''

if arg_len == 2:
    arg1 = sys.argv[1]
    match arg1:
        case 'test':
            import tests.all_test as at
            at.run_all()
            exit()
        case 'local':
            du.ROBTcp.ip = 'localhost'
            dev_avail = True<<4
        case 'overwrite':
            du.ROBTcp.ip = '192.168.125.1'
            du.ROBTcp.port = '10001'
            dev_avail = True<<4
        case _: 
            raise KeyError(f"{arg1} is not a valid argument for PRINT.py!")

elif arg_len > 2:
    raise KeyError(f"PRINT.py got too many arguments!")


################################    SETUP    #################################

if arg1 != 'local' and arg1 != 'overwrite':
    # ask user if default TCP (or USB) connection parameters are to be used,
    # otherwise set new ones
    ret, dev_avail, rob_set, p_port, prh_url, db_url = conn_dialog(
        title="Welcome to PRINT_py  --  Connection setup",
        standalone=True,
    )
    if not ret:
        print(f"User choose to abort setup! Exiting..")
        exit()
    else:
        du.ROBTcp.set_params(rob_set)
        du.PMP_port = p_port
        du.PRH_url = prh_url
        du.DB_url = db_url


    # get the go from user
    welc_text = (
        f"STARTING PRINT APP...\n\nYou're about to establish "
        f"a TCP connection with the robot at {du.ROBTcp.ip}.\n"
        f"This can take up to {du.ROBTcp.c_tout} s. You may begin.\n\n"
    )
    ret = strd_dialog(
        welc_text,
        "Welcome to PRINT_py",
        standalone=True
    )
    if not ret:
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
win = Mainframe(logpath, dev_avail)
win.show()
app.exec()
# sys.exit(app.exec())
