#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0
#   International (CC BY-SA 4.0).
#   (https://creativecommons.org/licenses/by-sa/4.0/)
#   Feel free to use, modify or distribute this code as far as you like, so
#   long as you make anything based on it publicly avialable under the same
#   license.


############################     IMPORTS      ################################

import re
import os
import sys
import serial
import socket
import struct
import math as m
from pathlib import Path
from datetime import datetime, timedelta
from copy import deepcopy as dcpy

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod



############################     CLASSES      ################################

class Coordinate:
    """standard 7-axis coordinate block (8 attributes, as quaterion
    positioning is possible); initialization by value list is also possible
    in form of 'du.Coordinate([x, y, z, rx, ry, rz, q, ext])'

    ATTRIBUTES:
        x, y, z:
            position in cartesian coordinates
        rx, ry, rz:
            angle relative to cartesian coordinates
        q:
            additional var for fourth quaternion coordinate
        ext:
            external axis position

    METHODS:
        __init__, __str__, __add__, __sub__, __round__, __eq__, __ne__
    """

    _iter_value = 0
    _attr_names = ['x', 'y', 'z', 'rx', 'ry', 'rz', 'q', 'ext']

    def __init__(
            self,
            x=0.0,
            y=0.0,
            z=0.0,
            rx=0.0,
            ry=0.0,
            rz=0.0,
            q=0.0,
            ext=0.0
    ) -> None:
        
        if isinstance(x, list):
            if len(x) != 8:
                raise ValueError(f"length of {x} does not fit attribute list")
            else:
                ext, q, rz, ry, rx = x[7], x[6], x[5], x[4], x[3]
                y, z = x[2], x[1]
                x = x[0]

        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.rx = float(rx)
        self.ry = float(ry)
        self.rz = float(rz)
        self.q = float(q)
        self.ext = float(ext)


    def __str__(self) -> str:

        return (
            f"X: {self.x}   Y: {self.y}   Z: {self.z}   "
            f"Rx: {self.rx}   Ry: {self.ry}   Rz: {self.rz}   "
            f"Q: {self.q}   EXT: {self.ext}"
        )


    def __add__(self, summand) -> 'Coordinate':
        """round everything to 2 digits because less than 10µm accuracy is
        just pointless with a meter-large robot
        """

        if isinstance(summand, Coordinate):
            res = Coordinate(
                (self.x + summand.x),
                (self.y + summand.y),
                (self.z + summand.z),
                (self.rx + summand.rx),
                (self.ry + summand.ry),
                (self.rz + summand.rz),
                (self.q + summand.q),
                (self.ext + summand.ext),
            )
            return round(res, 2)

        else:
            res = Coordinate(
                (self.x + summand),
                (self.y + summand),
                (self.z + summand),
                (self.rx + summand),
                (self.ry + summand),
                (self.rz + summand),
                (self.q + summand),
                (self.ext + summand),
            )
            return round(res, 2)


    def __iter__(self) -> 'Coordinate':
        
        self._iter_val = 0
        return self
    

    def __next__(self) -> float:
        
        val = self._iter_value

        if val >= len(self._attr_names):
            raise StopIteration
        
        self._iter_value = val + 1
        return getattr(self, self._attr_names[val])
    
    
    def __sub__(self, subtrahend) -> 'Coordinate':
        """round everything to 2 digits because less than 10µm accuracy is
        just pointless with a meter-large robot
        """

        if isinstance(subtrahend, Coordinate):
            res = Coordinate(
                (self.x - subtrahend.x),
                (self.y - subtrahend.y),
                (self.z - subtrahend.z),
                (self.rx - subtrahend.rx),
                (self.ry - subtrahend.ry),
                (self.rz - subtrahend.rz),
                (self.q - subtrahend.q),
                (self.ext - subtrahend.ext),
            )
            return round(res, 2)

        else:
            res = Coordinate(
                (self.x - subtrahend),
                (self.y - subtrahend),
                (self.z - subtrahend),
                (self.rx - subtrahend),
                (self.ry - subtrahend),
                (self.rz - subtrahend),
                (self.q - subtrahend),
                (self.ext - subtrahend),
            )
            return round(res, 2)


    def __round__(self, digits) -> 'Coordinate':

        return Coordinate(
            round(self.x, digits),
            round(self.y, digits),
            round(self.z, digits),
            round(self.rx, digits),
            round(self.ry, digits),
            round(self.rz, digits),
            round(self.q, digits),
            round(self.ext, digits),
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, Coordinate):
            if (
                self.x == other.x
                and self.y == other.y
                and self.z == other.z
                and self.rx == other.rx
                and self.ry == other.ry
                and self.rz == other.rz
                and self.q == other.q
                and self.ext == other.ext
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'Coordinate'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, Coordinate):
            if (
                self.x != other.x
                or self.y != other.y
                or self.z != other.z
                or self.rx != other.rx
                or self.ry != other.ry
                or self.rz != other.rz
                or self.q != other.q
                or self.ext != other.ext
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'Coordinate'!"
            )

        return False
    

    @property
    def attr_names(self):
        return self._attr_names



class SpeedVector:
    """standard speed vector (4 attributes).

    ATTRIBUTES:
        acr:
            acceleration ramp
        dcr:
            deceleration ramp
        ts:
            transition speed
        os:
            orientation speed

    METHODS:
        __init__, __str__, __mul__, __rmul__, __eq__, __ne__
    """


    def __init__(self, acr=50, dcr=50, ts=200, ors=50) -> None:

        self.acr = int(round(acr, 0))
        self.dcr = int(round(dcr, 0))
        self.ts = int(round(ts, 0))
        self.ors = int(round(ors, 0))


    def __str__(self) -> str:

        return (
            f"TS: {self.ts}   OS: {self.ors}   "
            f"ACR: {self.acr}   DCR: {self.dcr}"
        )


    def __mul__(self, other) -> 'SpeedVector':
        """round everything to 2 digits because less than 10µm accuracy is
        just pointless with a meter-large robot
        """

        res = SpeedVector(
            ts=int(round(self.ts * other, 0)),
            ors=int(round(self.ors * other, 0)),
            acr=int(round(self.acr * other, 0)),
            dcr=int(round(self.dcr * other, 0)),
        )
        return res


    def __rmul__(self, other) -> 'SpeedVector':

        return self.__mul__(other)


    def __eq__(self, other) -> bool:

        if isinstance(other, SpeedVector):
            if (
                self.acr == other.acr
                and self.dcr == other.dcr
                and self.ts == other.ts
                and self.ors == other.ors
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'SpeedVector'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, SpeedVector):
            if (
                self.acr != other.acr
                or self.dcr != other.dcr
                or self.ts != other.ts
                or self.ors != other.ors
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'SpeedVector'!"
            )

        return False



