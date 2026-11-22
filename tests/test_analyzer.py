import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from openpyxl import load_workbook

from seo_analyzer.analysis import analyze_text, tokenize
from seo_analyzer.exporter import export_workbook
from seo_analyzer.parser import parse_page

SAMPLE_HTML = """
<html>
<head>
  <title>  Best CRM Software for Startups </title>
  <meta name="description" content="Compare the best CRM tools for startups in 2025.">
  <script>var tracker = "secret script text";</script>
  <style>.hidden { color: red; }</style>
</head>
<body>
  <h1>Best CRM for Startups</h1>
  <h2>Why CRM matters</h2>
  <h2>Top features</h2>
  <h3>Pricing</h3>
  <p>CRM software helps startups manage sales pipelines and customer data.
     CRM tools organize contacts, track deals and automate follow-ups.</p>
</body>
</html>
"""


class TestParser(unittest.TestCase):
    def test_extracts_title_description_headings(self):
        parsed = parse_page(SAMPLE_HTML)
        self.assertEqual(parsed["title"], "Best CRM Software for Startups")
        self.assertEqual(
            parsed["description"], "Compare the best CRM tools for startups in 2025."
        )
        self.assertEqual(parsed["headings"]["h1"], ["Best CRM for Startups"])
        self.assertEqual(parsed["headings"]["h2"], ["Why CRM matters", "Top features"])
        self.assertEqual(parsed["headings"]["h3"], ["Pricing"])

    def test_script_and_style_excluded_from_text(self):
        parsed = parse_page(SAMPLE_HTML)
        self.assertNotIn("secret script text", parsed["text"])
        self.assertNotIn("color: red", parsed["text"])
        self.assertIn("CRM software helps startups", parsed["text"])

    def test_missing_meta_description(self):
        parsed = parse_page("<html><head><title>T</title></head><body><p>hi</p></body></html>")
        self.assertEqual(parsed["description"], "")
        self.assertEqual(parsed["headings"], {"h1": [], "h2": [], "h3": []})


class TestAnalysis(unittest.TestCase):
    def test_tokenize_removes_stopwords_and_digits(self):
        tokens = tokenize("The CRM and the 2025 tools are the best!")
        self.assertNotIn("the", tokens)
        self.assertNotIn("and", tokens)
        self.assertNotIn("2025", tokens)
        self.assertIn("crm", tokens)
        self.assertIn("tools", tokens)

    def test_analyze_counts_and_frequencies(self):
        text = "alpha beta alpha gamma alpha beta"
        stats = analyze_text(text, top=5)
        self.assertEqual(stats["char_count"], len(text))
        self.assertEqual(stats["words"]["alpha"], 3)
        self.assertEqual(stats["words"]["beta"], 2)
        self.assertEqual(stats["bigrams"][("alpha", "beta")], 2)
        self.assertEqual(stats["trigrams"][("alpha", "beta", "alpha")], 1)
        self.assertIn("alpha (3)", stats["top_words"])
        self.assertIn("alpha beta (2)", stats["top_bigrams"])


class TestExporter(unittest.TestCase):
    def _record(self, rank, url, status="ok"):
        parsed = parse_page(SAMPLE_HTML)
        stats = analyze_text(parsed["text"], top=5)
        rec = {
            "rank": rank,
            "url": url,
            "status": status,
            "error": "" if status == "ok" else "HTTP 500",
            "title": parsed["title"],
            "description": parsed["description"],
            "headings": parsed["headings"],
            **stats,
        }
        return rec

    def test_workbook_structure_and_sorting(self):
        records = [self._record(2, "https://b.example"), self._record(1, "https://a.example")]
        records.append(self._record(3, "https://c.example", status="error"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.xlsx"
            export_workbook(records, query="crm startups", out_path=str(out), top=5)
            wb = load_workbook(out)
            self.assertEqual(wb.sheetnames, ["Results", "Overview"])
            ws = wb["Results"]
            self.assertEqual(ws.max_row, 4)  # header + 3 records
            self.assertEqual(ws.cell(row=2, column=1).value, 1)  # sorted by rank
            self.assertEqual(ws.cell(row=2, column=2).value, "https://a.example")
            self.assertEqual(ws.cell(row=2, column=5).value, "Best CRM Software for Startups")
            self.assertEqual(ws.cell(row=4, column=3).value, "error")
            self.assertEqual(ws.cell(row=4, column=4).value, "HTTP 500")
            ov = wb["Overview"]
            labels = [ov.cell(row=r, column=1).value for r in range(1, ov.max_row + 1)]
            self.assertIn("Query", labels)
            self.assertIn("Results analyzed", labels)


class TestEndToEndMocked(unittest.TestCase):
    def test_main_produces_xlsx(self):
        from seo_analyzer import cli

        fake_serp = [
            {"rank": i, "url": f"https://site{i}.example", "serp_title": f"Site {i}", "snippet": ""}
            for i in range(1, 4)
        ]
        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "e2e.xlsx")
            with patch.object(cli, "fetch_organic_results", return_value=fake_serp), patch.object(
                cli, "fetch_page", return_value=(SAMPLE_HTML, None)
            ), patch.object(cli.Config, "__init__", lambda self, **kw: None):
                cli.Config.api_key = "k"
                cli.Config.cx = "c"
                rc = cli.main(["crm startups", "--out", out, "--delay", "0"])
            self.assertEqual(rc, 0)
            wb = load_workbook(out)
            ws = wb["Results"]
            self.assertEqual(ws.max_row, 4)
            self.assertEqual(ws.cell(row=2, column=2).value, "https://site1.example")
            self.assertEqual(ws.cell(row=2, column=15).value, len(parse_page(SAMPLE_HTML)["text"]))


if __name__ == "__main__":
    unittest.main()
