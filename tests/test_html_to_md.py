"""Tests for HTMLToMarkdown converter."""

import pytest
from doc2md.html_to_md import HTMLToMarkdown


@pytest.fixture
def converter():
    return HTMLToMarkdown()


# ------------------------------------------------------------------
# Heading conversion
# ------------------------------------------------------------------

class TestHeadings:
    def test_h1(self, converter):
        html = '<h1 id="title">Hello World</h1>'
        result = converter.convert(html)
        assert "# Hello World" in result

    def test_h2(self, converter):
        result = converter.convert('<h2 id="sub">Sub Section</h2>')
        assert "## Sub Section" in result

    def test_h3_through_h6(self, converter):
        for level in range(3, 7):
            tag = f"h{level}"
            result = converter.convert(f'<{tag}>Heading</{tag}>')
            assert f"{'#' * level} Heading" in result

    def test_plugin_anchor_stripped_from_heading(self, converter):
        html = (
            '<h1 id="quick-start">'
            '<a name="quick-start" class="plugin-anchor" href="#quick-start">'
            '<i class="fa fa-link"></i></a>Quick Start</h1>'
        )
        result = converter.convert(html)
        assert "# Quick Start" in result
        assert "plugin-anchor" not in result
        assert "fa-link" not in result


# ------------------------------------------------------------------
# Paragraph conversion
# ------------------------------------------------------------------

class TestParagraphs:
    def test_simple_paragraph(self, converter):
        result = converter.convert("<p>Hello, world.</p>")
        assert "Hello, world." in result

    def test_bold_in_paragraph(self, converter):
        result = converter.convert("<p><strong>Bold text</strong></p>")
        assert "**Bold text**" in result

    def test_italic_in_paragraph(self, converter):
        result = converter.convert("<p><em>Italic text</em></p>")
        assert "*Italic text*" in result

    def test_inline_code(self, converter):
        result = converter.convert("<p>Use <code>pip install</code> to install.</p>")
        assert "`pip install`" in result


# ------------------------------------------------------------------
# Links
# ------------------------------------------------------------------

class TestLinks:
    def test_external_link(self, converter):
        result = converter.convert('<a href="https://example.com">Example</a>')
        assert "[Example](https://example.com)" in result

    def test_glossary_term_becomes_plain_text(self, converter):
        html = (
            '<a href="../GLOSSARY.html#indicators" class="glossary-term" '
            'title="Indicators contain a pattern...">Indicators</a>'
        )
        result = converter.convert(html)
        assert "Indicators" in result
        assert "glossary-term" not in result
        assert "GLOSSARY.html" not in result

    def test_plugin_anchor_stripped(self, converter):
        html = '<a class="plugin-anchor" href="#foo"><i class="fa fa-link"></i></a>'
        result = converter.convert(html)
        assert result.strip() == ""

    def test_link_without_text(self, converter):
        result = converter.convert('<a href="https://example.com"></a>')
        # Should render the href itself or be empty — not crash
        assert "example.com" in result or result.strip() == ""


# ------------------------------------------------------------------
# Code blocks
# ------------------------------------------------------------------

class TestCodeBlocks:
    def test_fenced_code_block(self, converter):
        html = "<pre><code>sudo apt-get update\nsudo apt-get upgrade\n</code></pre>"
        result = converter.convert(html)
        assert "```" in result
        assert "sudo apt-get update" in result

    def test_code_block_with_language(self, converter):
        html = '<pre><code class="language-python">print("hello")\n</code></pre>'
        result = converter.convert(html)
        assert "```python" in result
        assert 'print("hello")' in result

    def test_inline_code(self, converter):
        result = converter.convert("<p>Run <code>ls -la</code></p>")
        assert "`ls -la`" in result


# ------------------------------------------------------------------
# Lists
# ------------------------------------------------------------------

class TestLists:
    def test_unordered_list(self, converter):
        html = "<ul><li>Item one</li><li>Item two</li></ul>"
        result = converter.convert(html)
        assert "- Item one" in result
        assert "- Item two" in result

    def test_ordered_list(self, converter):
        html = "<ol><li>First</li><li>Second</li><li>Third</li></ol>"
        result = converter.convert(html)
        assert "1. First" in result
        assert "2. Second" in result
        assert "3. Third" in result

    def test_nested_list(self, converter):
        html = "<ul><li>Parent<ul><li>Child</li></ul></li></ul>"
        result = converter.convert(html)
        assert "- Parent" in result
        assert "  - Child" in result


# ------------------------------------------------------------------
# Tables
# ------------------------------------------------------------------

