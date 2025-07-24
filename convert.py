# convert.py
######################### IMPORTS #########################

import sys
import shutil
import argparse
from pathlib import Path
from copy import deepcopy as dcpy

import libs.global_var as g
import libs.func_utilities as fu
import libs.data_utilities as du
from libs.win_dialogs import file_dialog, strd_dialog


max_lines = 2000  # maximum lines per file
num_files = 0
dir_exists = False


######################### FUNCTIONs #########################


def generate_prefix(name: str, loads: int, split: bool) -> str:
    out = f"MODULE {name}\n\n"
    if not split:
        out += f"\tLOCAL CONST robtarget pHome := [[7307.0,6245.0,-154.0],[0.625267,-0.348239,0.608726,0.342379],[1,0,-1,1],[6200.01,9E+09,9E+09,9E+09,9E+09,9E+09]];\n"
    for i in range(loads):
        out += f"\tVAR loadsession load{i+1};\n"
    out += f"\n\tPROC {name}_main("
    if split:
        out += f"robtarget pHome)\n"
    else:
        out += f")\n\t\tMoveL pHome,v200,fine,tool0;\n"
    return out


def commlist_to_output(comm_list: du.Queue, args: argparse.Namespace) -> str:
    out = ""
    for Entry in comm_list:
        if args.scale != 1.0:
            Entry.Coor1 = Entry.Coor1.scale(args.scale)
        if args.xy_mirror:
            Entry.Coor1.x, Entry.Coor1.y = Entry.Coor1.y, Entry.Coor1.x
        if args.xshift != 0.0:
            Entry.Coor1.x += args.xshift
        if args.yshift != 0.0:
            Entry.Coor1.y += args.yshift
        if to_rapid:
            out += Entry.to_rapid(tool=tool)
        else:
            out += Entry.to_gcode()
    return out


def file_split():
    global num_files
    global dir_exists
    global f_path
    global f_stem
    global f_type
    global CommList
    global args

    if not dir_exists:
        try:
            new_dir = f_path.parent / f"{f_stem}"
            new_dir.mkdir()
        except FileExistsError:
            res = strd_dialog(
                "Do you want to overwrite the existing directory?",
                "Directory exists!",
                True,
            )
            if res:
                shutil.rmtree(new_dir)
                new_dir.mkdir()
            else:
                print("File not overwritten.")
                sys.exit(1)
        f_path = new_dir / f"{f_stem + f_type}"
        dir_exists = True

    num_files += 1
    output = commlist_to_output(CommList, args)
    CommList.clear()
    # overwrite directly because user has already confirmed
    with open(f_path.with_name(f"{f_stem}_{num_files}.mod"), "w") as output_file:
        split_prefix = generate_prefix(f"{f_stem}_{num_files}", 0, True)
        output_file.write(split_prefix + output + suffix)


############################ COMMAND LINE PARSER ############################

# parsing comand line arguments
parser = argparse.ArgumentParser(
    prog="convert.py",
    usage="%(prog)s [options]",
    epilog="Example: python convert.py --name new_file --max_lines 1000\n",
    description="Convert between RAPID and GCode formats.",
)
parser.add_argument(
    "--name",
    "-n",
    type=str,
    nargs="?",
    help="Set a new name for the output file.",
)
parser.add_argument(
    "--max_lines",
    "-ml",
    type=int,
    nargs="?",
    default=max_lines,
    help="Set the maximum number of lines per output file (default: 2000).",
)
parser.add_argument(
    "--scale",
    "-s",
    type=float,
    nargs="?",
    default=1.0,
    help="Scale the coordinates by a given factor (default: 1.0).",
)
parser.add_argument(
    "--xy_mirror",
    "-m",
    action="store_true",
    default=False,
    help="Mirror the x and y coordinates along y=x (default: False).",
)
parser.add_argument(
    "--xshift",
    "-x",
    type=float,
    nargs="?",
    default=0.0,
    help="Shift the x coordinates by a given value (default: 0.0).",
)
parser.add_argument(
    "--yshift",
    "-y",
    type=float,
    nargs="?",
    default=0.0,
    help="Shift the y coordinates by a given value (default: 0.0).",
)
parser.add_argument(
    "--terminal-move",
    "-t",
    type=str,
    nargs="?",
    default="",
    help="Add a printhead movement after the print is finished.",
)
args = parser.parse_args()


######################### MAIN PROGRAM #########################

# open file dialog
files = file_dialog("select file to convert", standalone=True)
if not files:
    print("No files choosen, exiting..")
    sys.exit(1)
# if only one file is selected, it is a string, otherwise a list
# we need a list
if isinstance(files, str):
    files = [files]