class ToolCommand:
    """standard tool command according to Jonas' protocol

    ATTRIBUTES:
        trolley_steps:
            motor 1 steps as abolsute position relative to reference
        clamp:
            0: released, 1: engaged
        cut:
            0: cutter off, 1: cutter on
            invokes corresponding command 'cutter_position'
            (0: to rest prosition, 1: to cutting position)
        place_spring:
            place a spring from barrel onto fiber;
        load_spring:
            load a new spring from pre-position into barrel
        wait:
            0: robot not stopping
            >0: robot stops for >0 seconds

    METHODS:
        __def__, __str__, __eq__, __ne__
    """


    def __init__(
        self,
        trolley_steps=0,
        clamp=False,
        cut=False,
        place_spring=False,
        load_spring=False,
        wait=0,
    ) -> None:

        self.trolley_steps = int(trolley_steps)
        self.clamp = bool(clamp)
        self.cut = bool(cut)
        self.place_spring = bool(place_spring)
        self.load_spring = bool(load_spring)
        self.wait = int(wait)


    def __str__(self) -> str:

        return (
            f"TRL: {self.trolley_steps}   PS: {self.place_spring}   "
            f"LS: {self.load_spring}   CUT: {self.cut}   CL: {self.clamp}   "
            f"W: {self.wait}"
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, ToolCommand):
            if (
                self.trolley_steps == other.trolley_steps
                and self.clamp == other.clamp
                and self.cut == other.cut
                and self.place_spring == other.place_spring
                and self.load_spring == other.load_spring
                and self.wait == other.wait
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'ToolCommand'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, ToolCommand):
            if (
                self.trolley_steps != other.trolley_steps
                or self.clamp != other.clamp
                or self.cut != other.cut
                or self.place_spring != other.place_spring
                or self.load_spring != other.load_spring
                or self.wait != other.wait
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'ToolCommand'!"
            )

        return False



class QEntry:
    """standard 159 byte command queue entry for TCP robot according to the
    protocol running on the robot

    ATTRIBUTES:
        id:
            command ID, list number in robot internal queue
        mt:
            type of movement or special command (L = linear, J = joint,
            C = circular, S = stop after current movement
            & delete robot internal queue, E = end TCP protocol on robot)
        pt:
            position type, type of rotation given (E = Euler angles,
            Q = quaternion, A = axis positioning)
        Coor1:
            coordinates of the first given point
        Coor2:
            coordinates of the second given point
        Speed:
            speed vector for given movement
        sbt:
            (speed by time) time to calculate speed by
        sc:
            speed command, set movement speed by movement time (SBT) or speed
            vector (SV), (T = time, V = vector)
        z:
            zone, endpoint precision
        Tool:
            tool command in Jonas' standard format
        p_mode:
            option for automatic pump control
        p_ratio:
            option for dual pump printing

    METHODS:
        __init__, __str__, __eq__, __ne__

        print_short:
            prints only most important parameters
    """


    def __init__(
        self,
        id=0,
        mt='L',
        pt='E',
        Coor1=None,
        Coor2=None,
        Speed=None,
        sbt=0,
        sc='V',
        z=10,
        Tool=None,
        p_mode=-1001, # -1001 is indicator for 'no p_mode given'
        p_ratio=1.0,
        pinch=False,
    ) -> None:

        self.id = int(id)
        self.mt = str(mt)
        self.pt = str(pt)
        self.sbt = int(sbt)
        self.sc = str(sc)
        self.z = int(z)
        self.p_mode = int(p_mode)
        self.p_ratio = float(p_ratio)
        self.pinch = bool(pinch)

        # handle those beasty mutables
        self.Coor1 = Coordinate() if (Coor1 is None) else Coor1
        self.Coor2 = Coordinate() if (Coor2 is None) else Coor2
        self.Speed = SpeedVector() if (Speed is None) else Speed
        self.Tool = ToolCommand() if (Tool is None) else Tool


    def __str__(self) -> str:

        return (
            f"ID: {self.id}  MT: {self.mt}  PT: {self.pt} "
            f"\t|| COOR_1: {self.Coor1}"
            f"\n\t\t|| COOR_2: {self.Coor2}"
            f"\n\t\t|| SV:     {self.Speed} "
            f"\t|| SBT: {self.sbt}   SC: {self.sc}   Z: {self.z}"
            f"\n\t\t|| TOOL:   {self.Tool}"
            f"\n\t\t|| PM/PR:  {self.p_mode}/{self.p_ratio}   "
            f"PIN: {self.pinch}"
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, QEntry):
            if (
                self.id == other.id
                and self.mt == other.mt
                and self.pt == other.pt
                and self.Coor1 == other.Coor1
                and self.Coor2 == other.Coor2
                and self.Speed == other.Speed
                and self.sbt == other.sbt
                and self.sc == other.sc
                and self.z == other.z
                and self.Tool == other.Tool
                and self.p_mode == other.p_mode
                and self.p_ratio == other.p_ratio
                and self.pinch == other.pinch
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'QEntry'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, QEntry):
            if (
                self.id != other.id
                or self.mt != other.mt
                or self.pt != other.pt
                or self.Coor1 != other.Coor1
                or self.Coor2 != other.Coor2
                or self.Speed != other.Speed
                or self.sbt != other.sbt
                or self.sc != other.sc
                or self.z != other.z
                or self.Tool != other.Tool
                or self.p_mode != other.p_mode
                or self.p_ratio != other.p_ratio
                or self.pinch != other.pinch
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'QEntry'!"
            )

        return False


    def print_short(self) -> str:
        """prints only most important parameters, saving display space"""

        return (
            f"ID: {self.id} -- {self.mt}, {self.pt} -- "
            f"COOR_1: {self.Coor1} -- SV: {self.Speed} -- "
            f"PM/PR,PIN:  {self.p_mode}/{self.p_ratio}, {self.pinch}"
        )



