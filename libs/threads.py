#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

# python standard libraries
import os
import cv2
import sys
import math as m
import requests
from copy import deepcopy as dcpy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# PyQt stuff
from PyQt5.QtCore import QObject, QTimer, pyqtSignal, QMutexLocker
from PyQt5.QtGui import QImage

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
        which is checked in win_mainframe.disconnect_tcp"""

        with QMutexLocker(GlobalMutex):
            du.PMP_comm_active = True
        self.send()
        self.receive()
        with QMutexLocker(GlobalMutex):
            du.PMP_comm_active = False
    

    def get_speed_settings() -> tuple[int, int, int]:
        """see if pump settings have been scripted, otherwise use user 
        input; interpret total_speed as combined maximum possible flow,
        if both pumps are connected; pump values are capped at 100, e.g.
        when P1 & P2 are connected, speed is set to 100 & ratio is set to
        1.0, pump1_speed would otherwise be 200.
        """

        # SEND TO PUMPS
        p_ratio = du.PMP_output_ratio
        if du.SC_q_processing:
            total_speed, p_ratio = pu.calc_speed()
        else: 
            total_speed = du.PMP_speed

        # get speed
        if du.PMP1Serial.connected and du.PMP2Serial.connected:
            total_speed *= 2
            p1_speed = total_speed * p_ratio
            p2_speed = total_speed * (1 - p_ratio)
        else:
            p1_speed = p2_speed = total_speed

        # look for user overwrite, no mutex, as changing 
        # global PUMP_user_speed would not harm the process
        if du.PMP1_user_speed != -999:
            p1_speed = du.PMP1_user_speed
            du.PMP1_user_speed = -999
        if du.PMP2_user_speed != -999:
            p2_speed = du.PMP2_user_speed
            du.PMP2_user_speed = -999
        
        return total_speed, p1_speed, p2_speed


    def send(self) -> None:
        """send pump speed to pump, uses modified setter in mtec's script 
        (changed to function), which recognizes a value change and returns
        the machines answer and the original command string, uses user-set
        pump speed if no script is running
        """
        
        # send to P1 and P2 & keepAlive both
        pmp_speed, p1_speed, p2_speed = self.get_speed_settings() 
        for serial, speed, live_ad, speed_global, p_num in [
                (du.PMP1Serial, p1_speed, 'PMP1_live_ad', 'PMP1_speed', 'P1'),
                (du.PMP2Serial, p2_speed, 'PMP2_live_ad', 'PMP2_speed', 'P2'),
        ]:
            if serial.connected and speed is not None:
                res = serial.set_speed(int(speed * getattr(du, live_ad)))
                
                if res is not None:
                    with QMutexLocker(GlobalMutex):
                        setattr(du, speed_global, speed)
                    print(f"{p_num}: {speed}")
                    self.dataSend.emit(speed, res[0], res[1], p_num)

                serial.keepAlive()

        # SEND TO MIXER
        if du.MIX_connected and du.MIX_last_speed != du.MIX_speed:
            if du.MIX_act_with_pump:
                mixer_speed = pmp_speed * du.MIX_max_speed / 100.0
            else:
                mixer_speed = du.MIX_speed
            
            ip = du.DEF_TCP_MIXER['IP']
            port = du.DEF_TCP_MIXER['PORT']
            post_url = f"http://{ip}:{port}/motor"
            post_resp = requests.post(post_url, data=f"{mixer_speed}")

            if post_resp.ok and post_resp.text == f"RECV{mixer_speed}":
                with QMutexLocker(GlobalMutex):
                    du.MIX_last_speed = mixer_speed
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
                        with QMutexLocker(GlobalMutex):
                            setattr(du, last_telem, Telem)
                            setattr(du.STTDataBlock, stt_attr, Telem)
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

        def err_handler(err_txt):
            self.logEntry.emit('RTel', err_txt)
            with QMutexLocker(GlobalMutex):
                fu.add_to_comm_protocol(f"RECV:    {err_txt}")

        Telem, raw_data = du.ROBTcp.receive()
        if isinstance(Telem, Exception):
            # inform user if error occured in websocket connection (ignore timeouts)
            if(
                not isinstance(Telem, TimeoutError)
                and not isinstance(Telem, WindowsError)
            ):
                err_handler(f"ERROR from ROBTcp ({Telem}), raw data: {raw_data}")

        elif Telem.id < 0:
            # handle robot internal error catching
            try:
                LastPos = du.ROBCommQueue[0].Coor1
            except:
                LastPos = None
            err_handler(f"given position out of reach! last given pos: {LastPos}")

        else:
            # standard telemetry handler
            Telem = round(Telem, 1)
            self.dataReceived.emit()

            with QMutexLocker(GlobalMutex):
                fu.add_to_comm_protocol(
                    f"RECV:    ID {Telem.id},   {Telem.Coor}   "
                    f"TCP: {Telem.t_speed}"
                )

                # check for ID overflow, reduce SC_queue IDs 
                if Telem.id < du.ROBLastTelem.id:
                    for x in du.SCQueue:
                        x.id -= du.DEF_ROB_BUFF_SIZE
                    # and clear ROBCommQueue entries with IDs
                    # near DEF_ROB_BUFF_SIZE
                    try:
                        while du.ROBCommQueue[0].id > Telem.id:
                            du.ROBCommQueue.pop_first_item()
                    except:
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
                    if (
                            Telem.id != du.ROBLastTelem.id
                            and len(du.ROBCommQueue) > 0
                        ):
                        du.ROBMovStartP = du.ROBMovEndP
                        du.ROBMovEndP = dcpy(du.ROBCommQueue[0].Coor1)

                    # set new values to globals
                    du.ROBTelem = dcpy(Telem)
                    du.ROBLastTelem = dcpy(Telem)

                    # prep database entry
                    STTEntry = dcpy(Telem)
                    STTEntry.Coor -= du.DCCurrZero
                    du.STTDataBlock.Robo = dcpy(STTEntry) 
                    self.dataUpdated.emit(str(raw_data), Telem)
                    
                    # print
                    print(f"RECV:    {Telem}")

            # reset robMoving indicator if near end, skip if queue is processed
            if du.DC_rob_moving and not du.SC_q_processing:
                check_dist = self.check_zero_dist()
                if check_dist is not None:
                    if check_dist < 1:
                        self.endDcMoving.emit()


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
                with QMutexLocker(GlobalMutex):
                    try:
                        while (rob_id + du.ROB_comm_fr) >= du.SCQueue[0].id:
                            comm_tuple = (du.SCQueue.pop_first_item(), False)
                            du.ROB_send_list.append(comm_tuple)
                    except AttributeError:
                        pass

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
            Comm = comm_tuple[0]
            direct_ctrl = comm_tuple[1]

            # check for type, ID overflow & live adjustments to tcp speed
            if not isinstance(Comm, du.QEntry):
                err = ValueError(f"{Comm} is not an instance of QEntry!")
                self.sendElem.emit(Comm, False, err, direct_ctrl)
                print(f"send error: {err}")
                break
            # check for TCP speed overwrites
            if du.ROB_speed_overwrite >= 0.0:
                Comm.Speed.ts = du.ROB_speed_overwrite
            else:
                Comm.Speed.ts = int(Comm.Speed.ts * du.ROB_live_ad)
            while Comm.id > du.DEF_ROB_BUFF_SIZE:
                Comm.id -= du.DEF_ROB_BUFF_SIZE

            # if testrun, skip actually sending the message
            if testrun:
                res, msg_len = True, 159
            else:
                res, msg_len = du.ROBTcp.send(Comm)

            # see if sending was successful
            if res:
                with QMutexLocker(GlobalMutex):
                    num_send += 1
                    du.ROBCommQueue.append(Comm)
                    fu.add_to_comm_protocol(
                        f"SEND:    ID: {Comm.id}  MT: {Comm.mt}  PT: {Comm.pt} "
                        f"\t|| COOR_1: {Comm.Coor1}"
                        f"\n\t\t\t|| COOR_2: {Comm.Coor2}"
                        f"\n\t\t\t|| SV:     {Comm.Speed} \t|| SBT: {Comm.sbt}   "
                        f"SC: {Comm.sc}   Z: {Comm.z}"
                        f"\n\t\t\t|| TOOL:   {Comm.Tool}"
                    )
                    if direct_ctrl:
                        du.SCQueue.increment()

                self.logEntry.emit('ROBO', f"send: {Comm}")

            else:
                print(f" Message Error: {msg_len}")
                self.sendElem.emit(Comm, False, msg_len, direct_ctrl)
        
            # inform mainframe if command block was send successfully 
            if len(du.ROB_send_list) == 0:
                self.sendElem.emit(Comm, res, num_send, direct_ctrl)


    def check_zero_dist(self) -> float | None:
        """calculates distance between next entry in ROB_commQueue and current
        position; calculates 4 dimensional only to account for external axis
        movement (0,0,0,1) 
        """

        if len(du.ROBCommQueue) == 1:
            CurrCommTarget = dcpy(du.ROBCommQueue[0].Coor1)
            CurrCoor = dcpy(du.ROBTelem.Coor)
            return m.sqrt(
                m.pow(CurrCommTarget.x - CurrCoor.x, 2)
                + m.pow(CurrCommTarget.y - CurrCoor.y, 2)
                + m.pow(CurrCommTarget.z - CurrCoor.z, 2)
                + m.pow(CurrCommTarget.ext - CurrCoor.ext, 2)
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

                        with QMutexLocker(GlobalMutex):
                            du.STTDataBlock.store(latest_data, key, sub_key)

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
    these files can have more than 50000 lines"""

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
            StartVector = dcpy(self._CommList[0])
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
        Speed = dcpy(du.PRINSpeed)
        try:
            if len(self._CommList) == 0:
                Pos = dcpy(du.SCQueue.entry_before_id(id).Coor1)
            else:
                Pos = dcpy(self._CommList.last_entry().Coor1)
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
    #     except:
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



