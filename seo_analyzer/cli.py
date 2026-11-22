import argparse
import sys
import time

import requests

from .analysis import analyze_text
from .config import Config
from .exporter import default_out_path, export_workbook
from .fetcher import RobotsCache, fetch_page
from .parser import parse_page
from .serp import fetch_organic_results


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="seo_analyzer",
        description=(
            "Analyze the top 10 organic Google results for a query: meta titles, "
            "meta descriptions, H1/H2/H3 headings, word/phrase frequency and page "
            "character count, exported to a sorted Excel file."
        ),
    )
    parser.add_argument("query", nargs="+", help="Search query, e.g. \"best crm for startups\"")
    parser.add_argument("-o", "--out", default=None, help="Output .xlsx path (default: auto-generated name)")
    parser.add_argument("--num", type=int, default=10, help="Number of organic results (1-10, default 10)")
    parser.add_argument("--gl", default=None, help="Country code for results, e.g. us, de, fr")
    parser.add_argument("--lr", default=None, help="Language restriction, e.g. lang_en")
    parser.add_argument("--hl", default=None, help="Interface language, e.g. en")
    parser.add_argument("--top", type=int, default=20, help="How many top words/phrases to list (default 20)")
    parser.add_argument("--delay", type=float, default=1.5, help="Seconds between page fetches (default 1.5)")
    parser.add_argument("--no-robots", action="store_true", help="Do not check robots.txt before fetching")
    parser.add_argument("--no-fetch", action="store_true", help="Only collect SERP data, skip page fetching")
    parser.add_argument("--api-key", default=None, help="Google API key (or set GOOGLE_API_KEY)")
    parser.add_argument("--cx", default=None, help="Programmable Search Engine ID (or set GOOGLE_CSE_ID)")
    return parser


def _empty_record(rank, url, error):
    return {
        "rank": rank,
        "url": url,
        "status": "error",
        "error": error,
        "title": "",
        "description": "",
        "headings": {"h1": [], "h2": [], "h3": []},
        "char_count": 0,
        "word_count": 0,
        "top_words": "",
        "top_bigrams": "",
        "top_trigrams": "",
    }


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    query = " ".join(args.query)
    config = Config(api_key=args.api_key, cx=args.cx)

    print(f'Query: "{query}"')
    results = fetch_organic_results(
        query,
        config.api_key,
        config.cx,
        num=args.num,
        gl=args.gl,
        lr=args.lr,
        hl=args.hl,
    )
    print(f"Got {len(results)} organic results from Google.")

    robots = None if args.no_robots else RobotsCache()
    session = requests.Session()
    records = []

    for result in results:
        rank, url = result["rank"], result["url"]
        if args.no_fetch:
            rec = _empty_record(rank, url, "not fetched (--no-fetch)")
            rec["status"] = "serp-only"
            rec["title"] = result.get("serp_title", "")
            rec["error"] = result.get("snippet", "")
        else:
            print(f"[{rank}/{len(results)}] Fetching {url}")
            html, error = fetch_page(url, session=session, robots=robots)
            if html is None:
                print(f"  skipped: {error}")
                rec = _empty_record(rank, url, error)
            else:
                parsed = parse_page(html)
                stats = analyze_text(parsed["text"], top=args.top)
                rec = {
                    "rank": rank,
                    "url": url,
                    "status": "ok",
                    "error": "",
                    "title": parsed["title"],
                    "description": parsed["description"],
                    "headings": parsed["headings"],
                    **stats,
                }
                print(
                    f"  ok: title={len(parsed['title'])} chars, "
                    f"text={stats['char_count']} chars, "
                    f"h1={len(parsed['headings']['h1'])}"
                )
            time.sleep(args.delay)
        records.append(rec)

    out_path = args.out or default_out_path(query)
    export_workbook(records, query=query, out_path=out_path, top=args.top)
    ok = sum(1 for r in records if r["status"] == "ok")
    print(f"Done: {ok}/{len(records)} pages analyzed. Saved to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
