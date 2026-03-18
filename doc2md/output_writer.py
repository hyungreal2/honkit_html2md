"""
Writes converted Markdown files to an output directory.

Output structure mirrors the _book directory:
    output/
        index.md           (root page)
        quick-start.md
        administration.md
        ...
        SUMMARY.md         (table of contents)
"""

from __future__ import annotations

from pathlib import Path

from .book_crawler import BookStructure, PageInfo


class OutputWriter:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)

    def write_page(self, page: PageInfo, markdown: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / page.output_filename
        out_path.write_text(markdown, encoding="utf-8")
        return out_path

    def write_summary(self, structure: BookStructure) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"# {structure.title}\n\n"]
        for page in structure.pages:
            lines.append(f"* [{page.title}]({page.output_filename})\n")
        summary_path = self.output_dir / "SUMMARY.md"
        summary_path.write_text("".join(lines), encoding="utf-8")
        return summary_path
