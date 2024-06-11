
############################     IMPORTS     ################################

from mtec_mod import MtecMod
from threading import Timer


############################     METHODS     ################################

def connect():
    # pump.serial_port = '/dev/cu.usbmodem1431201'
    pump.serial_port = "COM3"
    pump.connect()
    KeepAliveTmr.start()


def stop():
    pump.set_speed(0)


def change_speed(newSpeed):
    ans = pump.set_speed(int(newSpeed))
    print(ans)


def change_keep_alive():
    if keepAliveStt:
        print("active")
        KeepAliveTmr.start()
        keepAliveStt = False
    else:
        print("inactive")
        KeepAliveTmr.cancel()
        keepAliveStt = True


def keep_alive_routine():
    global keep_alive_end

    pump.keepAlive()
    keepAliveTmr = Timer(0.25, keep_alive_routine)
    if not keep_alive_end:
        keepAliveTmr.start()


##############################     MAIN     ##################################

import tkinter

keep_alive_end = False

pump = MtecMod(None, "02")
KeepAliveTmr = Timer(0.25, keep_alive_routine)

master = tkinter.Tk()

connectButton = tkinter.Button(master, text="Connect", command=connect)
stopButton = tkinter.Button(master, text="Stop", command=stop)
connectButton.pack()
stopButton.pack()

slider = tkinter.Scale(
    master,
    from_=-100,
    to=100,
    orient=tkinter.HORIZONTAL,
    command=change_speed,
    label="Input: ",
)
slider.pack()

keep_alive_var = tkinter.IntVar(value=1)
keepAlive = tkinter.Checkbutton(
    master,
    text="keepAlive",
    variable=keep_alive_var,
    onvalue=1,
    offvalue=0,
    command=change_keep_alive,
)
keepAlive.pack()

tkinter.mainloop()

KeepAliveTmr.cancel()
keep_alive_end = True

print("waiting for KATmr..")
while not KeepAliveTmr.finished:
    pass

pump.disconnect()
exit()
