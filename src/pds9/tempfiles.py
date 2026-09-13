# Licensed under a 3-clause BSD style license - see LICENSE.rst
import os
import os.path
import pathlib

DS9TMP = None


def get_ds9_tmp_dir(*, create=False):
    """
    Return the configured ds9 temporary directory path.

    If ``create`` is True, ensure the directory exists and cache it in DS9TMP.
    Otherwise, return the expected path without touching the filesystem.
    """
    global DS9TMP  # noqa: PLW0603
    if DS9TMP is None:
        DS9TMP = pathlib.Path.home() / "ds9tmp"
    if create:
        DS9TMP.mkdir(exist_ok=True)
    return DS9TMP


def create_ds9_tmp_dir():
    """
    Currently generates a ds9tmp directory in user's home directory
    if one doesn't already exist
    """
    get_ds9_tmp_dir(create=True)



def create_ds9_tmpfile_name(asdf_full_path):
    """
    First delete any files in the ds9tmp directory, then return a handle
    to a new writable binary file.
    """
    # If the global is None, either this is the first call during this
    # session, in which case if the directory already exists, the
    # global will be set, if not, the directory will be created.
    if DS9TMP is None:
        create_ds9_tmp_dir()
    # Delete any existing files.
    for filepath in DS9TMP.glob("*"):
        if filepath.is_file() and filepath.parts[-1] != "ds9cmd":
            filepath.unlink()
    # Remove any directories in the supplied asdf_full_path
    dummy, asdf_truncated_full_path = os.path.split(asdf_full_path)
    fn = str((DS9TMP / asdf_truncated_full_path).resolve())
    # Replace square brackets with curly brackets since they will confuse ds9
    fn = fn.replace("[", "(")
    fn = fn.replace("]", ")")
    return fn  # noqa: RET504