class Queue:
    """QEntry-based list incl. data handling

    ATTRIBUTES:
        queue:
            a list of QEntry elements, careful: list index does not match
            QEntry.id

    METHODS:
        __add__, __init__, __iter__, __getitem__, __len__, __next__,
        __str__, __eq__

        last_entry:
            returns last entry
        id_pos:
            returns queue entry index(!) of given ID
        entry_before_id
        id:
            returns entry before given ID
        display:
            returns queue as a str list (uses QEntry.print_short())
        increment:
            increments all QEntry.ID to handle DC commands send before
            the queue
        add:
            adds a new QEntry to queue, checks if QEntry.ID makes sense,
            places QEntry in queue according to the ID given
        add_queue:
            adds another queue, hopefully less time-consuming than a for loop
            with self.add
        append:
            other than '.add' this simply appends an entry indifferently to
            its ID
        clear:
            deletes single or multiple QEntry from queue, adjusts following
            ID accordingly
        pop_first_item:
            returns and deletes the QEntry at index 0
    """

    _iter_value = 0


    def __add__(self, other) -> 'Queue':

        if not isinstance(other, Queue):
            raise ValueError(f"{other} is not an instance of 'Queue'!")
        self.add_queue(other)
        return self


    def __init__(self, queue=None) -> None:

        self._queue = [] if (queue is None) else queue


    def __getitem__(self, i) -> QEntry | None:

        try:
            return self._queue[i]
        except IndexError:
            return None
    

    def __iter__(self) -> 'Queue':

        self._iter_value = 0
        return self


    def __len__(self) -> int:

        return len(self._queue)
    

    def __next__(self) -> QEntry:
        
        val = self._iter_value

        if val >= len(self):
            raise StopIteration
        
        self._iter_value = val + 1
        return self[val]


    def __str__(self) -> str:

        if len(self) != 0:
            ans = ''
            for x in self._queue:
                ans += f'{x}\n'
            return ans
        
        return 'Queue is empty!'


    def __eq__(self, other) -> bool:

        if isinstance(other, Queue):
            length = len(self)
            if length != len(other):
                return False

            for elem in range(length):
                if self[elem] != other[elem]:
                    return False

            return True

        elif other is not None:
            raise ValueError(f"{other} is not an instance of 'Queue'!")
        
        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, Queue):
            length = len(self)
            if length != len(other):
                return True

            for elem in range(length):
                if self[elem] != other[elem]:
                    return True

            return False

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'Queue'!"
            )


    def last_entry(self) -> QEntry | None:
        """returns last item in queue (surprise!), returns None if queue
        is empty
        """

        if len(self) == 0:
            return None
        return self._queue[len(self) - 1]


    def id_pos(self, id:int) -> int | None:
        """return queue entry index(!) at given ID, not the entry itself,
        returns None if no such entry
        """

        length = len(self)
        i = 0

        if length <= 0:
            return None

        for entry in range(length):
            if self[entry].id == id:
                break
            else:
                i += 1

        if i < 0 or i >= length:
            return None

        return i


    def entry_before_id(self, id:int) -> QEntry:
        """return queue entry before (index - 1) a specific ID, raises
        AttributeError if no such entry
        """

        length = len(self)
        i = 0

        if length <= 0:
            raise AttributeError

        for j in range(length):
            if self[j].id == id:
                break
            else:
                i += 1

        if i < 1 or i >= length:
            raise AttributeError

        return self[i - 1]


    def display(self) -> list[str]:
        """returns queue as a str list (uses QEntry.print_short())"""

        if len(self) != 0:
            ans = []

            for x in self:
                if not isinstance(x, QEntry):
                    raise ValueError(
                        f"could not print entry '{x}', it's not 'QEntry' type!"
                    )
                ans.append(x.print_short())

            return ans
        return ['Queue is empty!']


    def increment(self, summand=1) -> None:
        """increments all QEntry.ID to handle DC commands send before the
        queue
        """

        for i in self:
            i.id += int(summand)


    def add(self, entry:QEntry, thread_call=False) -> None | Exception:
        """adds a new QEntry to queue, checks if QEntry.ID makes sense, places
        QEntry in queue according to the ID given, threadCall option allows
        the first ID to be 0
        """

        new_entry = dcpy(entry)
        last_item = len(self) - 1
        if not isinstance(new_entry, QEntry):
            return ValueError('entry is not an instance of QEntry')

        if last_item < 0:
            global SC_curr_comm_id
            if not thread_call:
                new_entry.id = SC_curr_comm_id
            self._queue.append(new_entry)
            return None

        last_id = self[last_item].id
        first_id = self[0].id

        if new_entry.id == 0 or new_entry.id > last_id:
            if thread_call and new_entry.id == 0:
                self.increment()
                self._queue.insert(0, new_entry)
            else:
                new_entry.id = last_id + 1
                self._queue.append(new_entry)

        elif new_entry.id < 0:
            return ValueError

        else:
            if new_entry.id < first_id:
                new_entry.id = first_id

            front_skip = new_entry.id - first_id
            self._queue.insert(front_skip, new_entry)
            for i in range(last_item + 1 - front_skip):
                i += 1
                self[i + front_skip].id += 1

        return None


    def add_queue(self, add_queue:'Queue') -> None | Exception:
        """adds another queue, hopefully less time-consuming than a for loop
        with self.add
        """

        new_list = dcpy(add_queue)
        if not isinstance(new_list, Queue):
            return ValueError(f"{new_list} is not an instance of 'Queue'!")
        try:
            nl_first_id = new_list[0].id
        except Exception as err:
            return err

        last_item = len(self) - 1
        # if current queue is empty
        if last_item < 0:
            global SC_curr_comm_id
            if nl_first_id != SC_curr_comm_id:
                new_list.increment(SC_curr_comm_id - nl_first_id)
            self._queue.extend(new_list._queue)
            return

        len_new_list = len(new_list)
        last_id = self[last_item].id
        first_id = self[0].id

        if (nl_first_id > last_id + 1) or (nl_first_id == 0):
            new_list.increment(last_id + 1 - nl_first_id)
            nl_first_id = last_id + 1
            
        if nl_first_id == (last_id + 1):
            self._queue.extend(new_list._queue)
        
        else:
            if nl_first_id < first_id:
                new_list.increment(first_id - nl_first_id)
                nl_first_id = first_id
            front_skip = nl_first_id - first_id
            for i in range(len(self) - front_skip):
                self[i + front_skip].id += len_new_list
            self._queue[front_skip:front_skip] = new_list._queue


    def append(self, entry:QEntry) -> None:
        """other than '.add' this simply appends an entry indifferently
        to its ID
        """

        new_entry = dcpy(entry)
        self._queue.append(new_entry)
        return None


    def clear(self, all=True, id='') -> None:
        """deletes single or multiple QEntry from queue, adjusts following
        ID accordingly
        """

        if all:
            self._queue = []
            return

        if len(self) == 0:
            return

        ids = re.findall(r'\d+', id)
        id_num = len(ids)
        first_id = self[0].id
        last_id = self[len(self) - 1].id

        match id_num:
            case 1:
                id1 = int(ids[0])
                if id1 < first_id or id1 > last_id:
                    return

                i = 0
                for entry in self:
                    if entry.id == id1:
                        break
                    else:
                        i += 1

                self._queue.__delitem__(i)
                while i < len(self):
                    self[i].id -= 1
                    i += 1

            case 2:
                id1, id2 = int(ids[0]), int(ids[1])
                if (
                    id1 < first_id
                    or id1 > last_id
                    or id2 < id1
                    or id2 > last_id
                    or id.find('..') == -1
                ):
                    return

                id_dist = id2 - id1 + 1
                i = 0
                for entry in self:
                    if entry.id == id1:
                        break
                    else:
                        i += 1
                
                # dont get confused, I'm iterating for the num of entries to
                # delete, but I'm always deleting the i-th entry as the stack
                # moves along
                for n in range(id_dist):
                    self._queue.__delitem__(i)

                while i < len(self):
                    self[i].id -= id_dist
                    i += 1

            case _:
                return


    def pop_first_item(self) -> QEntry | Exception:
        """returns and deletes the QEntry at index 0"""

        if len(self) <= 0:
            return BufferError('Queue empty!')

        entry = self[0]
        self._queue.__delitem__(0)
        return entry



