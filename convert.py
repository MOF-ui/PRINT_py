from pathlib import Path
import libs.func_utilities as fu
from libs.win_dialogs import file_dialog

files = file_dialog('select file to convert', standalone=True)
if isinstance(files, str):
    files = [files]

for file in files:
    f_path = Path(file)
    f_type = f_path.suffix

    with open(file, 'r') as input_file:
        input = input_file.read()
    rows = input.split('\n')

    if f_type == '.mod':
        
    for row in rows:
        fu.gcode_to_qentry