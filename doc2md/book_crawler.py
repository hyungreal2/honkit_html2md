"""
Crawls a HonKit _book directory to discover all pages in navigation order.

Reads the sidebar <ul class="summary"> from index.html to extract:
- Page title
- Relative path (directory name)
- Navigation level
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from bs4 import BeautifulSoup


@dataclass
class PageInfo:
    title: str
    rel_path: str          # e.g. "quick-start" or "" for root
    html_path: Path        # absolute path to the page's index.html
    level: str = "1.1"     # data-level attribute from sidebar

    @property
    def output_filename(self) -> str:
        """Suggested output .md filename."""
        if self.rel_path == "":
            return "index.md"
        return self.rel_path + ".md"


@dataclass
class BookStructure:
    book_dir: Path
    title: str
    pages: List[PageInfo] = field(default_factory=list)


class BookCrawler:
    """Discovers all pages in a HonKit _book directory."""

    def __init__(self, book_dir: str | Path):
        self.book_dir = Path(book_dir).resolve()
        if not self.book_dir.is_dir():
            raise ValueError(f"Not a directory: {self.book_dir}")

    def crawl(self) -> BookStructure:
        index_html = self.book_dir / "index.html"
        if not index_html.exists():
            raise FileNotFoundError(f"No index.html in {self.book_dir}")

        with open(index_html, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        title = self._extract_book_title(soup)
        pages = self._extract_pages(soup)
        return BookStructure(book_dir=self.book_dir, title=title, pages=pages)

    def _extract_book_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text()
            # HonKit format: "Page · Book Title"
            if " · " in raw:
                return raw.split(" · ", 1)[1].strip()
            return raw.strip()
        return "Untitled"

    def _extract_pages(self, soup: BeautifulSoup) -> List[PageInfo]:
        summary = soup.find("ul", class_="summary")
        if not summary:
            raise ValueError("Could not find <ul class='summary'> navigation in index.html")

        pages: List[PageInfo] = []
        for li in summary.find_all("li", class_="chapter"):
            page = self._parse_chapter_li(li)
            if page:
                pages.append(page)
        return pages

    def _parse_chapter_li(self, li) -> Optional[PageInfo]:
        a_tag = li.find("a", href=True)
        if not a_tag:
            return None

        href = a_tag["href"].strip()
        # HonKit sidebar hrefs are relative to index.html (root of _book):
        #   "../"               -> root page
        #   "../quick-start/"   -> quick-start chapter
        #   "./"                -> current page (same as root in index.html context)
        #   "quick-start/"      -> chapter relative to index
        # Normalise to a directory name
        rel_path = self._href_to_rel_path(href)

        html_path = self._resolve_html_path(rel_path)
        if not html_path.exists():
            return None  # skip pages that weren't built

        title = a_tag.get_text(strip=True)
        level = li.get("data-level", "")
        return PageInfo(title=title, rel_path=rel_path, html_path=html_path, level=level)

    def _href_to_rel_path(self, href: str) -> str:
        """Convert sidebar href to a directory name relative to book_dir."""
        # Normalize trailing slash first
        path = href.rstrip("/")

        # "." or ".." or "" all mean the root page
        if path in (".", "..", ""):
            return ""

        # "../chapter" — from a chapter page linking back to another chapter or root
        if path.startswith("../"):
            path = path[3:].rstrip("/")
            return "" if path in ("", ".") else path

        # "./chapter" — from the root page
        if path.startswith("./"):
            return path[2:].rstrip("/")

        return path

    def _resolve_html_path(self, rel_path: str) -> Path:
        if rel_path == "":
            return self.book_dir / "index.html"
        return self.book_dir / rel_path / "index.html"