for file in files:
    f_path = Path(file)
    f_stem = f_path.stem
    f_type = f_path.suffix
    print(f"Converting {f_stem} ({f_path})...")

    # check file
    if not f_path.is_file():
        print(f"File does not exist!")
        sys.exit(1)
    if f_type == ".mod":
        to_rapid = False
    elif f_type == ".gcode":
        to_rapid = True
        suffix = f"\n\tENDPROC\n" f"ENDMODULE\n"
    else:
        print(f"Unsupported file type: {f_type} in {file}")
        sys.exit(1)

    with open(file, "r") as input_file:
        input = input_file.read()
    rows = input.split("\n")

    # rename if specified
    if args.name:
        f_stem = args.name

    LastEntry = du.QEntry()
    CommList = du.Queue()
    # all conversions relative to origin
    g.ROBCurrZero = du.Coordinate()
    lines = 0
    skips = 0
    errors = 0
    tool = "tool0"

    # read and add to CommList
    for row in rows:
        if to_rapid:
            NewEntry, sort = fu.gcode_to_qentry(LastEntry, row)
            # check for errors & skips
            if isinstance(NewEntry, du.QEntry):
                LastEntry = dcpy(NewEntry)
                CommList.add(NewEntry, 0)
                lines += 1
                if len(CommList) >= args.max_lines:
                    file_split()
                    CommList.clear()
                continue
        else:
            NewEntry, sort = fu.rapid_to_qentry(row)
            # check for errors & skips
            if isinstance(NewEntry, du.QEntry):
                CommList.add(NewEntry, 0)
                lines += 1
                continue

        # handle if unreadable
        if sort in [";", "!"]:
            skips += 1
        else:
            print(f"Syntax error in line: {row}!")
            errors += 1

    # add movement at end of print if specified
    TermMove = None
    if args.terminal_move and len(CommList) != 0:
        match args.terminal_move:
            case "X":
                term_gcode = "G1 X-200 F300 PMP0 PIN1"
            case "Y":
                term_gcode = "G1 Y-200 F300 PMP0 PIN1"
            case "Z":
                term_gcode = "G1 Z400 F300 PMP0 PIN1"
            case "XZ":
                term_gcode = "G1 X-200 Z400 F300 PMP0 PIN1"
            case "YZ":
                term_gcode = "G1 Y-200 Z400 F300 PMP0 PIN1"
            case _:
                term_gcode = args.terminal_move
        TermMove = fu.gcode_to_qentry(CommList[-1], term_gcode)[0]
        if not isinstance(TermMove, du.QEntry):
            raise SyntaxError(f"{term_gcode} does not yield a valid QEntry!")

    # convert to str
    t_move = ""
    if to_rapid:
        if TermMove is not None:
            t_move += "! do not stop on the model path\n"
            t_move += TermMove.to_rapid(tool=tool)
        if num_files > 0:
            file_split()
            output = (
                f'\t\tStartLoad \\Dynamic, "HOME:/{f_stem}/" '
                f'\\File:="{f_stem}_1.mod", load1;\n'
                f"\t\tWaitLoad load1;\n\n"
            )
            for i in range(1, num_files):
                output += (
                    f'\t\tStartLoad \\Dynamic, "HOME:/{f_stem}/" '
                    f'\\File:="{f_stem}_{i+1}.mod", load{i+1};\n'
                    f'\t\t%"{f_stem}_{i}:{f_stem}_{i}_main"%(pHome);\n'
                    f'\t\tUnLoad "HOME:/{f_stem}/" \\File:="{f_stem}_{i}.mod";\n'
                    f"\t\tWaitLoad load{i+1};\n\n"
                )
            output += (
                f'\t\t%"{f_stem}_{num_files}:{f_stem}_{num_files}_main"%(pHome);\n'
                f'\t\tUnLoad "HOME:/{f_stem}/" \\File:="{f_stem}_{num_files}.mod";\n\n'
            )
            output = generate_prefix(f_stem + "_0", num_files, False) + output + suffix
        else:
            output = commlist_to_output(CommList, args)
            output = generate_prefix(f_stem, 0, False) + output + suffix
    else:
        if TermMove is not None:
            t_move += "! do not stop on the model path\n"
            t_move += TermMove.to_gcode()
        output = commlist_to_output(CommList, args) + t_move

    # write output
    print(
        f"converted {lines} lines,\n"
        f"Skipped {skips} lines,\n"
        f"found {errors} errors."
    )

    # dump output to file
    new_suffix = ".mod" if to_rapid else ".gcode"
    if num_files > 0:
        d_path = f_path.with_name(f_stem + "_0" + new_suffix)
    else:
        d_path = f_path.with_name(f_stem + new_suffix)
    try:
        with open(d_path, "x") as output_file:
            output_file.write(output)
    except FileExistsError:
        res = strd_dialog(
            "Do you want to overwrite the existing file?", "File exists!", True
        )
        if res:
            with open(d_path, "w") as output_file:
                output_file.write(output)
        else:
            print("File not overwritten.")
