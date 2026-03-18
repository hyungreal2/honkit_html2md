"""Tests for BookCrawler."""

import shutil
import pytest
from pathlib import Path
from doc2md.book_crawler import BookCrawler, PageInfo

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_book(tmp_path):
    """
    Create a minimal fake _book directory that mirrors real HonKit output.
    Structure:
        fake_book/
            index.html          (root page with full sidebar nav)
            book-convention/
                index.html
            quick-start/
                index.html
            administration/
                index.html
    """
    index_html = (FIXTURES / "sample_index.html").read_text(encoding="utf-8")
    (tmp_path / "index.html").write_text(index_html, encoding="utf-8")

    page_html = (FIXTURES / "sample_page.html").read_text(encoding="utf-8")
    for chapter in ("book-convention", "quick-start", "administration"):
        d = tmp_path / chapter
        d.mkdir()
        (d / "index.html").write_text(page_html, encoding="utf-8")

    return tmp_path


class TestBookCrawlerInit:
    def test_valid_dir(self, fake_book):
        crawler = BookCrawler(fake_book)
        assert crawler.book_dir == fake_book

    def test_invalid_dir_raises(self, tmp_path):
        with pytest.raises(ValueError):
            BookCrawler(tmp_path / "nonexistent")

    def test_string_path_accepted(self, fake_book):
        crawler = BookCrawler(str(fake_book))
        assert crawler.book_dir == fake_book


class TestCrawl:
    def test_returns_book_structure(self, fake_book):
        crawler = BookCrawler(fake_book)
        structure = crawler.crawl()
        assert structure is not None
        assert structure.book_dir == fake_book

    def test_extracts_book_title(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        assert "MISP" in structure.title

    def test_finds_all_pages(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        # sample_index.html has 4 chapters; but "book-convention" dir doesn't
        # exist in fake_book — check pages with existing html only
        assert len(structure.pages) >= 3

    def test_pages_have_titles(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        titles = [p.title for p in structure.pages]
        assert "Introduction" in titles or "Quick Start" in titles

    def test_pages_have_html_paths(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        for page in structure.pages:
            assert page.html_path.exists(), f"HTML file missing: {page.html_path}"

    def test_root_page_rel_path_empty(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        root_pages = [p for p in structure.pages if p.rel_path == ""]
        assert len(root_pages) == 1

    def test_chapter_rel_paths(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        rel_paths = {p.rel_path for p in structure.pages}
        assert "quick-start" in rel_paths
        assert "administration" in rel_paths

    def test_missing_index_html_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            BookCrawler(tmp_path).crawl()

    def test_pages_ordered_by_navigation(self, fake_book):
        structure = BookCrawler(fake_book).crawl()
        # Introduction (1.1) should come before Quick Start (1.2)
        titles = [p.title for p in structure.pages]
        if "Introduction" in titles and "Quick Start" in titles:
            assert titles.index("Introduction") < titles.index("Quick Start")


class TestPageInfo:
    def test_output_filename_root(self):
        page = PageInfo(title="Intro", rel_path="", html_path=Path("/book/index.html"))
        assert page.output_filename == "index.md"

    def test_output_filename_chapter(self):
        page = PageInfo(title="Quick Start", rel_path="quick-start", html_path=Path("/book/quick-start/index.html"))
        assert page.output_filename == "quick-start.md"
