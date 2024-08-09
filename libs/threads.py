#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# python standard libraries
import os
import sys
import copy
import math as m
import requests

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import QObject, QTimer, pyqtSignal

# import my own libs
import libs.data_utilities as du
import libs.func_utilities as fu
import libs.pump_utilities as pu
from libs.win_mainframe_prearrange import GlobalMutex



##########################     PUMP WORKER      ##############################

class PumpCommWorker(QObject):
    """manages data updates and keepalive commands to pump"""

    # naming conventions in PyQT are different,
    # for the signals I will stick with mixedCase
    p1Active = pyqtSignal()
    p2Active = pyqtSignal()
    dataRecv = pyqtSignal(du.PumpTelemetry, str)
    dataMixerRecv = pyqtSignal(int)
    dataSend = pyqtSignal(int, str, int, str)
    dataMixerSend = pyqtSignal(float)
    logEntry = pyqtSignal(str, str)


    def run(self) -> None:
        """start timer with standard operation on timeout,
        connect to pump via M-Tec Interface"""

        self.LoopTimer = QTimer()
        self.LoopTimer.setInterval(250)
        self.LoopTimer.timeout.connect(self.active_state)
        self.LoopTimer.start()

        self.logEntry.emit('THRT','PumpComm thread running.')


    def stop(self) -> None:
        """stop loop"""

        self.LoopTimer.stop()
        self.LoopTimer.deleteLater()
    
    def active_state(self):
        """extra function needed to set global indicator 'PMP_comm_active'
        with is checked in win_mainframe.disconnect_tcp"""

        GlobalMutex.lock()
        du.PMP_comm_active = True
        GlobalMutex.unlock()

        self.send()
        self.receive()
        
        GlobalMutex.lock()
        du.PMP_comm_active = False
        GlobalMutex.unlock()

    def send(self) -> None:
        """send pump speed to pump, uses modified setter in mtec's script 
        (changed to function), which recognizes a value change and returns
        the machines answer and the original command string, uses user-set
        pump speed if no script is running
        """

        # SEND TO PUMPS
        pump_speed = pu.calc_speed() if (du.SC_q_processing) else du.PMP_speed

        # get speed
        if du.PMP1Serial.connected and du.PMP2Serial.connected:
            pump_speed *= 2
            pump1_speed = pump_speed * du.PMP_output_ratio
            pump2_speed = pump_speed * (1 - du.PMP_output_ratio)
        else:
            pump1_speed = pump2_speed = pump_speed

        # look for user overwrite, no mutex, as changing 
        # global PUMP_user_speed would not harm the process
        for du_user_speed, calc_speed in [
                ('PMP1_user_speed', 'pump1_speed'),
                ('PMP2_user_speed', 'pump2_speed'),
        ]:
            user_speed = getattr(du, du_user_speed)
            if user_speed != -999:
                locals()[calc_speed] = user_speed
                setattr(du, du_user_speed, -999)
        
        # send to P1 and P2 & keepAlive both
        for serial, speed, live_ad, speed_global, p_num in [
                (du.PMP1Serial, pump1_speed, 'PMP1_live_ad', 'PMP1_speed', 'P1'),
                (du.PMP2Serial, pump2_speed, 'PMP2_live_ad', 'PMP2_speed', 'P2'),
        ]:
            if serial.connected and speed is not None:
                res = serial.set_speed(int(speed * getattr(du, live_ad)))
                
                if res is not None:
                    GlobalMutex.lock()
                    setattr(du, speed_global, speed)
                    GlobalMutex.unlock()
                    print(f"{p_num}: {speed}")
                    self.dataSend.emit(speed, res[0], res[1], p_num)

                serial.keepAlive()

        # SEND TO MIXER
        if du.MIX_connected and du.MIX_last_speed != du.MIX_speed:
            if du.MIX_act_with_pump:
                mixer_speed = pump_speed * du.MIX_max_speed / 100.0
            else:
                mixer_speed = du.MIX_speed
            
            ip = du.DEF_TCP_MIXER['IP']
            port = du.DEF_TCP_MIXER['PORT']
            post_url = f"http://{ip}:{port}/motor"
            post_resp = requests.post(post_url, data=f"{mixer_speed}")

            if post_resp.ok and post_resp.text == f"RECV{mixer_speed}":
                GlobalMutex.lock()
                du.MIX_last_speed = mixer_speed
                GlobalMutex.unlock()
                print(f"MIX: {mixer_speed}")
                self.dataMixerSend.emit(mixer_speed)
            

            


    def receive(self) -> None:
        """request data updates for frequency, voltage, current and torque
        from pump, pass to mainframe
        """

        # for serial,dummy in [(du.PMP1Serial, None),(du.PMP2Serial, None)]:
        #     if serial.connected:
        #         print(f"P2 freq: {serial.frequency}")

        # RECEIVE FROM PUMPS:
        for serial, last_telem, speed_global, stt_attr, p_num in [
                (du.PMP1Serial, 'PMP1LastTelem', 'PMP1_speed', 'Pump1', 'P1'),
                (du.PMP2Serial, 'PMP2LastTelem', 'PMP2_speed', 'Pump2', 'P2'),
        ]:
            if serial.connected:
                freq = serial.frequency
                volt = serial.voltage
                amps = serial.current
                torq = serial.torque

                if None in [freq, volt, amps, torq]:
                    self.logEntry.emit(
                        'PTel',
                        f"{p_num} telemetry package broken or not received, "
                        f"connection probably lost!"
                    )
                else:
                    Telem = du.PumpTelemetry(freq, volt, amps, torq)
                    Telem = round(Telem, 3)
                    if p_num == 'P1': self.p1Active.emit()
                    elif p_num == 'P2': self.p2Active.emit()

                    # telemetry contains no info about the rotation direction,
                    # interpret according to settings
                    if getattr(du, speed_global) < 0:
                        Telem.freq *= -1

                    if Telem != getattr(du, last_telem):
                        GlobalMutex.lock()
                        setattr(du, last_telem, Telem)
                        setattr(du.STTDataBlock, stt_attr, Telem)
                        GlobalMutex.unlock()
                        self.dataRecv.emit(Telem, p_num)

        # RECEIVE FROM MIXER
        if du.MIX_connected:
            pass # to-do



