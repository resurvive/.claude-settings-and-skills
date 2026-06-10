#!/usr/bin/env python3
"""Extract annotations from a PDF file using pikepdf and pdftotext.

Usage:
    uv run --with pikepdf --python 3.13 python extract_annotations.py <pdf_file>

Outputs:
    - <pdf_basename>_full_text.txt: Full text extraction
    - <pdf_basename>_annotation_report.txt: Structured annotation report
"""

import pikepdf
import subprocess
import sys
import os
from datetime import datetime
from collections import Counter


def get_page_text(pdf_path, page_num):
    """Extract text for a specific page using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', '-f', str(page_num), '-l', str(page_num),
             '-layout', pdf_path, '-'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        return result.stdout
    except Exception as e:
        return f"[Error extracting text: {e}]"


def get_color_name(color):
    """Classify annotation color."""
    if not color:
        return 'none'
    r, g, b = color
    if r >= 0.9 and g >= 0.9 and b <= 0.5:
        return 'YELLOW'
    elif r <= 0.4 and g >= 0.7 and b <= 0.4:
        return 'GREEN'
    elif r >= 0.9 and 0.4 <= g <= 0.8 and b <= 0.3:
        return 'ORANGE'
    elif r >= 0.9 and g >= 0.9 and b >= 0.8:
        return 'LIGHT_YELLOW'
    elif b >= 0.4 and r <= 0.5 and g <= 0.5:
        return 'BLUE/PURPLE'
    elif r >= 0.9 and g <= 0.5 and b <= 0.5:
        return 'RED'
    else:
        return f'({r:.1f},{g:.1f},{b:.1f})'


def extract_annotations(pdf_path):
    """Main extraction routine."""
    sys.stdout.reconfigure(encoding='utf-8')

    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    dirname = os.path.dirname(pdf_path) or '.'

    pdf = pikepdf.open(pdf_path)

    print(f"PDF Info: {len(pdf.pages)} pages, encrypted={pdf.is_encrypted}")

    # ================================================================
    # STEP 1: Collect all highlights
    # ================================================================
    highlights = []

    for page_num, page in enumerate(pdf.pages, 1):
        if '/Annots' not in page:
            continue

        for annot_obj in page['/Annots']:
            try:
                annot = annot_obj if isinstance(annot_obj, dict) else annot_obj
                subtype = str(annot.get('/Subtype', '')).strip('/')
                if subtype != 'Highlight':
                    continue

                contents = str(annot.get('/Contents', ''))
                subj = str(annot.get('/Subj', ''))
                author = str(annot.get('/T', ''))
                mod_date = str(annot.get('/M', ''))

                color = None
                if '/C' in annot:
                    color = [round(float(x), 3) for x in annot['/C']]

                rect = None
                if '/Rect' in annot:
                    rect = [round(float(x), 1) for x in annot['/Rect']]

                # Parse date
                date_str = mod_date
                if date_str.startswith('D:'):
                    try:
                        dt = datetime.strptime(date_str[2:16], '%Y%m%d%H%M%S')
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass

                highlights.append({
                    'page': page_num,
                    'date': date_str,
                    'author': author,
                    'subject': subj,
                    'contents': contents,
                    'color': color,
                    'rect': rect,
                })
            except:
                pass

    # ================================================================
    # STEP 2: Extract text for highlighted pages
    # ================================================================
    pages_with_highlights = sorted(set(h['page'] for h in highlights))
    page_text_map = {}

    print(f"Extracting text for {len(pages_with_highlights)} highlighted pages...")
    for pg in pages_with_highlights:
        page_text_map[pg] = get_page_text(pdf_path, pg)

    # ================================================================
    # STEP 3: Generate report
    # ================================================================
    report = []
    sep = "=" * 75
    subsep = chr(0x2500) * 60  # Unicode box drawing

    report.append(sep)
    report.append(f"  PDF ANNOTATION EXTRACTION REPORT")
    report.append(f"  File: {os.path.basename(pdf_path)}")
    report.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(sep)
    report.append("")

    # Color coding legend
    color_notes = []
    for h in highlights:
        c = h['contents']
        if c and c not in ('Highlight',):
            # skip generic/placeholder content strings
            color_notes.append(c)
    if color_notes:
        report.append("--- COLOR CODING (from annotations) ---")
        for note in color_notes:
            report.append(f"  {note}")
        report.append("")

    # Summary
    color_counts = Counter()
    for h in highlights:
        color_counts[get_color_name(h['color']) if h['color'] else 'none'] += 1

    authors = Counter(h['author'] for h in highlights)
    dates = sorted(set(h['date'] for h in highlights))

    report.append("--- SUMMARY ---")
    report.append(f"  Total highlights: {len(highlights)}")
    report.append(f"  Pages with highlights: {len(pages_with_highlights)}")
    report.append(f"  Authors: {dict(authors)}")
    report.append(f"  Date range: {dates[0] if dates else 'N/A'} to {dates[-1] if dates else 'N/A'}")
    report.append("")
    report.append("  Color distribution:")
    for color_name, count in color_counts.most_common():
        report.append(f"    {color_name}: {count}")
    report.append("")

    # ================================================================
    # STEP 4: Detailed listing by page
    # ================================================================
    report.append(sep)
    report.append("  DETAILED HIGHLIGHTS BY PAGE")
    report.append(sep)

    for pg in pages_with_highlights:
        page_highlights = [h for h in highlights if h['page'] == pg]

        report.append(f"\n{subsep}")
        report.append(f"  PAGE {pg}")
        report.append(f"{subsep}")

        # Page preview (first 5 lines)
        text = page_text_map.get(pg, '')
        lines = text.strip().split('\n')
        first_text = '\n'.join(lines[:5]) if lines else '(no text)'
        preview = '  Page preview: ' + first_text[:300].replace('\n', '\n  ')
        report.append(preview)

        for i, h in enumerate(page_highlights):
            color_name = get_color_name(h['color'])

            report.append(f"\n  Highlight #{i+1}: [{color_name}]")
            report.append(f"    Date: {h['date']} | Author: {h['author']}")

            if h['contents'] and h['contents'] not in ('Highlight',):
                report.append(f"    Note: {h['contents']}")

            if h['rect']:
                report.append(f"    Position: y={h['rect'][1]:.0f}-{h['rect'][3]:.0f}, x={h['rect'][0]:.0f}-{h['rect'][2]:.0f}")

    # ================================================================
    # Write report
    # ================================================================
    report_path = os.path.join(dirname, f"{basename}_annotation_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    print(f"Report written to: {report_path}")

    return {
        'highlights': highlights,
        'pages_with_highlights': pages_with_highlights,
        'report_path': report_path,
    }


def extract_full_text(pdf_path):
    """Extract full text from PDF using pdftotext."""
    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    dirname = os.path.dirname(pdf_path) or '.'
    output_path = os.path.join(dirname, f"{basename}_full_text.txt")

    subprocess.run(
        ['pdftotext', '-layout', pdf_path, output_path],
        capture_output=True
    )
    size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
    print(f"Full text extracted to: {output_path} ({size:,} bytes)")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python extract_annotations.py <pdf_file>")
        print("  Extracts annotations and text from a PDF file.")
        print("  Requires: uv run --with pikepdf --python 3.13")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Step A: Extract full text
    extract_full_text(pdf_path)

    # Step B: Extract annotations
    result = extract_annotations(pdf_path)

    print(f"\nDone! {len(result['highlights'])} highlights across {len(result['pages_with_highlights'])} pages.")
