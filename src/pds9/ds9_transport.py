# Licensed under a 3-clause BSD style license - see LICENSE.rst
import ds9samp
import numpy as np

from pds9.tempfiles import create_ds9_tmpfile_name



def asdf_send_array(
        self,
        img: np.ndarray,
        filename,
        *,
        timeout: int | None = None,
    ) -> None:
        """Send the array to DS9.

        This creates a temporary file to store the data,
        sends the data, and then deletes the file.

        This version is based on whe ds9samp method of the same name with
        changes to how temporary files are named and where they are stored.

        The created file is not deleted until this method is called again.
        In prinicple, there will one file remaining in the directory, to
        simplify the initial version of this code.

        Files currently are stored in the ds9tmp subdirectory of the user's
        home directory.

        """
        # Map between NumPy and DS9 storage fields.
        #
        # Hack in support for bool values
        if img.dtype.type == np.bool_:
            img = img.astype("int8")

        arr = ds9samp.np_to_array(img)
        # Create a frame if necessary, since otherwise the ARRAY call
        # will fail.
        #
        if self.get("frame active") is None:
            self.set("frame new")

        # with tempfile.NamedTemporaryFile(prefix="ds9samp", suffix=".arr") as fh:
        ##with open(create_ds9_tmpfile(filename), 'wb')  as fh:

        tmp_filename = create_ds9_tmpfile_name(filename)
        fp = np.memmap(tmp_filename, mode="w+", dtype=img.dtype, shape=img.shape)
        fp[:] = img
        fp.flush()

        # If given a RGB/HLS/HSV cube then create a frame. We
        # could try and check if we have one already, but it's not
        # clear how to do this, so always create it. If a user
        # wants to re-use the frame then they can try and do this
        # manually (probably by creating a FITS file and loading
        # that?).

        # Should this over-ride the filename as it is going to be
        # invalid as soon as this call ends? I am not sure that it
        # is possible.

        cmd = "array "
        cmd += f" {tmp_filename}{arr}"
        self.set(cmd, timeout=timeout)
