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
from PyQt5.QtGui import QImage, QPixmap

# import my own libs
import libs.global_var as g 
import libs.data_utilities as du
import libs.func_utilities as fu
import libs.pump_utilities as pu
from libs.win_mainframe_prearrange import GlobalMutex, PmpMutex



##########################     PUMP WORKER      ##############################

class PumpCommWorker(QObject):
    """manages data updates and keepalive commands to pump"""

    # naming conventions in PyQT are different,
    # for the signals I will stick with mixedCase
    p1Active = pyqtSignal()
    p2Active = pyqtSignal()
    dataRecv = pyqtSignal(du.PumpTelemetry, str)
    prhActive = pyqtSignal()
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

        with QMutexLocker(PmpMutex):
            self.send()
            self.receive()


    def send(self) -> None:
        """send pump speed to pump, uses modified setter in mtec's script 
        (changed to function), which recognizes a value change and returns
        the machines answer and the original command string, uses user-set
        pump speed if no script is running
        """
        
        # send to P1 and P2 & keepAlive both
        p1_speed, p2_speed, pinch = pu.get_pmp_speeds()
        min_speed, max_speed = g.PMP_SAFE_RANGE
        for serial, speed, live_ad, speed_global, p_num in [
                (g.PMP1Serial, p1_speed, 'PMP1_live_ad', 'PMP1_speed', 'P1'),
                (g.PMP2Serial, p2_speed, 'PMP2_live_ad', 'PMP2_speed', 'P2'),
        ]:
            if serial.connected and speed is not None:
                new_speed = speed * getattr(du, live_ad)
                new_speed = fu.domain_clip(new_speed, min_speed, max_speed)
                new_speed = int(round(new_speed, 0))
                res = serial.set_speed(new_speed)
                if res is not None:
                    with QMutexLocker(GlobalMutex):
                        setattr(du, speed_global, speed)
                    print(f"{p_num}: {speed}")
                    self.dataSend.emit(speed, res[0], res[1], p_num)

                serial.keepAlive()
        if pinch is not None and g.PRH_connected:
            try:
                ans = requests.post(f"{g.PRH_url}/pinch", data={'s': str(float(pinch))}, timeout=0.1)
                print(ans.text)
            except requests.Timeout as e:
                log_txt = f"post to pinch valve failed! {g.PRH_url} not present!"
                self.logEntry.emit('CONN', log_txt)
                print(log_txt)

        # SEND TO MIXER
        if g.PRH_connected and g.MIX_last_speed != g.MIX_speed:
            if g.PRH_act_with_pump:
                mixer_speed = g.MIX_max_speed * (p1_speed + p2_speed) / (2 * 100.0)
            else:
                mixer_speed = g.MIX_speed
            
            post_url = f"{du.PRH_url}/motor"
            try:
                post_resp = requests.post(post_url, data={'s': mixer_speed}, timeout=0.1)
                if post_resp.ok and f"RECV: " in post_resp.text:
                    with QMutexLocker(GlobalMutex):
                        du.MIX_last_speed = mixer_speed
                    print(f"MIX: {mixer_speed}; resp: {post_resp.text}")
                    self.dataMixerSend.emit(mixer_speed)
            except:
                pass


    def receive(self) -> None:
        """request data updates for frequency, voltage, current and torque
        from pump, pass to mainframe
        """

        # for serial,_ in [(g.PMP1Serial, None),(g.PMP2Serial, None)]:
        #     if serial.connected:
        #         print(f"P2 freq: {serial.frequency}")

        # RECEIVE FROM PUMPS:
        for serial, last_telem, speed_global, stt_attr, p_num in [
                (g.PMP1Serial, 'PMP1LastTelem', 'PMP1_speed', 'Pump1', 'P1'),
                (g.PMP2Serial, 'PMP2LastTelem', 'PMP2_speed', 'Pump2', 'P2'),
        ]:
            if serial.connected:
                freq = serial.frequency
                # override to reduce traffic on shared bus
                # volt = -1.0
                # amps = -1.0
                # torq = -1.0
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
                            setattr(g.DBDataBlock, stt_attr, Telem)
                        self.dataRecv.emit(Telem, p_num)

        # RECEIVE FROM PRINTHEAD (just ping to check)
        if du.PRH_connected:
            try:
                ping_resp = requests.get(f"{du.PRH_url}/ping", timeout=0.2)
                if ping_resp.ok and ping_resp.text == 'ack':
                    self.prhActive.emit()
            except:
                pass



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
        self.CommTimer.setInterval(100)
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
            if g.SC_q_processing:
                self.endProcessing.emit()
            else:
                self.endDcMoving.emit()

        Telem, raw_data = g.ROBTcp.receive()
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
                LastPos = g.ROBCommQueue[0].Coor1
            except:
                LastPos = 'POSITION NOT RETRIEVABLE'
            err_handler(f"given position out of reach! last given pos: {LastPos}")

        else:
            # standard telemetry handler
            Telem = round(Telem, 1)
            self.dataReceived.emit()

            with QMutexLocker(GlobalMutex):
                fu.add_to_comm_protocol(f"RECV:    {Telem}")

                # check for ID overflow, reduce SC_queue IDs
                if Telem.id < g.ROBLastTelem.id:
                    buff_size = g.ROB_BUFFER_SIZE
                    # avoid errors from SC_curr_comm_id resets:
                    if all(entry.id > buff_size for entry in g.SCQueue):
                        for x in g.SCQueue:
                            x.id -= buff_size
                        # and clear ROBCommQueue entries with IDs
                        # near DEF_ROB_BUFF_SIZE
                        try:
                            while g.ROBCommQueue[0].id > Telem.id:
                                g.ROBCommQueue.pop_first_item()
                        except:
                            pass
                    # otherwise it has to be a SC_curr_comm_id reset,
                    # indicate robot idle state
                    else:
                        g.ROBCommQueue.clear()
                        self.endDcMoving.emit()

                # delete all finished commands from ROB_commQueue
                try:
                    while g.ROBCommQueue[0].id < Telem.id:
                        g.ROBCommQueue.pop_first_item()
                except AttributeError:
                    pass

                # refresh data only if new
                if Telem != g.ROBLastTelem:
                    # check if robot is processing a new command
                    # (length check to skip in first loop)
                    if (
                            Telem.id != g.ROBLastTelem.id
                            and len(g.ROBCommQueue) > 0
                        ):
                        g.ROBMovStartP = g.ROBMovEndP
                        g.ROBMovEndP = dcpy(g.ROBCommQueue[0].Coor1)
                        g.PRH_status = dcpy(g.ROBCommQueue[0].Tool)

                    # set new values to globals
                    g.ROBTelem = dcpy(Telem)
                    g.ROBLastTelem = dcpy(Telem)

                    # prep database entry
                    STTEntry = dcpy(Telem)
                    STTEntry.Coor -= g.ROBCurrZero
                    g.DBDataBlock.Robo = dcpy(STTEntry) 
                    self.dataUpdated.emit(str(raw_data), Telem)
                    
                    # print
                    print(f"RECV:    {Telem}")

            # reset robMoving indicator if near end, skip if queue is processed
            if g.DC_rob_moving and not g.SC_q_processing:
                if self._check_target_reached():
                    self.endDcMoving.emit()


    def check_queue(self) -> None:
        """add queue element to sendList if qProcessing and robot queue has
        space
        """

        len_sc = len(g.SCQueue)
        len_rob = len(g.ROBCommQueue)
        rob_id = g.ROBTelem.id

        # if qProcessing is ending, define end as being in 1mm range of
        # the last robtarget
        if g.SC_q_prep_end:
            if self._check_target_reached():
                self.endProcessing.emit()

        # if qProcessing is active and not ending, pop first queue item if
        # robot is nearer than ROB_commFr; if no entries in SC_queue left,
        # end qProcessing (immediately if ROB_commQueue is empty as well)
        elif g.SC_q_processing:
            if len_sc > 0:
                with QMutexLocker(GlobalMutex):
                    try:
                        while (rob_id + g.ROB_comm_fr) >= g.SCQueue[0].id:
                            comm_tuple = (g.SCQueue.pop_first_item(), False)
                            g.ROB_send_list.append(comm_tuple)
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
        while len(g.ROB_send_list) > 0:
            Comm, direct_ctrl = g.ROB_send_list.pop(0)

            # check type and ID
            if not isinstance(Comm, du.QEntry):
                err = TypeError(f"{Comm} is not an instance of QEntry!")
                self.sendElem.emit(Comm, False, err, direct_ctrl)
                print(f"send error: {err}")
                break
            if Comm.id < 0:
                err = ValueError(f"Command has negative ID: {Comm.id}!")
                self.sendElem.emit(Comm, False, err, direct_ctrl)
                print(f"send error: {err}")
                break
            # check for ID overflow
            while Comm.id > g.ROB_BUFFER_SIZE:
                Comm.id -= g.ROB_BUFFER_SIZE
            # check for TCP speed overwrites
            if g.ROB_speed_overwrite >= 0.0:
                Comm.Speed.ts = g.ROB_speed_overwrite
                # limit reorientation speed to avoid damage
                r_speed = (g.ROB_speed_overwrite / 2)
                Comm.Speed.ors = min([r_speed, g.ROB_max_r_speed])
            else:
                Comm.Speed.ts = int(Comm.Speed.ts * g.ROB_live_ad)
                Comm.Speed.ors = int(Comm.Speed.ors * g.ROB_live_ad)

            # if testrun, skip actually sending the message
            if testrun:
                res, msg_len = True, 159
            else:
                res, msg_len = g.ROBTcp.send(Comm)

            # see if sending was successful
            if res:
                with QMutexLocker(GlobalMutex):
                    num_send += 1
                    g.ROBCommQueue.append(Comm)
                    fu.add_to_comm_protocol(f"SEND:    {Comm}")
                    if direct_ctrl:
                        g.SCQueue.increment()

                self.logEntry.emit('ROBO', f"send: {Comm}")
            else:
                print(f" Message Error: {msg_len}")
                self.sendElem.emit(Comm, False, msg_len, direct_ctrl)
        
            # inform mainframe if command block was send successfully 
            if len(g.ROB_send_list) == 0:
                self.sendElem.emit(Comm, True, num_send, direct_ctrl)


    def _check_target_reached(self) -> bool:
        """calculates distance between next entry in ROB_commQueue and current
        position; calculates 4 dimensional only to account for external axis
        movement (0,0,0,1) 
        """

        # as long as there a more commands comming, target is not reached
        command_num = len(g.ROBCommQueue)
        if command_num > 1 or len(g.ROB_send_list) != 0:
            return False
        # otherwise calc distance to target
        elif command_num == 1:
            CurrTarget = dcpy(g.ROBCommQueue[0].Coor1)
            CurrCoor = dcpy(g.ROBTelem.Coor)
            target_dist =  m.sqrt(
                m.pow(CurrTarget.x - CurrCoor.x, 2)
                + m.pow(CurrTarget.y - CurrCoor.y, 2)
                + m.pow(CurrTarget.z - CurrCoor.z, 2)
                + m.pow(CurrTarget.ext - CurrCoor.ext, 2)
            )
        # failsafe
        else:
            return True

        if target_dist < g.ROB_min_target_dist:
            return True
        return False



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
                            g.DBDataBlock.store(latest_data, key, sub_key)

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
        for key in g.SEN_dict:
            loc_request(g.SEN_dict[key], key)

        self.cycleDone.emit()



