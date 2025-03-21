
#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

import os
import re
import sys
import socket
import struct

from inputimeout import inputimeout
from threading import Thread
from time import sleep

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import my own libs
import libs.data_utilities as du


############################     THREADS      ################################


def stt_update() -> None:
    global LastComm
    global CommandList
    global toggle
    global id_offs
    global instant
    global reply_repetitions

    curr_rr = 0
    while toggle:
        # generate reply
        reply = du.RoboTelemetry(t_speed=99.0, id=0)
        if instant:
            while len(CommandList) > 1:
                CommandList.pop_first_item()
            CurrComm = CommandList[0]
            reply.id = CurrComm.id
            reply.Coor.x = CurrComm.Coor1.x
            reply.Coor.y = CurrComm.Coor1.y
            reply.Coor.z = CurrComm.Coor1.z
            reply.Coor.rx = CurrComm.Coor1.rx
            reply.Coor.ry = CurrComm.Coor1.ry
            reply.Coor.rz = CurrComm.Coor1.rz
            reply.Coor.ext = CurrComm.Coor1.ext
        else:
            comm_num = len(CommandList)
            curr_rr += 1
            # reply every command multiple times (reply repetitions)
            if curr_rr > reply_repetitions:
                curr_rr = 0
                if comm_num > 1:
                    # keep the command if its the last one
                    # otherwise overwrite LasComm
                    LastComm = CommandList.pop_first_item()
                else:
                    curr_rr = reply_repetitions
            # simulate movement
            NextComm = CommandList[0]
            MovementVector = NextComm.Coor1 - LastComm.Coor1
            perc_to_do = (reply_repetitions-curr_rr) / reply_repetitions
            reply.id = NextComm.id
            reply.Coor.x = NextComm.Coor1.x - (MovementVector.x * perc_to_do)
            reply.Coor.y = NextComm.Coor1.y - (MovementVector.y * perc_to_do)
            reply.Coor.z = NextComm.Coor1.z - (MovementVector.z * perc_to_do)
            reply.Coor.rx = NextComm.Coor1.rx - (MovementVector.rx * perc_to_do)
            reply.Coor.ry = NextComm.Coor1.ry - (MovementVector.ry * perc_to_do)
            reply.Coor.rz = NextComm.Coor1.rz - (MovementVector.rz * perc_to_do)
            reply.Coor.ext = NextComm.Coor1.ext - (MovementVector.ext * perc_to_do)
        # send reply
        try:
            reply_packed = struct.pack(
                "<fifffffff",
                reply.t_speed,
                reply.id,
                reply.Coor.x,
                reply.Coor.y,
                reply.Coor.z,
                reply.Coor.rx,
                reply.Coor.ry,
                reply.Coor.rz,
                reply.Coor.ext,
            )
            conn.sendall(reply_packed)
        except:
            print("OSError in stt_update, last package lost..")
            toggle = 0
            break
        sleep(0.5)


def usr_input():
    global toggle
    global newline
    global id_offs
    global instant
    global reply_repetitions

    while toggle:
        try:
            ans = inputimeout(prompt='')
        except Exception:
            print('                                              ', end="\r")
            print('command: ', end='')
            continue

        if ans == 'end':
            print('Bye!')
            os._exit(1)
        elif ans == 'instant':
            instant = not instant
            print(f"instant: {instant}\ncommand: ", end='')
        elif 'offset' in ans:
            try:
                num = re.findall(r'-?\d+', ans)
                id_offs = int(num[0])
                print(f"ID offset set to: {id_offs}\ncommand: ", end='')
            except:
                print(f"{num} not convertable to int!\ncommand: ", end='')
        elif 'delay' in ans:
            try:
                num = re.findall(r'\d+[,\.]?[\d+]?', ans)
                reply_repetitions = int(num[0])
                print(
                    f"Repetitions set to: {reply_repetitions}\ncommand: ",
                    end='',
                )
            except:
                print(f"{num} not convertable to int!\ncommand: ", end='')
        


#############################     MAIN      #################################

HOST = "localhost"
PORT = 10001
id_offs = 0
reply_repetitions = 4
instant = False
newline = False
LastComm = du.QEntry(id=42)
CommandList = du.Queue()
# at empty entry to simulate last robot state
CommandList.add(LastComm, thread_call=True)

toggle = 1
print("Booting server...")

