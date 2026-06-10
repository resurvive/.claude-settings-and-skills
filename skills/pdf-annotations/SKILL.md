---
name: pdf-annotations
description: Extract text content and annotations (highlights, popup notes, comments) from PDF files, generating a comprehensive report with color coding, page locations, and annotation metadata.
---

# PDF Annotation Extractor

Extract text content and all annotations (highlights, popup notes, comments) from PDF files
using Python (pikepdf) and pdftotext. Generates a structured report with color coding,
page locations, and annotation metadata.

## When to Use

- User asks to read a PDF, especially one with annotations or highlights
- User wants to extract highlights, notes, or comments from a PDF
- User has marked up a textbook or document and wants to review all marks
- Trigger keywords (any language): annotate, highlight, markup, notes, PDF comments,
  gao liang, zhu jie, pi zhu, biao zhu

## Required Tools

These must be discoverable on PATH or via common package managers:

- **Python 3.10+** — prefer `uv run --with pikepdf --python 3.13 python` for zero-install
  isolation. Fallback: any `python3` on PATH with `pikepdf` installed.
- **uv** — install via `pip install uv` or from <https://docs.astral.sh/uv/>
- **pdftotext** — part of poppler-utils. Install:
  - macOS: `brew install poppler`
  - Linux: `apt install poppler-utils` / `pacman -S poppler`
  - Windows (MSYS2): `pacman -S mingw-w64-x86_64-poppler`
- **pdfinfo** — also from poppler-utils (used for quick PDF metadata checks)

### Tool Discovery

Before running the workflow, locate the required tools. On Unix-like systems they are
typically on PATH. On Windows common locations include:

| Tool | Typical locations |
|------|-------------------|
| `uv` | `~/.local/bin/uv.exe`, `%USERPROFILE%\.local\bin\uv.exe` |
| `python` (via uv) | `%USERPROFILE%\AppData\Roaming\uv\python\` |
| `pdftotext` | `/mingw64/bin/pdftotext`, `/usr/bin/pdftotext` |
| `pdfinfo` | Part of texlive or poppler; search with `which pdfinfo` |

**Primary command pattern** (cross-platform):
```bash
uv run --with pikepdf --python 3.13 python ~/.claude/skills/pdf-annotations/extract_annotations.py "file.pdf"
```

If `uv` is not on PATH, use its full path from the locations above.
If Python is not found, search: `find /c /d -maxdepth 4 -name "python.exe" -type f 2>/dev/null`

## Workflow

### Step 1: Verify the PDF exists and check its properties

```bash
pdfinfo "path/to/file.pdf"
ls -la "path/to/file.pdf"
```

### Step 2: Extract full text to a .txt file

```bash
pdftotext -layout "input.pdf" "output.txt"
```

### Step 3: Run the Python annotation extraction script

The script lives at `~/.claude/skills/pdf-annotations/extract_annotations.py`.

```bash
cd "<directory_containing_pdf>" && \
  uv run --with pikepdf --python 3.13 python \
    "$HOME/.claude/skills/pdf-annotations/extract_annotations.py" \
    "<pdf_filename>"
```

On Windows, `$HOME` resolves to your user profile directory (e.g. `C:\Users\<you>`).

The script generates two output files:
- `<pdf_basename>_full_text.txt` — full text extraction
- `<pdf_basename>_annotation_report.txt` — structured annotation report

### Step 4: Read and summarize the results

Read the annotation report file and present a summary:
1. Total annotation count by type (highlights, popups, text notes)
2. Color coding system (if any — check for a legend in the annotations)
3. Page distribution and chapter coverage
4. Date range and authors
5. Key annotations with their associated text

### Step 5: Offer chapter-specific deep dives

Ask the user if they want to explore specific chapters or pages in detail.

## Color Coding Interpretation

When annotations use colors, infer meaning from the Contents/Subject fields:

| Color | RGB range | Typical meaning |
|-------|-----------|-----------------|
| Yellow | (1.0, 1.0, ~0) | found / confirmed |
| Green  | (~0, 0.8, ~0) | not found / unconfirmed |
| Orange | (1.0, ~0.5, ~0) | partial / mismatch |
| Purple | (1.0, ~0.4, ~0.6) | deprecated / no longer relevant |
| Blue   | (~0, ~0.5, 1.0) | info / note |

Always check the actual Contents field for the author's own color legend — it overrides
the defaults above.

## Encoding Notes

- On Windows the terminal may use GBK encoding. The script calls
  `sys.stdout.reconfigure(encoding='utf-8')` internally. Avoid emoji in terminal output.
- Save reports to files and read them with the Read tool to avoid encoding corruption.

## Troubleshooting

- **PDF is DRM-protected** (Read tool says "password-protected" but pdfinfo says
  "Encrypted: no"): use pdftotext + Python pikepdf as described — these bypass most
  DRM restrictions on annotation extraction.
- **`uv run --with pikepdf` fails**: try `uv run --with pikepdf --python 3.13 python`
- **Python not found**: search with `find /c /d -maxdepth 4 -name "python.exe" -type f 2>/dev/null`
- **pdftotext not found**: check MSYS2 `/mingw64/bin/pdftotext` or install poppler
- **uv not found**: install with `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`
