# doc2md

Reverse-engineers a [HonKit](https://github.com/honkit/honkit)-built `_book` directory into Confluence-compatible Markdown files.

No access to the original `.md` sources is required — everything is derived from the generated HTML.

## How it works

```
_book/index.html           →  BookCrawler    →  ordered list of pages
_book/<chapter>/index.html →  HTMLExtractor  →  clean content HTML
                           →  HTMLToMarkdown →  Confluence Markdown
                           →  OutputWriter   →  output/<chapter>.md
```

| Module | Responsibility |
|---|---|
| `book_crawler.py` | Reads `<ul class="summary">` sidebar from `index.html` to discover all pages in navigation order |
| `html_extractor.py` | Extracts `<section class="normal markdown-section">`, strips HonKit artifacts (last-modified timestamp, HTML comments) |
| `html_to_md.py` | Recursive HTML → Markdown converter with HonKit-specific handling |
| `output_writer.py` | Writes one `.md` per page + a `SUMMARY.md` table of contents |
| `main.py` | CLI entry point |

### HonKit-specific conversions

| HTML pattern | Markdown output |
|---|---|
| `<a class="plugin-anchor">` in headings | stripped |
| `<a class="glossary-term">` | plain text (tooltip dropped) |
| `<div class="pagebreak">` | `---` |
| `<div class="image-wrapper">` | `![alt](src)` |
| Last-modified blockquote | stripped |
| `<!-- HTML comments -->` | stripped |
| `<html><head></head><body>` wrapper | transparent |
| Table without `<th>` | empty header row added for Confluence compatibility |

## Installation

### Option 1 — Standalone binary (no Python required)

A pre-built Linux x86_64 binary is included in the repository:

```bash
chmod +x bin/doc2md
./bin/doc2md <book_dir> [output_dir]
```

Or copy it to your PATH:

```bash
sudo cp bin/doc2md /usr/local/bin/
doc2md <book_dir> [output_dir]
```

### Option 2 — Install as Python package

Requires Python 3.10+.

```bash
pip install -r requirements.txt
pip install -e .
```

This installs a `doc2md` command into your Python environment.

## Usage

```bash
doc2md <book_dir> [output_dir]
```

| Argument | Description | Default |
|---|---|---|
| `book_dir` | Path to the HonKit `_book` directory (must contain `index.html`) | — |
| `output_dir` | Directory where `.md` files will be written | `./output` |

### Example

```bash
doc2md _book output
```

```
[doc2md] Book dir : _book
[doc2md] Output   : output
[doc2md] Book     : User guide of MISP intelligence sharing platform
[doc2md] Pages    : 36
  [ok] index → index.md
  [ok] quick-start → quick-start.md
  [ok] administration → administration.md
  ...
[doc2md] SUMMARY  : output/SUMMARY.md
[doc2md] Done.
```

The `output/` directory will contain one `.md` file per chapter plus a `SUMMARY.md` index.

## Running tests

```bash
pytest tests/ -v
```

59 tests covering `BookCrawler`, `HTMLExtractor`, and `HTMLToMarkdown`.

## Project structure

```
doc2md/
├── bin/
│   └── doc2md              (standalone binary, Linux x86_64)
├── doc2md/
│   ├── __init__.py
│   ├── __main__.py
│   ├── book_crawler.py
│   ├── html_extractor.py
│   ├── html_to_md.py
│   ├── output_writer.py
│   └── main.py
├── tests/
│   ├── fixtures/
│   │   ├── sample_index.html
│   │   └── sample_page.html
│   ├── test_book_crawler.py
│   ├── test_html_extractor.py
│   └── test_html_to_md.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Limitations

- Image files are referenced by their original relative path (`figures/image.png`). You will need to upload them separately to Confluence and update links.
- Internal cross-page links (e.g. `../administration/`) are preserved as-is and will need manual adjustment after importing to Confluence.
- Glossary term tooltips are dropped (only the visible text is kept).
- Nested ordered list sub-items written as raw text in the original (e.g. `3.1 ...`) remain as text since they have no semantic list markup in the HTML.
- The standalone binary targets Linux x86_64. For other platforms, use the Python package installation.