##########################     ROBO WORKER      ##############################

class RoboCommWorker(QObject):
    """a worker object that check every 50 ms if the Robot queue has empty 
    slots (according to ROBO_comm_forerun), emits signal to send data if so,
    beforehand checks the TCPIP connection every 50 ms and writes the result
    to global vars
    """

    dataReceived = pyqtSignal()
    dataUpdated = pyqtSignal(str, du.RoboTelemetry)
    endDcMoving = pyqtSignal()
    endProcessing = pyqtSignal()
    logEntry = pyqtSignal(str, str)
    queueEmtpy = pyqtSignal()
    # sendElem contains object as third parameter,
    # however this will be either int or Exception type
    sendElem = pyqtSignal(du.QEntry, bool, object, bool)


    def run(self) -> None:
        """start timer, receive and send on timeout"""

        self.CommTimer = QTimer()
        self.CommTimer.setInterval(10)
        self.CommTimer.timeout.connect(self.receive)
        self.CommTimer.timeout.connect(self.send)
        self.CommTimer.start()

        self.CheckTimer = QTimer()
        self.CheckTimer.setInterval(200)
        self.CheckTimer.timeout.connect(self.check_queue)
        self.CheckTimer.start()

        self.logEntry.emit('THRT','RoboComm thread running.')


    def stop(self) -> None:
        """stop loop"""

        self.CommTimer.stop()
        self.CommTimer.deleteLater()

        self.CheckTimer.stop()
        self.CheckTimer.deleteLater()


    def receive(self) -> None:
        """receive 36-byte data block, write to ROB vars"""

        Telem, raw_data = du.ROBTcp.receive()
        if not isinstance(Telem, Exception):
            Telem = round(Telem, 1)
            self.dataReceived.emit()

            GlobalMutex.lock()
            fu.add_to_comm_protocol(
                f"RECV:    ID {Telem.id},   {Telem.Coor}   "
                f"TCP: {Telem.t_speed}"
            )

            # check for ID overflow, reduce SC_queue IDs 
            if Telem.id < du.ROBLastTelem.id:
                for x in du.SCQueue:
                    x.id -= 3000
                # and clear ROBCommQueue entries with IDs near 3000
                try:
                    while du.ROBCommQueue[0].id > Telem.id:
                        du.ROBCommQueue.pop_first_item()
                except Exception:
                    pass

            # delete all finished commands from ROB_commQueue
            try:
                while du.ROBCommQueue[0].id < Telem.id:
                    du.ROBCommQueue.pop_first_item()
            except AttributeError:
                pass

            # refresh data only if new
            if Telem != du.ROBLastTelem:
                # check if robot is processing a new command
                # (length check to skip in first loop)
                if (Telem.id != du.ROBLastTelem.id) and (len(du.ROBCommQueue) > 0):
                    du.ROBMovStartP = du.ROBMovEndP
                    du.ROBMovEndP = copy.deepcopy(du.ROBCommQueue[0].Coor1)

                # set new values to globals
                du.ROBTelem = copy.deepcopy(Telem)
                du.ROBLastTelem = copy.deepcopy(Telem)

                # prep database entry
                STTEntry = copy.deepcopy(Telem)
                STTEntry.Coor -= du.DCCurrZero
                du.STTDataBlock.Robo = copy.deepcopy(STTEntry) 
                self.dataUpdated.emit(str(raw_data), Telem)
                
                # print
                print(f"RECV:    {Telem}")
            GlobalMutex.unlock()

            # reset robMoving indicator if near end, skip if queue is processed
            if du.DC_rob_moving and not du.SC_q_processing:
                check_dist = self.check_zero_dist()
                if check_dist is not None:
                    if check_dist < 1:
                        self.endDcMoving.emit()

        # inform user if error occured in websocket connection (ignore timeouts)
        elif (
                not isinstance(Telem, TimeoutError)
                and not isinstance(Telem, WindowsError)
        ):
            err_txt = f"ERROR from ROBTcp ({Telem}), raw data: {raw_data}"
            self.logEntry.emit('RTel', err_txt)
            GlobalMutex.lock()
            fu.add_to_comm_protocol(f"RECV:    {err_txt}")
            GlobalMutex.unlock()


    def check_queue(self) -> None:
        """add queue element to sendList if qProcessing and robot queue has
        space
        """

        len_sc = len(du.SCQueue)
        len_rob = len(du.ROBCommQueue)
        rob_id = du.ROBTelem.id

        # if qProcessing is ending, define end as being in 1mm range of
        # the last robtarget
        if du.SC_q_prep_end:
            check_dist = self.check_zero_dist()
            if check_dist is not None:
                if check_dist < 1:
                    self.endProcessing.emit()

        # if qProcessing is active and not ending, pop first queue item if
        # robot is nearer than ROB_commFr; if no entries in SC_queue left,
        # end qProcessing (immediately if ROB_commQueue is empty as well)
        elif du.SC_q_processing:
            if len_sc > 0:
                GlobalMutex.lock()
                try:
                    while (rob_id + du.ROB_comm_fr) >= du.SCQueue[0].id:
                        comm_tuple = (du.SCQueue.pop_first_item(), False)
                        du.ROB_send_list.append(comm_tuple)
                except AttributeError:
                    pass
                GlobalMutex.unlock()

            else:
                if len_rob == 0:
                    self.endProcessing.emit()
                else:
                    self.queueEmtpy.emit()


    def send(self, testrun=False) -> None:
        """iterate over ROB_send_list entries and send one by one,
        check if sending was successful each time
        """

        num_send = 0

        # send commands until send_list is empty
        while len(du.ROB_send_list) > 0:
            comm_tuple = du.ROB_send_list.pop(0)
            Command = comm_tuple[0]
            direct_ctrl = comm_tuple[1]

            # check for type, ID overflow & live adjustments to tcp speed
            if not isinstance(Command, du.QEntry):
                err = ValueError(f"{Command} is not an instance of QEntry!")
                self.sendElem.emit(Command, False, err, direct_ctrl)
                print(f"send error: {err}")
                break
            Command.Speed.ts = int(Command.Speed.ts * du.ROB_live_ad)
            while Command.id > 3000:
                Command.id -= 3000

            # if testrun, skip actually sending the message
            if testrun:
                res, msg_len = True, 159
            else:
                res, msg_len = du.ROBTcp.send(Command)

            # see if sending was successful
            if res:
                GlobalMutex.lock()
                num_send += 1
                du.ROBCommQueue.append(Command)
                fu.add_to_comm_protocol(
                    f"SEND:    ID: {Command.id}  MT: {Command.mt}  PT: {Command.pt} "
                    f"\t|| COOR_1: {Command.Coor1}"
                    f"\n\t\t\t|| COOR_2: {Command.Coor2}"
                    f"\n\t\t\t|| SV:     {Command.Speed} \t|| SBT: {Command.sbt}   "
                    f"SC: {Command.sc}   Z: {Command.z}"
                    f"\n\t\t\t|| TOOL:   {Command.Tool}"
                )
                if direct_ctrl:
                    du.SCQueue.increment()
                GlobalMutex.unlock()

                self.logEntry.emit('ROBO', f"send: {Command}")

            else:
                print(f" Message Error: {msg_len}")
                self.sendElem.emit(Command, False, msg_len, direct_ctrl)
        
            # inform mainframe if command block was send successfully 
            if len(du.ROB_send_list) == 0:
                self.sendElem.emit(Command, res, num_send, direct_ctrl)


    def check_zero_dist(self) -> float | None:
        """calculates distance between next entry in ROB_commQueue and current
        position; calculates 4 dimensional only to account for external axis
        movement (0,0,0,1) 
        """

        if len(du.ROBCommQueue) == 1:
            return m.sqrt(
                m.pow(du.ROBCommQueue[0].Coor1.x - du.ROBTelem.Coor.x, 2)
                + m.pow(du.ROBCommQueue[0].Coor1.y - du.ROBTelem.Coor.y, 2)
                + m.pow(du.ROBCommQueue[0].Coor1.z - du.ROBTelem.Coor.z, 2)
                + m.pow(du.ROBCommQueue[0].Coor1.ext - du.ROBTelem.Coor.ext, 2)
            )
        else:
            return None



