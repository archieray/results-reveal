"""
Creates mock_released.html — this year's real page structure with fake marks injected.
Run: python3 make_mock.py
Then test: python3 scraper.py --from-file mock_released.html
"""
import re

MOCK_MARKS = {
    "CS260":  {"mark": 72, "grade": "21", "components": [85, 61, 58, 71]},
    "MA117":  {"mark": 81, "grade": "1",  "components": [88, 79, 77]},
    "MA240":  {"mark": 68, "grade": "21", "components": [72, 65, 65]},
    "MA260":  {"mark": 77, "grade": "1",  "components": [95, 74]},
    "MA262":  {"mark": 85, "grade": "1",  "components": [87, 90, 80, 78, 75]},
    "MA265":  {"mark": 74, "grade": "21", "components": [92, 72]},
    "MA266":  {"mark": 63, "grade": "21", "components": [88, 60]},
    "MA268":  {"mark": 88, "grade": "1",  "components": [95, 87]},
    "MA270":  {"mark": 71, "grade": "1",  "components": [89, 69]},
    "ST227":  {"mark": 66, "grade": "21", "components": [80, 64]},
    "ST232":  {"mark": 79, "grade": "21", "components": [85, 78]},
}

CATS = {
    "CS260": 15, "MA117": 10, "MA240": 10, "MA260": 10, "MA262": 15,
    "MA265": 10, "MA266": 10, "MA268": 10, "MA270": 10, "ST227": 10, "ST232": 15,
}

def compute_year_mark():
    total_weighted = sum(MOCK_MARKS[c]["mark"] * CATS[c] for c in MOCK_MARKS)
    return round(total_weighted / sum(CATS.values()), 1)

def component_grade(mark):
    if mark >= 70: return "1"
    if mark >= 60: return "21"
    if mark >= 50: return "22"
    if mark >= 40: return "3"
    return "F"

lines = open("raw_page.txt").read().splitlines()
out = []
i = 0
n = len(lines)
current_code = None
component_index = 0
year_mark = compute_year_mark()

while i < n:
    line = lines[i]

    if "not visible on this page" in line or "results information page" in line:
        i += 1
        continue

    if line.strip() == "Year mark:" and i + 1 < n and lines[i + 1].strip() == "-":
        out.append(line)
        out.append(f"{year_mark}%")
        out.append("Progression decision")
        out.append("Summer exam period")
        out.append("Congratulations on your success – you have passed the year and are able to proceed to the next stage of your honours degree.")
        i += 2
        continue

    detail_match = re.match(r'^([A-Z]{2,3}\d[A-Z0-9]{1,3})\s+(.+)$', line)
    if detail_match and i + 1 < n and lines[i + 1].strip() == "Assessment group:":
        current_code = detail_match.group(1)
        component_index = 0
        out.append(line)
        i += 1
        continue

    if line.strip() == "CATS:" and current_code:
        out.append(line)
        cats_val = lines[i + 1].strip() if i + 1 < n else "0"
        out.append(cats_val)
        i += 2
        if current_code in MOCK_MARKS:
            m = MOCK_MARKS[current_code]
            out += ["Mark:", str(m["mark"]), "Grade:", m["grade"], "Passed CATS:", cats_val]
        continue

    if (line.strip() == "Sequence" and i + 3 < n
            and lines[i+1].strip() == "Type"
            and lines[i+2].strip() == "Name"
            and lines[i+3].strip() == "Weighting"):
        out += ["Sequence", "Type", "Name", "Weighting", "Mark", "Grade"]
        i += 4
        component_index = 0
        continue

    if re.match(r'^\d+%$', line.strip()) and current_code in MOCK_MARKS:
        out.append(line)
        i += 1
        comp_marks = MOCK_MARKS[current_code]["components"]
        cmark = comp_marks[component_index] if component_index < len(comp_marks) else 70
        out += [str(cmark), component_grade(cmark)]
        component_index += 1
        continue

    out.append(line)
    i += 1

html_lines = ["<html><body>"] + [f"<div>{l}</div>" for l in out] + ["</body></html>"]
with open("mock_released.html", "w") as f:
    f.write("\n".join(html_lines))

print(f"Written mock_released.html — year mark: {year_mark}%, {len(MOCK_MARKS)} modules")
