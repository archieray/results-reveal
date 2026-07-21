# Results Reveal

Warwick releases your end of your results in the most boring way possible - a sheet of paper with some numbers on it. Wouldn't it be better to get it presented to you in a fancy animated slideshow? This repo does it all for you, it parses your results page without you having to see it and puts it into a fancy slideshow to make results day more exciting!

---

## On the day — full runbook

Run these in order in a terminal. Don't skip steps.

**1. Re-login (session will have expired — always do this first)**
```bash
cd ~/ResultsReveal
python3 scraper.py --login
```
A browser window opens to the Tabula homepage. Log in via Warwick SSO. Once you're on any Tabula page, press Enter in the terminal. Takes ~30 seconds.

**2. Scrape your results (headless — results never appear on screen)**
```bash
python3 scraper.py "https://tabula.warwick.ac.uk/profiles/view/course/5603732_2/2025/modules"
```
Expected output:
```
Wrote 11 modules to /Users/archie-raythompson/ResultsReveal/results.json
```
If it says "Session expired" → go back to step 1.
If module count is 0 → something is wrong, see Troubleshooting below.
If it says "Results aren't out yet" → too early, try again later.

**3. Start the local server**
```bash
python3 -m http.server 8765
```
Leave this running. Open a new terminal tab if you need to run more commands.

**4. Open the animation**

Open in a browser: `http://localhost:8765/animation/index.html`

Click (or press Space/Enter/→) to advance through each screen.

---

## Setup (already done — don't redo unless on a new machine)
```bash
pip3 install playwright beautifulsoup4
playwright install chromium
```

---

## Testing without real results

Use last year's hand-verified fixture:
```bash
cd ~/ResultsReveal
python3 -m http.server 8765
# open http://localhost:8765/animation/index.html?data=../test_results.json
```

Or re-scrape last year's page (real scraper, real auth):
```bash
python3 scraper.py "https://tabula.warwick.ac.uk/profiles/view/course/5603732_1/2024/modules"
python3 -m http.server 8765
# open http://localhost:8765/animation/index.html
```

---

## Troubleshooting

**"Session expired or not logged in"** — Run `python3 scraper.py --login` again.

**"Wrote 0 modules"** — Session expired (redirected to login) OR Tabula's page structure changed. Run with `--save-raw` and inspect `raw_page.txt` to diagnose:
```bash
python3 scraper.py --save-raw "https://tabula.warwick.ac.uk/profiles/view/course/5603732_2/2025/modules"
```

**Animation shows fetch error** — Server isn't running. Go back to step 3.

**Animation shows "Results aren't released yet"** — `results.json` has no marks in it. Re-run step 2 once marks are actually published.

---

## Notes
- `auth_state.json`, `results.json`, `raw_page.html`, `raw_page.txt` are all gitignored — never commit them.
- Do NOT use `--save-raw` on the day — it writes the raw page text to disk which would let you read marks before the reveal.
