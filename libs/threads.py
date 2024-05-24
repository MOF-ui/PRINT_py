#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


####################################################   IMPORTS  ####################################################

# python standard libraries
import os
import sys
import copy
import math as m

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import QObject, QTimer, QMutex, pyqtSignal

# import my own libs
import libs.data_utilities as du
import libs.func_utilities as fu
import libs.pump_utilities as pu



####################################################   WORKER   ####################################################

class PumpCommWorker(QObject):
    """manages data updates and keepalive commands to pump"""

    # naming conventions in PyQT are different,
    # for the signals I will stick with mixedCase
    connActive = pyqtSignal(str)
    dataRecv = pyqtSignal(du.PumpTelemetry, str)
    dataMixerRecv = pyqtSignal(int)
    dataSend = pyqtSignal(int, str, int, str)
    dataMixerSend = pyqtSignal(int, bool, int)
    logError = pyqtSignal(str, str)


    def run(self):
        """start timer with standard operation on timeout,
        connect to pump via M-Tec Interface"""

        self.LoopTimer = QTimer()
        self.LoopTimer.setInterval(250)
        self.LoopTimer.timeout.connect(self.send)
        self.LoopTimer.timeout.connect(self.receive)
        self.LoopTimer.start()


    def stop(self):
        """stop loop"""

        self.LoopTimer.stop()
        self.LoopTimer.deleteLater()


    def send(self):
        """send pump speed to pump, uses modified setter in mtec's script (changed to function),
        which recognizes a value change and returns the machines answer and the original command string,
        uses user-set pump speed if no script is running"""
        global PCW_lastMixerSpeed

        # SEND TO PUMPS
        pump_speed = pu.calc_speed() if (du.SC_q_processing) else du.PMP_speed

        # get speed
        if du.PMP1Serial.connected and du.PMP2Serial.connected:
            pump_speed *= 2
            pump1_speed = pump_speed * du.PMP_output_ratio
            pump2_speed = pump_speed * (1 - du.PMP_output_ratio)
        else:
            pump1_speed = pump2_speed = pump_speed

        # look for user overwrite, no mutex, as changing global PUMP_userSpeed would not harm the process
        if du.PMP1_user_speed != -999:
            pump1_speed = du.PMP1_user_speed
            du.PMP1_user_speed = -999
        if du.PMP2_user_speed != -999:
            pump2_speed = du.PMP2_user_speed
            du.PMP2_user_speed = -999

        # send to P1 and P2 & keepAlive both
        if du.PMP1Serial.connected and (pump1_speed is not None):
            res = du.PMP1Serial.set_speed(int(pump1_speed * du.PMP1_live_ad))

            if res is not None:
                Mutex.lock()
                du.PMP1_speed = pump1_speed
                Mutex.unlock()
                print(f"P1: {pump1_speed}")
                self.dataSend.emit(pump1_speed, res[0], res[1], "P1")

            du.PMP1Serial.keepAlive()

        if du.PMP2Serial.connected and (pump2_speed is not None):
            res = du.PMP2Serial.set_speed(int(pump2_speed * du.PMP2_live_ad))

            if res is not None:
                Mutex.lock()
                du.PMP2_speed = pump2_speed
                Mutex.unlock()
                print(f"P2: {pump2_speed}")
                self.dataSend.emit(pump2_speed, res[0], res[1], "P2")

            du.PMP2Serial.keepAlive()

        # send to mixer
        if du.MIXTcp._connected:
            mixer_speed = pump_speed if (du.MIX_act_with_pump) else du.MIX_speed

            if mixer_speed != PCW_lastMixerSpeed:
                res, data_len = du.MIXTcp.send(int(mixer_speed))
                if res:
                    PCW_lastMixerSpeed = mixer_speed
                    self.dataMixerSend.emit(mixer_speed, res, data_len)
                else:
                    self.logError.emit(
                        "CONN", f"MIXER - sending data failed ({data_len})"
                    )


    def receive(self):
        """request data updates for frequency, voltage, current and torque from pump, pass to mainframe"""

        # RECEIVE FROM PUMPS, first P1:
        if du.PMP1Serial.connected:
            freq = du.PMP1Serial.frequency
            volt = du.PMP1Serial.voltage
            amps = du.PMP1Serial.current
            torq = du.PMP1Serial.torque

            if None in [freq, volt, amps, torq]:
                self.logError.emit(
                    "PTel", "Pump1 telemetry package broken or not received..."
                )

            else:
                Telem = du.PumpTelemetry(freq, volt, amps, torq)
                Telem = round(Telem, 3)
                self.connActive.emit("P1")

                # telemetry contains no info about the rotation direction, interpret according to settings
                if du.PMP1_speed < 0:
                    Telem.freq *= -1

                if Telem != du.PMP1LastTelem:
                    Mutex.lock()
                    du.PMP1LastTelem = Telem
                    du.STTDataBlock.Pump1 = Telem
                    Mutex.unlock()
                    self.dataRecv.emit(Telem, "P1")

        # P2
        if du.PMP2Serial.connected:
            freq = du.PMP2Serial.frequency
            volt = du.PMP2Serial.voltage
            amps = du.PMP2Serial.current
            torq = du.PMP2Serial.torque

            if None in [freq, volt, amps, torq]:
                self.logError.emit(
                    "PTel", "Pump2 telemetry package broken or not received..."
                )

            else:
                Telem = du.PumpTelemetry(freq, volt, amps, torq)
                Telem = round(Telem, 3)
                self.connActive.emit("P2")

                # telemetry contains no info about the rotation direction, interpret according to settings
                if du.PMP2_speed < 0:
                    Telem.freq *= -1

                if Telem != du.PMP2LastTelem:
                    Mutex.lock()
                    du.PMP2LastTelem = Telem
                    du.STTDataBlock.Pump2 = Telem
                    Mutex.unlock()
                    self.dataRecv.emit(Telem, "P2")

        # RECEIVE FROM MIXER
        if du.MIXTcp._connected:
            res, data = du.MIXTcp.receive()
            if res:
                self.connActive.emit("MIX")

                if data != du.MIX_last_speed:
                    Mutex.lock()
                    du.MIX_last_speed = data
                    du.STTDataBlock.k_pump_freq = data
                    Mutex.unlock()

                    self.dataMixerRecv.emit(data)

            else:
                self.logError.emit("MTel", f"MIXER - receiving data failed ({data})")



