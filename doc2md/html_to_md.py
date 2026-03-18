"""
Converts HonKit HTML content to Confluence-compatible Markdown.

Handles HonKit-specific patterns:
- Heading anchor links (.plugin-anchor)  → stripped
- Glossary term links (.glossary-term)   → plain text
- div.pagebreak                          → horizontal rule
- div.image-wrapper > img               → standard image
- html/head/body wrapper                → transparent (lxml adds these)
- <!-- HTML comments -->                → stripped
- [warning] blockquotes                 → preserved as blockquotes

Confluence Markdown notes:
- Standard ATX headings (# ## ###)
- Pipe tables
- Fenced code blocks (``` ```)
- Standard bold/italic/links/images
"""

from __future__ import annotations

import re
from typing import List

from bs4 import BeautifulSoup, Comment, NavigableString, Tag


class HTMLToMarkdown:
    """Converts HonKit-flavoured HTML to Confluence-compatible Markdown."""

    def convert(self, html_str: str) -> str:
        soup = BeautifulSoup(html_str, "lxml")
        # lxml wraps loose HTML in <html><body>; find body or use root
        root = soup.find("body") or soup
        text = self._process_node(root)
        return self._normalise_whitespace(text)

    # ------------------------------------------------------------------
    # Core recursive converter
    # ------------------------------------------------------------------

    def _process_node(self, node) -> str:
        if isinstance(node, Comment):
            return ""  # strip HTML comments

        if isinstance(node, NavigableString):
            return str(node)

        tag = node.name
        if tag in ("html", "head"):
            return ""
        if tag == "body":
            return self._process_children(node)

        # --- Block elements ---
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            return self._convert_heading(node)

        if tag == "p":
            return self._convert_p(node)

        if tag in ("ul", "ol"):
            return self._convert_list(node, ordered=(tag == "ol"))

        if tag == "li":
            return self._process_children(node).strip()

        if tag == "pre":
            return self._convert_pre(node)

        if tag == "blockquote":
            return self._convert_blockquote(node)

        if tag == "table":
            return self._convert_table(node)

        if tag == "hr":
            return "\n\n---\n\n"

        if tag == "div":
            return self._convert_div(node)

        if tag in ("section", "article", "main"):
            return self._process_children(node)

        # --- Inline elements ---
        if tag in ("strong", "b"):
            inner = self._process_children(node).strip()
            return f"**{inner}**" if inner else ""

        if tag in ("em", "i"):
            inner = self._process_children(node).strip()
            return f"*{inner}*" if inner else ""

        if tag == "code":
            return self._convert_inline_code(node)

        if tag == "a":
            return self._convert_a(node)

        if tag == "img":
            return self._convert_img(node)

        if tag in ("br",):
            return "\n"

        if tag in ("span",):
            return self._process_children(node)

        if tag in ("thead", "tbody", "tfoot"):
            return self._process_children(node)

        if tag in ("tr", "td", "th"):
            # Handled by _convert_table; here as fallback
            return self._process_children(node)

        # Unknown tags: just render children
        return self._process_children(node)

    def _process_children(self, node) -> str:
        return "".join(self._process_node(child) for child in node.children)

    # ------------------------------------------------------------------
    # Block element converters
    # ------------------------------------------------------------------

    def _convert_heading(self, node: Tag) -> str:
        level = int(node.name[1])
        # Remove plugin-anchor links (the icon links HonKit adds to headings)
        for anchor in node.find_all("a", class_="plugin-anchor"):
            anchor.decompose()
        text = self._process_children(node).strip()
        return f"\n\n{'#' * level} {text}\n\n"

    def _convert_p(self, node: Tag) -> str:
        inner = self._process_children(node).strip()
        if not inner:
            return ""
        return f"\n\n{inner}\n\n"

    def _convert_list(self, node: Tag, ordered: bool) -> str:
        items = []
        counter = 1
        for child in node.children:
            if not isinstance(child, Tag) or child.name != "li":
                continue
            # Recurse: a li may contain nested ul/ol
            content = self._process_li(child, ordered, counter)
            items.append(content)
            if ordered:
                counter += 1
        return "\n\n" + "\n".join(items) + "\n\n"

    def _process_li(self, li: Tag, ordered: bool, index: int) -> str:
        prefix = f"{index}." if ordered else "-"
        lines = []
        for child in li.children:
            if isinstance(child, Tag) and child.name in ("ul", "ol"):
                # Nested list: indent each line
                nested = self._convert_list(child, ordered=(child.name == "ol")).strip()
                for line in nested.splitlines():
                    lines.append("  " + line)
            else:
                text = self._process_node(child)
                if text.strip():
                    lines.append(text.strip())

        first_line = " ".join(lines[0:1]) if lines else ""
        rest = "\n".join(lines[1:])
        if rest:
            return f"{prefix} {first_line}\n{rest}"
        return f"{prefix} {first_line}"

    def _convert_pre(self, node: Tag) -> str:
        code_tag = node.find("code")
        if code_tag:
            # Try to extract language from class (e.g. "language-python")
            lang = ""
            for cls in (code_tag.get("class") or []):
                if cls.startswith("language-"):
                    lang = cls[len("language-"):]
                    break
            code_text = code_tag.get_text()
        else:
            code_text = node.get_text()
            lang = ""
        return f"\n\n```{lang}\n{code_text}```\n\n"

    def _convert_blockquote(self, node: Tag) -> str:
        inner = self._process_children(node).strip()
        if not inner:
            return ""
        # Prefix every line with "> "
        lines = inner.splitlines()
        quoted = "\n".join(f"> {line}" if line.strip() else ">" for line in lines)
        return f"\n\n{quoted}\n\n"

    def _convert_table(self, node: Tag) -> str:
        rows = node.find_all("tr")
        if not rows:
            return ""

        table_data: List[List[str]] = []
        has_header = False

        for row in rows:
            cells = row.find_all(["td", "th"])
            cell_texts = [self._process_children(c).strip().replace("\n", " ") for c in cells]
            table_data.append(cell_texts)
            if row.find("th"):
                has_header = True

        if not table_data:
            return ""

        # Normalise column count
        col_count = max(len(r) for r in table_data)
        for row in table_data:
            while len(row) < col_count:
                row.append("")

        def render_row(cells: List[str]) -> str:
            return "| " + " | ".join(cells) + " |"

        def render_separator(n: int) -> str:
            return "| " + " | ".join(["---"] * n) + " |"

        lines = []
        if has_header:
            lines.append(render_row(table_data[0]))
            lines.append(render_separator(col_count))
            for row in table_data[1:]:
                lines.append(render_row(row))
        else:
            # No header row: add an empty header so Confluence renders a proper table
            lines.append(render_row([""] * col_count))
            lines.append(render_separator(col_count))
            for row in table_data:
                lines.append(render_row(row))

        return "\n\n" + "\n".join(lines) + "\n\n"

    def _convert_div(self, node: Tag) -> str:
        classes = node.get("class") or []

        if "pagebreak" in classes:
            return "\n\n---\n\n"

        # image-wrapper div: extract the img directly
        if any(c.startswith("image-wrapper") for c in classes):
            img = node.find("img")
            if img:
                return f"\n\n{self._convert_img(img)}\n\n"
            return ""

        # atoc (auto table of contents) div: skip — it's auto-generated noise
        if "atoc" in classes or "book-toc" in classes:
            return ""

        return self._process_children(node)

    # ------------------------------------------------------------------
    # Inline element converters
    # ------------------------------------------------------------------

    def _convert_inline_code(self, node: Tag) -> str:
        # Inline code (not inside <pre>)
        if node.parent and node.parent.name == "pre":
            # Handled by _convert_pre
            return node.get_text()
        text = node.get_text()
        # Use double backticks if text contains a backtick
        if "`" in text:
            return f"`` {text} ``"
        return f"`{text}`"

    def _convert_a(self, node: Tag) -> str:
        classes = node.get("class") or []

        # Plugin anchor (heading icon link) — already removed in _convert_heading,
        # but guard here too
        if "plugin-anchor" in classes:
            return ""

        # Glossary term: just render visible text (tooltip is too noisy for MD)
        if "glossary-term" in classes:
            return self._process_children(node).strip()

        href = node.get("href", "")
        text = self._process_children(node).strip()

        if not text:
            return href
        if not href:
            return text

        # Simplify internal GLOSSARY.html links to anchor-only
        if "GLOSSARY.html" in href:
            anchor = href.split("#")[-1] if "#" in href else ""
            if anchor:
                return f"[{text}](#{anchor})"
            return text

        return f"[{text}]({href})"

    def _convert_img(self, node: Tag) -> str:
        src = node.get("src", "")
        alt = node.get("alt", "")
        return f"![{alt}]({src})"

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _normalise_whitespace(self, text: str) -> str:
        # Collapse 3+ consecutive blank lines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
