# Results Reveal

<<<<<<< HEAD
Warwick releases your end of your results in the most boring way possible - a sheet of paper with some numbers on it. Wouldn't it be better to get it presented to you in a fancy animated slideshow? This repo does it all for you, it parses your results page without you having to see it and puts it into a fancy slideshow to make results day more exciting!
=======
Warwick released your end of your results in the most boring way possible - a sheet of paper with some numbers on it. Wouldn't it be better to get it presented to you in a fancy animated slideshow? This repo does it all for you, it parses your results page without you having to see it and puts it into a fancy slideshow to make results day more exciting!
>>>>>>> c1664aa (Wait for JS DOM render after page load; update README)

## Setup
```
pip3 install playwright beautifulsoup4
playwright install chromium
```

## First time (or whenever the saved session expires)
```
python3 scraper.py --login
```
A real browser window opens to the Tabula homepage (not your results — no spoilers). Log in via Warwick SSO, then press Enter in the terminal. This saves `auth_state.json` (gitignored, never delete it before results day).

## INSTRUCTIONS
```
first do `python3 scraper.py -login`
then do `python3 scraper.py <resultsurl>`
then do `python3 -m http.server 8765`
then results should be here `http://localhost:8765/animation/index.html`

on the day my results url is `https://tabula.warwick.ac.uk/profiles/view/course/5603732_2/2025/modules`

```