class RoboCommWorker(QObject):
    """a worker object that check every 50 ms if the Robot queue has empty slots (according to ROBO_comm_forerun),
    emits signal to send data if so, beforehand
    checks the TCPIP connection every 50 ms and writes the result to global vars"""

    commLost = pyqtSignal(int)
    dataReceived = pyqtSignal()
    dataUpdated = pyqtSignal(str, du.RoboTelemetry)
    endDcMoving = pyqtSignal()
    endProcessing = pyqtSignal()
    logError = pyqtSignal(str, str)
    queueEmtpy = pyqtSignal()
    sendElem = pyqtSignal(du.QEntry, object, int, bool, bool)

    transmitting = False


    def run(self):
        """start timer, receive and send on timeout"""

        self.StatusCheckTimer = QTimer()
        self.StatusCheckTimer.setInterval(10)
        self.StatusCheckTimer.timeout.connect(self.check_new_status)
        self.StatusCheckTimer.start()

        self.CommTimer = QTimer()
        self.CommTimer.setInterval(10)
        self.CommTimer.timeout.connect(self.receive)
        self.CommTimer.timeout.connect(self.send)

        self.CheckTimer = QTimer()
        self.CheckTimer.setInterval(200)
        self.CheckTimer.timeout.connect(self.check_queue)


    def stop(self):
        """stop loop"""

        self.CommTimer.stop()
        self.CommTimer.deleteLater()

        self.CheckTimer.stop()
        self.CheckTimer.deleteLater()

        self.StatusCheckTimer.stop()
        self.StatusCheckTimer.deleteLater()


    def check_new_status(self):
        """change connection status if requested, request via permanent check of global variable as I'm unwilling
        to program a custom QThread class with the according slot and also havent figured out another way yet
        """
        global rcw_new_status

        if rcw_new_status == self.transmitting:
            return

        if rcw_new_status:
            self.CommTimer.start()
            self.CheckTimer.start()
            self.transmitting = True
        else:
            self.CommTimer.stop()
            self.CheckTimer.stop()
            self.transmitting = False
            if len(du.ROB_send_list) != 0:
                self.commLost.emit(len(du.ROB_send_list))


    def receive(self):
        """receive 36-byte data block, write to ROB vars"""

        Telem, raw_data = du.ROBTcp.receive()

        if raw_data != None:
            if Telem is not None:
                Telem = round(Telem, 1)
            self.dataReceived.emit()

            Mutex.lock()
            fu.add_to_comm_protocol(
                f"RECV:    ID {Telem.id},   {Telem.Coor}   TCP: {Telem.t_speed}"
            )

            # check for ID overflow, reduce SC_queue IDs & get rid off ROB_commQueue entries with IDs at ~3000
            if Telem.id < du.ROBLastTelem.id:
                for x in du.SCQueue:
                    x.id -= 3000

                try:
                    id = du.ROBCommQueue[0].id
                    while id <= 3000:
                        du.ROBCommQueue.pop_first_item()
                        try:
                            id = du.ROBCommQueue[0].id
                        except Exception:
                            break

                except AttributeError:
                    pass

            # delete all finished command from ROB_commQueue
            try:
                while du.ROBCommQueue[0].id < Telem.id:
                    du.ROBCommQueue.pop_first_item()
            except AttributeError:
                pass

            # refresh data only if new
            if Telem != du.ROBLastTelem:

                # check if robot is processing a new command (length check to skip in first loop)
                if (Telem.id != du.ROBLastTelem.id) and (len(du.ROBCommQueue) > 0):
                    du.ROBMovStartP = du.ROBMovEndP
                    du.ROBMovEndP = copy.deepcopy(du.ROBCommQueue[0].Coor1)

                # set new values to globals
                du.ROBTelem = copy.deepcopy(Telem)
                du.ROBLastTelem = copy.deepcopy(Telem)

                # prep database entry
                Zero = copy.deepcopy(du.DCCurrZero)
                du.STTDataBlock.Robo = copy.deepcopy(Telem)
                du.STTDataBlock.Robo.Coor -= Zero
                self.dataUpdated.emit(str(raw_data), Telem)

                print(f"RECV:    {Telem}")

            Mutex.unlock()

            # reset robMoving indicator if near end, skip if queue is processed
            if du.DC_rob_moving and not du.SC_q_processing:
                check_dist = self.check_zero_dist()
                if check_dist is not None:
                    if check_dist < 1:
                        self.endDcMoving.emit()

        elif Telem is not None:
            self.logError.emit(
                "RTel", f"error ({Telem}) from TCPIP class ROB_tcpip, data: {raw_data}"
            )

            Mutex.lock()
            fu.add_to_comm_protocol(
                f"RECV:    error ({Telem}) from TCPIP class ROB_tcpip, data: {raw_data}"
            )
            Mutex.unlock()


    def check_queue(self):
        """add queue element to sendList if qProcessing and robot queue has space"""

        len_sc = len(du.SCQueue)
        len_rob = len(du.ROBCommQueue)
        rob_id = du.ROBTelem.id

        # if qProcessing is ending, define end as being in 1mm range of the last robtarget
        if du.SC_q_prep_end:
            check_dist = self.check_zero_dist()
            if check_dist is not None:
                if check_dist < 1:
                    self.endProcessing.emit()

        # if qProcessing is active and not ending, pop first queue item if robot is nearer than ROB_commFr
        # if no entries in SC_queue left, end qProcessing (immediately if ROB_commQueue is empty as well)
        elif du.SC_q_processing:

            if len_sc > 0:
                Mutex.lock()

                try:
                    while (rob_id + du.ROB_comm_fr) >= du.SCQueue[0].id:
                        comm_tuple = (du.SCQueue.pop_first_item(), False)
                        du.ROB_send_list.append(comm_tuple)

                except AttributeError:
                    pass
                Mutex.unlock()

            else:
                if len_rob == 0:
                    self.endProcessing.emit()
                else:
                    self.queueEmtpy.emit()


    def send(self, testrun=False):
        """send sendList entries if not empty"""

        num_to_send = len(du.ROB_send_list)
        num_send = 0
        while num_to_send > 0:

            comm_tuple = du.ROB_send_list.pop(0)
            num_to_send = len(du.ROB_send_list)
            command = comm_tuple[0]
            direct_ctrl = comm_tuple[1]

            if not isinstance(command, du.QEntry): 
                break
            else:
                Comm = command

            while Comm.id > 3000:
                Comm.id -= 3000

            Comm.Speed.ts = int(Comm.Speed.ts * du.ROB_live_ad)

            if not testrun:
                res, msg_len = du.ROBTcp.send(Comm)
            else:
                res, msg_len = True, 159

            if res:
                num_send += 1

                Mutex.lock()
                du.ROBCommQueue.append(Comm)
                fu.add_to_comm_protocol(
                    f"SEND:    ID: {Comm.id}  MT: {Comm.mt}  PT: {Comm.pt} \t|| COOR_1: {Comm.Coor1}"
                    f"\n\t\t\t|| COOR_2: {Comm.Coor2}"
                    f"\n\t\t\t|| SV:     {Comm.Speed} \t|| SBT: {Comm.sbt}   SC: {Comm.sc}   Z: {Comm.z}"
                    f"\n\t\t\t|| TOOL:   {Comm.Tool}"
                )
                if direct_ctrl:
                    du.SCQueue.increment()
                Mutex.unlock()

            else:
                print(f" Message Error: {msg_len}")
                self.sendElem.emit(Comm, res, msg_len, direct_ctrl, False)

            if num_to_send == 0:
                if not testrun:
                    print(" Block send ")
                self.sendElem.emit(Comm, res, num_send, direct_ctrl, True)
            # else: self.sendElem.emit(command, msg, msgLen, directCtrl, False)


    def check_zero_dist(self):
        """calculates distance between next entry in ROB_commQueue and current position;
        calculates 4 dimensional only to account for external axis movement (0,0,0,1) 
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



class SensorCommWorker(QObject):
    """cycle through all sensors, collect the data"""

    cycleDone = pyqtSignal()
    logError = pyqtSignal(str, str)


    def start(self):
        """start cycling through the sensors"""

        self.CycleTimer = QTimer()
        self.CycleTimer.setInterval(200)
        self.CycleTimer.timeout.connect(self.cycle)
        self.CycleTimer.start()


    def stop(self):
        """stop cycling"""

        self.CycleTimer.stop()
        self.CycleTimer.deleteLater()


    def cycle(self):
        """check every sensor once"""

        temp, t_err, uptime = fu.sensor_data_req()
        if not isinstance(temp, Exception):
            data_len = len(temp)
            if data_len <= 0:
                self.logError.emit(
                    'SENS',
                    f"http request from <IP> successful but data unreadable!"
                )

            # to-do: write data rescue handler
            # elif data_len > 1:

            else:
                Mutex.lock()
                if t_err:
                    du.STTDataBlock.deliv_pump_temp = -666.0
                du.STTDataBlock.deliv_pump_temp = temp[0]
                Mutex.unlock()

        else:
            if not isinstance(temp, ValueError):
                self.logError.emit('SENS', f"request error from <IP>: {temp}")
                    
        self.cycleDone.emit()



class LoadFileWorker(QObject):
    """worker converts .gcode or .mod into QEntries, outsourced to worker as
    these files can have more than 10000 lines"""

    convFinished = pyqtSignal(int, int, int)
    convFailed = pyqtSignal(str)
    _CommList = du.Queue()


    def start(self, testrun=False):
        """get data, start conversion loop"""

        global lfw_file_path
        global lfw_line_id
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

                if (command == "G92") or (command == ";") or (command is None):
                    skips += 1
                elif (command == "G1") or (command == "G28"):
                    line_id += 1
                elif command == ValueError:
                    self.convFailed.emit(f"VALUE ERROR: {command}")
                    lfw_running = False
                    return
                else:
                    self.convFailed.emit(f"{command}!, ABORTED")
                    lfw_running = False
                    return

        else:
            for row in rows:
                Entry, err = self.rapid_conv(id=line_id, txt=row)

                if err == ValueError:
                    self.convFailed.emit(f"VALUE ERROR: {command}")
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
        um_check = fu.re_short("\&\&: \d+.\d+", txt, None, "\&\&: \d+")[0]
        if um_check is not None:
            um_dist = fu.re_short("\d+.\d+", um_check, ValueError, "\d+")[0]
            um_conv_res = self.add_um_tool(um_dist)
            if um_conv_res is not None:
                self.convFailed.emit(um_conv_res)
                lfw_running = False
                return

        # automatic pump control
        if lfw_p_ctrl:
            # set all entries to pmode=default
            for Entry in self._CommList:
                Entry.p_mode = "default"

            # add a 3mm long startvector with a speed of 3mm/s (so 3s of approach), with pMode=start
            StartVector = copy.deepcopy(self._CommList[0])
            StartVector.id = start_id
            StartVector.Coor1.x += lfw_pre_run_time
            StartVector.Coor1.y += lfw_pre_run_time
            StartVector.p_mode = "zero"
            StartVector.Speed = du.SpeedVector(acr=50, dcr=50, ts=200, ors=100)

            self._CommList[0].Speed = du.SpeedVector(acr=1, dcr=1, ts=1, ors=1)
            self._CommList[0].p_mode = "start"
            self._CommList.add(StartVector, thread_call=True)

            # set the last entry to pMode=end
            self._CommList[len(self._CommList) - 1].p_mode = "end"

        du.SCQueue.add_list(self._CommList)
        self.convFinished.emit(line_id, start_id, skips)
        lfw_running = False


    def gcode_conv(self, id, txt):
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
        Entry, command = fu.gcode_to_qentry(Pos, Speed, du.IO_zone, txt)

        if (command != "G1") and (command != "G28"):
            return Entry, command

        Entry.id = id
        res = self._CommList.add(Entry, thread_call=True)

        if res == ValueError:
            return None, ValueError

        return Entry, command


    def rapid_conv(self, id, txt):
        """single line conversion from RAPID"""

        Entry, err = fu.rapid_to_qentry(txt)
        if Entry == None:
            return None, err

        Entry.id = id
        res = self._CommList.add(Entry, thread_call=True)

        if res == ValueError:
            return None, ValueError

        return Entry, None


    def add_um_tool(self, umd):
        """check if the data makes send, add the tooldata to entries"""

        try:
            um_dist = float(umd)
        except Exception:
            return f"UM-Mode failed reading {umd}"

        if um_dist < 0.0 or um_dist > 2000.0:
            return f"UM-Distance <0 or >2000"

        for Entry in self._CommList:
            travel_time = um_dist / Entry.Speed.ts
            if (um_dist % Entry.Speed.ts) != 0:
                return f"UM-Mode failed setting {travel_time} to int."

            Entry.sc = "T"
            Entry.sbt = int(travel_time)
            Entry.Tool.time_time = int(travel_time)
        return None



####################################################   MAIN  ####################################################

Mutex = QMutex()

# RoboCommWorker:
rcw_new_status = False

# LoadFileWorker:
lfw_file_path = None
lfw_line_id = 0
lfw_p_ctrl = False
lfw_running = False
lfw_pre_run_time = 5