###########################     LF WORKER      ###############################

class LoadFileWorker(QObject):
    """worker converts .gcode or .mod into QEntries, outsourced to worker as
    these files can have more than 50000 lines"""

    convFinished = pyqtSignal(int, int, int)
    convFailed = pyqtSignal(str)
    rangeChkWarning = pyqtSignal(str)
    _CommList = du.Queue()


    def run(self, testrun=False) -> None:
        """get data, start conversion loop"""
        global lfw_file_path
        global lfw_line_id
        global lfw_ext_trail
        global lfw_p_ctrl
        global lfw_range_chk
        global lfw_base_dist_chk
        global lfw_running
        global lfw_pre_run_time

        lfw_running = True
        line_id = lfw_line_id
        file_path = lfw_file_path
        if file_path is None:
            self.convFailed.emit("No filepath given!")
            lfw_running = False
            return

        # init vars
        with open(file_path, 'r') as file:
            txt = file.read()
        rows = txt.split("\n")
        self._CommList.clear()
        start_id = line_id

        # iterate over file rows
        if file_path.suffix == ".gcode":
            result, line_id, skips = self.gcode_conv(line_id, rows)
        else:
            result, line_id, skips = self.rapid_conv(line_id, rows)
        if len(self._CommList) == 0:
            self.convFailed.emit("No commands found!")
            result = False
        if not result:
            lfw_running = False
            return

        # automatic pump control
        if lfw_p_ctrl:
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
        
        # entry checks
        if lfw_range_chk:
            self.check_routine(fu.range_check)
        if lfw_base_dist_chk:
            self.check_routine(fu.base_dist_check)

        # add to command queue
        g.SCQueue.add_queue(self._CommList, g.SC_curr_comm_id)
        self.convFinished.emit(line_id, start_id, skips)
        lfw_running = False


    def gcode_conv(self, line:int, rows:list) -> tuple[bool, int, int]:
        """row-wise conversion from GCode"""

        skips = 0
        # file import always starts from home, regardless of current pos:
        LastEntry = du.QEntry(
            id=0,
            Coor1=g.ROBCurrZero,
            Speed=g.SCSpeed,
            z=g.IO_zone
        )
        for row in rows:
            Entry, command = fu.gcode_to_qentry(LastEntry, row, lfw_ext_trail)
            # check if valid command
            if (command == "G1") or (command == "G28"):
                Entry.id = line
                res = self._CommList.add(Entry, thread_call=True)
                if res == ValueError:
                    self.convFailed.emit(f"COULD NOT ADD: {command}!")
                    return False, 0, 0
                line += 1
                LastEntry = Entry
            elif (command == "G92") or (command == ";") or (command == ''):
                skips += 1
            else:
                # if invalid, break conversion
                if isinstance(Entry, Exception):
                    self.convFailed.emit(f"VALUE ERROR: {command}!")
                else:
                    self.convFailed.emit(f"{command}, ABORTED!")
                return False, 0, 0
        return True, line, skips


    def rapid_conv(self, line:int, rows:list) -> tuple[bool, int, int]:
        """single line conversion from RAPID"""

        skips = 0
        for row in rows:
            Entry = fu.rapid_to_qentry(row, lfw_ext_trail)
            if Entry is None:
                skips += 1
            elif isinstance(Entry, Exception):
                self.convFailed.emit(f"ERROR: {Entry}")
                return False, 0, 0
            else:
                Entry.id = line
                res = self._CommList.add(Entry, thread_call=True)
                if res == ValueError:
                    return False, 0, 0
                line += 1
        return True, line, skips


    def check_routine(self, func):
        """preformes a line-wise check, check function to be stated unter 
        'func', needs to be a callable that returns (bool, str)"""
        if not callable(func):
            raise TypeError(f"{func} is not callable!")
        line = 0
        warnings = 0
        chk_msg = ''
        for Entry in self._CommList:
            line += 1
            result, msg = func(Entry)
            if not result:
                warnings += 1
                chk_msg += f"Line {line}: {msg}\n"
                if warnings >= g.WARN_MAX_RAISED:
                    chk_msg += (
                        f"Maximum number of warnings reached, "
                        f"stopping check.."
                    )
                    break
        if chk_msg != '':
            self.rangeChkWarning.emit(chk_msg)



##########################     ROBO WORKER      ##############################

class IPCamWorker(QObject):
    """worker captures video streams from IP cams, displays them via signal"""

    imageCaptured = pyqtSignal(int, QPixmap)
    logEntry = pyqtSignal(str, str)
    cam_streams = []

    def run(self) -> None:
        """create capture timer and fill active streams according to 
        given URLs"""

        for url in g.CAM_urls:
            self.cam_streams.append(cv2.VideoCapture(url, cv2.CAP_FFMPEG,))
        
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
                self.imageCaptured.emit(cam_num, QPixmap.fromImage(qt_image))



##############################     MAIN      #################################

# LoadFileWorker:
lfw_file_path = None
lfw_line_id = 0
lfw_ext_trail = True
lfw_p_ctrl = False
lfw_range_chk = True
lfw_base_dist_chk = True
lfw_running = False
lfw_pre_run_time = 10
