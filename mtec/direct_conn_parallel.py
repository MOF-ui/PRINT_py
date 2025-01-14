
############################     IMPORTS     ################################
import os
import sys
import time

from mtec_mod import MtecMod
from threading import Timer

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du

############################     METHODS     ################################

def connect():
    if not Pmp1.connected:
        if Pmp1.connect():
            print('Pump 1 connected.')
        else: 
            print('Pump 1 CONNECTION ERROR!')
    if not Pmp2.connected:
        if Pmp2.connect():
            print('Pump 2 connected.')
        else: 
            print('Pump 2 CONNECTION ERROR!')
    KeepAliveTmr.start()

def stop(pmp=None):
    match pmp:
        case 1:
            Pmp1.set_speed(0)
        case 2:
            Pmp2.set_speed(0)
        case _:
            raise KeyError()


def change_speed_1(new_speed):
    pmp1_speed = int(new_speed)
    if pmp1_speed >= -100 and pmp1_speed <= 100:
        ans = Pmp1.set_speed(pmp1_speed)
        print(ans)
    else:
        raise KeyError()
    
def change_speed_2(new_speed):
    pmp2_speed = int(new_speed)
    if pmp2_speed >= -100 and pmp2_speed <= 100:
        ans = Pmp2.set_speed(pmp2_speed)
        print(ans)
    else:
        raise KeyError()


def keep_alive_routine():
    global keep_alive_end

    if not keep_alive_end:
        if Pmp1.connected:
            Pmp1.keepAlive()
        if Pmp2.connected:
            Pmp2.keepAlive()
        keepAliveTmr = Timer(0.25, keep_alive_routine)
        keepAliveTmr.start()


##############################     MAIN     ##################################

import tkinter

SerialBus = du.serial.Serial(
    baudrate=du.DEF_SERIAL_PUMP["BR"],
    parity=du.DEF_SERIAL_PUMP["P"],
    stopbits=du.DEF_SERIAL_PUMP["SB"],
    bytesize=du.DEF_SERIAL_PUMP["BS"],
    port=du.DEF_SERIAL_PUMP["PORT"],
)
Pmp1 = MtecMod(SerialBus, "01")
Pmp2 = MtecMod(SerialBus, "02")
pmp1_speed = 0
pmp2_speed = 0

keep_alive_end = False
KeepAliveTmr = Timer(0.25, keep_alive_routine)

master = tkinter.Tk()

connectButton = tkinter.Button(master, text="Connect 1", command=connect)
stopButton1 = tkinter.Button(master, text="Stop Motor 1", command=(lambda:stop(1)))
stopButton2 = tkinter.Button(master, text="Stop Motor 2", command=(lambda:stop(2)))
connectButton.pack()
stopButton1.pack()
stopButton2.pack()

slider_1 = tkinter.Scale(
    master,
    from_=-100,
    to=100,
    orient=tkinter.HORIZONTAL,
    command=change_speed_1,
    label="Input 1: ",
)
slider_2 = tkinter.Scale(
    master,
    from_=-100,
    to=100,
    orient=tkinter.HORIZONTAL,
    command=change_speed_2,
    label="Input 2: ",
)
slider_1.pack()
slider_2.pack()

tkinter.mainloop()

KeepAliveTmr.cancel()
keep_alive_end = True

print("waiting for KATmr..")
while not KeepAliveTmr.finished:
    pass

if Pmp1.connected:
    Pmp1.disconnect()
if Pmp2.connected:
    Pmp2.disconnect()
exit()
