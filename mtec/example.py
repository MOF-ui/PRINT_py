
###########################################   IMPORTS   ########################################################

from mtec_mod import MtecMod
from threading import Timer





############################################   METHODs   ########################################################


def connect():
    #pump.serial_port = '/dev/cu.usbmodem1431201'
    pump.serial_port = 'COM3'
    pump.connect()
    keepAliveTmr.start()
    
def stop():
    pump.setSpeed(0)
    
def changeSpeed(newSpeed):
    ans = pump.setSpeed(int(newSpeed))
    print(ans)

def changeKeepAlive():
    if keepAliveStt:
        print("active")
        keepAliveTmr.start()
        keepAliveStt = False
    else:
        print("inactive")
        keepAliveTmr.cancel()
        keepAliveStt = True       

def keepAliveRoutine():
    pump.keepAlive()
    keepAliveTmr    = Timer(0.25, keepAliveRoutine)
    keepAliveTmr.start()
    
    
    
    
############################################   MAIN   ##########################################################

import tkinter

pump            = MtecMod("01")
keepAliveTmr    = Timer(0.25, keepAliveRoutine)
keepAliveStt    = True

master          = tkinter.Tk()

connectButton   = tkinter.Button(master, text="Connect", command=connect)
stopButton      = tkinter.Button(master, text="Stop", command=stop)
connectButton.pack()
stopButton.pack()

slider          = tkinter.Scale(master, from_=-100, to=100, orient=tkinter.HORIZONTAL, command=changeSpeed, label="Input: ")
slider.pack()

keepAliveVar    = tkinter.IntVar(value=1)
keepAlive       = tkinter.Checkbutton(master, text='keepAlive',variable=keepAliveVar, onvalue=1, offvalue=0, command=changeKeepAlive)
keepAlive.pack()

tkinter.mainloop()

keepAliveTmr.cancel()