from __future__ import annotations

from pds9 import tempfiles, ui
from pds9.asdf_paths import convert_path_list, parse_filename, process_path_lists


def test_parse_filename_parses_attribute_and_index_path():
    result = parse_filename("example.asdf:roman.data[2].sci")

    assert result == (
        "example.asdf",
        [("a", "roman"), ("a", "data"), ("i", 2), ("a", "sci")],
    )



def test_parse_filename_supports_path_starting_with_index():
    result = parse_filename("example.asdf:[0].data")

    assert result == ("example.asdf", [("i", 0), ("a", "data")])



def test_parse_filename_reports_missing_closing_bracket(monkeypatch):
    errors = []
    monkeypatch.setattr(
        "pds9.asdf_paths.messagebox.showerror",
        lambda title, message: errors.append((title, message)),
    )

    result = parse_filename("example.asdf:data[12")

    assert result is None
    assert errors == [
        ("Path Syntax Error", "matching end of index ']' not found"),
    ]



def test_parse_filename_reports_non_integer_index(monkeypatch):
    errors = []
    monkeypatch.setattr(
        "pds9.asdf_paths.messagebox.showerror",
        lambda title, message: errors.append((title, message)),
    )

    result = parse_filename("example.asdf:data[abc]")

    assert result is None
    assert errors == [
        ("Path Syntax Error", "Index must be an integer instead of abc"),
    ]



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



def test_remove_terminal_markup_strips_known_escape_sequences():
    text = "prefix\x1b[0m mid\x1b[1m more\x1b[2m end\x1b[3m"

    assert ui.remove_terminal_markup(text) == "prefix mid more end"



def test_create_ds9_tmpfile_name_uses_basename_and_preserves_ds9cmd(monkeypatch, tmp_path):
    monkeypatch.setattr(tempfiles, "DS9TMP", tmp_path)
    removable = tmp_path / "old.arr"
    removable.write_text("old")
    keep = tmp_path / "ds9cmd"
    keep.write_text("raise\n")

    tmp_filename = tempfiles.create_ds9_tmpfile_name("/data/example[2].asdf")

    assert tmp_filename == str((tmp_path / "example(2).asdf").resolve())
    assert not removable.exists()
    assert keep.exists()
