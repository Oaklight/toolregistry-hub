"""Multi-format file reader with line numbers and pagination.

Supports plain text (with line-numbered output and offset/limit),
Jupyter notebooks (stdlib ``json``), PDF files (optional dependency),
and image files (returned as multimodal content blocks).
"""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Safety caps
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB for text files
_MAX_LINES_DEFAULT = 2000
_MAX_PDF_PAGES = 20

# Image constants
_SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
_EXTENSION_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}
_MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB base64 budget


class FileReader:
    """Multi-format file reader with line numbers and pagination."""

    @staticmethod
    def read(
        path: str,
        offset: int = 1,
        limit: int | None = None,
    ) -> str:
        """Read a text file with line numbers.

        Args:
            path: Path to file.
            offset: Starting line number (1-indexed). Defaults to 1.
            limit: Maximum number of lines to read. Defaults to 2000.

        Returns:
            File content with line numbers in ``"N | content"`` format.
            Includes a metadata header with file path, total lines, and
            the range actually read.

        Raises:
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path is a directory.
            ValueError: If offset is less than 1.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if p.is_dir():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")
        if offset < 1:
            raise ValueError("offset must be >= 1")

        effective_limit = limit if limit is not None else _MAX_LINES_DEFAULT

        # Size guard
        file_size = p.stat().st_size
        if file_size > _MAX_FILE_SIZE_BYTES:
            return (
                f"[File too large: {file_size:,} bytes "
                f"(limit {_MAX_FILE_SIZE_BYTES:,}). "
                f"Use offset/limit to read in segments.]"
            )

        text = p.read_text(encoding="utf-8", errors="replace")
        all_lines = text.splitlines()
        total_lines = len(all_lines)

        start = offset - 1  # convert to 0-indexed
        end = min(start + effective_limit, total_lines)
        selected = all_lines[start:end]

        # Build line-numbered output
        width = len(str(end))
        numbered = [
            f"{i + offset:>{width}} | {line}" for i, line in enumerate(selected)
        ]

        # Metadata header
        range_str = f"{offset}-{start + len(selected)}"
        header = f"[{path}] lines {range_str} of {total_lines}"
        if end < total_lines:
            header += f" (use offset={end + 1} to read more)"

        return header + "\n" + "\n".join(numbered)

    @staticmethod
    def read_pdf(
        path: str,
        pages: str | None = None,
    ) -> str:
        """Read a PDF file and extract text.

        Uses ``pypdf`` (zero-dependency, BSD) by default. If ``pdfplumber``
        is installed, uses it for better text quality.

        Args:
            path: Path to PDF file.
            pages: Page range string (e.g. ``"1-5"``, ``"3"``, ``"10-20"``).
                Max 20 pages per call. Defaults to all pages (up to cap).

        Returns:
            Extracted text content with page markers.

        Raises:
            FileNotFoundError: If the file does not exist.
            ImportError: If neither ``pypdf`` nor ``pdfplumber`` is installed.
            ValueError: If page range is invalid.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        start_page, end_page = FileReader._parse_page_range(pages)

        # Try pdfplumber first (better quality), fall back to pypdf
        try:
            return FileReader._read_pdf_pdfplumber(p, start_page, end_page)
        except ImportError:
            pass

        try:
            return FileReader._read_pdf_pypdf(p, start_page, end_page)
        except ImportError:
            raise ImportError(
                "PDF reading requires 'pypdf' or 'pdfplumber'. "
                "Install with: pip install toolregistry-hub[reader]"
            ) from None

    @staticmethod
    def read_notebook(path: str) -> str:
        """Read a Jupyter notebook and return formatted cell contents.

        Uses stdlib ``json`` only — no external dependencies.

        Args:
            path: Path to ``.ipynb`` file.

        Returns:
            All cells with type markers (code/markdown) and outputs.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid notebook.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid notebook JSON: {e}") from e

        if "cells" not in data:
            raise ValueError(f"Not a valid Jupyter notebook (no 'cells' key): {path}")

        # Detect language from kernel info
        lang = "python"
        kernel_info = data.get("metadata", {}).get("kernelspec", {})
        if kernel_info.get("language"):
            lang = kernel_info["language"]

        lines: list[str] = []
        lines.append(f"[Notebook: {path}]")

        for i, cell in enumerate(data["cells"]):
            cell_type = cell.get("cell_type", "unknown")
            source = "".join(cell.get("source", []))

            lines.append(f"\n--- Cell {i + 1} [{cell_type}] ---")

            if cell_type == "code":
                lines.append(f"```{lang}")
                lines.append(source)
                lines.append("```")

                # Process outputs
                for output in cell.get("outputs", []):
                    output_text = FileReader._extract_notebook_output(output)
                    if output_text:
                        lines.append(f"Output:\n{output_text}")
            else:
                lines.append(source)

        return "\n".join(lines)

    @staticmethod
    def read_image(
        path: str,
        max_size: int = _MAX_IMAGE_SIZE_BYTES,
    ) -> list:
        """Read an image file and return as multimodal content blocks.

        Returns a list of content blocks (TextBlock + ImageBlock) that the
        toolregistry pipeline can expand into format-specific multimodal
        messages via ``expand_content_blocks()``.

        If the base64-encoded image exceeds ``max_size``, Pillow is used to
        downsample it. If Pillow is not installed, the original image is
        returned with a warning.

        Args:
            path: Path to image file (.png, .jpg, .jpeg, .gif, .webp).
            max_size: Maximum base64-encoded size in bytes. Defaults to 5 MB.

        Returns:
            A list of two content blocks::

                [
                    {"type": "text", "text": "[Image: name (mime, size)]"},
                    {"type": "image", "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "iVBOR..."
                    }}
                ]

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file extension is not supported.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {path}")

        ext = p.suffix.lower()
        if ext not in _SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: '{ext}'. "
                f"Supported: {', '.join(sorted(_SUPPORTED_IMAGE_EXTENSIONS))}"
            )

        media_type = _EXTENSION_TO_MIME[ext]
        img_data = p.read_bytes()
        raw_size = len(img_data)

        b64_data = base64.b64encode(img_data).decode("ascii")

        if len(b64_data) > max_size:
            img_data, media_type = FileReader._downsample_image(
                img_data, media_type, max_size
            )
            b64_data = base64.b64encode(img_data).decode("ascii")

        return [
            {
                "type": "text",
                "text": f"[Image: {p.name} ({media_type}, {raw_size} bytes)]",
            },
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": b64_data,
                },
            },
        ]

    @staticmethod
    def _downsample_image(
        img_data: bytes,
        media_type: str,
        max_size: int,
    ) -> tuple[bytes, str]:
        """Downsample an image to fit within the base64 size budget.

        Uses adaptive quality reduction based on ``target_ratio``. Strategy
        inspired by payload-size-based compression (similar to argo-proxy).

        If Pillow is not available, returns the original data with a warning
        logged.

        Args:
            img_data: Raw image bytes.
            media_type: MIME type of the image.
            max_size: Target maximum base64-encoded size in bytes.

        Returns:
            Tuple of (compressed_bytes, output_media_type).
        """
        try:
            from PIL import Image
        except ImportError:
            logger.warning(
                "Pillow not installed; returning original image without "
                "compression. Install with: pip install Pillow"
            )
            return img_data, media_type

        current_b64_size = len(base64.b64encode(img_data))
        target_ratio = max_size / current_b64_size

        img = Image.open(io.BytesIO(img_data))

        buf = io.BytesIO()

        if media_type == "image/jpeg":
            quality = max(int(85 * target_ratio), 20)
            img = img.convert("RGB") if img.mode != "RGB" else img
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue(), "image/jpeg"

        if media_type == "image/png":
            # Convert to JPEG for better compression; handle transparency
            quality = max(int(75 * target_ratio), 15)
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue(), "image/jpeg"

        if media_type == "image/webp":
            quality = max(int(80 * target_ratio), 15)
            img = img.convert("RGB") if img.mode not in ("RGB", "RGBA") else img
            img.save(buf, format="WEBP", quality=quality)
            return buf.getvalue(), "image/webp"

        if media_type == "image/gif":
            # Extract first frame and convert to JPEG
            quality = max(int(70 * target_ratio), 15)
            img = img.convert("RGB")
            img.save(buf, format="JPEG", quality=quality)
            return buf.getvalue(), "image/jpeg"

        # Fallback: return as-is
        return img_data, media_type

    # --- Private helpers ---

    @staticmethod
    def _parse_page_range(pages: str | None) -> tuple[int, int]:
        """Parse a page range string into (start, end) 0-indexed.

        Args:
            pages: Page range like "1-5", "3", or None for all.

        Returns:
            Tuple of (start_page, end_page) as 0-indexed integers.
            end_page is -1 to indicate "to the end".

        Raises:
            ValueError: If page range format is invalid.
        """
        if pages is None:
            return (0, -1)

        pages = pages.strip()
        if "-" in pages:
            parts = pages.split("-", 1)
            try:
                start = int(parts[0]) - 1
                end = int(parts[1]) - 1 if parts[1] else -1
            except ValueError:
                raise ValueError(f"Invalid page range: {pages}") from None
        else:
            try:
                start = int(pages) - 1
                end = start
            except ValueError:
                raise ValueError(f"Invalid page range: {pages}") from None

        if start < 0:
            raise ValueError(f"Page numbers must be >= 1, got: {pages}")
        if end != -1 and end < start:
            raise ValueError(f"End page must be >= start page: {pages}")

        return (start, end)

    @staticmethod
    def _clamp_page_range(start: int, end: int, total_pages: int) -> tuple[int, int]:
        """Clamp page range to valid bounds.

        Args:
            start: 0-indexed start page.
            end: 0-indexed end page (-1 means to the end).
            total_pages: Total number of pages in the document.

        Returns:
            Clamped (start, end) tuple, both 0-indexed inclusive.
        """
        if end == -1:
            end = total_pages - 1
        end = min(end, total_pages - 1)

        # Enforce page cap
        if end - start + 1 > _MAX_PDF_PAGES:
            end = start + _MAX_PDF_PAGES - 1

        return (start, end)

    @staticmethod
    def _read_pdf_pypdf(p: Path, start: int, end: int) -> str:
        """Extract text from PDF using pypdf.

        Args:
            p: Path to PDF file.
            start: 0-indexed start page.
            end: 0-indexed end page (-1 means to the end).

        Returns:
            Extracted text with page markers.
        """
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        total = len(reader.pages)
        start, end = FileReader._clamp_page_range(start, end, total)

        lines: list[str] = [f"[PDF: {p.name}] pages {start + 1}-{end + 1} of {total}"]

        for i in range(start, end + 1):
            text = reader.pages[i].extract_text() or ""
            lines.append(f"\n--- Page {i + 1} ---")
            lines.append(text)

        return "\n".join(lines)

    @staticmethod
    def _read_pdf_pdfplumber(p: Path, start: int, end: int) -> str:
        """Extract text from PDF using pdfplumber (higher quality).

        Args:
            p: Path to PDF file.
            start: 0-indexed start page.
            end: 0-indexed end page (-1 means to the end).

        Returns:
            Extracted text with page markers.
        """
        import pdfplumber

        with pdfplumber.open(str(p)) as pdf:
            total = len(pdf.pages)
            start, end = FileReader._clamp_page_range(start, end, total)

            lines: list[str] = [
                f"[PDF: {p.name}] pages {start + 1}-{end + 1} of {total}"
            ]

            for i in range(start, end + 1):
                text = pdf.pages[i].extract_text() or ""
                lines.append(f"\n--- Page {i + 1} ---")
                lines.append(text)

        return "\n".join(lines)

    @staticmethod
    def _extract_notebook_output(output: dict) -> str | None:
        """Extract text from a single notebook cell output.

        Args:
            output: A notebook cell output dict.

        Returns:
            Extracted text string, or None if output is not text-representable.
        """
        output_type = output.get("output_type", "")

        if output_type == "stream":
            text = "".join(output.get("text", []))
            if len(text) > 10240:
                return f"[Output truncated: {len(text):,} chars]"
            return text

        if output_type in ("execute_result", "display_data"):
            data = output.get("data", {})
            # Prefer text/plain, skip images (not representable as text)
            if "text/plain" in data:
                text = "".join(data["text/plain"])
                if len(text) > 10240:
                    return f"[Output truncated: {len(text):,} chars]"
                return text
            if "text/html" in data:
                return "[HTML output omitted]"
            if any(k.startswith("image/") for k in data):
                return "[Image output omitted]"

        if output_type == "error":
            ename = output.get("ename", "Error")
            evalue = output.get("evalue", "")
            return f"{ename}: {evalue}"

        return None
