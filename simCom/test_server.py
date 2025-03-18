
#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

import os
import re
import socket
import struct

from inputimeout import inputimeout
from threading import Thread
from time import sleep


############################     THREADS      ################################


def stt_update() -> None:
    global id
    global x1
    global y1
    global z1
    global rx
    global ry
    global rz
    global ext
    global toggle
    global id_offs

    while toggle:
        if id < 0:
            id = 0
        id_ans = id - id_offs
        try:
            conn.sendall(
                struct.pack(
                    "<fifffffff",
                    99.0,
                    id_ans,
                    x1,
                    y1,
                    z1,
                    rx,
                    ry,
                    rz,
                    ext
                )
            )
        except OSError:
            print("OSError in stt_update, last package lost..")
            toggle = 0
            break
        sleep(0.5)


def usr_input():
    global toggle
    global newline
    global id_offs

    while toggle:
        try:
            ans = inputimeout(prompt="", timeout=8)
        except Exception:
            ans = ""
            print("                                       ", end="\r")

        if ans is None:
            pass
        elif ans == "end":
            print("Bye!")
            os._exit(1)
        elif "Offset:" in ans:
            num = re.findall(r'-?\d+', ans)
            print(num)
            try:
                num = int(num[0])
            except Exception:
                num = None
            if num is not None:
                print("                                       ", end="\r")
            if type(num) == int:
                id_offs = num
                print(f"ID offset set to: {num}\ncommand:")
            else:
                print(f"Invalid number for ID offset: {num}\ncommand:")


#############################     MAIN      #################################

HOST = "localhost"
PORT = 10001
id = 0
x1 = 0
y1 = 0
z1 = 0
rx = 0
ry = 0
rz = 0
ext = 0
id_offs = 0
newline = False

toggle = 1
print("Booting server...")

while toggle:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Listening...\ncommand: ")

        usr_thread = Thread(target=usr_input)
        usr_thread.start()
        conn, addr = s.accept()

        with conn:
            print(f"Connected by {addr}\ncommand: ")

            stt_thread = Thread(target=stt_update)
            stt_thread.start()
            while True:
                data = conn.recv(159)
                if not data:
                    toggle = 0
                    print("Client disconnected...\nWaiting for stt_update...")
                    stt_thread.join()
                    usr_thread.join()
                    break

                id = struct.unpack("<i", data[0:4])[0]

                mt = struct.unpack("c", data[4:5])[0]
                pt = struct.unpack("c", data[5:6])[0]

                x1 = struct.unpack("<f", data[6:10])[0]
                y1 = struct.unpack("<f", data[10:14])[0]
                z1 = struct.unpack("<f", data[14:18])[0]
                rx = struct.unpack("<f", data[18:22])[0]
                ry = struct.unpack("<f", data[22:26])[0]
                rz = struct.unpack("<f", data[26:30])[0]
                q = struct.unpack("<f", data[30:34])[0]
                ext = struct.unpack("<f", data[34:38])[0]

                x2 = struct.unpack("<f", data[38:42])[0]
                y2 = struct.unpack("<f", data[42:46])[0]
                z2 = struct.unpack("<f", data[46:50])[0]
                rx2 = struct.unpack("<f", data[50:54])[0]
                ry2 = struct.unpack("<f", data[54:58])[0]
                rz2 = struct.unpack("<f", data[58:62])[0]
                q2 = struct.unpack("<f", data[62:66])[0]
                ext2 = struct.unpack("<f", data[66:70])[0]

                acr = struct.unpack("<i", data[70:74])[0]
                dcr = struct.unpack("<i", data[74:78])[0]
                ts = struct.unpack("<i", data[78:82])[0]
                ors = struct.unpack("<i", data[82:86])[0]

                t = struct.unpack("<i", data[86:90])[0]

                sc = struct.unpack("c", data[90:91])[0]

                z = struct.unpack("<i", data[91:95])[0]

                trolley_id = struct.unpack("<i", data[95:99])[0]
                trolley_steps = struct.unpack("<i", data[99:103])[0]
                cutter_id = struct.unpack("<i", data[103:107])[0]
                cutter_yn = struct.unpack("<i", data[107:111])[0]
                cut_id = struct.unpack("<i", data[111:115])[0]
                cut_yn = struct.unpack("<i", data[115:119])[0]
                load_spring_id = struct.unpack("<i", data[119:123])[0]
                load_spring_yn = struct.unpack("<i", data[123:127])[0]
                place_spring_id = struct.unpack("<i", data[127:131])[0]
                place_spring_yn = struct.unpack("<i", data[131:135])[0]
                clamp_id = struct.unpack("<i", data[135:139])[0]
                clamp_steps = struct.unpack("<i", data[139:143])[0]
                wait_id = struct.unpack("<i", data[143:147])[0]
                wait_ms = struct.unpack("<i", data[147:151])[0]

                print(
                    f"ID: {id}\nMT: {mt}\nPT: {pt}"
                    f"\nX1: {x1} Y1: {y1} Z1: {z1} "
                    f"Rx: {rx} Ry: {ry} Rz: {rz} Q: {q} "
                    f"Ext: {ext}"
                    f"\nX2: {x2} Y2: {y2} Z2: {z2} "
                    f"Rx2: {rx2} Ry2: {ry2} Rz2: {rz2} Q2: {q2} "
                    f"Ext2: {ext2}"
                    f"\nACR: {acr} DCR: {dcr} TS: {ts} OS: {ors} "
                    f"T: {t} SC: {sc} Z: {z}"
                    f"\nT_ID: {trolley_id} T_ST: {trolley_steps} CUTTER_ID: {cutter_id} "
                    f"CUTTER: {cutter_yn} CU_ID: {cut_id} CU: {cut_yn} "
                    f"LS_ID: {load_spring_id} LS_YN: {load_spring_yn} "
                    f"PS_ID: {place_spring_id} PS_YN: {place_spring_yn} C_ID: {clamp_id} "
                    f"C: {clamp_steps} W_ID: {wait_id} "
                    f"W: {wait_ms}"
                )

    a = input("Connection closed...  Wait for reconnect? Y/N\n")
    if a != "Y":
        print("Exiting...")
        s.close()
    else:
        toggle = 1
        print("Restarting socket...")
