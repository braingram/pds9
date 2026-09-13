from __future__ import annotations

import pytest

from pds9.asdf_paths import convert_path_list, parse_filename, process_path_lists
from pds9.errors import PathSyntaxError


def test_parse_filename_parses_attribute_and_index_path():
    result = parse_filename("example.asdf:roman.data[2].sci")

    assert result == (
        "example.asdf",
        [("a", "roman"), ("a", "data"), ("i", 2), ("a", "sci")],
    )


def test_parse_filename_supports_path_starting_with_index():
    result = parse_filename("example.asdf:[0].data")

    assert result == ("example.asdf", [("i", 0), ("a", "data")])


def test_parse_filename_reports_missing_closing_bracket():
    with pytest.raises(PathSyntaxError, match=r"matching end of index '\]' not found") as err:
        parse_filename("example.asdf:data[12")

    assert err.value.title == "Path Syntax Error"


def test_parse_filename_reports_non_integer_index():
    with pytest.raises(PathSyntaxError, match="Index must be an integer instead of abc") as err:
        parse_filename("example.asdf:data[abc]")

    assert err.value.title == "Path Syntax Error"


def test_convert_path_list_formats_ds9_path():
    path, shape = convert_path_list(
        {"path": ["roman", "data", 2, "sci"], "iminfo": ("float32", (10, 20))}
    )

    assert path == "roman.data[2].sci"
    assert shape == "(10, 20)"


def test_process_path_lists_returns_parallel_lists():
    paths, shapes = process_path_lists(
        [
            {"path": ["images", 0], "iminfo": ("int16", (32, 32))},
            {"path": ["roman", "data"], "iminfo": ("float32", (64, 16))},
        ]
    )

    assert paths == ["images[0]", "roman.data"]
    assert shapes == ["(32, 32)", "(64, 16)"]
