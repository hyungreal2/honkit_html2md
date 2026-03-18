"""
doc2md — Convert a HonKit _book directory to Confluence-compatible Markdown.

Usage:
    python -m src.main <book_dir> [output_dir]

    book_dir    Path to the HonKit _book directory (contains index.html)
    output_dir  Where to write .md files (default: ./output)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .book_crawler import BookCrawler
from .html_extractor import HTMLExtractor
from .html_to_md import HTMLToMarkdown
from .output_writer import OutputWriter


def convert_book(book_dir: str | Path, output_dir: str | Path) -> None:
    book_dir = Path(book_dir)
    output_dir = Path(output_dir)

    print(f"[doc2md] Book dir : {book_dir}")
    print(f"[doc2md] Output   : {output_dir}")

    crawler = BookCrawler(book_dir)
    extractor = HTMLExtractor()
    converter = HTMLToMarkdown()
    writer = OutputWriter(output_dir)

    structure = crawler.crawl()
    print(f"[doc2md] Book     : {structure.title}")
    print(f"[doc2md] Pages    : {len(structure.pages)}")

    for page in structure.pages:
        try:
            content = extractor.extract(page.html_path)
            markdown = converter.convert(content.content_html)
            out_path = writer.write_page(page, markdown)
            print(f"  [ok] {page.rel_path or 'index'} → {out_path.name}")
        except Exception as exc:
            print(f"  [error] {page.rel_path}: {exc}", file=sys.stderr)

    summary_path = writer.write_summary(structure)
    print(f"[doc2md] SUMMARY  : {summary_path}")
    print("[doc2md] Done.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a HonKit _book directory to Confluence-compatible Markdown"
    )
    parser.add_argument("book_dir", help="Path to the _book directory")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="output",
        help="Output directory for .md files (default: ./output)",
    )
    args = parser.parse_args()
    convert_book(args.book_dir, args.output_dir)


if __name__ == "__main__":
    main()
