# Licensed under a 3-clause BSD style license - see LICENSE.rst
from collections.abc import Collection, Mapping
from contextlib import redirect_stdout
from io import StringIO

import asdf
import gwcs
import numpy as np
from asdf.tags.core.ndarray import NDArrayType
from asdf.tagged import TaggedDict, TaggedList
from asdf.yamlutil import tagged_tree_to_custom_tree

from pds9.errors import AsdfArrayError, AsdfFileNotFoundError, AsdfPathError, PathSyntaxError


class AsdfHandler:
    def __init__(self):
        self.filename = None
        self.af = None

    def close(self):
        if self.af is not None:
            self.af.close()
            self.af = None

    def set_filename(self, filename):
        self.filename = filename

    def split_selection(self, selection):
        if ":" in selection:
            filename, apath = selection.split(":", 1)
            return filename, apath
        return selection, None

    def get_asdf_image(self, selection):
        filename, apath = self._parse_filename(selection)
        af = self._open(filename)
        image = self._extract_asdf_array(af, apath)
        wcs = self._extract_gwcs(af) if "roman" in af.tree else None
        return image, wcs

    def browse_images(self, selection):
        filename, _apath = self.split_selection(selection)
        af = self._open(filename)
        pathlists = self._search_tree(af)
        return self._process_path_lists(pathlists)

    def render_header_text(self, selection, *, omit=True):
        filename, _apath = self.split_selection(selection)
        af = self._open(filename)
        tree = af.tree.copy()
        if omit:
            omitstr = "OMITTED for BREVITY in ds9 header display"
            if "asdf_library" in tree:
                tree["asdf_library"] = omitstr
            if "history" in tree:
                tree["history"] = omitstr
            if "cal_logs" in tree.get("roman", {}).get("meta", {}):
                tree["roman"]["meta"] = tree["roman"]["meta"].copy()
                tree["roman"]["meta"]["cal_logs"] = omitstr
        output = StringIO()
        with redirect_stdout(output):
            asdf.info(tree, max_rows=None, max_cols=None)
        return output.getvalue()

    def _current_filename(self):
        return self.filename

    def _open(self, filename=None):
        self.close()
        if filename is not None:
            self.filename = filename
        if not self.filename:
            return None
        try:
            self.af = asdf.open(self.filename, lazy_tree=True)
        except FileNotFoundError as err:
            raise AsdfFileNotFoundError(f"File {self.filename} not found") from err
        return self.af

    def _parse_filename(self, selection):
        fn, apath = selection.split(":", 1)
        alist = []
        index = 0

        while index < len(apath):
            if apath[index] == ".":
                index += 1
                continue

            if apath[index] == "[":
                endind = apath.find("]", index + 1)
                if endind < 0:
                    raise PathSyntaxError("matching end of index ']' not found")
                indexstr = apath[index + 1:endind]
                try:
                    alist.append(("i", int(indexstr)))
                except ValueError as err:
                    raise PathSyntaxError(
                        f"Index must be an integer instead of {indexstr}"
                    ) from err
                index = endind + 1
                continue

            start = index
            while index < len(apath) and apath[index] not in ".[":
                index += 1
            if start == index:
                raise PathSyntaxError("Expected path delimiters: '.'' or '[' not found")
            alist.append(("a", apath[start:index]))

        return fn, alist

    def _convert_path_list(self, pathlist):
        plist = pathlist["path"]
        iminfo = pathlist["iminfo"]
        path = "".join(
            f"[{item}]" if isinstance(item, int) else item if index == 0 else f".{item}"
            for index, item in enumerate(plist)
        )
        return path, str(iminfo[1])

    def _process_path_lists(self, pathlists):
        converted = [self._convert_path_list(item) for item in pathlists]
        paths = [path for path, _shape in converted]
        shapes = [shape for _path, shape in converted]
        return paths, shapes

    def _extract_asdf_array(self, af, apath):
        node = af.tree
        for ptype, value in apath:
            if ptype == "a":
                try:
                    node = node.data[value] if type(node) is TaggedDict else node[value]
                except KeyError as err:
                    raise AsdfPathError(
                        f"Specified ADSF path component '{value}' not in file"
                    ) from err
            elif ptype == "i":
                try:
                    node = node.data[value] if type(node) is TaggedList else node[value]
                except KeyError as err:
                    raise AsdfPathError(
                        f"Specified ASDF index component '{value}' not in file"
                    ) from err
        if not isinstance(node, np.ndarray | NDArrayType):
            raise AsdfArrayError("Given ADSF path does not correspond to an array")
        return node if isinstance(node, np.ndarray) else tagged_tree_to_custom_tree(node, af)._make_array()  # noqa: SLF001

    def _fixwcs(self, hdr):
        delete_list = ["naxis", "naxis1", "naxis2", "sipmxerr"]
        for keyword in delete_list:
            del hdr[keyword]
        hdrstr = str(hdr)
        endstr = "END" + 77 * " "
        blankcard = 80 * " "
        return hdrstr.replace(endstr, blankcard)

    def _extract_gwcs(self, af):
        node = af.tree
        apath = (("a", "roman"), ("a", "meta"), ("a", "wcs"))
        for ptype, value in apath:
            if ptype == "a":
                try:
                    node = node[value]
                except KeyError as err:
                    raise AsdfPathError(
                        f"Specified ADSF path component '{value}' not in file"
                    ) from err
        if not isinstance(node, gwcs.WCS):
            node = tagged_tree_to_custom_tree(node, af)
        fitswcs = node.to_fits_sip(degree=5, max_inv_pix_error=None, npoints=10)
        return self._fixwcs(fitswcs)

    def _callsearch(self, pathlist, nodeitem, index, af, path, min_nelements):
        spath = path.copy()
        spath.append(index)
        sresult = self._search_tree(af, nodeitem[index], spath, min_nelements)
        if sresult is not None:
            if isinstance(sresult, Mapping):
                pathlist.append(sresult)
            else:
                pathlist += sresult

    def _search_tree(self, af, tree=None, path=None, min_nelements=1000):
        if tree is None:
            tree = af.tree
        if path is None:
            path = []
        pathlist = []
        if isinstance(tree, np.ndarray | NDArrayType):
            lazyim = tree if isinstance(tree, np.ndarray) else tagged_tree_to_custom_tree(tree, af)
            if len(lazyim.shape) < 2:
                return None
            nelements = np.prod(lazyim.shape)
            if nelements < min_nelements:
                return None
            if lazyim.dtype is complex:
                return None
            iminfo = (lazyim.dtype, lazyim.shape)
            return {"path": path, "iminfo": iminfo}
        if isinstance(tree, Mapping):
            for key in tree:
                self._callsearch(pathlist, tree, key, af, path, min_nelements)
        elif (
            isinstance(tree, Collection)
            and not isinstance(tree, Mapping | str | bytes | bytearray)
        ):
            for i, _item in enumerate(tree):
                self._callsearch(pathlist, tree, i, af, path, min_nelements)
        if pathlist:
            return pathlist
        return None