class TestTables:
    def test_table_with_header(self, converter):
        html = """
        <table>
            <tr><th>Name</th><th>Value</th></tr>
            <tr><td>admin</td><td>admin@admin.test</td></tr>
        </table>
        """
        result = converter.convert(html)
        assert "| Name | Value |" in result
        assert "| --- | --- |" in result
        assert "| admin | admin@admin.test |" in result

    def test_table_without_header(self, converter):
        html = """
        <table>
            <tr><td>Username:</td><td>admin@admin.test</td></tr>
            <tr><td>Password:</td><td>admin</td></tr>
        </table>
        """
        result = converter.convert(html)
        # Should still produce a valid Markdown table with separator
        assert "| --- |" in result
        assert "| Username: | admin@admin.test |" in result
        assert "| Password: | admin |" in result

    def test_empty_table(self, converter):
        html = "<table></table>"
        result = converter.convert(html)
        # Should not crash; output may be empty
        assert isinstance(result, str)


# ------------------------------------------------------------------
# Images
# ------------------------------------------------------------------

class TestImages:
    def test_plain_image(self, converter):
        result = converter.convert('<img src="figures/logo.png" alt="MISP Logo">')
        assert "![MISP Logo](figures/logo.png)" in result

    def test_image_in_wrapper_div(self, converter):
        html = '<div class="image-wrapper quick-start-README"><img src="figures/logo.png" alt="Logo"></div>'
        result = converter.convert(html)
        assert "![Logo](figures/logo.png)" in result

    def test_image_no_alt(self, converter):
        result = converter.convert('<img src="figures/pic.jpg">')
        assert "![](figures/pic.jpg)" in result


# ------------------------------------------------------------------
# Blockquotes
# ------------------------------------------------------------------

class TestBlockquotes:
    def test_simple_blockquote(self, converter):
        html = "<blockquote><p>Some quote here.</p></blockquote>"
        result = converter.convert(html)
        assert "> Some quote here." in result

    def test_warning_blockquote(self, converter):
        html = "<blockquote><p>[warning] Remember to change your password.</p></blockquote>"
        result = converter.convert(html)
        assert "> [warning] Remember to change your password." in result


# ------------------------------------------------------------------
# Special HonKit elements
# ------------------------------------------------------------------

class TestHonKitElements:
    def test_pagebreak_becomes_hr(self, converter):
        html = '<div class="pagebreak"></div>'
        result = converter.convert(html)
        assert "---" in result

    def test_html_comments_stripped(self, converter):
        html = "<!-- This is a comment --><p>Visible text</p>"
        result = converter.convert(html)
        assert "This is a comment" not in result
        assert "Visible text" in result

    def test_last_modified_in_content(self, converter):
        # The last-modified blockquote should pass through the converter
        # (stripping is done by HTMLExtractor, not the converter)
        html = "<blockquote><p><em>Last modified: Wed Mar 18 2026</em></p></blockquote>"
        result = converter.convert(html)
        # Converter produces a blockquote; extractor would strip this
        assert "Last modified" in result

    def test_honkit_html_body_wrapper_transparent(self, converter):
        # HonKit wraps content in <html><head></head><body>...</body></html>
        html = "<html><head></head><body><p>Content here</p></body></html>"
        result = converter.convert(html)
        assert "Content here" in result
        assert "<html>" not in result
        assert "<body>" not in result


# ------------------------------------------------------------------
# Whitespace normalisation
# ------------------------------------------------------------------

class TestWhitespace:
    def test_no_triple_blank_lines(self, converter):
        html = "<p>First</p><p>Second</p><p>Third</p>"
        result = converter.convert(html)
        assert "\n\n\n" not in result

    def test_output_stripped(self, converter):
        result = converter.convert("<p>Hello</p>")
        assert result == result.strip()


# ------------------------------------------------------------------
# Integration: full page section content
# ------------------------------------------------------------------

class TestFullPageSection:
    SAMPLE_CONTENT = """
    <html><head></head><body>
    <h1 id="quick-start">
        <a name="quick-start" class="plugin-anchor" href="#quick-start">
            <i class="fa fa-link"></i>
        </a>Quick Start
    </h1>
    <p>MISP facilitates sharing of <a href="../GLOSSARY.html#indicators" class="glossary-term" title="...">Indicators</a>.</p>
    <h2 id="login"><a name="login" class="plugin-anchor" href="#login"><i class="fa fa-link"></i></a>Login</h2>
    <table>
        <tr><td>Username:</td><td>admin@admin.test</td></tr>
        <tr><td>Password:</td><td>admin</td></tr>
    </table>
    <pre><code>sudo cake Password admin@admin.test NewPass1!</code></pre>
    <div class="pagebreak"></div>
    <ul>
        <li>At least 12 characters</li>
        <li>One upper-case letter</li>
    </ul>
    </body></html>
    """

    def test_full_conversion(self, converter):
        result = converter.convert(self.SAMPLE_CONTENT)
        assert "# Quick Start" in result
        assert "## Login" in result
        # Glossary term is plain text
        assert "Indicators" in result
        assert "glossary-term" not in result
        # Table rendered
        assert "| Username: | admin@admin.test |" in result
        # Code block
        assert "```" in result
        assert "sudo cake Password" in result
        # Pagebreak → hr
        assert "---" in result
        # List
        assert "- At least 12 characters" in result
        # No plugin-anchor artifacts
        assert "plugin-anchor" not in result
        assert "fa-link" not in result
