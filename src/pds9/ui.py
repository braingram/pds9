# Licensed under a 3-clause BSD style license - see LICENSE.rst
import pathlib
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

import ds9samp
import psutil

from pds9 import tempfiles
from pds9.asdf_handler import AsdfHandler
from pds9.ds9_transport import asdf_send_array
from pds9.errors import Pds9Error

FILEPATH_DOC = """
How to specify ASDF images for DS9

The first part of specifying an ADSF image is to specify
the path to an ASDF file, as one might expect. This can
be an absolute path or a path relative to the current
directory that ds9 has (normally the directory that ds9
was started from).

That alone isn't sufficient since there is not a standard
place within the file that the image may be located. (We
intend to provide mechanisms for presuming default
locations for variousdata types, but these do not exist
yet). Thus currently it is required to specify the
location of the image to be displayed.

Since the ASDF file is generally a tree structure, this
involves specifying the path from the base of the tree
to the image. There are two types of specifications, by
attribute name, or by an integer index depending on the
type of the nested structure (e.g., whether it is of a
dictionary type, or a list). The attribute names
(or keys, if you wish) are separated by periods.
Indices into lists use square brackets, i.e., '[]' and
do not need periods when adjacent to any other path
specifier, whether index or attribute.

So supposing the file is in the directory above the
default for ds9, then a more complex example would be:

../mydata.asdf:detector1.data.timeseries[7]image

Note the ':' separator between the file path and the
ADSF path.

Because ds9 uses square brackets as part of its mechanism
to load array data, the temporary file created replaces
the square brackets with parentheses when displayed in
its info section for the filename.

Once the file text entry box has a value, and it
corresponds to an existing file, the "Browse for
Image" button can be used to list all arrays of dimension
two or greater in the file, selecting one and pushing
the load button will append the ASDF object path to the
file/path specification and load the image.
"""


