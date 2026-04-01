"""Unit tests for FileReader module."""

import base64
import json
import os
import shutil
import struct
import tempfile
import zlib
from pathlib import Path
from unittest import mock

import pytest

from toolregistry_hub.file_reader import FileReader


class TestFileReaderRead:
    """Test cases for FileReader.read()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "sample.txt")
        # Create a 10-line file
        with open(self.test_file, "w", encoding="utf-8") as f:
            for i in range(1, 11):
                f.write(f"Line {i} content\n")

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_read_basic(self):
        """Full file read with line numbers."""
        result = FileReader.read(self.test_file)
        assert "[" in result and "sample.txt" in result
        assert " 1 | Line 1 content" in result
        assert "10 | Line 10 content" in result

    def test_read_offset(self):
        """Read starting from a specific line."""
        result = FileReader.read(self.test_file, offset=5)
        assert "5 | Line 5 content" in result
        assert "Line 1 content" not in result

    def test_read_limit(self):
        """Read limited number of lines."""
        result = FileReader.read(self.test_file, limit=3)
        assert "1 | Line 1 content" in result
        assert "3 | Line 3 content" in result
        assert "Line 4 content" not in result

    def test_read_offset_and_limit(self):
        """Read with both offset and limit."""
        result = FileReader.read(self.test_file, offset=3, limit=2)
        assert "3 | Line 3 content" in result
        assert "4 | Line 4 content" in result
        assert "Line 2 content" not in result
        assert "Line 5 content" not in result

    def test_read_continuation_hint(self):
        """Shows continuation hint when more lines available."""
        result = FileReader.read(self.test_file, limit=3)
        assert "use offset=" in result

    def test_read_no_continuation_hint_at_end(self):
        """No continuation hint when all lines read."""
        result = FileReader.read(self.test_file, limit=100)
        assert "use offset=" not in result

    def test_read_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileReader.read(os.path.join(self.temp_dir, "nope.txt"))

    def test_read_directory(self):
        with pytest.raises(IsADirectoryError):
            FileReader.read(self.temp_dir)

    def test_read_invalid_offset(self):
        with pytest.raises(ValueError, match="offset"):
            FileReader.read(self.test_file, offset=0)

    def test_read_empty_file(self):
        empty = os.path.join(self.temp_dir, "empty.txt")
        Path(empty).touch()
        result = FileReader.read(empty)
        assert "0" in result  # total lines = 0

    def test_read_large_file_guard(self):
        """File exceeding size limit returns warning message."""
        large = os.path.join(self.temp_dir, "large.txt")
        with open(large, "w") as f:
            f.write("x" * (11 * 1024 * 1024))  # 11 MB
        result = FileReader.read(large)
        assert "too large" in result.lower()


class TestFileReaderNotebook:
    """Test cases for FileReader.read_notebook()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _write_notebook(self, cells, language="python"):
        path = os.path.join(self.temp_dir, "test.ipynb")
        nb = {
            "metadata": {
                "kernelspec": {
                    "language": language,
                    "display_name": language.capitalize(),
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5,
            "cells": cells,
        }
        with open(path, "w") as f:
            json.dump(nb, f)
        return path

    def test_code_cell(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "code",
                    "source": ["print('hello')"],
                    "outputs": [{"output_type": "stream", "text": ["hello\n"]}],
                    "metadata": {},
                }
            ]
        )
        result = FileReader.read_notebook(path)
        assert "```python" in result
        assert "print('hello')" in result
        assert "hello" in result

    def test_markdown_cell(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "markdown",
                    "source": ["# Title\n", "Some text"],
                    "metadata": {},
                }
            ]
        )
        result = FileReader.read_notebook(path)
        assert "# Title" in result
        assert "[markdown]" in result

    def test_error_output(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "code",
                    "source": ["1/0"],
                    "outputs": [
                        {
                            "output_type": "error",
                            "ename": "ZeroDivisionError",
                            "evalue": "division by zero",
                            "traceback": [],
                        }
                    ],
                    "metadata": {},
                }
            ]
        )
        result = FileReader.read_notebook(path)
        assert "ZeroDivisionError" in result

    def test_execute_result(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "code",
                    "source": ["42"],
                    "outputs": [
                        {
                            "output_type": "execute_result",
                            "data": {"text/plain": ["42"]},
                            "metadata": {},
                        }
                    ],
                    "metadata": {},
                }
            ]
        )
        result = FileReader.read_notebook(path)
        assert "42" in result

    def test_image_output_omitted(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "code",
                    "source": ["plot()"],
                    "outputs": [
                        {
                            "output_type": "display_data",
                            "data": {"image/png": "base64data"},
                            "metadata": {},
                        }
                    ],
                    "metadata": {},
                }
            ]
        )
        result = FileReader.read_notebook(path)
        assert "[Image output omitted]" in result

    def test_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileReader.read_notebook("/nonexistent.ipynb")

    def test_invalid_json(self):
        path = os.path.join(self.temp_dir, "bad.ipynb")
        with open(path, "w") as f:
            f.write("not json")
        with pytest.raises(ValueError, match="Invalid notebook JSON"):
            FileReader.read_notebook(path)

    def test_missing_cells_key(self):
        path = os.path.join(self.temp_dir, "nocells.ipynb")
        with open(path, "w") as f:
            json.dump({"metadata": {}}, f)
        with pytest.raises(ValueError, match="no 'cells' key"):
            FileReader.read_notebook(path)

    def test_language_detection(self):
        path = self._write_notebook(
            [
                {
                    "cell_type": "code",
                    "source": ["console.log('hi')"],
                    "outputs": [],
                    "metadata": {},
                }
            ],
            language="javascript",
        )
        result = FileReader.read_notebook(path)
        assert "```javascript" in result