class RoboTelemetry:
    """class used to store the standard 36 byte telemetry data comming from
    the robot

    ATTRIBUTES:
        t_speed:
            speed with that the tool center point (TCP) is moving
        id:
            command ID the robot is currently processing
        Coor:
            current coordinate of the TCP, see Coordinates class

    METHODS:
        __init__, __str__, __round__, __eq__
    """


    def __init__(self, t_speed=0.0, id=-1, Coor=None) -> None:

        self.t_speed = float(t_speed)
        self.id = int(id)

        # handle those beasty mutables
        self.Coor = Coordinate() if (Coor is None) else Coor


    def __str__(self) -> str:

        return (
            f"ID: {self.id}   X: {self.Coor.x}   Y: {self.Coor.y}   "
            f"Z: {self.Coor.z}   Rx: {self.Coor.rx}   Ry: {self.Coor.ry}   "
            f"Rz: {self.Coor.rz}   EXT:   {self.Coor.ext}   "
            f"TOOL_SPEED: {self.t_speed}"
        )


    def __round__(self, digits) -> 'RoboTelemetry':

        return RoboTelemetry(
            round(self.t_speed, digits), self.id, round(self.Coor, digits)
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, RoboTelemetry):
            if (
                self.t_speed == other.t_speed
                and self.id == other.id
                and self.Coor == other.Coor
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'RoboTelemetry'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, RoboTelemetry):
            if (
                self.t_speed != other.t_speed
                or self.id != other.id
                or self.Coor != other.Coor
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'RoboTelemetry'!"
            )

        return False



class PumpTelemetry:
    """class used to store the standard telemetry data the pump

    ATTRIBUTES:
        freq:
            motor frequency (currently only given as 0 - 100%)
        volt:
            voltage at motor coil (presumably V, but the values seem to high)
        amps:
            current in motor coil (unit unknown, as for volt)
        torq:
            torque, probably in Nm

    METHODS:
        __init__, __str__, __round__, __eq__
    """


    def __init__(self, freq=0.0, volt=0.0, amps=0.0, torq=0.0) -> None:

        self.freq = float(freq)
        self.volt = float(volt)
        self.amps = float(amps)
        self.torq = float(torq)


    def __str__(self) -> str:

        return (
            f"FREQ: {self.freq}   VOLT: {self.volt}   "
            f"AMPS: {self.amps}   TORQ: {self.torq}"
        )


    def __round__(self, digits) -> 'PumpTelemetry':

        return PumpTelemetry(
            round(self.freq, digits),
            round(self.volt, digits),
            round(self.amps, digits),
            round(self.torq, digits),
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, PumpTelemetry):
            if (
                self.freq == other.freq
                and self.volt == other.volt
                and self.amps == other.amps
                and self.torq == other.torq
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance 'PumpTelemetry'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, PumpTelemetry):
            if (
                self.freq != other.freq
                or self.volt != other.volt
                or self.amps != other.amps
                or self.torq != other.torq
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance 'PumpTelemetry'!"
            )

        return False


