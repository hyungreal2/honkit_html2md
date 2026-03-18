# CLAUDE.md

## Project overview

`doc2md` reverse-engineers a HonKit-built `_book` directory into Confluence-compatible Markdown. No original `.md` sources are needed.

## Running the converter

```bash
python -m src.main _book output
```

## Running tests

```bash
pytest tests/ -v
```

All tests must pass (currently 59). Do not break existing tests when making changes.

## Architecture

Four pipeline stages, each in its own module:

1. **`src/book_crawler.py` — `BookCrawler`**
   - Parses `<ul class="summary">` sidebar from `_book/index.html`
   - Returns `BookStructure` with an ordered list of `PageInfo` objects
   - `PageInfo.rel_path` is the chapter directory name (empty string for root)
   - `_href_to_rel_path()` normalises all HonKit sidebar href variants (`./`, `../`, `../chapter/`) to a bare directory name

2. **`src/html_extractor.py` — `HTMLExtractor`**
   - Finds `<section class="normal markdown-section">` in each page
   - Strips the first `<blockquote>` if it contains "Last modified" (injected by gitbook-plugin-last-modified)
   - Strips `Comment` nodes in `_inner_html()` — `str(Comment)` loses the `<!-- -->` delimiters, so comments must be filtered before re-serialisation, not after
   - Returns cleaned inner HTML string for the converter

3. **`src/html_to_md.py` — `HTMLToMarkdown`**
   - Recursive `_process_node()` dispatcher — add new tag handlers there
   - lxml wraps loose HTML in `<html><body>`; both are passed through transparently
   - HonKit-specific rules:
     - `.plugin-anchor` → decomposed in `_convert_heading()` before text extraction
     - `.glossary-term` → plain text only (title/tooltip is too verbose for MD)
     - `div.pagebreak` → `---`
     - `div.image-wrapper` → extracts inner `<img>` directly
   - Tables without `<th>`: an empty header row is prepended so Confluence renders a proper table
   - `_normalise_whitespace()` collapses 3+ consecutive blank lines to 2

4. **`src/output_writer.py` — `OutputWriter`**
   - `write_page()` → `output/<rel_path>.md` (root page → `index.md`)
   - `write_summary()` → `output/SUMMARY.md`

## Test fixtures

`tests/fixtures/sample_index.html` — minimal root page with a 4-chapter sidebar (used by `BookCrawler` tests).

`tests/fixtures/sample_page.html` — minimal chapter page covering: last-modified blockquote, HTML comment, headings with plugin-anchors, image-wrapper, table, code block, ordered/unordered lists, glossary terms, pagebreak, warning blockquote.

When adding new HTML patterns, add a matching case to the fixture and a test in the appropriate test file.

## Key gotchas

- `str(Comment)` in BeautifulSoup returns the comment text without `<!-- -->` delimiters. Always filter `Comment` instances before joining children as strings.
- HonKit embeds page content inside a nested `<html><head></head><body>` inside the `<section>`. lxml flattens this when parsing the outer page, so the `<html>/<body>` tags disappear and only the body children survive in the section.
- Sidebar hrefs differ depending on which page you're reading from. From the index page, chapter links look like `"quick-start/"`. From a chapter page, they look like `"../quick-start/"`. Both must normalise to `"quick-start"`.
- The `[ok]` log line uses `page.rel_path or 'index'` — root page has `rel_path == ""`.

## Dependencies

- `beautifulsoup4` — HTML parsing
- `lxml` — BS4 parser backend (faster and more lenient than `html.parser`)
- `pytest` — testing only
