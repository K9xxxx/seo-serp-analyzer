import re
from collections import Counter
from datetime import datetime, timezone
from statistics import mean

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")

RESULT_HEADERS = [
    "Rank",
    "URL",
    "Status",
    "Error",
    "Title",
    "Title chars",
    "Meta description",
    "Description chars",
    "H1 count",
    "H1",
    "H2 count",
    "H2",
    "H3 count",
    "H3",
    "Total characters",
    "Word count",
    "Top words",
    "Top bigrams",
    "Top trigrams",
]

COLUMN_WIDTHS = {
    "A": 6,
    "B": 45,
    "C": 8,
    "D": 30,
    "E": 50,
    "F": 11,
    "G": 60,
    "H": 17,
    "I": 9,
    "J": 40,
    "K": 9,
    "L": 50,
    "M": 9,
    "N": 50,
    "O": 16,
    "P": 11,
    "Q": 60,
    "R": 60,
    "S": 60,
}


def _join_headings(headings, level):
    return " | ".join(headings.get(level, []))


def _style_header(ws, ncols):
    for col in range(1, ncols + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"


def export_workbook(records, query, out_path, top=20):
    records = sorted(records, key=lambda r: r["rank"])
    ok = [r for r in records if r["status"] == "ok"]

    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(RESULT_HEADERS)
    for rec in records:
        headings = rec.get("headings", {"h1": [], "h2": [], "h3": []})
        ws.append(
            [
                rec["rank"],
                rec["url"],
                rec["status"],
                rec.get("error", ""),
                rec.get("title", ""),
                len(rec.get("title", "")),
                rec.get("description", ""),
                len(rec.get("description", "")),
                len(headings.get("h1", [])),
                _join_headings(headings, "h1"),
                len(headings.get("h2", [])),
                _join_headings(headings, "h2"),
                len(headings.get("h3", [])),
                _join_headings(headings, "h3"),
                rec.get("char_count", 0),
                rec.get("word_count", 0),
                rec.get("top_words", ""),
                rec.get("top_bigrams", ""),
                rec.get("top_trigrams", ""),
            ]
        )
    _style_header(ws, len(RESULT_HEADERS))
    for col, width in COLUMN_WIDTHS.items():
        ws.column_dimensions[col].width = width
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ov = wb.create_sheet("Overview")
    all_words = Counter()
    all_bigrams = Counter()
    all_trigrams = Counter()
    for rec in ok:
        all_words.update(rec.get("words", Counter()))
        all_bigrams.update(rec.get("bigrams", Counter()))
        all_trigrams.update(rec.get("trigrams", Counter()))

    def fmt(counter, n):
        parts = []
        for gram, count in counter.most_common(n):
            text = gram if isinstance(gram, str) else " ".join(gram)
            parts.append(f"{text} ({count})")
        return ", ".join(parts)

    rows = [
        ("Query", query),
        ("Generated (UTC)", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")),
        ("Results analyzed", len(ok)),
        ("Failed fetches", len(records) - len(ok)),
        ("Avg title length (chars)", round(mean(len(r["title"]) for r in ok), 1) if ok else 0),
        ("Avg meta description length (chars)", round(mean(len(r["description"]) for r in ok), 1) if ok else 0),
        ("Avg total characters", round(mean(r["char_count"] for r in ok), 1) if ok else 0),
        ("Avg H1 per page", round(mean(len(r["headings"]["h1"]) for r in ok), 2) if ok else 0),
        ("Avg H2 per page", round(mean(len(r["headings"]["h2"]) for r in ok), 2) if ok else 0),
        ("Avg H3 per page", round(mean(len(r["headings"]["h3"]) for r in ok), 2) if ok else 0),
        ("", ""),
        (f"Top {top} words across all pages", fmt(all_words, top)),
        (f"Top {top} bigrams across all pages", fmt(all_bigrams, top)),
        (f"Top {top} trigrams across all pages", fmt(all_trigrams, top)),
    ]
    for label, value in rows:
        ov.append([label, value])
    ov.column_dimensions["A"].width = 38
    ov.column_dimensions["B"].width = 120
    for row in ov.iter_rows():
        row[0].font = Font(bold=True)
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    wb.save(out_path)
    return out_path


def default_out_path(query):
    slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")[:40] or "query"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"seo_results_{slug}_{stamp}.xlsx"