#########################     SENSOR WORKER      #############################

class SensorCommWorker(QObject):
    """cycle through all sensors, collect the data"""

    cycleDone = pyqtSignal()
    dataReceived = pyqtSignal(str)
    logEntry = pyqtSignal(str, str)

    _conn_error = False

    def run(self) -> None:
        """start cycling through the sensors"""

        self.CycleTimer = QTimer()
        self.CycleTimer.setInterval(1000)
        self.CycleTimer.timeout.connect(self.cycle)
        self.CycleTimer.start()

        self.logEntry.emit('THRT','SensorComm thread running.')


    def stop(self) -> None:
        """stop cycling"""

        self.CycleTimer.stop()
        self.CycleTimer.deleteLater()


    def cycle(self) -> None:
        """check every sensor once"""

        def loc_request(loc:dict, key:str) -> None:
            """runs sub-cycle for single location, sends data to
            fu.store_sensor_data while its at it
            """

            for sub_key in loc:
                if sub_key == 'ip' or sub_key == 'err': 
                    continue
                
                if loc[sub_key]: # only check true-marked sensors
                    data = fu.sensor_req(loc["ip"], sub_key)
                    
                    if isinstance(data, list):
                        # to-do: write handling for legacy data
                        self.dataReceived.emit(loc['ip'])
                        # extract tuple from list: (val, uptime)
                        # newest entry is at the end of the list
                        latest_data = data[len(data) - 1]
                        loc['err'] = False

                        GlobalMutex.lock()
                        fu.store_sensor_data(latest_data, key, sub_key)
                        GlobalMutex.unlock()

                    elif data is not None:
                        # log recurring error from one location only once
                        if loc['err'] == False:
                            loc['err'] = True
                            self.logEntry.emit(
                                'SENS',
                                f"request error from {loc['ip']}: {data}"
                            )
                            self.logEntry.emit(
                                'SENS',
                                f"trying to reconnect to {loc['ip']}.."
                            )
            
            return None

        # main cycle
        for key in du.SEN_dict:
            loc_request(du.SEN_dict[key], key)

        self.cycleDone.emit()



