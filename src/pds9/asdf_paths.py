# Licensed under a 3-clause BSD style license - see LICENSE.rst
from tkinter import messagebox



def parse_filename(filename):
    """
    Separate the filename into two major parts:
    First being the filename itself
    Second being a list of tuples,
    Each tuple consisting of a itemtype and value pair.
    The item type indicates whether the value is a dict key (attribute)
    or index into a list
    The expected syntax is that the filename is separated from the
    ASDF path with a colon.
    The asdf path uses '.' as a separator between keys and uses [<number>]
    to identify list indices.
    The tree attribute is considered implicit.
    Example of a filename input:
    /Users/bozo/data/mydata.asdf:level1.level2[4].image.sci
    """
    fn, apath = filename.split(":")
    # Parse asdf path (assumes no use of these special characters as part of
    # the attrbutes)
    # Prepend  '.' if it doesn't start with '['
    if apath[0] != "[":
        apath = "." + apath
    alist = []
    finished = False
    while not finished:
        if apath[0] == "[":  # index case
            endind = apath[1:].find("]")
            if endind < 0:
                messagebox.showerror("Path Syntax Error",
                    "matching end of index ']' not found")
                return None
            indexstr = apath[1:endind+1]
            try:
                index = int(indexstr)
            except ValueError:
                messagebox.showerror("Path Syntax Error",
                    f"Index must be an integer instead of {indexstr}")
                return None
            alist.append(("i", index))
            apath = apath[endind+2:]
        elif apath[0] == ".":  # attribute case
            nextperiod = apath[1:].find(".")
            nextbracket = apath[1:].find("[")
            end = len(apath[1:])
            if nextperiod > 0 and nextbracket > 0:
                attend = min(nextperiod, nextbracket)
            elif nextperiod > 0:
                attend = nextperiod
            elif nextbracket > 0:
                attend = nextbracket
            else:
                attend = end
            attr = apath[1:attend+1]
            apath = apath[attend+1:]
            if len(apath) == 0:
                finished = True
            alist.append(("a", attr))
        else:
            messagebox.showerror("Path Syntax Error",
                "Expected path delimiters: '.'' or '[' not found")
            return None
        if len(apath) == 0:
            finished = True
    return fn, alist



def process_path_lists(pathlists):
    """
    Generate a simple list of text paths useful for ds9 and a corresponding
    list of image info as single strings.
    """
    paths = []
    shapes = []
    for item in pathlists:
        path, imshape = convert_path_list(item)
        paths.append(path)
        shapes.append(imshape)
    return paths, shapes



def convert_path_list(pathlist):
    """
    Generate a text path useful for ds9 and a corresponding image description
    string.
    """
    plist = pathlist["path"]
    iminfo = pathlist["iminfo"]
    path = ""
    for item in plist:
        if type(item) is int:
            path += f"[{item}]"
        elif not path:
            path += item
        else:
            path += f".{item}"
    imshape = str(iminfo[1])
    return path, imshape