##########################     ROBO WORKER      ##############################

class IPCamWorker(QObject):
    """worker captures video streams from IP cams, displays them via signal"""

    imageCaptured = pyqtSignal(int, QImage)
    logEntry = pyqtSignal(str, str)

    cam_streams = []

    def run(self) -> None:
        """create capture timer and fill active streams according to 
        given URLs"""

        for url in du.CAM_urls:
            self.cam_streams.append(cv2.VideoCapture(url, cv2.CAP_FFMPEG))
        
        self.CapTimer = QTimer()
        self.CapTimer.setInterval(250)
        self.CapTimer.timeout.connect(self.cam_cap)
        self.CapTimer.start()

        self.logEntry.emit(
            'THRT',
            f"IPCam Thread running with {len(self.cam_streams)} streams."
        )


    def stop(self) -> None:
        """stop loop"""

        for cs in self.cam_streams:
            if isinstance(cs, cv2.VideoCapture):
                cs.release()

        self.CapTimer.stop()
        self.CapTimer.deleteLater()

    
    def cam_cap(self) -> None:
        """capture an image from all streams"""

        for cam_num, cam in enumerate(self.cam_streams):
            if not isinstance(cam, cv2.VideoCapture):
                continue
            flag, frame = cam.read()
            if flag:
                # Following example from 
                # https://github.com/god233012yamil/Streaming-IP-Cameras-Using-PyQt-and-OpenCV
                # Get the frame height, width, channels, and bytes per line
                height, width, channels = frame.shape
                bytes_per_line = width * channels
                # image from BGR (cv2 default color format) to RGB (Qt default color format)
                # '.copy()' is vital as the emitted qt_image is otherwise local and 
                # slots accessing it will crash with segmentation fault
                cv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                qt_image = QImage(
                    cv_image.data,
                    width,
                    height,
                    bytes_per_line,
                    QImage.Format_RGB888
                ).copy()
                self.imageCaptured.emit(cam_num, qt_image)



##############################     MAIN      #################################

# LoadFileWorker:
lfw_file_path = None
lfw_line_id = 0
lfw_ext_trail = True
lfw_p_ctrl = False
lfw_running = False
lfw_pre_run_time = 10