###########################     LF WORKER      ###############################

class LoadFileWorker(QObject):
    """worker converts .gcode or .mod into QEntries, outsourced to worker as
    these files can have more than 10000 lines"""

    convFinished = pyqtSignal(int, int, int)
    convFailed = pyqtSignal(str)
    _CommList = du.Queue()


    def run(self, testrun=False) -> None:
        """get data, start conversion loop"""

        global lfw_file_path
        global lfw_line_id
        global lfw_ext_trail
        global lfw_p_ctrl
        global lfw_running
        global lfw_pre_run_time

        lfw_running = True
        line_id = lfw_line_id
        file_path = lfw_file_path
        if file_path is None:
            self.convFailed.emit("No filepath given!")
            lfw_running = False
            return

        file = open(file_path, "r")
        txt = file.read()
        file.close()

        # init vars
        self._CommList.clear()
        rows = txt.split("\n")
        skips = 0
        start_id = line_id

        # iterate over file rows
        if not testrun:
            print(f"streaming file: {file_path}")

        if file_path.suffix == ".gcode":
            for row in rows:
                Entry, command = self.gcode_conv(id=line_id, txt=row)

                if isinstance(Entry, Exception):
                    self.convFailed.emit(f"VALUE ERROR: {command}")
                    lfw_running = False
                    return
                if (command == "G92") or (command == ";") or (command == ''):
                    skips += 1
                elif (command == "G1") or (command == "G28"):
                    line_id += 1
                else:
                    self.convFailed.emit(f"{command}!, ABORTED")
                    lfw_running = False
                    return

        else:
            for row in rows:
                Entry = self.rapid_conv(id=line_id, txt=row)

                if isinstance(Entry, Exception):
                    self.convFailed.emit(f"ERROR: {Entry}")
                    lfw_running = False
                    return
                elif Entry is None:
                    skips += 1
                else:
                    line_id += 1

        if len(self._CommList) == 0:
            self.convFailed.emit("No commands found!")
            lfw_running = False
            return

        # check for unidistance mode
        # um_check = fu.re_short("\&\&: \d+.\d+", txt, None, "\&\&: \d+")
        # if um_check is not None:
        #     um_dist = fu.re_short("\d+.\d+", um_check, ValueError, "\d+")
        #     um_conv_res = self.add_um_tool(um_dist)
        #     if um_conv_res is not None:
        #         self.convFailed.emit(um_conv_res)
        #         lfw_running = False
        #         return

        # automatic pump control
        if lfw_p_ctrl and (len(self._CommList) > 0):

            # set all entries to pmode=default
            for Entry in self._CommList:
                Entry.p_mode = "default"

            # add a startvector with a speed of 1mm/s with pMode=start
            # (so X seconds of approach if length is X mm (lfw_pre_run_time))
            StartVector = copy.deepcopy(self._CommList[0])
            StartVector.id = start_id
            StartVector.Coor1.x += lfw_pre_run_time
            StartVector.Coor1.y += lfw_pre_run_time
            StartVector.p_mode = "start"
            StartVector.Speed = du.SpeedVector(acr=1, dcr=1, ts=1, ors=1)
            self._CommList.add(StartVector, thread_call=True)

            # set the last entry to pMode=end
            self._CommList[len(self._CommList) - 1].p_mode = "end"

        du.SCQueue.add_queue(self._CommList)
        self.convFinished.emit(line_id, start_id, skips)
        lfw_running = False


    def gcode_conv(
            self,
            id:int,
            txt:str
    ) -> (
        tuple[du.QEntry | None | ValueError, str]
    ):
        """single line conversion from GCode"""

        # get text and position BEFORE PLANNED COMMAND EXECUTION
        Speed = copy.deepcopy(du.PRINSpeed)
        try:
            if len(self._CommList) == 0:
                Pos = copy.deepcopy(du.SCQueue.entry_before_id(id).Coor1)
            else:
                Pos = copy.deepcopy(self._CommList.last_entry().Coor1)
        except AttributeError:
            Pos = du.DCCurrZero

        # act according to GCode command
        Entry, command = fu.gcode_to_qentry(Pos, Speed, du.IO_zone, txt, lfw_ext_trail)

        if (command != "G1") and (command != "G28"):
            return Entry, command

        Entry.id = id
        res = self._CommList.add(Entry, thread_call=True)

        if res == ValueError:
            return ValueError, ''

        return Entry, command


    def rapid_conv(self, id:int, txt:str) -> du.QEntry | None | Exception:
        """single line conversion from RAPID"""

        Entry = fu.rapid_to_qentry(txt)
        if isinstance(Entry, Exception) or Entry is None:
            return Entry

        Entry.id = id
        res = self._CommList.add(Entry, thread_call=True)

        if res == ValueError:
            return ValueError

        return Entry


    # def add_um_tool(self, umd:float):
    #     """check if the data makes send, add the tooldata to entries"""

    #     try:
    #         um_dist = float(umd)
    #     except Exception:
    #         return f"UM-Mode failed reading {umd}"

    #     if um_dist < 0.0 or um_dist > 2000.0:
    #         return f"UM-Distance <0 or >2000"

    #     for Entry in self._CommList:
    #         travel_time = um_dist / Entry.Speed.ts
    #         if (um_dist % Entry.Speed.ts) != 0:
    #             return f"UM-Mode failed setting {travel_time} to int."

    #         Entry.sc = "T"
    #         Entry.sbt = int(travel_time)
    #         Entry.Tool.time_time = int(travel_time)
    #     return None



##############################     MAIN      #################################

# LoadFileWorker:
lfw_file_path = None
lfw_line_id = 0
lfw_ext_trail = True
lfw_p_ctrl = False
lfw_running = False
lfw_pre_run_time = 10
