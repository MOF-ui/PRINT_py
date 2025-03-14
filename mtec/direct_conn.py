
############################     IMPORTS     ################################
import os
import sys

from mtec_mod import MtecMod
from threading import Timer

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import libs.data_utilities as du

############################     METHODS     ################################

def connect():
    # pump.serial_port = '/dev/cu.usbmodem1431201'
    pump.settings_serial_port = 'COM3'
    serial_def_bus=du.serial.Serial(
        baudrate=du.DEF_PUMP_SERIAL['baud'],
        parity=du.DEF_PUMP_SERIAL['par'],
        stopbits=du.DEF_PUMP_SERIAL['stop'],
        bytesize=du.DEF_PUMP_SERIAL['size'],
        port=du.DEF_PUMP_SERIAL['port'],
    )
    pump.serial_default = serial_def_bus
    print(pump.connect())
    KeepAliveTmr.start()


def stop():
    pump.set_speed(0)


def change_speed(newSpeed):
    ans = pump.set_speed(int(newSpeed))
    print(ans)


def change_keep_alive():
    if keepAliveStt:
        print('active')
        KeepAliveTmr.start()
        keepAliveStt = False
    else:
        print('inactive')
        KeepAliveTmr.cancel()
        keepAliveStt = True


def keep_alive_routine():
    global keep_alive_end

    if not keep_alive_end:
        pump.keepAlive()
        keepAliveTmr = Timer(0.25, keep_alive_routine)
        keepAliveTmr.start()


##############################     MAIN     ##################################

import tkinter

keep_alive_end = False

pump = MtecMod(None, '02')
KeepAliveTmr = Timer(0.25, keep_alive_routine)

master = tkinter.Tk()

connectButton = tkinter.Button(master, text='Connect', command=connect)
stopButton = tkinter.Button(master, text='Stop', command=stop)
connectButton.pack()
stopButton.pack()

slider = tkinter.Scale(
    master,
    from_=-100,
    to=100,
    orient=tkinter.HORIZONTAL,
    command=change_speed,
    label='Input: ',
)
slider.pack()

keep_alive_var = tkinter.IntVar(value=1)
keepAlive = tkinter.Checkbutton(
    master,
    text='keepAlive',
    variable=keep_alive_var,
    onvalue=1,
    offvalue=0,
    command=change_keep_alive,
)
keepAlive.pack()

tkinter.mainloop()

KeepAliveTmr.cancel()
keep_alive_end = True

print('waiting for KATmr..')
while not KeepAliveTmr.finished:
    pass

pump.disconnect()
exit()
