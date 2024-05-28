#   This work is licensed under Creativ Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
#   (https://creativecommons.org/licenses/by-sa/4.0/). Feel free to use, modify or distribute this code as
#   far as you like, so long as you make anything based on it publicly avialable under the same license.


#######################################     IMPORTS      #####################################################

import re
import os
import sys
import copy
import serial
import socket
import struct

from datetime import datetime, timedelta

# appending the parent directory path
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# import interface for Toshiba frequency modulator by M-TEC
from mtec.mtec_mod import MtecMod


##############################################################################
#                                  CLASSES                                   #
##############################################################################

class Coordinate:
    """standard 7-axis coordinate block (8 attributes, as quaterion
    positioning is possible)

    ATTRIBUTES:
        x, y, z:
            position in cartesian coordinates
        rx, ry, rz:
            angle relative to cartesian coordinates
        q:
            additional var for fourth quaternion coordinate
        ext:
            external axis position

    FUNCTIONS:
        __init__, __str__, __add__, __sub__, __round__, __eq__, __ne__
    """

    def __init__(self, x=0.0, y=0.0, z=0.0, rx=0.0, ry=0.0, rz=0.0, q=0.0, ext=0.0) -> None:

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
            raise ValueError(f"{other} is not None or an instance of 'Coordinate'!")

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
            raise ValueError(f"{other} is not None or an instance of 'Coordinate'!")

        return False



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

    FUNCTIONS:
        __init__, __str__, __mul__, __rmul__, __eq__, __ne__
    """


    def __init__(self, acr=50, dcr=50, ts=200, ors=50) -> None:

        self.acr = int(round(acr, 0))
        self.dcr = int(round(dcr, 0))
        self.ts = int(round(ts, 0))
        self.ors = int(round(ors, 0))


    def __str__(self) -> str:

        return f"TS: {self.ts}   OS: {self.ors}   ACR: {self.acr}   DCR: {self.dcr}"


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
            raise ValueError(f"{other} is not None or an instance of 'SpeedVector'!")

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
            raise ValueError(f"{other} is not None or an instance of 'SpeedVector'!")

        return False



class ToolCommand:
    """standard tool command according to Jonas' protocol

    ATTRIBUTES:
        pan_id:
            motor 1 ID (fiber pivoting)
        pan_steps:
            motor 1 steps/position
        fib_deliv_id:
            motor 2 ID (fiber delivery)
        fib_deliv_steps:
            motor 2 steps/position
            used as [%] when move type is 'V'
            used as motor steps when move type is 'T'
        mor_pump_id:
            motor 3 ID (mortar pump)
        mor_pump_steps:
            motor 3 steps/position
        pnmtc_clamp_id:
            pneumatic fiber clamp ID
        pnmtc_clamp_yn:
            pneumatic fiber clamp on/off
        knife_pos_id:
            knife delivery ID
        knife_pos_yn:
            knife delivery on/off
        knife_id:
            motor 4 ID (rotation knife)
        knife_yn:
            motor 4 on/off
        pnmtc_fiber_id:
            pneumatic fiber conveyer ID
        pnmtc_fiber_yn:
            pneumatic fiber conveyer on/off
        time_id:
            time ID
        time_time:
            current time in milli seconds at EE

    FUNCTIONS:
        __def__, __str__, __eq__
    """


    def __init__(
        self,
        pan_id=0,
        pan_steps=0,
        fib_deliv_id=0,
        fib_deliv_steps=0,
        mor_pump_id=0,
        mor_pump_steps=0,
        pnmtc_clamp_id=0,
        pnmtc_clamp_yn=0,
        knife_pos_id=0,
        knife_pos_yn=0,
        knife_id=0,
        knife_yn=0,
        pnmtc_fiber_id=0,
        pnmtc_fiber_yn=0,
        time_id=0,
        time_time=0,
    ) -> None:

        self.pan_id = int(pan_id)  # pivoting value
        self.pan_steps = int(pan_steps)
        self.fib_deliv_id = int(fib_deliv_id)  # fiber value (calculated with V-option)
        self.fib_deliv_steps = int(fib_deliv_steps)
        self.mor_pump_id = int(mor_pump_id)  # mortar pump
        self.mor_pump_steps = int(mor_pump_steps)
        self.pnmtc_clamp_id = int(pnmtc_clamp_id)
        self.pnmtc_clamp_yn = bool(pnmtc_clamp_yn)
        self.knife_pos_id = int(knife_pos_id)
        self.knife_pos_yn = bool(knife_pos_yn)
        self.knife_id = int(knife_id)
        self.knife_yn = bool(knife_yn)
        self.pnmtc_fiber_id = int(pnmtc_fiber_id)
        self.pnmtc_fiber_yn = bool(pnmtc_fiber_yn)
        self.time_id = int(time_id)
        self.time_time = int(time_time)


    def __str__(self) -> str:

        return (
            f"PAN: {self.pan_id}, {self.pan_steps}   "
            f"FB: {self.fib_deliv_id}, {self.fib_deliv_steps}   "
            f"MP: {self.mor_pump_id}, {self.mor_pump_steps}   "
            f"PC: {self.pnmtc_clamp_id}, {self.pnmtc_clamp_yn}   "
            f"KP: {self.knife_pos_id}, {self.knife_pos_yn}   "
            f"K: {self.knife_id}, {self.knife_yn}   "
            f"PF: {self.pnmtc_fiber_id}, {self.pnmtc_fiber_yn}   "
            f"TIME: {self.time_id}, {self.time_time}"
        )


    def __eq__(self, other) -> bool:

        if isinstance(other, ToolCommand):
            if (
                self.pan_id == other.pan_id
                and self.pan_steps == other.pan_steps
                and self.fib_deliv_id == other.fib_deliv_id
                and self.fib_deliv_steps == other.fib_deliv_steps
                and self.mor_pump_id == other.mor_pump_id
                and self.mor_pump_steps == other.mor_pump_steps
                and self.pnmtc_clamp_id == other.pnmtc_clamp_id
                and self.pnmtc_clamp_yn == other.pnmtc_clamp_yn
                and self.knife_pos_id == other.knife_pos_id
                and self.knife_pos_yn == other.knife_pos_yn
                and self.knife_id == other.knife_id
                and self.knife_yn == other.knife_yn
                and self.pnmtc_fiber_id == other.pnmtc_fiber_id
                and self.pnmtc_fiber_yn == other.pnmtc_fiber_yn
                and self.time_id == other.time_id
                and self.time_time == other.time_time
            ):
                return True

        elif other is not None:
            raise ValueError(f"{other} is not None or an instance of 'ToolCommand'!")

        return False


    def __ne__(self, other) -> bool:

        if other is None:
            return True
        
        elif isinstance(other, ToolCommand):
            if (
                self.pan_id != other.pan_id
                or self.pan_steps != other.pan_steps
                or self.fib_deliv_id != other.fib_deliv_id
                or self.fib_deliv_steps != other.fib_deliv_steps
                or self.mor_pump_id != other.mor_pump_id
                or self.mor_pump_steps != other.mor_pump_steps
                or self.pnmtc_clamp_id != other.pnmtc_clamp_id
                or self.pnmtc_clamp_yn != other.pnmtc_clamp_yn
                or self.knife_pos_id != other.knife_pos_id
                or self.knife_pos_yn != other.knife_pos_yn
                or self.knife_id != other.knife_id
                or self.knife_yn != other.knife_yn
                or self.pnmtc_fiber_id != other.pnmtc_fiber_id
                or self.pnmtc_fiber_yn != other.pnmtc_fiber_yn
                or self.time_id != other.time_id
                or self.time_time != other.time_time
            ):
                return True

        else:
            raise ValueError(f"{other} is not None or an instance of 'ToolCommand'!")

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
            time to calculate speed by
        sc:
            speed command, set movement speed by movement time (SBT) or speed
            vector (SV), (T = time, V = vector)
        z:
            zone, endpoint precision
        Tool:
            tool command in Jonas' standard format
        p_mode:
            option for automatic pump control

    FUNCTIONS:
        __init__, __str__, __eq__

        print_short:
            prints only most important parameters
    """


    def __init__(
        self,
        id=0,
        mt="L",
        pt="E",
        Coor1=None,
        Coor2=None,
        Speed=None,
        sbt=0,
        sc="V",
        z=10,
        Tool=None,
        p_mode=None,
    ) -> None:

        self.id = int(id)
        self.mt = str(mt)
        self.pt = str(pt)
        self.sbt = int(sbt)
        self.sc = str(sc)
        self.z = int(z)
        self.p_mode = str(p_mode)

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
            f"\n\t\t|| PMODE:  {self.p_mode}"
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
            ):
                return True

        elif other is not None:
            raise ValueError(f"{other} is not None or an instance of 'QEntry'!")

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
            ):
                return True

        else:
            raise ValueError(f"{other} is not None or an instance of 'QEntry'!")

        return False


    def print_short(self) -> str:
        """prints only most important parameters, saving display space"""

        return (
            f"ID: {self.id} -- {self.mt}, {self.pt} -- "
            f"COOR_1: {self.Coor1} -- SV: {self.Speed} -- "
            f"PMODE:  {self.p_mode}"
        )