class TSData:
    """simple descriptor for timestamped data, will take values but only
    return them if there less old than the valid_time, otherwise returns None.
    
    ATTRIBUTES:
        val:
            the value itself
        created_at:
            creation or change time timestamp
        valid_time:
            user_defined time, the value remains valid

    METHODS:
        __init__, __get__, __set__, __eq__, __ne__, __str__
    """

    def __init__(self, val=0.0) -> None:
        self.val = float(val)
        self._created_at = datetime.now()


    def __get__(self, instance, owner) -> float | None:
        age = datetime.now() - self._created_at
        if age < instance.valid_time:
            return self.val
        return None
    

    def __set__(self, instance, value) -> None:
        self._created_at = datetime.now()
        if isinstance(value, TSData):
            self.val = float(value.val)
        elif isinstance(value, (float, int)):
            self.val = float(value)
        elif value is None:
            self.val = None
        else:
            raise ValueError(f"new value can not be of type {type(value)}!")
    
    
    def __eq__(self, other):
        if isinstance(other, TSData):
            if self.val == other.val:
                return True
        elif isinstance(other, (float, int)):
            if self.val == other:
                return True
        else:
            raise ValueError(
                f"{other} is not comparable to {TSData}!"
            )
        return False
    
    
    def __ne__(self, other):
        if isinstance(other, TSData):
            if self.val != other.val:
                return True
        elif isinstance(other, (float, int)):
            if self.val != other:
                return True
        else:
            raise ValueError(
                f"{other} is not comparable to {TSData}!"
            )
        return False


    def __str__(self) -> str:
        return f"{self.__get__(self, None)}"





