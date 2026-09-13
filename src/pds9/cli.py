"""CLI helpers for printing the ds9 configuration snippet.

Importing this module must not create user directories or touch the runtime
environment. Any filesystem setup happens only in explicit runtime functions in
``pds9.tempfiles``.
"""

import sys
from argparse import ArgumentParser
from pathlib import Path

import pds9
from pds9.tempfiles import get_ds9_tmp_dir


def main():
    parser = ArgumentParser()
    parser.add_argument("--print", "-p", action="store_true",
        help="Print ds9 config snippet")

    args = parser.parse_args()
    topdir = Path(pds9.__file__).parent
    inifile = topdir / "ds9.ini"
    python_bin = Path(sys.prefix) / "bin" / "python3"
    asdf_tmp_dir = str(get_ds9_tmp_dir())

    if args.print:
        print(f"set pds9_python {python_bin}") # noqa: T201
        print(f"set asdf_tmp_dir_arg {asdf_tmp_dir}") # noqa: T201
        print(f"source {inifile}") # noqa: T201