class Queue:
    """QEntry-based list incl. data handling

    ATTRIBUTES:
        queue:
            a list of QEntry elements, careful: list index does not match QEntry.id

    FUNCTIONS:
        __add__, __init__, __iter__, __getitem__, __len__, __next__, __str__, __eq__

        last_entry:
            returns last entry
        id_pos:
            returns queue entry index(!) of given ID
        entry_befo
        id:
            returns entry before given ID
        display:
            returns queue as a str list (uses __str__ of QEntry)
        increment:
            increments all QEntry.ID to handle DC commands send before the queue
        add:
            adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given
        add_list:
            adds another queue, hopefully less time-consuming than a for loop with self.add
        append:
            other than '.add' this simply appends an entry indifferently to its ID
        clear:
            deletes single or multiple QEntry from queue, adjusts following ID accordingly
        pop_first_item:
            returns and deletes the QEntry at index 0
    """

    _iter_value = 0


    def __add__(self, other) -> 'Queue':

        if not isinstance(other, Queue):
            raise ValueError(f"{other} is not an instance of 'Queue'!")
        
        return self._queue + other._queue


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

        if val >= len(self._queue):
            raise StopIteration
        
        self._iter_value = val + 1
        return self._queue[val]


    def __str__(self) -> str:

        if len(self._queue) != 0:
            i = 0
            ans = ""

            for x in self._queue:
                i += 1
                ans += f"Element {i}: {x}\n"

            return ans
        return "Queue is empty!"


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
            raise ValueError(f"{other} is not None or an instance of 'Queue'!")


    def last_entry(self) -> QEntry | None:
        """returns last item in queue (surprise!), returns None if queue is empty"""

        if len(self._queue) == 0:
            return None
        return self._queue[len(self._queue) - 1]


    def id_pos(self, id) -> int | None:
        """return queue entry index(!) at given ID, not the entry itself, returns None if no such entry"""

        length = len(self._queue)
        i = 0

        if length <= 0:
            return None

        for entry in range(length):
            if self._queue[entry].id == id:
                break
            else:
                i += 1

        if i < 1 or i >= length:
            raise AttributeError

        return i


    def entry_before_id(self, id) -> QEntry:
        """return queue entry before (index - 1) a specific ID, raises AttributeError if no such entry"""

        length = len(self._queue)
        i = 0

        if length <= 0:
            raise AttributeError

        for j in range(length):
            if self._queue[j].id == id:
                break
            else:
                i += 1

        if i < 1 or i >= length:
            raise AttributeError

        return self._queue[i - 1]


    def display(self) -> list[str]:
        """returns queue as a str list (uses __str__ of QEntry)"""

        if len(self._queue) != 0:
            ans = []

            for x in self._queue:
                if not isinstance(x, QEntry):
                    raise ValueError(f"could not print entry '{x}', it's not 'QEntry' type!")
                ans.append(x.print_short())

            return ans
        return ["Queue is empty!"]


    def increment(self) -> None:
        """increments all QEntry.ID to handle DC commands send before the queue"""

        for i in self._queue:
            i.id += 1


    def add(self, entry, thread_call=False) -> None | Exception:
        """adds a new QEntry to queue, checks if QEntry.ID makes sense, places QEntry in queue according to the ID given
        threadCall option allows the first ID to be 0"""

        new_entry = copy.deepcopy(entry)
        last_item = len(self._queue) - 1

        if not isinstance(new_entry, QEntry):
            return ValueError('entry is not an instance of QEntry')

        if last_item < 0:
            global SC_curr_comm_id

            if not thread_call:
                new_entry.id = SC_curr_comm_id

            self._queue.append(new_entry)
            return None

        last_id = self._queue[last_item].id
        first_id = self._queue[0].id

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
                self._queue[i + front_skip].id += 1

        return None


    def add_list(self, list) -> None | Exception:
        """adds another queue, hopefully less time-consuming than a for loop with self.add"""

        new_list = copy.deepcopy(list)
        if not isinstance(new_list, Queue):
            return ValueError(f"{new_list} is not an instance of 'Queue'!")

        try:
            nl_first_id = new_list[0].id
        except Exception as err:
            return err

        last_item = len(self._queue) - 1
        len_new_list = len(new_list)

        if last_item < 0:
            global SC_curr_comm_id

            if nl_first_id != SC_curr_comm_id:
                i = 0
                for entry in new_list._queue:
                    entry.id = SC_curr_comm_id + i
                    i += 1

            self._queue.extend(new_list._queue)
            return None

        last_id = self._queue[last_item].id
        first_id = self._queue[0].id

        if nl_first_id == (last_id + 1):
            self._queue.extend(new_list._queue)

        elif nl_first_id == 0:
            i = 1
            for entry in new_list:
                entry.id = last_id + i
                i += 1
            self._queue.extend(new_list._queue)

        else:
            if nl_first_id < first_id:
                i = 0
                for entry in new_list:
                    entry.id = first_id + i
                    i += 1

            front_skip = new_list[0].id - first_id
            self._queue[front_skip:front_skip] = new_list._queue

            for i in range(last_item + 1 - front_skip):
                i += len_new_list
                self._queue[i + front_skip].id += len_new_list

        return None


    def append(self, entry) -> None:
        """other than '.add' this simply appends an entry indifferently to its ID"""

        new_entry = copy.deepcopy(entry)
        self._queue.append(new_entry)
        return None


    def clear(self, all=True, id="") -> list[QEntry] | Exception | None:
        """deletes single or multiple QEntry from queue, adjusts following ID accordingly"""

        if all:
            self._queue = []
            return self._queue

        if len(self._queue) == 0:
            return None

        ids = re.findall("\d+", id)
        id_num = len(ids)
        first_id = self._queue[0].id
        last_id = self._queue[len(self._queue) - 1].id

        match id_num:
            case 1:
                id1 = int(ids[0])

                if id1 < first_id or id1 > last_id:
                    return ValueError

                i = 0
                for entry in self._queue:
                    if entry.id == id1:
                        break
                    else:
                        i += 1

                self._queue.__delitem__(i)
                while i < len(self._queue):
                    self._queue[i].id -= 1
                    i += 1

            case 2:
                id1, id2 = int(ids[0]), int(ids[1])

                if (
                    id1 < first_id
                    or id1 > last_id
                    or id2 < id1
                    or id2 > last_id
                    or id.find("..") == -1
                ):
                    return ValueError

                id_dist = id2 - id1 + 1
                i = 0
                for entry in self._queue:
                    if entry.id == id1:
                        break
                    else:
                        i += 1
                
                # dont get confused, I'm iterating for the num of entries to
                # delete, but I'm always deleting the i-th entry as the stack
                # moves along
                for n in range(id_dist):
                    self._queue.__delitem__(i)

                while i < len(self._queue):
                    self._queue[i].id -= id_dist
                    i += 1

            case _:
                return ValueError

        return self._queue


    def pop_first_item(self) -> QEntry | Exception:
        """returns and deletes the QEntry at index 0"""

        try:
            entry = self._queue[0]
        except IndexError:
            return IndexError

        self._queue.__delitem__(0)
        return entry