class TestFileReaderPdf:
    """Test cases for FileReader.read_pdf()."""

    def test_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileReader.read_pdf("/nonexistent.pdf")

    def test_invalid_page_range(self):
        with pytest.raises(ValueError):
            FileReader._parse_page_range("abc")

    def test_parse_single_page(self):
        assert FileReader._parse_page_range("3") == (2, 2)

    def test_parse_page_range(self):
        assert FileReader._parse_page_range("1-5") == (0, 4)

    def test_parse_open_end_range(self):
        assert FileReader._parse_page_range("3-") == (2, -1)

    def test_parse_none(self):
        assert FileReader._parse_page_range(None) == (0, -1)

    def test_parse_negative_page(self):
        with pytest.raises(ValueError, match="must be >= 1"):
            FileReader._parse_page_range("0")

    def test_parse_reversed_range(self):
        with pytest.raises(ValueError, match="End page must be >= start"):
            FileReader._parse_page_range("5-3")

    def test_clamp_page_range(self):
        # Caps at 20 pages
        start, end = FileReader._clamp_page_range(0, 99, 100)
        assert end - start + 1 == 20


def _make_minimal_png(width: int = 1, height: int = 1) -> bytes:
    """Generate a minimal valid PNG file in pure Python."""

    def _chunk(chunk_type: bytes, data: bytes) -> bytes:
        c = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr = _chunk(b"IHDR", ihdr_data)
    # Row data: filter byte + RGB pixels
    raw = b""
    for _ in range(height):
        raw += b"\x00" + b"\xff\x00\x00" * width  # red pixels
    idat = _chunk(b"IDAT", zlib.compress(raw))
    iend = _chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def _make_minimal_jpeg() -> bytes:
    """Generate a minimal valid JPEG using Pillow, or return a stub."""
    try:
        import io

        from PIL import Image

        img = Image.new("RGB", (2, 2), color=(255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        pytest.skip("Pillow required to generate JPEG test data")


class TestFileReaderImage:
    """Test cases for FileReader.read_image()."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def _write_image(self, name: str, data: bytes) -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def test_read_image_png(self):
        """PNG returns [TextBlock, ImageBlock]."""
        png_data = _make_minimal_png()
        path = self._write_image("test.png", png_data)
        result = FileReader.read_image(path)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["type"] == "text"
        assert result[1]["type"] == "image"
        assert result[1]["source"]["media_type"] == "image/png"
        assert result[1]["source"]["type"] == "base64"
        # Verify round-trip
        decoded = base64.b64decode(result[1]["source"]["data"])
        assert decoded == png_data

    def test_read_image_jpeg(self):
        """JPEG returns correct content blocks."""
        jpeg_data = _make_minimal_jpeg()
        path = self._write_image("photo.jpg", jpeg_data)
        result = FileReader.read_image(path)

        assert len(result) == 2
        assert result[1]["source"]["media_type"] == "image/jpeg"

    def test_read_image_metadata_text_block(self):
        """TextBlock contains filename, MIME type, and byte size."""
        png_data = _make_minimal_png()
        path = self._write_image("chart.png", png_data)
        result = FileReader.read_image(path)

        text = result[0]["text"]
        assert "chart.png" in text
        assert "image/png" in text
        assert str(len(png_data)) in text

    def test_read_image_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            FileReader.read_image(os.path.join(self.temp_dir, "nope.png"))

    def test_read_image_unsupported_format(self):
        path = self._write_image("photo.bmp", b"BM fake bmp data")
        with pytest.raises(ValueError, match="Unsupported image format"):
            FileReader.read_image(path)

    def test_read_image_downsample(self):
        """Large image is downsampled when Pillow is available."""
        PIL = pytest.importorskip("PIL")  # noqa: F841
        # Create a large PNG (100x100 = decent size after encoding)
        png_data = _make_minimal_png(width=100, height=100)
        path = self._write_image("big.png", png_data)

        # Use a very small max_size to force downsampling
        result = FileReader.read_image(path, max_size=100)

        assert len(result) == 2
        assert result[1]["type"] == "image"
        # After downsampling PNG → JPEG
        assert result[1]["source"]["media_type"] == "image/jpeg"

    def test_read_image_no_pillow_fallback(self):
        """Without Pillow, large image is returned as-is with warning."""
        png_data = _make_minimal_png(width=50, height=50)
        path = self._write_image("big.png", png_data)

        with mock.patch.dict("sys.modules", {"PIL": None, "PIL.Image": None}):
            result = FileReader.read_image(path, max_size=10)

        assert len(result) == 2
        # Original PNG data returned unchanged
        decoded = base64.b64decode(result[1]["source"]["data"])
        assert decoded == png_data
        assert result[1]["source"]["media_type"] == "image/png"