class DaqBlock:
    """structure for DAQ, uses TSData (except for Robo & Pumps) which have to
    be updated periodically to stay valid, for more see TSData() 

    ATTRIBUTES:
        Robo:
            RoboTelemetry datablock
        Pump1:
            PumpTelemetry datablock for pump 1
        Pump2:
            PumpTelemetry datablock for pump 2
        amb_temp:
            ambient temperature [°C]
        amb_humidity:
            ambient humidity [%]
        rb_temp:
            RB = robot base; temperature of the mortar tube at the second
            coupling [°C]
        msp_temp:
            MSP = main supply pump; temperature behind pump1's moineur
            pump [°C]
        msp_press:
            MSP = main supply pump; pressure behind pump1's moineur pump [bar]
        asp_freq:
            ASP = admixture supply pump; frequency of the admixture delivery
            pump
        asp_amps:
            ASP = admixture supply pump; current of the admixture delivery
            pump
        imp_temp:
            IMP = inline mixing pump; temperature behind the 2K pump [°C]
        imp_press:
            IMP = inline mixing pump; pressure in front of 2K pump [bar]
        imp_freq:
            IMP = inline mixing pump; frequency of the 2K pump
        imp_amps:
            IMP = inline mixing pump; current of the 2K pump
        phc_aircon:
            PHC = print head controller; air bubble/content analysis
            (not specified yet)
        phc_fdist:
            PHC = print head controller; deposition layer distance in front
            of the nozzle
        phc_edist:
            PHC = print head controller; deposition layer distance behind
            the nozzle

    METHODS:
        __init__, __str__, __eq__,

        store:
            Stores data according to key and sub_key, mutual exclusion needs to
            be called beforehand, as values are stored in global variables.
    """

    amb_temp = TSData()
    amb_humidity = TSData()
    rb_temp = TSData()
    msp_temp = TSData()
    msp_press = TSData()
    asp_freq = TSData()
    asp_amps = TSData()
    imp_temp = TSData()
    imp_press = TSData()
    imp_freq = TSData()
    imp_amps = TSData()
    phc_aircon = TSData()
    phc_fdist = TSData()
    phc_edist = TSData()
    
    def __init__(
            self,
            amb_temp=0.0,
            amb_humidity=0.0,
            rb_temp=0.0,
            msp_temp=0.0,
            msp_press=0.0,
            asp_freq=0.0,
            asp_amps=0.0,
            imp_temp=0.0,
            imp_press=0.0,
            imp_freq=0.0,
            imp_amps=0.0,
            Robo=None,
            Pump1=None,
            Pump2=None,
            phc_aircon=0.0,
            phc_fdist=0.0,
            phc_edist=0.0,
    ) -> None:
        global DEF_STT_VALID_TIME

        self.amb_temp = TSData(amb_temp)
        self.amb_humidity = TSData(amb_humidity)
        self.rb_temp = TSData(rb_temp)
        self.msp_temp = TSData(msp_temp)
        self.msp_press = TSData(msp_press)
        self.asp_freq = TSData(asp_freq)
        self.asp_amps = TSData(asp_amps)
        self.imp_temp = TSData(imp_temp)
        self.imp_press = TSData(imp_press)
        self.imp_freq = TSData(imp_freq)
        self.imp_amps = TSData(imp_amps)
        self.phc_aircon = TSData(phc_aircon)
        self.phc_fdist = TSData(phc_fdist)
        self.phc_edist = TSData(phc_edist)
        self.valid_time = DEF_STT_VALID_TIME

        # handle those beasty mutables
        self.Robo = RoboTelemetry() if (Robo is None) else Robo
        self.Pump1 = PumpTelemetry() if (Pump1 is None) else Pump1
        self.Pump2 = PumpTelemetry() if (Pump2 is None) else Pump2


    def __str__(self) -> str:

        return (
            f"Amb. temp.: {self.amb_temp}    Amb. humid.: {self.amb_humidity}"
            f"    RB temp.: {self.rb_temp}    MSP temp.: {self.msp_temp}    "
            f"MSP press.: {self.msp_press}    APS freq.: {self.asp_freq}    "
            f"APS amp.: {self.asp_amps}    IMP temp.: {self.imp_temp}    "
            f"IMP press.: {self.imp_press}    IMP freq.: {self.imp_freq}    "
            f"IMP amp.: {self.imp_amps}    ROB: {self.Robo}    "
            f"PUMP1: {self.Pump1}    PUMP2: {self.Pump2}    "
            f"PHC air cont.: {self.phc_aircon}    "
            f"PHC front dist.: {self.phc_fdist}    "
            f"PHC end dist.: {self.phc_edist}"
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, DaqBlock):
            if (
                self.amb_temp == other.amb_temp
                and self.amb_humidity == other.amb_humidity
                and self.msp_temp == other.msp_temp
                and self.rb_temp == other.rb_temp
                and self.imp_temp == other.imp_temp
                and self.msp_press == other.msp_press
                and self.imp_press == other.imp_press
                and self.Pump1 == other.Pump1
                and self.Pump2 == other.Pump2
                and self.asp_freq == other.asp_freq
                and self.asp_amps == other.asp_amps
                and self.imp_freq == other.imp_freq
                and self.imp_amps == other.imp_amps
                and self.Robo == other.Robo
                and self.phc_aircon == other.phc_aircon
                and self.phc_fdist == other.phc_fdist
                and self.phc_edist == other.phc_edist
            ):
                return True

        elif other is not None:
            raise ValueError(
                f"{other} is not None or an instance of 'DaqBlock'!"
            )

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, DaqBlock):
            if (
                self.amb_temp != other.amb_temp
                or self.amb_humidity != other.amb_humidity
                or self.msp_temp != other.msp_temp
                or self.rb_temp != other.rb_temp
                or self.imp_temp != other.imp_temp
                or self.msp_press != other.msp_press
                or self.imp_press != other.imp_press
                or self.Pump1 != other.Pump1
                or self.Pump2 != other.Pump2
                or self.asp_freq != other.asp_freq
                or self.asp_amps != other.asp_amps
                or self.imp_freq != other.imp_freq
                or self.imp_amps != other.imp_amps
                or self.Robo != other.Robo
                or self.phc_aircon != other.phc_aircon
                or self.phc_fdist != other.phc_fdist
                or self.phc_edist != other.phc_edist
            ):
                return True

        else:
            raise ValueError(
                f"{other} is not None or an instance of 'DaqBlock'!"
            )

        return False


    def store(self, data:tuple, key:str, sub_key:str) -> None:
        """Stores data according to key and sub_key, mutual exclusion needs to
        be called beforehand, as values are stored in global variables. If
        val_age (from data) exceeds the value-specific valid_time, nothing
        will be done

        accepts: 
            data:
                data to be stored, expected as a tuple: (value, uptime)
            key:
                superior key in du.SEN_dict, specifying sensor location
            sub_key:
                inferior key in du.SEN_dict, specifying parameter type
        """

        val, val_age = data
        if val_age > self.valid_time.seconds: 
            return
        err =  KeyError(f"no storage reserved for {sub_key} in {key}!")
        match key:
            case 'amb':
                match sub_key:
                    case 'temp': self.amb_temp = val
                    case 'humid': self.amb_humidity = val
                    case _: raise err
            case 'asp': 
                match sub_key:
                    case 'freq': self.asp_freq = val
                    case 'amps': self.asp_amps = val
                    case _: raise err
            case 'rb':
                match sub_key:
                    case 'temp': self.rb_temp = val
                    case _: raise err
            case 'msp': 
                match sub_key:
                    case 'temp': self.msp_temp = val
                    case 'press': self.msp_press = val
                    case _: raise err
            case 'imp':
                match sub_key:
                    case 'temp': self.imp_temp = val
                    case 'press': self.imp_press = val
                    case 'freq': self.imp_freq = val
                    case 'amps': self.imp_amps = val
                    case _: raise err
            case 'phc':
                match sub_key:
                    case 'aircon': self.imp_temp = val
                    case 'fdist': self.imp_press = val
                    case 'edist': self.imp_freq = val
                    case _: raise err
            case _:
                raise KeyError(
                    f"no storage reserved for {key} in du.STTDataBlock!"
                )
            
        return None
    
    
    @property
    def valid_time(self):
        return self._valid_time
    
    
    @valid_time.setter
    def valid_time(self, new_valid_time):
        # convert to int
        new_valid_time = int(round(new_valid_time, 0))
        self._valid_time = timedelta(seconds=new_valid_time) 



class TCPIP:
    """setup class for TCP/IP connection, provides all functions concerning
    the connection

    ATTRIBUTES:
        ip:
            endpoint IP address
        port:
            endpoint port nummber
        c_tout:
            timeout for connection attempts to endpoint
        rw_tout:
            timeout for reading from or writing to endpoint
        r_bl:
            data block length to read
        w_bl:
            data block length to write

    METHODS:
        __init__, __str__

        connect:
            tries to connect to the IP and PORT given, returns errors if
            not possible
        send:
            send data to server according to class attributes
        receive:
            receive according to class attributes
        close:
            close TCP/IP connection
    """


    def __init__(
            self,
            ip='',
            port=0,
            c_tout=1.0,
            rw_tout=1,
            r_bl=0,
            w_bl=0
    ) -> None:

        self.ip = str(ip)
        self.port = str(port)
        self.c_tout = float(c_tout)
        self.rw_tout = float(rw_tout)
        self.r_bl = int(r_bl)
        self.w_bl = int(w_bl)

        self.connected = False
        self._Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def __str__(self) -> str:

        return (
            f"IP: {self.ip}   PORT: {self.port}   "
            f"C_TOUT: {self.c_tout}   RW_TOUT: {self.rw_tout}   "
            f"R_BL: {self.r_bl}   W_BL: {self.w_bl}"
        )


    def set_params(self, param_dict) -> None:

        if self.connected:
            raise PermissionError(
                'params not changeable while connected to server!'
            )

        self.ip = str(param_dict['ip'])
        self.port = str(param_dict['port'])
        self.c_tout = float(param_dict['c_tout'])
        self.rw_tout = float(param_dict['rw_tout'])
        self.r_bl = int(param_dict['r_bl'])
        self.w_bl = int(param_dict['w_bl'])


    def connect(self) -> tuple[str, int] | Exception:
        """tries to connect to the IP and PORT given, returns errors if
        not possible
        """

        try:
            server_address = (self.ip, int(self.port))
        except ValueError:
            raise ConnectionError("requested TCP/IP connection via COM-Port!")

        self._Socket.settimeout(self.c_tout)

        try:
            self._Socket.connect(server_address)
            self.connected = True
            self._Socket.settimeout(self.rw_tout)

        except Exception as err:
            self.connected = 0
            return err

        return server_address


    def send(self, data=None) -> tuple[bool, int | Exception]:
        """send data to server according to class attributes"""

        if not self.connected:
            return False, ConnectionError(f"no active connection")
        if len(data) != self.w_bl:
            return False, ValueError('wrong message length')

        try:
            self._Socket.sendall(data)
        except Exception as err:
            return False, err

        return True, len(data)


    def receive(self) -> tuple[bool, bytes | Exception]:
        """receive according to class attributes"""

        data = ''

        try:
            while len(data) < self.r_bl:
                data = self._Socket.recv(self.r_bl)

            if len(data) != self.r_bl:
                raise ValueError('wrong server answer length')

        except Exception as err:
            return False, err

        return True, data


    def close(self, end=False) -> None:
        """close TCP connection; restarts the socket, if end isnt set to True
        """

        self._Socket.close()
        self.connected = False
        if not end:
            self._Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