class RoboTelemetry:
    """class used to store the standard 36 byte telemetry data comming from the robot

    ATTRIBUTES:
        t_speed:
            speed with that the tool center point (TCP) is moving
        id:
            command ID the robot is currently processing
        Coor:
            current coordinate of the TCP, see Coordinates class

    FUNCTIONS:
        __init__, __str__, __round__, __eq__
    """


    def __init__(self, t_speed=0.0, id=-1, Coor=None) -> None:

        self.t_speed = float(t_speed)
        self.id = int(id)

        # handle those beasty mutables
        self.Coor = Coordinate() if (Coor is None) else Coor


    def __str__(self) -> str:

        return (
            f"ID: {self.id}   X: {self.Coor.x}   Y: {self.Coor.y}   Z: {self.Coor.z}   Rx: {self.Coor.rx}   Ry: {self.Coor.ry}   Rz: {self.Coor.rz}   "
            f"EXT:   {self.Coor.ext}   TOOL_SPEED: {self.t_speed}"
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
            raise ValueError(f"{other} is not None or an instance of 'RoboTelemetry'!")

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
            raise ValueError(f"{other} is not None or an instance of 'RoboTelemetry'!")

        return False



class PumpTelemetry:
    """class used to store the standard telemetry data the pump

    ATTRIBUTES:
        freq:
            motor frequency (currently only given as 0 - 100%)
        volt:
            voltage at motor coil (I thought in V, but the values seem to high)
        amps:
            current in motor coil (unit unknown, as for volt)
        torq:
            torque, probably in Nm

    FUNCTIONS:
        __init__, __str__, __round__, __eq__
    """


    def __init__(self, freq=0.0, volt=0.0, amps=0.0, torq=0.0) -> None:

        self.freq = float(freq)
        self.volt = float(volt)
        self.amps = float(amps)
        self.torq = float(torq)


    def __str__(self) -> str:

        return f"FREQ: {self.freq}   VOLT: {self.volt}   AMPS: {self.amps}   TORQ: {self.torq}"


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
            raise ValueError(f"{other} is not None or an instance 'PumpTelemetry'!")

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
            raise ValueError(f"{other} is not None or an instance 'PumpTelemetry'!")

        return False


class TSData:
    """simple descriptor for timestamped data, will take values but only
    return them if there less old than the valid_time, otherwise returns None
    
    ATTRIBUTES:
        val:
            the value itself
        created_at:
            creation or change time timestamp
        valid_time:
            user_defined time, the value remains valid

    FUNCTIONS:
        __init__, __get__, __set__
    """

    def __init__(self, val=0.0) -> None:
        self.val = float(val)
        self.valid_time = timedelta(seconds=60)
        self._created_at = datetime.now()

    def __get__(self, instance, owner) -> float | None:
        age = datetime.now() - self._created_at
        if age < 60:
            return self.val
        return None
    
    def __set__(self, instance, value) -> None:
        self.val = value
        self._created_at = datetime.now()





class DaqBlock:
    """structure for DAQ, uses TSData except for Robo & Pumps which have to
    update periodically in order for the program to run anyways

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
            RB = robot base; temperature of the mortar tube at the second coupling [°C]
        msp_temp:
            MSP = main supply pump; temperature behind pump1's moineur pump [°C]
        msp_press:
            MSP = main supply pump; pressure behind pump1's moineur pump [bar]
        asp_freq:
            ASP = admixture supply pump; frequency of the admixture delivery pump
        asp_amps:
            ASP = admixture supply pump; current of the admixture delivery pump
        imp_temp:
            IMP = inline mixing pump; temperature behind the 2K pump [°C]
        imp_press:
            IMP = inline mixing pump; pressure in front of 2K pump [bar]
        imp_freq:
            IMP = inline mixing pump; frequency of the 2K pump
        imp_amps:
            IMP = inline mixing pump; current of the 2K pump
        phc_aircon:
            PHC = print head controller; air bubble/content analysis (not specified yet)
        phc_fdist:
            PHC = print head controller; deposition layer distance in front of the nozzle
        phc_edist:
            PHC = print head controller; deposition layer distance behind the nozzle

    FUNCTIONS:
        __init__, __str__, __eq__,

        set_valid_time:
            changes the valid_time of all TSData entries
    """


    def __init__(
        self,
        amb_temp=None,
        amb_humidity=None,
        rb_temp=None,
        msp_temp=None,
        msp_press=None,
        asp_freq=None,
        asp_amps=None,
        imp_temp=None,
        imp_press=None,
        imp_freq=None,
        imp_amps=None,
        Robo=None,
        Pump1=None,
        Pump2=None,
        phc_aircon=None,
        phc_fdist=None,
        phc_edist=None,
    ) -> None:

        self.amb_temp = TSData() if (amb_temp is None) else amb_temp
        self.amb_humidity = TSData() if (amb_humidity is None) else amb_humidity
        self.rb_temp = TSData() if(rb_temp is None) else rb_temp
        self.msp_temp = TSData() if (msp_temp is None) else msp_temp
        self.msp_press = TSData() if (msp_press is None) else msp_press
        self.asp_freq = TSData() if (asp_freq is None) else asp_freq
        self.asp_amps = TSData() if (asp_amps is None) else asp_amps
        self.imp_temp = TSData() if (imp_temp is None) else imp_temp
        self.imp_press = TSData() if (imp_press is None) else imp_press
        self.imp_freq = TSData() if (imp_freq is None) else imp_freq
        self.imp_amps = TSData() if (imp_amps is None) else imp_amps
        self.phc_aircon = TSData() if (phc_aircon is None) else phc_aircon
        self.phc_fdist = TSData() if (phc_fdist is None) else phc_fdist
        self.phc_edist = TSData() if (phc_edist is None) else phc_edist

        # handle those beasty mutables
        self.Robo = RoboTelemetry() if (Robo is None) else Robo
        self.Pump1 = PumpTelemetry() if (Pump1 is None) else Pump1
        self.Pump2 = PumpTelemetry() if (Pump2 is None) else Pump2


    def __str__(self) -> str:

        return (
            f"ambTemp: {self.amb_temp}    ambHum: {self.amb_humidity}    delivPumpTemp: {self.msp_temp}    robBaseTemp: {self.rb_temp}    "
            f"kPumpTemp: {self.imp_temp}    delivPumpPress: {self.msp_press}    kPumpPress: {self.imp_press}    PUMP1: {self.Pump1}    "
            f"PUMP2: {self.Pump2}    admPumpFreq: {self.asp_freq}    admPumpAmps: {self.asp_amps}    kPumpFreq: {self.imp_freq}    "
            f"kPumpAmps: {self.imp_amps}    ROB: {self.Robo}    porosAnalysis: {self.phc_aircon}    "
            f"distanceFront: {self.phc_fdist}    distanceEnd: {self.phc_edist}"
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
            raise ValueError(f"{other} is not None or an instance of 'DaqBlock'!")

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
            raise ValueError(f"{other} is not None or an instance of 'DaqBlock'!")

        return False
    

    def set_valid_time(self, new_valid_time) -> None | ValueError:
        """ sets valid time (given in seconds) of all TSData objects
        to new_valid_time
        """
        
        if not isinstance(new_valid_time, int):
            return ValueError(f"{new_valid_time} is not an instance of int!")
        
        for varkey in vars(self):
            attr = vars(self)[varkey]
            if isinstance(attr, TSData):
                attr.valid_time = new_valid_time
        
        return None



class TCPIP:
    """setup class for TCP/IP connection, provides all functions concerning the connection

    ATTRIBUTES:
        IP:
            endpoint IP address
        PORT:
            endpoint port nummber
        C_TOUT:
            timeout for connection attempts to endpoint
        RW_TOUT:
            timeout for reading from or writing to endpoint
        R_BL:
            data block length to read
        W_BL:
            data block length to write

    FUNCTIONS:
        __init__, __str__

        connect:
            tries to connect to the IP and PORT given, returns errors if not possible
        send:
            send data to server according to class attributes
        receive:
            receive according to class attributes
        close:
            close TCP/IP connection
    """


    def __init__(self, ip="", PORT=0, C_TOUT=1.0, RW_TOUT=1, R_BL=0, W_BL=0) -> None:

        self.ip = str(ip)
        self.port = str(PORT)
        self.c_tout = float(C_TOUT)
        self.rw_tout = float(RW_TOUT)
        self.r_bl = int(R_BL)
        self.w_bl = int(W_BL)

        self.connected = False
        self._Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    def __str__(self) -> str:

        return (
            f"IP: {self.ip}   PORT: {self.port}   C_TOUT: {self.c_tout}   RW_TOUT: {self.rw_tout}   "
            f"R_BL: {self.r_bl}   W_BL: {self.w_bl}"
        )


    def set_params(self, param_dict) -> None:

        if self.connected:
            raise PermissionError("params not changeable while connected to server!")

        self.ip = str(param_dict["IP"])
        self.port = str(param_dict["PORT"])
        self.c_tout = float(param_dict["C_TOUT"])
        self.rw_tout = float(param_dict["RW_TOUT"])
        self.r_bl = int(param_dict["R_BL"])
        self.w_bl = int(param_dict["W_BL"])


    def connect(self) -> tuple[bool, tuple[str, int]] | tuple[Exception, tuple[str, int]]:
        """tries to connect to the IP and PORT given, returns errors if not possible"""

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
            return err, server_address

        return True, server_address


    def send(self, data=None) -> tuple[bool, int] | tuple[bool, Exception]:
        """send data to server according to class attributes"""

        if not self.connected:
            return False, ConnectionError(f"no active connection")
        if len(data) != self.w_bl:
            return False, ValueError("wrong message length")

        try:
            self._Socket.sendall(data)
        except Exception as err:
            return False, err

        return True, len(data)


    def receive(self) -> tuple[bool, bytes] | tuple[bool, Exception]:
        """receive according to class attributes"""

        data = ""

        try:
            while len(data) < self.r_bl:
                data = self._Socket.recv(self.r_bl)

            if len(data) != self.r_bl:
                raise ValueError("wrong server answer length")

        except Exception as err:
            return False, err

        return True, data


    def close(self, end=False) -> None:
        """close TCP connection; restarts the socket, if end isnt set to True"""

        self._Socket.close()
        self.connected = False
        if not end:
            self._Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)



class RobConnection(TCPIP):
    """sets robot specific send/receive operations, inherits from TCPIP class, overwrites send & receive functions

    ATTRIBUTES:
        inherited from TCPIP class

    FUNCTIONS:
        send:
            sends a QEntry object to server, packing according to robots protocol
        receive:
            receives and unpacks data from robot, returns it as RobTelemetry object
    """


    def send(self, entry) -> tuple[bool, int] | tuple[bool, Exception]:
        """sends QEntry object to robot, packing according to robots protocol"""

        message = []

        try:
            if not self.connected:
                raise ConnectionError
            if not isinstance(entry, QEntry):
                raise ValueError(f"{entry} is not an instance of 'QEntry'!")

            message = struct.pack(
                "<iccffffffffffffffffiiiiiciiiiiiiiiiiiiiiii",
                entry.id,
                bytes(entry.mt, "utf-8"),
                bytes(entry.pt, "utf-8"),
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
                bytes(entry.sc, "utf-8"),
                entry.z,
                entry.Tool.pan_id,
                entry.Tool.pan_steps,
                entry.Tool.fib_deliv_id,
                entry.Tool.fib_deliv_steps,
                entry.Tool.mor_pump_id,
                entry.Tool.mor_pump_steps,
                entry.Tool.pnmtc_clamp_id,
                entry.Tool.pnmtc_clamp_yn,
                entry.Tool.knife_pos_id,
                entry.Tool.knife_pos_yn,
                entry.Tool.knife_id,
                entry.Tool.knife_yn,
                entry.Tool.pnmtc_fiber_id,
                entry.Tool.pnmtc_fiber_yn,
                entry.Tool.time_id,
                entry.Tool.time_time,
            )

            if len(message) != self.w_bl:
                raise ValueError("wrong message length")

            self._Socket.sendall(message)

        except Exception as err:
            return False, err

        print(f"SEND:    {entry.id}, length: {len(message)}")
        return True, len(message)


    def receive(self) -> tuple[RoboTelemetry, bytes] | tuple[None, None]:
        """receives and unpacks data from robot"""

        data = []
        Telem = RoboTelemetry()

        try:
            while len(data) < self.r_bl:
                data = self._Socket.recv(self.r_bl)

            if len(data) != self.r_bl:
                raise ValueError

        except Exception as err:
            return None, None

        Telem.t_speed = struct.unpack("<f", data[0:4])[0]
        Telem.id = struct.unpack("<i", data[4:8])[0]
        Telem.Coor.x = struct.unpack("<f", data[8:12])[0]
        Telem.Coor.y = struct.unpack("<f", data[12:16])[0]
        Telem.Coor.z = struct.unpack("<f", data[16:20])[0]
        Telem.Coor.rx = struct.unpack("<f", data[20:24])[0]
        Telem.Coor.ry = struct.unpack("<f", data[24:28])[0]
        Telem.Coor.rz = struct.unpack("<f", data[28:32])[0]
        Telem.Coor.ext = struct.unpack("<f", data[32:36])[0]

        return Telem, data


# not needed yet
# class MixerConnection(TCPIP):
#     """sets robot specific send/receive operations, inherits from TCPIP class, overwrites send & receive functions

#     ATTRIBUTES:
#         inherited from TCPIP class

#     FUNCTIONS:
#         send:
#             sends instruction block to mixer: speed[float], admixture[float], pinch[bool]; packing according to mixer protocol
#     """


#     def send(self, msg) -> tuple[bool, int] | tuple[bool, Exception]:
#         """sends instruction block to mixer: speed[float], admixture[float], pinch[bool]; packing according to mixer protocol"""

#         message = []

#         try:
#             if not self._connected:
#                 raise ConnectionError
#             message = struct.pack("<ffb", msg[0:4], msg[4:8], msg[8])

#             if len(message) != self.w_bl:
#                 raise ValueError("wrong message length")

#             self._Socket.sendall(message)

#         except Exception as err:
#             return False, err

#         return True, len(message)


#############################################################################################
#                                    GLOBALS
#############################################################################################

###################################### global constants #####################################
# defaut connection settings (the byte length for writing to the robot wont be user setable
# for safety reasons, it can only be changed here, but only if you know what your doing!)

DEF_TCP_MIXER = {
    "IP": "193.0.0.1",
    "PORT": "3000",
    "C_TOUT": 10000,
    "RW_TOUT": 10,
    "R_BL": 4,
    "W_BL": 4,
}

DEF_TCP_PUMP = {
    "IP": "",
    "PORT": "COM3",
    "C_TOUT": 0,
    "RW_TOUT": 0,
    "R_BL": 0,
    "W_BL": 0,
}

DEF_SERIAL_PUMP = {
    "BR": 19200,
    "P": serial.PARITY_NONE,
    "SB": serial.STOPBITS_TWO,
    "BS": serial.EIGHTBITS,
    "PORT": "COM3",
}

DEF_TCP_ROB = {
    "IP": "192.168.125.1",
    "PORT": 10001,
    "C_TOUT": 60000,
    "RW_TOUT": 5,
    "R_BL": 36,
    "W_BL": 159,
}

# default user settings
DEF_AMC_PANNING = 0
DEF_AMC_FIB_DELIV = 100
DEF_AMC_CLAMP = False
DEF_AMC_KNIFE_POS = False
DEF_AMC_KNIFE = False
DEF_AMC_FIBER_PNMTC = False

DEF_DC_SPEED = SpeedVector()

DEF_IO_ZONE = 10
DEF_IO_FR_TO_TS = 0.1

DEF_ICQ_MAX_LINES = 200

DEF_PRIN_SPEED = SpeedVector()

DEF_PUMP_LPS = 0.5
DEF_PUMP_RETR_SPEED = -50
DEF_PUMP_OUTP_RATIO = 1.0
DEF_PUMP_CLASS1 = 75.0
DEF_PUMP_CLASS2 = 50.0

DEF_ROB_COMM_FR = 10

DEF_SC_VOL_PER_M = 0.4  # calculated for 1m of 4cm wide and 1cm high filament
DEF_SC_MAX_LINES = 400
DEF_SC_EXT_FLLW_BHVR = (5, 2)

DEF_TERM_MAX_LINES = 300

DEF_TOOL_FIB_STPS = 10
DEF_TOOL_FIB_RATIO = 1.0


###################################### global variables ######################################

ADC_panning = DEF_AMC_PANNING
ADC_fib_deliv = DEF_AMC_FIB_DELIV
ADC_clamp = DEF_AMC_CLAMP
ADC_knife_pos = DEF_AMC_KNIFE_POS
ADC_knife = DEF_AMC_KNIFE
ADC_fib_pnmtc = DEF_AMC_FIBER_PNMTC

DCCurrZero = Coordinate()
DCSpeed = copy.deepcopy(DEF_DC_SPEED)
DC_rob_moving = False

IO_curr_filepath = None
IO_fr_to_ts = DEF_IO_FR_TO_TS
IO_zone = DEF_IO_ZONE

MIX_last_speed = 0
MIX_speed = 0
MIX_act_with_pump = False
MIXTcp = TCPIP(
    DEF_TCP_MIXER["IP"],
    DEF_TCP_MIXER["PORT"],
    DEF_TCP_MIXER["C_TOUT"],
    DEF_TCP_MIXER["RW_TOUT"],
    DEF_TCP_MIXER["R_BL"],
    DEF_TCP_MIXER["W_BL"],
)

PRINSpeed = copy.deepcopy(DEF_PRIN_SPEED)

PMP_retract_speed = DEF_PUMP_RETR_SPEED
PMP_output_ratio = DEF_PUMP_OUTP_RATIO
PMP_serial_def_bus = None  # is created after user input in win_mainframe
PMP_speed = 0

PMP1LastTelem = PumpTelemetry()
PMP1_liter_per_s = DEF_PUMP_LPS
PMP1_live_ad = 1.0
PMP1_speed = 0
PMP1Serial = MtecMod(None, "01")
PMP1_user_speed = -999
PMP1Tcp = TCPIP(
    DEF_TCP_PUMP["IP"],
    DEF_TCP_PUMP["PORT"],
    DEF_TCP_PUMP["C_TOUT"],
    DEF_TCP_PUMP["RW_TOUT"],
    DEF_TCP_PUMP["R_BL"],
    DEF_TCP_PUMP["W_BL"],
)

PMP2LastTelem = PumpTelemetry()
PMP2_liter_per_s = DEF_PUMP_LPS
PMP2_live_ad = 1.0
PMP2_speed = 0
PMP2Serial = MtecMod(None, "02")
PMP2_user_speed = -999
PMP2Tcp = TCPIP(
    DEF_TCP_PUMP["IP"],
    DEF_TCP_PUMP["PORT"],
    DEF_TCP_PUMP["C_TOUT"],
    DEF_TCP_PUMP["RW_TOUT"],
    DEF_TCP_PUMP["R_BL"],
    DEF_TCP_PUMP["W_BL"],
)

ROB_comm_fr = DEF_ROB_COMM_FR
ROBCommQueue = Queue()
ROBLastTelem = RoboTelemetry()
ROBTelem = RoboTelemetry()
ROBMovStartP = Coordinate()
ROBMovEndP = Coordinate()
ROB_send_list = []
ROB_live_ad = 1.0
ROBTcp = RobConnection(
    DEF_TCP_ROB["IP"],
    DEF_TCP_ROB["PORT"],
    DEF_TCP_ROB["C_TOUT"],
    DEF_TCP_ROB["RW_TOUT"],
    DEF_TCP_ROB["R_BL"],
    DEF_TCP_ROB["W_BL"],
)

SC_vol_per_m = DEF_SC_VOL_PER_M
SC_curr_comm_id = 1
SCQueue = Queue()
SC_q_processing = False
SC_q_prep_end = False
SC_ext_fllw_bhvr = DEF_SC_EXT_FLLW_BHVR

SEN_dict = { # add available datasources here
    'msp': { # Main Supply Pump
        'ip': "",
        'temp': float(0.0),
        #"pressure": float(0.0)
    },
    'asp': { # Admixture Supply Pump
        None
    },
    'imp': { # Inline Mixing Pump
        None
    },
    'phc': { # Print Head Controller
        None
    }
}
STTDataBlock = DaqBlock()

TERM_log = []

TOOL_fib_ratio = DEF_TOOL_FIB_RATIO