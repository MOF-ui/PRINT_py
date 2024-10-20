 PRINT_py
    python-ui to remote-control an ABB robot arm, mortar pumps, admixture pumps and DAQ devices in order to 3D print conrete/mortar on a large scale

    Hi! First of all: be careful with this program. Keep in mind, that it controls a very large robot arm
    that can easily cause a lot of damage. Also, I am not a programmer (nor is english my first language
    for that matter). Therefore you can not count on me following standard industrial procedures or that 
    all of the docstrings convey the meaning I intended. I tried to build this application according to the 
    standards that I know of, though. The script style doesn't follow PEP8 closely, I'll change that, if I 
    find the time.

    OVERVIEW
    gh -    grasshopper scripts used to extract control points as list or GCode from one or multiple Rhino3D curve objects
            either controlled by minimum control points per degree of curviture (with or without alternating curve seams)
            or with unidistance mode
    libs -  actual software libraries for PRINT_py, libs with the "win" prefix control the GUIs, TCP and COM interfaces
            are scripted in threads.py
    mtec -  Modbus interface for mtec P20
    simCom -used for simplified integration tests 
    test -  unittests für most libs
    ui -    Qt designer files and pyuic5 outputs

    SCOPE
    This programm was written to remotely control the second robot arm (Roboter 2) of the instituts robotic cell.
    The robot arms were manufactured by ABB while all of their subroutines were programmed by Klero Roboter 
    Automatisation from Berlin. This code requires a TCP/IP interface running on the robot, which takes 159 byte 
    commands. The robot can either act upon them immediately or buffer up to 3000 commands. The current version
    runs on 10 forwarded commands, which goes easier on the robots internal route planning. While the interface 
    is connected the robot sends positional data (36 byte blocks) around every 0.2 seconds.
    The blocks are structured as follows:
 

    COMMAND BLOCK
    4 byte, INT -   ID                      (command ID for robot to stay on track)
    1 byte, CHAR -  move type               (use L -> linear movement, J -> joint movement, C -> circular movement)
    1 byte, CHAR -  pos type                (use E -> rotation in Euler angles, Q -> rotation as quaternion, A -> pass 6 axis values)
    4 byte, FLOAT - X or A1                 (X = X position in global coordinate system in mm, A = axis position)
    4 byte, FLOAT - Y or A2
    4 byte, FLOAT - Z or A3
    4 byte, FLOAT - Q1, Rx or A4            (Q = quaternion value, Rx = rotation around X in degrees)
    4 byte, FLOAT - Q2, Ry or A5
    4 byte, FLOAT - Q3, Rz or A6
    4 byte, FLOAT - Q4 or 0
    4 byte, FLOAT - EXT:                    (EXT = postion of external axis in mm)
    4 byte, FLOAT - (2) X or A1             (second block of coordinates for C-type movement)
    4 byte, FLOAT - (2) Y or A2
    4 byte, FLOAT - (2) Z or A3
    4 byte, FLOAT - (2) Q1, Rx or A4
    4 byte, FLOAT - (2) Q2, Ry or A5
    4 byte, FLOAT - (2) Q3, Rz or A6
    4 byte, FLOAT - (2) Q4 or 0
    4 byte, FLOAT - (2) EXT
    4 byte, INT -   acceleration ramp
    4 byte, INT -   deceleration ramp
    4 byte, INT -   transition speed
    4 byte, INT -   orientation speed
    4 byte; INT -   time                    (for time-dependent movement)
    1 byte, CHAR -  speed calculation       (either V for velocity- or T for time-dependent)
    4 byte, INT -   zone
    4 byte, INT -   ID, motor 1             (all tool specific data from here)
    4 byte, INT -   steps, motor 1
    4 byte, INT -   ID, motor 2
    4 byte, INT -   steps, motor 2
    4 byte, INT -   ID, motor 3
    4 byte, INT -   steps, motor 3
    4 byte, INT -   ID, pnmtc clamp
    4 byte, INT -   Y/N, pnmtc clamp
    4 byte, INT -   ID, knife
    4 byte, INT -   Y/N, knife
    4 byte, INT -   ID, motor 4
    4 byte, INT -   steps, motor 4
    4 byte, INT -   ID, fiber
    4 byte, INT -   steps, fiber
    4 byte, INT -   ID, time
    4 byte, INT -   time [ms], time
 

    POSITION BLOCK
    4 byte, FLOAT - tool center point velocity
    1 byte, INT -   current command ID processing
    4 byte, FLOAT - X
    4 byte, FLOAT - Y
    4 byte, FLOAT - Z
    4 byte, FLOAT - Rx
    4 byte, FLOAT - Ry
    4 byte, FLOAT - Rz
    4 byte, FLOAT - EXT

more detail documentation may follows in future commits...


Shield: [![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]

This work is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[![CC BY-SA 4.0][cc-by-sa-image]][cc-by-sa]

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