class RobConnection(TCPIP):
    """sets robot specific send/receive operations, inherits from TCPIP class,
    overwrites send & receive functions

    ATTRIBUTES:
        inherited from ~TCPIP class

    METHODS (redefinition of ~TCPIP methods):
        send:
            sends a QEntry object to server, packing according to robots
            protocol
        receive:
            receives and unpacks data from robot, returns it as RobTelemetry
            object
    """


    def send(self, entry) -> tuple[bool, int | Exception]:
        """sends QEntry object to robot, packing according to robots protocol
        """

        message = []

        try:
            if not self.connected:
                raise ConnectionError
            if not isinstance(entry, QEntry):
                raise ValueError(f"{entry} is not an instance of 'QEntry'!")

            message = struct.pack(
                '<iccffffffffffffffffiiiiiciiiiiiiiiiiiiii',
                entry.id,
                bytes(entry.mt, 'utf-8'),
                bytes(entry.pt, 'utf-8'),
                entry.Coor1.x,
                entry.Coor1.y,
                entry.Coor1.z,
                entry.Coor1.rx,
                entry.Coor1.ry,
                entry.Coor1.rz,
                entry.Coor1.q,
                entry.Coor1.ext,
                entry.Coor2.x,
                entry.Coor2.y,
                entry.Coor2.z,
                entry.Coor2.rx,
                entry.Coor2.ry,
                entry.Coor2.rz,
                entry.Coor2.q,
                entry.Coor2.ext,
                entry.Speed.acr,
                entry.Speed.dcr,
                entry.Speed.ts,
                entry.Speed.ors,
                entry.sbt,
                bytes(entry.sc, 'utf-8'),
                entry.z,
                0, # ID int, always 0
                entry.Tool.trolley_steps,
                0,
                # byte for cutter position, but simply coupled to cutting here 
                # as no other usage makes sense
                entry.Tool.cut,
                0,
                entry.Tool.load_spring,
                0,
                entry.Tool.cut,
                0,
                entry.Tool.place_spring,
                0,
                entry.Tool.clamp,
                0,
                entry.Tool.wait,
            )

            if len(message) != self.w_bl:
                raise ValueError('wrong message length')

            self._Socket.sendall(message)

        except Exception as err:
            return False, err

        print(f"SEND:    {entry.id}, length: {len(message)}")
        return True, len(message)


    def receive(self) -> tuple[RoboTelemetry | Exception, bytes]:
        """receives and unpacks data from robot"""

        data = b''
        Telem = RoboTelemetry()

        try:
            while len(data) < self.r_bl:
                data = self._Socket.recv(self.r_bl)

            if len(data) != self.r_bl:
                raise ValueError

        except Exception as err:
            return err, data

        Telem.t_speed = struct.unpack('<f', data[0:4])[0]
        Telem.id = struct.unpack('<i', data[4:8])[0]
        Telem.Coor.x = struct.unpack('<f', data[8:12])[0]
        Telem.Coor.y = struct.unpack('<f', data[12:16])[0]
        Telem.Coor.z = struct.unpack('<f', data[16:20])[0]
        Telem.Coor.rx = struct.unpack('<f', data[20:24])[0]
        Telem.Coor.ry = struct.unpack('<f', data[24:28])[0]
        Telem.Coor.rz = struct.unpack('<f', data[28:32])[0]
        Telem.Coor.ext = struct.unpack('<f', data[32:36])[0]
        return Telem, data




#########################     GLOBALS CONST     #############################

# defaut connection settings (the byte length for writing to the robot
# wont be user setable for safety reasons, it can only be changed here, but 
# only if you know what your doing!)

# MTEC P20 DEFAULT SETTINGS
DEF_PUMP_CLASS1 = 75.0
DEF_PUMP_CLASS2 = 50.0
DEF_PUMP_LPS = 0.5
DEF_PUMP_RETR_SPEED = -50.0 # [%]
DEF_PUMP_SERIAL = {
    'baud': 19200,
    'par': serial.PARITY_NONE,
    'stop': serial.STOPBITS_TWO,
    'size': serial.EIGHTBITS,
    'port': 'COM3',
}
DEF_PUMP_OUTP_RATIO = 1.0
DEF_PUMP_VALID_COMMANDS = [
    -1001, # = no p_mode
    1001, # default mode
    1002, # start profile
    1003, # end profile
    1101, # class 1 profile
    1102, # class 2 profile
]

