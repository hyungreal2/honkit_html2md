"""Tests for HTMLExtractor."""

import pytest
from pathlib import Path
from doc2md.html_extractor import HTMLExtractor

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor():
    return HTMLExtractor()


@pytest.fixture
def sample_page_html():
    return (FIXTURES / "sample_page.html").read_text(encoding="utf-8")


class TestTitleExtraction:
    def test_extracts_page_title(self, extractor, sample_page_html):
        content = extractor.extract_from_string(sample_page_html)
        assert content.title == "Quick Start"

    def test_title_without_book_name(self, extractor):
        html = "<html><head><title>My Page · My Book</title></head><body></body></html>"
        content = extractor.extract_from_string(html)
        assert content.title == "My Page"

    def test_title_without_separator(self, extractor):
        html = "<html><head><title>Simple Title</title></head><body></body></html>"
        content = extractor.extract_from_string(html)
        assert content.title == "Simple Title"

    def test_no_title_returns_empty(self, extractor):
        html = "<html><head></head><body><p>Content</p></body></html>"
        content = extractor.extract_from_string(html)
        assert content.title == ""


class TestContentExtraction:
    def test_extracts_markdown_section(self, extractor, sample_page_html):
        content = extractor.extract_from_string(sample_page_html)
        assert content.content_html.strip() != ""

    def test_last_modified_stripped(self, extractor, sample_page_html):
        content = extractor.extract_from_string(sample_page_html)
        assert "Last modified" not in content.content_html

    def test_real_content_preserved(self, extractor, sample_page_html):
        content = extractor.extract_from_string(sample_page_html)
        assert "Quick Start" in content.content_html
        assert "Login into MISP" in content.content_html

    def test_html_comment_preserved_for_converter(self, extractor, sample_page_html):
        # The extractor leaves comments in; the converter strips them.
        # Just verify the extractor doesn't crash on comments.
        content = extractor.extract_from_string(sample_page_html)
        assert isinstance(content.content_html, str)

    def test_no_content_returns_empty_string(self, extractor):
        html = "<html><head><title>Test</title></head><body><p>No section</p></body></html>"
        content = extractor.extract_from_string(html)
        assert content.content_html == ""

    def test_last_modified_only_first_blockquote(self, extractor):
        """Second blockquote (e.g. a warning) should NOT be stripped."""
        html = """
        <html><head><title>T · B</title></head><body>
        <section class="normal markdown-section">
            <html><head></head><body>
            <blockquote><p><em>Last modified: Wed Mar 18 2026</em></p></blockquote>
            <p>Content here</p>
            <blockquote><p>[warning] Important note.</p></blockquote>
            </body></html>
        </section>
        </body></html>
        """
        content = extractor.extract_from_string(html)
        assert "Last modified" not in content.content_html
        assert "[warning] Important note." in content.content_html


class TestExtractFromFile:
    def test_extract_from_file(self, extractor):
        path = FIXTURES / "sample_page.html"
        content = extractor.extract(path)
        assert content.title == "Quick Start"
        assert "Quick Start" in content.content_html
        assert "Last modified" not in content.content_html

    def test_missing_file_raises(self, extractor, tmp_path):
        with pytest.raises(FileNotFoundError):
            extractor.extract(tmp_path / "nonexistent.html")
