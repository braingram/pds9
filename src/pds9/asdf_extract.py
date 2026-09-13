# Licensed under a 3-clause BSD style license - see LICENSE.rst
import asdf
import numpy as np
from tkinter import messagebox

from asdf.tagged import TaggedDict, TaggedList
from asdf.yamlutil import tagged_tree_to_custom_tree

from pds9.asdf_paths import parse_filename



def get_asdf_image(asdfpath):

    retval = parse_filename(asdfpath)
    if retval is not None:
        fn, alist = retval
    else:
        return None
    # Must load in raw format to make the entire structure easily searchable
    try:
        af = asdf.open(fn, _force_raw_types=True)
    except FileNotFoundError:
        messagebox.showerror("File not Found", f"File {fn} not found")
        return None
    # Extract the referenced array
    node = af.tree
    im = extract_asdf_array(node, alist, af)
    wcs = extract_gwcs(af.tree, af) if "roman" in af.tree else None
    return im, wcs



def extract_asdf_array(tree, apath, ctx):
    """
    Given an asdf tree instance, follow the path to the array item,
    convert it into an array and return the array instance.
    """
    node = tree
    for ptype, value in apath:
        if ptype == "a":
            try:
                node = node.data[value] if type(node) is TaggedDict else node[value]
            except KeyError:
                messagebox.showerror("ASDF Path Error",
                    f"Specified ADSF path component '{value}' not in file")
                return None
        elif ptype == "i":
            try:
                node = node.data[value] if type(node) is TaggedList else node[value]
            except KeyError:
                messagebox.showerror("ASDF Path Error",
                    f"Specified ASDF index component '{value}' not in file")
                return None
    if not node._tag.startswith("tag:stsci.edu:asdf/core/ndarray-"):  # noqa: SLF001
        messagebox.showerror("Given ADSF path does not correspond to an array")
        return None
    return tagged_tree_to_custom_tree(node, ctx)._make_array()  # noqa: SLF001



def fixwcs(hdr):
    """
    Put the GWCS generated SIP header in a form that ds9 will accept.

    Assumes the argument is an astropy.io.fit Header instance
    """
    delete_list = ["naxis", "naxis1", "naxis2", "sipmxerr"]
    for keyword in delete_list:
        del hdr[keyword]
    hdrstr = str(hdr)
    # Must strip the END statement out of this
    endstr = "END" + 77 * " "
    blankcard = 80 * " "
    return hdrstr.replace(endstr, blankcard)



def extract_gwcs(tree, ctx):
# def extract_gwcs(tree, ctx):
    """
    This currently only works for roman data
    """
    node = tree
    apath = (("a", "roman"), ("a", "meta"), ("a", "wcs"))
    for ptype, value in apath:
        if ptype == "a":
            try:
                node = node[value]
            except KeyError:
                messagebox.showerror("ASDF Path Error",
                          f"Specified ADSF path component '{value}' not in file")
                return None
    gwcs = node
    gwcs = tagged_tree_to_custom_tree(gwcs, ctx)
    fitswcs = gwcs.to_fits_sip(degree=5, max_inv_pix_error=None, npoints=10)
    return fixwcs(fitswcs)



def callsearch(pathlist, nodeitem, index, ctx, path, min_nelements):  # noqa: PLR0917
    spath = path.copy()
    spath.append(index)
    sresult = search_tree(nodeitem[index], ctx, spath, min_nelements)
    if sresult is not None:
        if isinstance(sresult, dict):
            pathlist.append(sresult)
        else:
            pathlist += sresult



def search_tree(tree, ctx, path=None, min_nelements=1000):
    """
    Walk through the tree recursively to find all images and their associated paths
    """
    if path is None:
        path = []
    pathlist = []
    if isinstance(tree, TaggedDict):
        if tree._tag.startswith("tag:stsci.edu:asdf/core/ndarray-"):  # noqa: SLF001
            # Convert and check for size
            lazyim = tagged_tree_to_custom_tree(tree, ctx)
            if len(lazyim.shape) < 2:
                return None
            nelements = np.prod(lazyim.shape)
            if nelements < min_nelements:
                return None
            if lazyim.dtype is complex:
                return None
            iminfo = (lazyim.dtype, lazyim.shape)
            return {"path": path, "iminfo": iminfo}
        for key in tree.data:
            callsearch(pathlist, tree.data, key, ctx, path, min_nelements)
    elif isinstance(tree, TaggedList):
        for i, _item in enumerate(tree.data):
            callsearch(pathlist, tree.data, i, ctx, path, min_nelements)
    elif isinstance(tree, dict):
        for key in tree:
            callsearch(pathlist, tree, key, ctx, path, min_nelements)
    elif isinstance(tree, list):
        for i, _item in enumerate(tree):
            callsearch(pathlist, tree, i, ctx, path, min_nelements)
    if pathlist:
        return pathlist
    return None
