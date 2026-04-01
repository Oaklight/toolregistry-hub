"""Multi-format file reader with line numbers and pagination.

Supports plain text (with line-numbered output and offset/limit),
Jupyter notebooks (stdlib ``json``), and PDF files (optional dependency).
Image reading is planned but blocked on upstream multimodal support.
"""

from __future__ import annotations

import json
from pathlib import Path

# Safety caps
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB for text files
_MAX_LINES_DEFAULT = 2000
_MAX_PDF_PAGES = 20


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
    def read_image(path: str) -> str:
        """Read an image file and return as multimodal content block.

        .. note::
            Not yet implemented. Blocked on upstream ``toolregistry`` support
            for multimodal return types (image content blocks).
            See: https://github.com/Oaklight/ToolRegistry/issues/101
            Tracking: https://github.com/Oaklight/toolregistry-hub/issues/74

        Args:
            path: Path to image file.

        Raises:
            NotImplementedError: Always. Pending upstream multimodal support.
        """
        raise NotImplementedError(
            "Image reading requires multimodal return type support from "
            "upstream toolregistry. "
            "See https://github.com/Oaklight/ToolRegistry/issues/101"
        )

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
