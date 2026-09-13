from __future__ import annotations

from pathlib import Path

import pytest

from pds9.asdf_handler import AsdfHandler
from pds9.errors import AsdfPathError, PathSyntaxError

FIXTURE = Path(__file__).parent / "data" / "ex.asdf"



def test_set_and_get_current_filename():
    handler = AsdfHandler()

    handler.set_filename(str(FIXTURE))

    assert handler._current_filename() == str(FIXTURE)



def test_split_selection_returns_filename_and_optional_path():
    handler = AsdfHandler()

    assert handler.split_selection(f"{FIXTURE}:image") == (str(FIXTURE), "image")
    assert handler.split_selection(str(FIXTURE)) == (str(FIXTURE), None)



def test_parse_filename_parses_attribute_and_index_path():
    handler = AsdfHandler()

    result = handler._parse_filename("example.asdf:roman.data[2].sci")

    assert result == (
        "example.asdf",
        [("a", "roman"), ("a", "data"), ("i", 2), ("a", "sci")],
    )



def test_parse_filename_supports_path_starting_with_index():
    handler = AsdfHandler()

    result = handler._parse_filename("example.asdf:[0].data")

    assert result == ("example.asdf", [("i", 0), ("a", "data")])



def test_parse_filename_reports_missing_closing_bracket():
    handler = AsdfHandler()

    with pytest.raises(PathSyntaxError, match=r"matching end of index '\]' not found"):
        handler._parse_filename("example.asdf:data[12")



def test_parse_filename_reports_non_integer_index():
    handler = AsdfHandler()

    with pytest.raises(PathSyntaxError, match="Index must be an integer instead of abc"):
        handler._parse_filename("example.asdf:data[abc]")



def test_convert_path_list_formats_ds9_path():
    handler = AsdfHandler()

    path, shape = handler._convert_path_list(
        {"path": ["roman", "data", 2, "sci"], "iminfo": ("float32", (10, 20))}
    )

    assert path == "roman.data[2].sci"
    assert shape == "(10, 20)"



def test_normalize_search_path_converts_asdf_search_format():
    handler = AsdfHandler()

    result = handler._normalize_search_path("root['moredata']['images'][2]")

    assert result == ["moredata", "images", 2]



def test_process_path_lists_returns_parallel_lists():
    handler = AsdfHandler()

    paths, shapes = handler._process_path_lists(
        [
            {"path": ["images", 0], "iminfo": ("int16", (32, 32))},
            {"path": ["roman", "data"], "iminfo": ("float32", (64, 16))},
        ]
    )

    assert paths == ["images[0]", "roman.data"]
    assert shapes == ["(32, 32)", "(64, 16)"]



def test_open_and_close_fixture_file():
    handler = AsdfHandler()

    af = handler._open(str(FIXTURE))
    try:
        assert af.tree["desc"] == "top of the tree"
        assert handler.af is af
    finally:
        handler.close()

    assert handler.af is None



def test_get_asdf_image_extracts_array_from_open_file_path():
    handler = AsdfHandler()

    try:
        image, wcs = handler.get_asdf_image(f"{FIXTURE}:image")

        assert image.shape == (512, 512)
        assert wcs is None
    finally:
        handler.close()



def test_extract_asdf_array_raises_for_missing_path_component():
    handler = AsdfHandler()
    af = handler._open(str(FIXTURE))
    try:
        with pytest.raises(AsdfPathError, match="Specified ADSF path component 'missing' not in file"):
            handler._extract_asdf_array(af, [("a", "missing")])
    finally:
        handler.close()



def test_browse_images_finds_expected_images():
    handler = AsdfHandler()
    try:
        paths, shapes = handler.browse_images(str(FIXTURE))

        assert "cubedata" in paths
        assert "image" in paths
        assert "moredata.deepstuff.image" in paths
        assert "moredata.images[0]" in paths
        assert "(512, 512)" in shapes
        assert "(10, 60, 60)" in shapes
    finally:
        handler.close()



def test_render_header_text_returns_rendered_text():
    handler = AsdfHandler()
    try:
        text = handler.render_header_text(str(FIXTURE), omit=True)

        assert "OMITTED for BREVITY in ds9 header display" in text
        assert "top of the tree" in text
    finally:
        handler.close()