# ROBOT DEFAULT SETTINGS
DEF_ROB_BUFF_SIZE = 3000
DEF_ROB_COMM_FR = 10
DEF_ROB_COOR_CHK_RANGE = ( # to-do: better mapping
    Coordinate(-1600.0, 1200.0, -80.0, 0.0, 0.0, 0.0, 0.0, 10.0),
    Coordinate(3500.0, 2600.0, 2000.0, 360.0, 360.0, 360.0, 1.0, 3000.0),
)
DEF_ROB_TCP = {
    'ip': '192.168.125.1',
    'port': 10001,
    'c_tout': 60000,
    'rw_tout': 5,
    'r_bl': 36,
    'w_bl': 151,
}

# GENERAL DEFAULT SETTINGS
DEF_DC_SPEED = SpeedVector()
DEF_ICQ_MAX_LINES = 200
DEF_IO_FR_TO_TS = 0.1
DEF_IO_ZONE = 10 # [mm]
DEF_PRH_CLAMP = False
DEF_PRH_CUT = False
DEF_PRH_PLACE_SPR = False
DEF_PRH_TROLLEY = 0
DEF_PRH_WAIT = 0
DEF_PRIN_SPEED = SpeedVector()
DEF_SC_EXT_FLLW_BHVR = (5, 2) # [mm]
DEF_SC_MAX_LINES = 400
DEF_SC_VOL_PER_M = 0.4  # [L/m] calculated for 1m of 4cm x 1cm high filament
DEF_STT_VALID_TIME = 60 # [seconds]
DEF_TERM_MAX_LINES = 300
DEF_TOOL_TROL_RATIO = 500
DEF_WD_TIMEOUT = 10000 # [ms]


##########################     GLOBALS VARS     ##############################

# GENERAL SETTINGS
CAM_urls = [
    'rtsp://admin:KameraNr4@192.168.178.51:554/ch1/main/av_stream',
    'rtsp://admin:KameraNr1@192.168.178.38:554/ch1/main/av_stream',
]
DC_rob_moving = False
DCCurrZero = Coordinate()
DCSpeed = dcpy(DEF_DC_SPEED)
IO_curr_filepath = None
IO_fr_to_ts = DEF_IO_FR_TO_TS
IO_zone = DEF_IO_ZONE
LOG_safe_path = Path()
PRINSpeed = dcpy(DEF_PRIN_SPEED)
SC_curr_comm_id = 1
SC_ext_fllw_bhvr = DEF_SC_EXT_FLLW_BHVR
SC_q_prep_end = False
SC_q_processing = False
SC_vol_per_m = DEF_SC_VOL_PER_M
SCBreakPoint = Coordinate() # to-do: write routine to stop at predefined point during SC using this Coordinate + decide if useful
SCQueue = Queue()
STTDataBlock = DaqBlock()
TERM_log = []
TOOL_trol_ratio = DEF_TOOL_TROL_RATIO

# DATABASE SETTINGS
DB_log_interval = 10
DB_org = 'MC3DB'
DB_session = 'not set'
DB_token = None
DB_url = '192.168.178.50:8086'

# PRINTHEAD SETTINGS
PRH_act_with_pump = False
MIX_last_speed = 0.0
MIX_max_speed = 300.0 # [rpm]
MIX_speed = 0.0
PRH_connected = False
PRH_url = '192.168.178.58:17'

# MTEC P20 SETTINGS
PMP_comm_active = False
PMP_output_ratio = DEF_PUMP_OUTP_RATIO
PMP_port = DEF_PUMP_SERIAL['port']
PMP_retract_speed = DEF_PUMP_RETR_SPEED
PMP_serial_def_bus = None  # is created after user input in win_mainframe
PMP_speed = 0
PMP1_liter_per_s = DEF_PUMP_LPS
PMP1_live_ad = 1.0
PMP1_modbus_id = '01'
PMP1_speed = 0
PMP1_user_speed = -999
PMP1LastTelem = PumpTelemetry()
PMP1Serial = MtecMod(None, PMP1_modbus_id)
PMP2_liter_per_s = DEF_PUMP_LPS
PMP2_live_ad = 1.0
PMP2_modbus_id = '02'
PMP2_speed = 0
PMP2_user_speed = -999
PMP2LastTelem = PumpTelemetry()
PMP2Serial = MtecMod(None, PMP2_modbus_id)

# ROBOT SETTINGS
ROB_comm_fr = DEF_ROB_COMM_FR
ROB_live_ad = 1.0
ROB_send_list = []
ROB_speed_overwrite = -1
ROBCommQueue = Queue()
ROBLastTelem = RoboTelemetry()
ROBMovStartP = Coordinate()
ROBMovEndP = Coordinate()
ROBTelem = RoboTelemetry()
ROBTcp = RobConnection(
    DEF_ROB_TCP['ip'],
    DEF_ROB_TCP['port'],
    DEF_ROB_TCP['c_tout'],
    DEF_ROB_TCP['rw_tout'],
    DEF_ROB_TCP['r_bl'],
    DEF_ROB_TCP['w_bl'],
)

# SENSOR ARRAY SETTINGS
SEN_timeout = 0.5
SEN_dict = { # add available datasources here
    'amb': { # AMBient
        'ip': '192.168.178.36:17',
        'err': False,
        'temp': False,
        'humid': False,
    },
    'asp': { # Admixture Supply Pump
        'ip': '',
        'err': False,
        'freq': False,
        'amps': False,
    },
    'rb': { # Robot Base
        'ip': '',
        'err': False,
        'temp': False,
    },
    'msp': { # Main Supply Pump
        'ip': '192.168.178.36:17',
        'err': False,
        'temp': True,
        'pressure': False,
    },
    'imp': { # Inline Mixing Pump
        'ip': '',
        'err': False,
        'temp': False,
        'pressure': False,
        'freq': False,
        'amps': False
    },
    'phc': { # Print Head Controller
        'ip': '',
        'err': False,
        'aircon': False,
        'fdist': False,
        'edist': False
    }
}