class AsdfEvents:

    def __init__(self, root, pid):
        self.root = root
        self.pid = pid
        self.imbrow = None
        self.imlist = None
        self.impaths = None
        self.imshapes = None
        self.headers = {} # Holds the header display state for different files. 
        self.asdf_handler = AsdfHandler()
        self.ds9 = ds9samp.start()
        self.ds9.send_array = asdf_send_array.__get__(self.ds9, ds9samp.Connection)
        tk.Label(root, text="asdf filename").grid(row=1)
        self.entry = tk.Entry(root)
        self.entry.grid(row=1, column=1)
        self.entry.bind("<Return>", self.load_entry_field)
        self.show_header_button = tk.Button(root, text="show header",
                        command=self.show_header)
        self.show_header_button.grid(row=1, column=2)
        self.show_header_button.config(state=tk.DISABLED)
        tk.Button(root, text="quit",
                        command=root.quit).grid(row=2, column=0,
                        sticky=tk.W, pady=4)
        tk.Button(root, text="load",
                        command=self.load_entry_field).grid(row=2, column=1,
                        sticky=tk.W, pady=4)
        tk.Button(root, text="Help",
                        command=self.show_filename_help).grid(row=2, column=2,
                        sticky=tk.W, pady=4)
        tk.Button(root, text="Browse for ASDF file",
                        command=self.browse_filename).grid(row=0, column=0,
                        sticky=tk.W, pady=4)
        self.browse_image_button = tk.Button(root, text="Browse for Image",
                                                command=self.browse_image)

        self.browse_image_button.grid(row=0, column=1, sticky=tk.W, pady=4)
        self.browse_image_button.config(state=tk.DISABLED)

    def load_entry_field(self, event=None):
        filepath = self.entry.get()
        if filepath:
            self.browse_image_button.config(state=tk.NORMAL)
            self.show_header_button.config(state=tk.NORMAL)
        else:
            self.browse_image_button.config(state=tk.DISABLED)
            self.show_header_button.config(state=tk.DISABLED)
            return
        if ":" in filepath:
            try:
                im, fitswcs = self.asdf_handler.get_asdf_image(filepath)
            except Pds9Error as err:
                messagebox.showerror(err.title, err.message)
                return
        else:
            return
        self.ds9.send_array(im, filepath)
        if fitswcs is not None:
            wcsfn = str((tempfiles.DS9TMP / "wcs.fits").resolve())
            with pathlib.Path.open(wcsfn, "wb") as fwcs:
                fwcs.write(bytes(fitswcs, "utf-8"))
            self.ds9.set(f"wcs load {wcsfn}")

    def show_filename_help(self):
        messagebox.showinfo(title="Filename/Image Path Info", message=FILEPATH_DOC)

    def browse_filename(self):
        filename = filedialog.askopenfilename()
        self.asdf_handler.set_filename(filename)
        self.entry.delete(0, tk.END)
        self.entry.insert(0, filename)
        self.browse_image_button.config(state=tk.NORMAL)
        self.show_header_button.config(state=tk.NORMAL)

    def browse_image(self):
        try:
            impaths, imshapes = self.asdf_handler.browse_images(self.entry.get())
        except Pds9Error as err:
            messagebox.showerror(err.title, err.message)
            return
        imbrow = tk.Toplevel(self.root)
        imbrow.wm_title("ASDF Image Browser")
        imlist = tk.Listbox(imbrow, width=60, height=20)
        imlist.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        button_load = tk.Button(imbrow, text="Load Image",
                                command=self.load_selected_image)
        button_load.pack()
        self.imbrow = imbrow
        self.imlist = imlist
        self.impaths = impaths
        self.imshapes = imshapes
        imdescs = ["  ".join((impath, str(imshape))) for impath, imshape
                                in zip(impaths, imshapes, strict=True)]
        for imdesc in imdescs:
            imlist.insert(tk.END, imdesc)

    def show_header(self):
        """
        Currently targeted for Roman, needs generalization.

        Omits attributes, asdf_library and history (virtually useless for most people)
        And for Roman, omits roman.meta.cal_logs (nearly as useless for quick looks)
        """
        filename = self.asdf_handler.split_selection(self.entry.get())[0]
        header_window = tk.Toplevel(self.root)
        if filename not in self.headers:
            self.headers[filename] = ['omit', header_window]
        else:
            self.headers[filename][1] = header_window
        header_window.title(f"Header for {filename}")
        header_window.grid_rowconfigure(0, weight=1)
        header_window.grid_columnconfigure(0, weight=1)
        text_area = ScrolledText(header_window, wrap=tk.WORD, width=80, height=80)
        text_area.grid(row=0, column=0, sticky="nsew", pady=4)
        if self.headers[filename][0] == 'omit':
            display_option_label = 'expand omitted sections'
        else:
            display_option_label = 'omit expanded sections'
        tk.Button(header_window, text=display_option_label,
            command=lambda: self.toggle_display_option(filename)).grid(
            row=1, column=0, sticky=tk.W, pady=4)
        tk.Button(header_window, text="quit", command=header_window.destroy).grid(
            row=2, column=0, sticky=tk.W, pady=4)
        try:
            text = self.asdf_handler.render_header_text(
                self.entry.get(),
                omit=self.headers[filename][0] == 'omit',
            )
        except Pds9Error as err:
            messagebox.showerror(err.title, err.message)
            header_window.destroy()
            return
        text_area.insert(tk.END, text)

    def toggle_display_option(self, filename):
        if self.headers[filename][0] == 'omit':
            self.headers[filename][0] = 'expand'
        else:
            self.headers[filename][0] = 'omit'
        self.headers[filename][1].destroy()
        self.headers[filename][1] = None
        self.filename = filename
        self.show_header()

    def header_destroy(self, filename):
        header_window = self.headers[filename][1]
        del self.headers[filename]
        header_window.destroy()

    def load_selected_image(self):
        impathindex = self.imlist.curselection()[0]
        impath = self.impaths[impathindex]
        filepath = self.entry.get()
        if ":" in filepath:
            filepath = filepath.split(":")[0]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, f"{filepath}:{impath}")
        self.imbrow.destroy()
        self.load_entry_field()

    def poll_for_ds9_updates(self):
        """
        Continually check to see that the ds9 process is still running
        or that ds9 wants something done (such as bringing the windows
        to the front.

        If the process no longer exists kill the Python Tkinter windows.
        """
        if not psutil.pid_exists(self.pid):
            self.asdf_handler.close()
            self.root.destroy()
        if check_for_window_raise():
            raise_all_windows(self.root)
            bring_to_front(self.root)

        self.root.after(1000, self.poll_for_ds9_updates)


def check_for_window_raise():
    """
    Check for the ds9tmp/ds9cmd file, and if it has the raise command.

    Return True if it does, and False otherwise.
    """
    tempfiles.create_ds9_tmp_dir()
    cmdfile = tempfiles.DS9TMP / "ds9cmd"
    if cmdfile.is_file():
        with pathlib.Path.open(cmdfile) as cmds:
            lines = cmds.readlines()
        if lines and lines[0] == "raise\n":
            cmdfile.unlink()
            return True
    return False


def raise_all_windows(root):
    windows = root.winfo_children()
    for window in windows:
        if isinstance(window, tk.Toplevel) or window == root:
            window.lift()


def bring_to_front(window):
    window.attributes("-topmost", True)
    window.update_idletasks()
    window.attributes("-topmost", False)
    window.focus_force()


def main():
    root = tk.Tk()
    root.title("ASDF File Access")
    root.lift()
    bring_to_front(root)
    ae = AsdfEvents(root, int(sys.argv[1]))
    root.after(1000, ae.poll_for_ds9_updates)
    root.mainloop()


if __name__ == "__main__":
    sys.exit(main())
