#####################################################################################################################
#
#
#   PRINT_py main
#   Release: 1.0
#
#   author:     Max Ole Frohmüller
#   instituion: TU Berlin, Department Baustoffe und Bauchemie (Material Science and Technology)
#   email:      m.frohmue@web.de
#   date:       2023-06-21
#
#   Hi! First of all: be careful with this program. Keep in mind, that it controls a very large robot arm
#   that can easily cause a lot of damage. Also, I am not a programmer (nor is english my first language
#   for that matter). Therefore you can not count on me following standard industrial procedures or that
#   all of the docstrings convey the meaning I intended. I tried to build this application according to the
#   standards that I know of, though. The script style doesn't follow PEP8 closely, I'll change that, if I
#   find the time.
#
#   LICENSE
#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.
#
#   SCOPE
#   This programm was written to remotely control the second robot arm (Roboter 2) of the instituts robotic cell.
#   The robot arms were manufactured by ABB while all of their subroutines were programmed by Klero Roboter
#   Automatisation from Berlin. This code requires a TCP/IP interface running on the robot, which takes 159 byte
#   commands. The robot can either act upon them immediately or buffer up to 3000 commands. The current version
#   runs on 10 forwarded commands, which goes easier on the robots internal route planning. While the interface
#   is connected the robot sends positional data (36 byte blocks) around every 0.2 seconds.
#   The blocks are structured as follows:
#
#
#   COMMAND BLOCK
#   4 byte, INT -   ID                      (command ID for robot to stay on track)
#   1 byte, CHAR -  move type               (use L -> linear movement, J -> joint movement, C -> circular movement)
#   1 byte, CHAR -  pos type                (use E -> rotation in Euler angles, Q -> rotation as quaternion, A -> pass 6 axis values)
#   4 byte, FLOAT - X or A1                 (X = X position in global coordinate system in mm, A = axis position)
#   4 byte, FLOAT - Y or A2
#   4 byte, FLOAT - Z or A3
#   4 byte, FLOAT - Q1, Rx or A4            (Q = quaternion value, Rx = rotation around X in degrees)
#   4 byte, FLOAT - Q2, Ry or A5
#   4 byte, FLOAT - Q3, Rz or A6
#   4 byte, FLOAT - Q4 or 0
#   4 byte, FLOAT - EXT:                    (EXT = postion of external axis in mm)
#   4 byte, FLOAT - (2) X or A1             (second block of coordinates for C-type movement)
#   4 byte, FLOAT - (2) Y or A2
#   4 byte, FLOAT - (2) Z or A3
#   4 byte, FLOAT - (2) Q1, Rx or A4
#   4 byte, FLOAT - (2) Q2, Ry or A5
#   4 byte, FLOAT - (2) Q3, Rz or A6
#   4 byte, FLOAT - (2) Q4 or 0
#   4 byte, FLOAT - (2) EXT
#   4 byte, INT -   acceleration ramp
#   4 byte, INT -   deceleration ramp
#   4 byte, INT -   transition speed
#   4 byte, INT -   orientation speed
#   4 byte; INT -   time                    (for time-dependent movement)
#   1 byte, CHAR -  speed calculation       (either V for velocity- or T for time-dependent)
#   4 byte, INT -   zone
#   4 byte, INT -   ID, motor 1             (all tool specific data from here)
#   4 byte, INT -   steps, motor 1
#   4 byte, INT -   ID, motor 2
#   4 byte, INT -   steps, motor 2
#   4 byte, INT -   ID, motor 3
#   4 byte, INT -   steps, motor 3
#   4 byte, INT -   ID, pnmtc clamp
#   4 byte, INT -   Y/N, pnmtc clamp
#   4 byte, INT -   ID, knife
#   4 byte, INT -   Y/N, knife
#   4 byte, INT -   ID, motor 4
#   4 byte, INT -   steps, motor 4
#   4 byte, INT -   ID, fiber
#   4 byte, INT -   steps, fiber
#   4 byte, INT -   ID, time
#   4 byte, INT -   time [ms], time
#
#
#   POSITION BLOCK
#   4 byte, FLOAT - tool center point velocity
#   1 byte, INT -   current command ID processing
#   4 byte, FLOAT - X
#   4 byte, FLOAT - Y
#   4 byte, FLOAT - Z
#   4 byte, FLOAT - Rx
#   4 byte, FLOAT - Ry
#   4 byte, FLOAT - Rz
#   4 byte, FLOAT - EXT
#
#
#####################################################################################################################



########################################     IMPORTS      ######################################################

# python standard libraries
import sys


# PyQt stuff
from PyQt5.QtWidgets import QApplication


# import my own libs and UIs
from libs.win_dialogs import strd_dialog, conn_dialog
from libs.win_mainframe import Mainframe
import libs.data_utilities as du
import libs.func_utilities as fu



###########################################    SETUP    #########################################################

# ask user if default TCP (or USB) connection parameters are to be used, otherwise set new ones
connection_setup = conn_dialog(
    du.DEF_TCP_ROB,
    du.DEF_TCP_PUMP,
    du.DEF_TCP_PUMP,
    title="Welcome to PRINT_py  --  Connection setup",
    standalone=True,
)

cs_result = connection_setup[0]
cs_robot = connection_setup[1]
cs_pump1 = connection_setup[2]
cs_pump2 = connection_setup[3]
cs_conn_def = (connection_setup[4], connection_setup[5])

if not cs_result:
    print(f"User choose to abort setup! Exiting..")
    exit()
else:
    du.ROBTcp.set_params(cs_robot)
    du.PMP1Tcp.set_params(cs_pump1)
    du.PMP2Tcp.set_params(cs_pump2)


# get the go from user
welc_text = (
    f"STARTING PRINT APP...\n\n"
    f"You're about to establish a TCP connection with the robot at {du.ROBTcp.ip}.\n"
    f"This can take up to {du.ROBTcp.c_tout} s. You may begin.\n\n"
)

welc_choice = strd_dialog(welc_text, "Welcome to PRINT_py", standalone=True)
if not welc_choice:
    print(f"User choose to abort setup! Exiting..")
    exit()


#######################################     MAINFRAME     #####################################################

# create logfile and get path
logpath = fu.create_logfile()

print(
    f"PRINT_py started.\n"
    f"Writing log at {logpath}.\n"
    f"Got command line arguments: {sys.argv}"
)

arg1 = sys.argv[0]
test_arg = True if (arg1 == 'test') else False

# start the UI and show the window to user
app = 0  # leave that here so app doesnt include the remnant of a previous QApplication instance
win = 0
app = QApplication(sys.argv)
win = Mainframe(lpath=logpath, conn_def=cs_conn_def, testrun=test_arg)
win.show()
app.exec()
# sys.exit(app.exec())
