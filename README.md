> [!WARNING]
> This software controls expensive and possible dangerous machines. You may use
> it at your own risk, if so, you're responsible to ensure safety of people and
> material. PRINT_py is distributed on an 'AS IS' basis, without warranties of
> conditions of any kind, either expressed or implied.


# General

Hi! First of all: be careful with this program. Keep in mind, that it 
controls a very large robot arm that can easily cause a lot of damage. 
Also, I am not a programmer (nor is english my first language for that
matter). Therefore, you can not count on me following standard industrial
procedures or that all of the docstrings convey the meaning I intended.
I tried to build this application according to the standards that I know
of, though. You can write me issues, I'll see to them, if I find the time.

## File structure

> [!NOTE]
>
> #### c
>
>   * source codes for data access points and microcontrollers
>   * everything written in C or C++ 
>   * [PlatformIO](https://platformio.org/) projects for [esp-idf](https://github.com/espressif/esp-idf) or Arduino using [OLIMEX ESP32-PoE-ISO](https://github.com/OLIMEX/ESP32-POE-ISO)
>
> #### conv
>
>   * [LabView](https://www.ni.com/de.html) VI for GCode :arrow_right: RAPID conversion
>   * used for testing and in hand mode operation
>
> #### gh
>
>   * grasshopper scripts used for conversion of:
>       * CAD object :arrow_right: GCode
>       * CAD object :arrow_right: RAPID
>       * CAD object :arrow_right: point list
>   * uses one or multiple curve objects
>   * solids or surfaces need to be sliced beforehand
>   * conversion either controlled by minimum CP[^1] per curviture or fixed CP distance
> [^1]: control points
>
> #### libs
>
>   * actual software libraries for PRINT_py
>   * libs with the `win_` prefix for GUIs
>   * TCP and COM interfaces are scripted in `threads.py`
>
> #### mtec 
>
>   * Modbus interface for mtec P20 & P50 mortar pumps 
>   * modded version with custom return values and common serial interface
>     for multipe pumps ([original module by m-tec](https://github.com/m-tec-com/m-tecConnectModbus))
>
> #### simCom
>
>   * virtual robot used for simplified integration tests
> 
> #### test
>
>   * unittests für most libs (:warning: not up-to-date)
>
> ### ui
>
>   * Qt designer files and pyuic5 outputs

## Scope

This programm was written to remotely control the second robot arm
(Roboter 2) of the instituts robotic cell. The robot arms were
manufactured by ABB while all of their subroutines were programmed by
Klero Roboter Automatisation from Berlin. This code requires a TCP/IP
interface running on the robot, which takes 159 byte commands. The robot
can either act upon them immediately or buffer up to 3000 commands. The
current version runs on 10 forwarded commands, which goes easier on the
robots internal route planning. While the interface is connected the robot
sends positional data (36 byte blocks) around every 0.2 seconds. Additionally,
PRINT_py controls 2 mtec P20 or P50 mortar pumps and maybe an inline mixing
device in the future.

# Usage

start with `py .\PRINT.py`

> [!TIP]
> you can also start a testing environment with:
>
> start a virtual robot with `py .\simCom\test_server.py`
>
> start PRINT_py in local mode with `py .\PRINT.py local`

Pumps are currently connected via COM port using a USB001Z-3 USB-to-Serial
conversion unit. Both pumps are connected to this converter via Modbus, sharing
the same bus and therefore the same COM port. Modbus adresses are '01' & '02'. 
There is no testing environment for the pumps, yet.

## Shortcuts

#### Script control

| button | shortcut |
| ------ | -------- |
| start queue processing | :arrow_right: `CTRL+ALT+S` |
| stop queue processing | :arrow_right: `CTRL+A` |
| send first queue command | :arrow_right: `CTRL+F` |
| clear queue | :arrow_right: `CTRL+#` |
| forced stop | :arrow_right: `CTRL+Q` |
| reset script ID to robot ID | :arrow_right: `CTRL+ALT+I` |

#### Direct control

| button | shortcut |
| ------ | -------- |
| (step) + X | :arrow_right: `CTRL+U` |
| (step) - X | :arrow_right: `CTRL+J` |
| (step) + Y | :arrow_right: `CTRL+I` |
| (step) - Y | :arrow_right: `CTRL+K` |
| (step) + Z | :arrow_right: `CTRL+O` |
| (step) - Z | :arrow_right: `CTRL+L` |
| (step) + EXT | :arrow_right: `CTRL+P` |
| (step) - EXT | :arrow_right: `CTRL+OE` |
| NC set current position | :arrow_right: `CTRL+T` |

#### Other

| button | shortcut |
| ------ | -------- |
| browse files | :arrow_right: `CTRL+N` |
| load selected file | :arrow_right: `CTRL+M` |
| stop pumps | :arrow_right: `CTRL+E` |
| invert pump speed | :arrow_right: `CTRL+R` |

## Robot communication syntax 

#### Command

| size [byte] | type | description |
| ---- | ---- | ----------- |
| 4 | INT | **ID**: |
|   |     | command ID for robot to keep track |
| 1 | CHAR | **MT** (move type): |
|   |      | `L` (linear movement) |
|   |      | `J` (joint movement) |
|   |      | `C` (circular movement) |
| 1 | CHAR | **PT** (position type): |
|   |      | `E` (rotation in Euler angles) |
|   |      | `Q` (rotation as quaternion) |
|   |      | `A` (pass 6 axis values) |
| 4 | FLOAT | **X** or **A1**: |
|   |       | **X** = position in global coordinate [mm]|
|   |       | **A** = axis 1 position [deg] |
| 4 | FLOAT | **Y** or **A2** |
| 4 | FLOAT | **Z** or **A3** |
| 4 | FLOAT | **Q1**, **Rx** or **A4**: |
|   |       | **Q1** = quaternion 1. dimension [-] |
|   |       | **Rx** = rotation around **X** [deg] |
| 4 | FLOAT | **Q2**, **Ry** or **A5** |
| 4 | FLOAT | **Q3**, **Rz** or **A6** |
| 4 | FLOAT | **Q4** or **0** |
| 4 | FLOAT | **EXT**: |
|   |       | postion of external axis [mm] |
| 4 | FLOAT | (2) **X** or **A1**: |
|   |       | (2) = second coordinate block for C-type movement |
| 4 | FLOAT | (2) **Y** or **A2** |
| 4 | FLOAT | (2) **Z** or **A3** |
| 4 | FLOAT | (2) **Q1**, **Rx** or **A4** |
| 4 | FLOAT | (2) **Q2**, **Ry** or **A5** |
| 4 | FLOAT | (2) **Q3**, **Rz** or **A6** |
| 4 | FLOAT | (2) **Q4** or **0** |
| 4 | FLOAT | (2) **EXT** |
| 4 | INT | **ACR**: |
|   |     | acceleration ramp [mm s<sup>-2</sup>] |
| 4 | INT | **DCR**: |
|   |     | deceleration ramp [mm s<sup>-2</sup>] |
| 4 | INT | **TS**: |
|   |     | transition speed [mm s<sup>-1</sup>] |
| 4 | INT | **OS**: |
|   |     | orientation speed [deg s<sup>-1</sup>] |
| 4 | INT | **SBT**: |
|   |     | speed by time (if **SC** = `T`) [ms] |
| 1 | CHAR | **SC**: |
|   |      | `V` = velocity dependent |
|   |      | `T` = time-dependent |
| 4 | INT | **Z**: |
|   |     | zone (destination accuracy) |
| 4 | INT | **PAN_ID** |
| 4 | INT | **PAN_STEPS**: |
|   |     | tool panning step-motor [-] |
| 4 | INT | **FIB_DELIV_ID** |
| 4 | INT | **FIB_DELIV_STEPS**: |
|   |     | fiber delivery step-motor [-] |
| 4 | INT | **MOR_PUMP_ID** |
| 4 | INT | **MOR_PUMP_STEPS**: |
|   |     | *not in use* |
| 4 | INT | **PNMTC_CLAMP_ID** |
| 4 | INT | **PNMTC_CLAMP_YN**: |
|   |     | pneumatic clamp on/off [0/1] |
| 4 | INT | **KNIFE_POS_ID** |
| 4 | INT | **KNIFE_POS_YN**: |
|   |     | knife in cutting pos on/off [0/1] |
| 4 | INT | **KNIFE_ID** |
| 4 | INT | **KNIFE_YN**: |
|   |     | rotary knife on/off [0/1] |
| 4 | INT | **PNMTC_FIBER_ID** |
| 4 | INT | **PNMTC_FIBER_YN**: |
|   |     | pneumatic fiber delivery system on/off [0/1] |
| 4 | INT | **TIME_ID** |
| 4 | INT | **TIME_TIME**: |
|   |     | time [ms] |

#### Position update

| size [byte] | type | description |
| ---- | ---- | ----------- |
| 4 | FLOAT | **TCP_SPEED**: |
|   |       | tool center point velocity [mm s<sup>-1</sup>] |
| 1 | INT | **ID**: |
|   |     | current command ID being processed |
| 4 | FLOAT | **X**: |
|   |       | current position on global x-axis [mm] |
| 4 | FLOAT | **Y** |
| 4 | FLOAT | **Z** |
| 4 | FLOAT | **Rx** |
| 4 | FLOAT | **Ry** |
| 4 | FLOAT | **Rz** |
| 4 | FLOAT | **EXT** |

more detailed documentation may follows in future commits...


Shield: [![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
