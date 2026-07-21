const RESULTS_URL = new URLSearchParams(location.search).get("data") || "../results.json";

const screens = {
  intro: document.getElementById("intro"),
  overall: document.getElementById("overall"),
  modules: document.getElementById("modules"),
  summary: document.getElementById("summary"),
  titleCard: document.getElementById("title-card"),
};

function showScreen(name) {
  Object.values(screens).forEach((s) => s.classList.remove("active"));
  screens[name].classList.add("active");
}

function gradeClass(grade) {
  const g = (grade || "").toLowerCase();
  if (g === "1") return "grade-1";
  if (g === "21") return "grade-21";
  if (g === "22") return "grade-22";
  if (g === "3") return "grade-3";
  return "grade-f";
}

async function loadResults() {
  const res = await fetch(RESULTS_URL);
  if (!res.ok) throw new Error(`Failed to load ${RESULTS_URL}: ${res.status}`);
  return res.json();
}

function renderOverall(data) {
  document.getElementById("overall-mark").textContent =
    data.year_mark != null ? `${data.year_mark}%` : "—";
  document.getElementById("overall-decision").textContent = data.decision_text || "";
}

function renderModuleCard(mod) {
  const card = document.getElementById("module-card");
  card.innerHTML = `
    <div class="module-code">${mod.code}</div>
    <div class="module-name">${mod.name}</div>
    <div class="module-mark ${gradeClass(mod.grade)}">${mod.mark}%</div>
    <div class="module-meta">${mod.cats} CATS · Grade ${mod.grade} · ${mod.status || ""}</div>
  `;
  // restart card-in animation
  card.style.animation = "none";
  void card.offsetWidth;
  card.style.animation = "";
}

function renderSummary(data) {
  document.getElementById("summary-stats").innerHTML = `
    <div class="stat"><div class="value">${data.total_cats ?? "—"}</div><div class="label">Total CATS</div></div>
    <div class="stat"><div class="value">${data.year_mark ?? "—"}%</div><div class="label">Year Mark</div></div>
    <div class="stat"><div class="value">${data.modules.length}</div><div class="label">Modules</div></div>
  `;
}

async function run() {
  let data;
  try {
    data = await loadResults();
  } catch (err) {
    document.getElementById("intro").innerHTML = `<p style="color:#f66e6e">${err.message}</p>`;
    return;
  }

  if (data.results_released === false) {
    document.getElementById("intro").innerHTML =
      `<p style="color:#f6e06e">Results aren't released yet on the scraped page — nothing to reveal. Re-run the scraper once marks are out.</p>`;
    return;
  }

  document.getElementById("start-btn").addEventListener("click", () => {
    const sortedModules = [...data.modules].sort((a, b) => a.mark - b.mark);
    const slop = sortedModules.filter((m) => m.mark < 70);
    const averageJoes = sortedModules.filter((m) => m.mark >= 70 && m.mark < 80);
    const bigBoys = sortedModules.filter((m) => m.mark >= 80 && m.mark < 90);
    const soopCircles = sortedModules.filter((m) => m.mark >= 90);

    playSequence([
      (next) => showTitleCard("The slop modules...", next),
      (next) => playModuleGroup(slop, next),
      (next) => showTitleCard("The average Joes", next),
      (next) => playModuleGroup(averageJoes, next),
      (next) => showTitleCard("The big boys", next),
      (next) => playModuleGroup(bigBoys, next),
      (next) => showTitleCard("The soop circles", next),
      (next) => playModuleGroup(soopCircles, next),
      (next) => showTitleCard("And for your final grade...", next),
      (next) => { showScreen("overall"); next(); },
    ]);
  });

  function playSequence(steps) {
    let i = 0;
    function next() {
      if (i >= steps.length) return;
      const step = steps[i++];
      step(next);
    }
    next();
  }

  function playModuleGroup(modules, onDone) {
    if (modules.length === 0) {
      onDone();
      return;
    }
    showScreen("modules");
    playModules(modules, onDone);
  }

  function showTitleCard(text, onContinue) {
    showScreen("titleCard");
    document.getElementById("title-card-text").textContent = text;
    screens.titleCard.onclick = () => {
      screens.titleCard.onclick = null;
      onContinue();
    };
  }

  document.getElementById("to-summary-btn").addEventListener("click", () => {
    showScreen("summary");
  });

  document.getElementById("restart-btn").addEventListener("click", () => {
    showScreen("intro");
  });

  renderOverall(data);
  renderSummary(data);
}

let moduleIndex = 0;
function playModules(modules, onDone) {
  moduleIndex = 0;
  const progress = document.getElementById("module-progress");

  function showNext() {
    if (moduleIndex >= modules.length) {
      screens.modules.onclick = null;
      onDone();
      return;
    }
    renderModuleCard(modules[moduleIndex]);
    progress.textContent = `${moduleIndex + 1} / ${modules.length}`;
    moduleIndex++;
  }

  showNext();
  screens.modules.onclick = showNext;
}

document.addEventListener("keydown", (e) => {
  if (e.code === "Space" || e.code === "Enter" || e.code === "ArrowRight") {
    e.preventDefault();
    const active = Object.values(screens).find((s) => s.classList.contains("active"));
    if (active) active.click();
  }
});

run();
