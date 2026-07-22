"""
Scrapes a Tabula (Warwick) module results page into results.json.

Usage:
    python3 scraper.py --login         # one-time: log in manually (homepage only, no spoilers), save session
    python3 scraper.py <url>           # headless scrape using saved session
"""
import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

AUTH_STATE_PATH = Path(__file__).parent / "auth_state.json"
RESULTS_PATH = Path(__file__).parent / "results.json"
RAW_HTML_PATH = Path(__file__).parent / "raw_page.html"
RAW_TEXT_PATH = Path(__file__).parent / "raw_page.txt"

DETAIL_START_RE = re.compile(r"^([A-Z]{2,3}\d[A-Z0-9]{1,3})\s+(.+)$")
COMPONENT_SEQ_RE = re.compile(r"^[A-Z]\d{2}$")
COMPONENT_HEADER = ["Sequence", "Type", "Name", "Weighting", "Mark", "Grade"]


TABULA_HOME = "https://tabula.warwick.ac.uk/"


def do_login():
    """
    Logs in against the Tabula homepage rather than the results page itself,
    so the results never appear on screen during login — the actual scrape
    later runs headless and is never displayed.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(TABULA_HOME)
        print("Log in to Warwick SSO in the opened window.")
        print("Once you're back on a Tabula page (you won't see your results here), press Enter to continue...")
        input()
        context.storage_state(path=str(AUTH_STATE_PATH))
        browser.close()
        print(f"Session saved to {AUTH_STATE_PATH}")


def fetch_html(url: str) -> str:
    if not AUTH_STATE_PATH.exists():
        sys.exit("No saved session found. Run: python3 scraper.py --login")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(AUTH_STATE_PATH))
        page = context.new_page()
        page.goto(url, timeout=60_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
        final_url = page.url
        if "tabula.warwick.ac.uk" not in final_url:
            browser.close()
            sys.exit(
                f"Session expired or not logged in — redirected to:\n  {final_url}\n"
                "Run: python3 scraper.py --login   then try again."
            )
        # Give JS-rendered accordions a moment to finish populating the DOM
        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()
        return html


def parse_results(html: str) -> dict:
    """
    Tabula renders each label and its value as separate text nodes (one per line
    once flattened), not as 'Label: value' on one line. A module's detailed block
    looks like (each item below is its own line):

        <CODE> <Name>
        Assessment group: | <val>
        Occurrence: | <val>
        Status: | <val>
        CATS: | <val>
        Mark: | <val>
        Grade: | <val>
        Passed CATS: | <val>
        Components:
        Sequence Type Name Weighting Mark Grade   (header, one cell per line)
        <row 1, 6 lines> <row 2, 6 lines> ...

    terminated by the next module's detail block or the 'Examinations' section.
    """
    soup = BeautifulSoup(html, "html.parser")
    lines = [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]
    n = len(lines)

    year_mark = None
    total_cats = None
    decision_text = None
    results_released = True
    for i, line in enumerate(lines):
        if line == "Total CATS:" and total_cats is None and i + 1 < n:
            total_cats = int(lines[i + 1])
        if line == "Year mark:" and year_mark is None and i + 1 < n:
            raw = lines[i + 1].rstrip("%")
            year_mark = float(raw) if raw != "-" else None
        if "Congratulations" in line and decision_text is None:
            decision_text = line
        if "not visible on this page" in line or "results release" in line.lower():
            results_released = False

    modules = []
    i = 0
    while i < n:
        m = DETAIL_START_RE.match(lines[i])
        if not (m and i + 1 < n and lines[i + 1] == "Assessment group:"):
            i += 1
            continue

        code, name = m.group(1), m.group(2)
        j = i + 1  # at the "Assessment group:" label

        def take_value(j):
            # lines[j] is a label like "Status:", value is lines[j+1]
            return lines[j + 1], j + 2

        _, j = take_value(j)  # Assessment group value
        _, j = take_value(j)  # Occurrence value
        status, j = take_value(j)  # Status
        cats_str, j = take_value(j)  # CATS

        # Mark/Grade/Passed CATS are only present once results are released
        mark_str = grade = passed_cats_str = None
        if j < n and lines[j] == "Mark:":
            mark_str, j = take_value(j)
            grade, j = take_value(j)
            passed_cats_str, j = take_value(j)

        components = []
        if j < n and lines[j] == "Components:":
            j += 1
            has_marks = lines[j : j + 6] == COMPONENT_HEADER
            has_no_marks = lines[j : j + 4] == COMPONENT_HEADER[:4]
            if has_marks:
                j += 6
                row_width = 6
            elif has_no_marks:
                j += 4
                row_width = 4
            else:
                row_width = None
            if row_width:
                while j + row_width - 1 < n and COMPONENT_SEQ_RE.match(lines[j]):
                    row = lines[j : j + row_width]
                    component = {"sequence": row[0], "type": row[1], "name": row[2], "weighting": row[3]}
                    if row_width == 6:
                        component["mark"], component["grade"] = row[4], row[5]
                    components.append(component)
                    j += row_width

        def safe_int(s):
            try:
                return int(s.strip()) if s else None
            except ValueError:
                return None

        def safe_float(s):
            try:
                return float(s.strip()) if s else None
            except ValueError:
                return None

        modules.append({
            "code": code,
            "name": name,
            "cats": safe_int(cats_str),
            "mark": safe_float(mark_str),
            "grade": grade,
            "status": status,
            "passed_cats": safe_int(passed_cats_str),
            "components": components,
        })
        i = j

    return {
        "year_mark": year_mark,
        "total_cats": total_cats,
        "decision_text": decision_text,
        "results_released": results_released and any(m["mark"] is not None for m in modules),
        "modules": modules,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", nargs="?")
    parser.add_argument("--login", action="store_true", help="open a browser to log in manually and save the session")
    parser.add_argument("--save-raw", action="store_true", help="also dump the fetched page as raw_page.html / raw_page.txt for debugging the parser")
    parser.add_argument("--from-file", metavar="PATH", help="parse a previously saved HTML file instead of fetching (no login/network needed)")
    args = parser.parse_args()

    if args.login:
        do_login()
        return

    if args.from_file:
        html = Path(args.from_file).read_text()
    else:
        if not args.url:
            sys.exit("url is required (or use --from-file)")
        html = fetch_html(args.url)
        if args.save_raw:
            RAW_HTML_PATH.write_text(html)
            soup = BeautifulSoup(html, "html.parser")
            RAW_TEXT_PATH.write_text(soup.get_text("\n", strip=True))
            print(f"Saved raw page to {RAW_HTML_PATH} and {RAW_TEXT_PATH}")

    data = parse_results(html)
    RESULTS_PATH.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data['modules'])} modules to {RESULTS_PATH}")
    if not data["modules"]:
        print("WARNING: no modules were parsed — the page structure may not match what the parser expects. Re-run with --save-raw and inspect raw_page.txt.")
    elif not data["results_released"]:
        print("Results aren't out yet on this page — results.json has module/component structure but no marks/grades. Re-run once results are released.")


if __name__ == "__main__":
    main()
