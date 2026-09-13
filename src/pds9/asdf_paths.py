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
    fn, apath = filename.split(":", 1)
    alist = []
    index = 0

    while index < len(apath):
        if apath[index] == ".":
            index += 1
            continue

        if apath[index] == "[":
            endind = apath.find("]", index + 1)
            if endind < 0:
                messagebox.showerror("Path Syntax Error",
                    "matching end of index ']' not found")
                return None
            indexstr = apath[index + 1:endind]
            try:
                alist.append(("i", int(indexstr)))
            except ValueError:
                messagebox.showerror("Path Syntax Error",
                    f"Index must be an integer instead of {indexstr}")
                return None
            index = endind + 1
            continue

        start = index
        while index < len(apath) and apath[index] not in ".[":
            index += 1
        if start == index:
            messagebox.showerror("Path Syntax Error",
                "Expected path delimiters: '.'' or '[' not found")
            return None
        alist.append(("a", apath[start:index]))

    return fn, alist



def process_path_lists(pathlists):
    """
    Generate a simple list of text paths useful for ds9 and a corresponding
    list of image info as single strings.
    """
    converted = [convert_path_list(item) for item in pathlists]
    paths = [path for path, _shape in converted]
    shapes = [shape for _path, shape in converted]
    return paths, shapes



def convert_path_list(pathlist):
    """
    Generate a text path useful for ds9 and a corresponding image description
    string.
    """
    plist = pathlist["path"]
    iminfo = pathlist["iminfo"]
    path = "".join(
        f"[{item}]" if isinstance(item, int) else item if index == 0 else f".{item}"
        for index, item in enumerate(plist)
    )
    imshape = str(iminfo[1])
    return path, imshape
