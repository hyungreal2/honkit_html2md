"""
Extracts the main content section from a HonKit-generated HTML page.

The content lives inside:
    <section class="normal markdown-section">

HonKit artifacts that are removed:
- "Last modified" blockquote (injected by gitbook-plugin-last-modified)
- Plugin anchor <a> tags inside headings (class="plugin-anchor")
- Search-results wrapper (the section is inside it but we only want the content)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, Comment, Tag


class PageContent:
    def __init__(self, title: str, content_html: str, raw_soup: BeautifulSoup):
        self.title = title
        self.content_html = content_html  # cleaned inner HTML of the content section
        self.raw_soup = raw_soup          # full page soup, useful for metadata


class HTMLExtractor:
    """Extracts cleaned content HTML from a HonKit HTML page."""

    def extract(self, html_path: str | Path) -> PageContent:
        html_path = Path(html_path)
        with open(html_path, encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "lxml")

        title = self._extract_title(soup)
        content_html = self._extract_content(soup)
        return PageContent(title=title, content_html=content_html, raw_soup=soup)

    def extract_from_string(self, html_str: str) -> PageContent:
        soup = BeautifulSoup(html_str, "lxml")
        title = self._extract_title(soup)
        content_html = self._extract_content(soup)
        return PageContent(title=title, content_html=content_html, raw_soup=soup)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        if title_tag:
            raw = title_tag.get_text()
            # "Page Title · Book Title"
            if " · " in raw:
                return raw.split(" · ", 1)[0].strip()
            return raw.strip()
        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        section = soup.find("section", class_="markdown-section")
        if not section:
            # Fallback: try the page-inner div
            section = soup.find("div", class_="page-inner")
        if not section:
            return ""

        # Work on a copy so we don't mutate the original
        section = BeautifulSoup(str(section), "lxml").find("section") or \
                  BeautifulSoup(str(section), "lxml")

        self._remove_last_modified(section)
        self._remove_search_results_noise(section)

        # Return the inner HTML (content of the section tag itself)
        inner = self._inner_html(section)
        return inner

    def _remove_last_modified(self, section: Tag) -> None:
        """Remove the first blockquote if it contains 'Last modified'."""
        first_blockquote = section.find("blockquote")
        if first_blockquote:
            text = first_blockquote.get_text()
            if "Last modified" in text or "last modified" in text.lower():
                first_blockquote.decompose()

    def _remove_search_results_noise(self, section: Tag) -> None:
        """Remove search-related divs that HonKit injects."""
        for div in section.find_all("div", class_="search-results"):
            div.decompose()

    def _inner_html(self, tag: Tag) -> str:
        parts = []
        for child in tag.children:
            if isinstance(child, Comment):
                continue  # strip HTML comments (str(Comment) loses delimiters)
            parts.append(str(child))
        return "".join(parts)
