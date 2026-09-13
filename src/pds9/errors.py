# Licensed under a 3-clause BSD style license - see LICENSE.rst


class Pds9Error(Exception):
    """Base exception for pds9 core logic errors."""

    title = "pds9 Error"

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class PathSyntaxError(Pds9Error):
    """Raised when the ASDF path syntax is invalid."""

    title = "Path Syntax Error"


class AsdfPathError(Pds9Error):
    """Raised when an ASDF path component cannot be resolved."""

    title = "ASDF Path Error"


class AsdfArrayError(Pds9Error):
    """Raised when an ASDF path does not resolve to an array."""

    title = "ASDF Path Error"


class AsdfFileNotFoundError(Pds9Error):
    """Raised when the referenced ASDF file cannot be opened."""

    title = "File not Found"
