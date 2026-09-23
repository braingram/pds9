import os
import subprocess
import sys
import tempfile
import importlib.resources

import pds9

template = """
set pds9_python {python_bin}
set asdf_tmp_dir_arg {asdf_tmp_dir}
source {inifile}
"""


def main():
    with tempfile.TemporaryDirectory() as asdf_tmp_dir, importlib.resources.path(pds9, "ds9.ini") as inifile_path:
        inifile = str(inifile_path)
        tcl_filename = os.path.join(asdf_tmp_dir, "tcl.ini")
        with open(tcl_filename, "w") as tcl_file:
            tcl_file.write(template.format(asdf_tmp_dir=asdf_tmp_dir, python_bin=sys.executable, inifile=inifile))
        subprocess.check_call(["ds9", "-source", tcl_filename])