while toggle:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Listening...\ncommand: ", end='')

        usr_thread = Thread(target=usr_input)
        usr_thread.start()
        conn, addr = s.accept()

        with conn:
            print(f"Connected by {addr}\ncommand: ", end='')

            stt_thread = Thread(target=stt_update)
            stt_thread.start()
            while True:
                data = conn.recv(151)
                if not data:
                    toggle = 0
                    print("Client disconnected...\nWaiting for stt_update...")
                    stt_thread.join()
                    usr_thread.join()
                    break
                
                RecvEntry = du.QEntry()
                RecvEntry.id = struct.unpack("<i", data[0:4])[0]
                RecvEntry.mt = struct.unpack("c", data[4:5])[0]
                RecvEntry.pt = struct.unpack("c", data[5:6])[0]
                RecvEntry.Coor1.x = struct.unpack("<f", data[6:10])[0]
                RecvEntry.Coor1.y = struct.unpack("<f", data[10:14])[0]
                RecvEntry.Coor1.z = struct.unpack("<f", data[14:18])[0]
                RecvEntry.Coor1.rx = struct.unpack("<f", data[18:22])[0]
                RecvEntry.Coor1.ry = struct.unpack("<f", data[22:26])[0]
                RecvEntry.Coor1.rz = struct.unpack("<f", data[26:30])[0]
                RecvEntry.Coor1.q = struct.unpack("<f", data[30:34])[0]
                RecvEntry.Coor1.ext = struct.unpack("<f", data[34:38])[0]
                RecvEntry.Coor2.x = struct.unpack("<f", data[38:42])[0]
                RecvEntry.Coor2.y = struct.unpack("<f", data[42:46])[0]
                RecvEntry.Coor2.z = struct.unpack("<f", data[46:50])[0]
                RecvEntry.Coor2.rx = struct.unpack("<f", data[50:54])[0]
                RecvEntry.Coor2.ry = struct.unpack("<f", data[54:58])[0]
                RecvEntry.Coor2.rz = struct.unpack("<f", data[58:62])[0]
                RecvEntry.Coor2.q = struct.unpack("<f", data[62:66])[0]
                RecvEntry.Coor2.ext = struct.unpack("<f", data[66:70])[0]
                RecvEntry.Speed.acr = struct.unpack("<i", data[70:74])[0]
                RecvEntry.Speed.dcr = struct.unpack("<i", data[74:78])[0]
                RecvEntry.Speed.ts = struct.unpack("<i", data[78:82])[0]
                RecvEntry.Speed.ors = struct.unpack("<i", data[82:86])[0]
                RecvEntry.Speed.t = struct.unpack("<i", data[86:90])[0]
                RecvEntry.sc = struct.unpack("c", data[90:91])[0]
                RecvEntry.z = struct.unpack("<i", data[91:95])[0]
                troll_id = struct.unpack("<i", data[95:99])[0]
                RecvEntry.Tool.trolley_steps = struct.unpack("<i", data[99:103])[0]
                cutter_id = struct.unpack("<i", data[103:107])[0]
                cutter = struct.unpack("<i", data[107:111])[0]
                cut_id = struct.unpack("<i", data[111:115])[0]
                cut = struct.unpack("<i", data[115:119])[0]
                ls_id = struct.unpack("<i", data[119:123])[0]
                RecvEntry.Tool.load_spring = struct.unpack("<i", data[123:127])[0]
                ps_id = struct.unpack("<i", data[127:131])[0]
                RecvEntry.Tool.place_spring = struct.unpack("<i", data[131:135])[0]
                clamp_id = struct.unpack("<i", data[135:139])[0]
                RecvEntry.Tool.clamp = struct.unpack("<i", data[139:143])[0]
                wait_id = struct.unpack("<i", data[143:147])[0]
                RecvEntry.Tool.wait = struct.unpack("<i", data[147:151])[0]

                print(
                    f"received:\n{RecvEntry}\n"
                    f"additional: {troll_id}, {cutter_id}/{cutter}, "
                    f"{cut_id}/{cut}, {ls_id}, {ps_id}, {clamp_id}, {wait_id}\n"
                )
                print('command: ', end='')
                if CommandList[0].id > RecvEntry.id:
                    CommandList.clear()
                CommandList.add(RecvEntry)

    a = input("Connection closed...  Wait for reconnect? Y/N\n")
    if a != "Y":
        print("Exiting...")
        s.close()
    else:
        toggle = 1
        print("Restarting socket...")
