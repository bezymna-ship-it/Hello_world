---
cssclasses:
  - weaver-card
width: 1200
---

```dataviewjs
// ============ ХАБ: главная страница Weaver ============
// Мост (живой статус) · задачи (собираются сами) · библиотека · правила агентов.
const IC = { folder:"📁", section:"🗂", card:"📄", note:"📝", home:"🏠", star:"⭐", agent:"🤖", assembly:"🎬", bridge:"🎛" };
const IMG = ["png","jpg","jpeg","webp","gif","avif"];
const VID = ["mp4","mov","webm","m4v","mkv"];
const BRIDGE = "Studio_bridge/weaver_bridge";
const shell = window.require ? window.require("electron").shell : null;
const vault = app.vault.adapter.getBasePath ? app.vault.adapter.getBasePath() : "";

const box = document.createElement("div");
dv.container.appendChild(box);
const add = (tag, styles, parent) => { const e = document.createElement(tag);
  if (styles) Object.assign(e.style, styles); (parent || box).appendChild(e); return e; };
const view = dv.container.closest(".markdown-preview-view, .markdown-source-view");
if (view) view.style.setProperty("--file-line-width", "min(1200px, 100%)");

const head = add("div", { display:"flex", alignItems:"center", gap:"11px", margin:"0 0 3px" });
add("span", { fontSize:"27px", lineHeight:"1" }, head).textContent = IC.home;
add("span", { fontSize:"25px", fontWeight:"800", letterSpacing:"-.01em" }, head).textContent = "Weaver";
add("div", { fontSize:"11.5px", color:"var(--text-faint)", margin:"0 0 6px" })
  .textContent = "Obsidian  ·  Todoist  ·  Eagle  ·  Claude";

const cards = app.vault.getMarkdownFiles()
  .filter(f => f.path.startsWith("Projects/") && f.basename === f.parent.name)
  .filter(f => f.basename !== "_Assembly" && !f.path.includes("/Context/"));
const all = app.vault.getFiles();
const info = f => {
  const fm = app.metadataCache.getFileCache(f)?.frontmatter || {};
  const out = f.parent.path + "/Output/";
  const n = all.filter(x => x.path.startsWith(out) && !x.path.includes("/Thumbs/")
    && (IMG.includes(x.extension.toLowerCase()) || VID.includes(x.extension.toLowerCase()))).length;
  return { fm, n, br: f.parent.path.split("/")[1] || "",
    last: Math.max(0, ...all.filter(x => x.path.startsWith(f.parent.path + "/")).map(x => x.stat.mtime)) };
};

const section = (icon, title) => {
  const h = add("div", { display:"flex", alignItems:"center", gap:"9px", margin:"22px 0 9px" });
  add("span", { fontSize:"17px", lineHeight:"1", opacity:".7" }, h).textContent = icon;
  add("span", { fontSize:"11px", textTransform:"uppercase", letterSpacing:".09em",
    opacity:".5", fontWeight:"700" }, h).textContent = title;
  return add("div", { display:"flex", flexWrap:"wrap", gap:"11px" });
};
const tile = (row, icon, title, sub, onClick, accent, chip) => {
  const a = add("a", { position:"relative", display:"flex", alignItems:"center", gap:"13px",
    padding:"14px 19px", borderRadius:"12px", minWidth:"210px", background:"var(--background-secondary)",
    border:"1px solid " + (accent ? "var(--interactive-accent)" : "var(--background-modifier-border)"),
    textDecoration:"none", cursor:"pointer", transition:"background .12s, transform .12s" }, row);
  add("span", { fontSize:"27px", lineHeight:"1" }, a).textContent = icon;
  const col = add("div", { display:"flex", flexDirection:"column", gap:"3px" }, a);
  add("span", { fontSize:"15px", fontWeight:"700",
    color: accent ? "var(--interactive-accent)" : "var(--text-normal)" }, col).textContent = title;
  add("span", { fontSize:"11px", color:"var(--text-faint)", letterSpacing:".02em" }, col).textContent = sub;
  if (chip) {
    const c = add("span", { position:"absolute", top:"9px", right:"11px", fontSize:"9px", fontWeight:"700",
      letterSpacing:".06em", textTransform:"uppercase", color:"var(--interactive-accent)", padding:"2px 7px",
      borderRadius:"999px", background:"color-mix(in srgb, var(--interactive-accent) 14%, transparent)" }, a);
    c.textContent = chip;
  }
  a.href = "#";
  a.addEventListener("mouseenter", () => { a.style.background = "var(--background-modifier-hover)"; a.style.transform = "translateY(-1px)"; });
  a.addEventListener("mouseleave", () => { a.style.background = "var(--background-secondary)"; a.style.transform = "none"; });
  a.addEventListener("click", e => { e.preventDefault(); onClick(); });
};
const go = p => app.workspace.openLinkText(p, "", false);

// ---------- мост: живой статус (status.json пишет supervisor) ----------
{
  let st = null, ctl = null;
  try { st = JSON.parse(await app.vault.adapter.read(BRIDGE + "/status.json")); } catch (e) {}
  try { ctl = JSON.parse(await app.vault.adapter.read(BRIDGE + "/control.json")); } catch (e) {}
  const MODE = { off:"⏸ guard off", on:"🛡 guard on", crash:"🛡 guard on", keep:"🔒 guard keep" };
  const age = st ? Math.round(Date.now() / 1000 - (st.time || 0)) : null;
  const alive = st && age < 120;
  const apps = st ? Object.values(st.apps || {}) : [];
  const ok = apps.filter(a => a.state === "ok").length;
  const a = add("a", { display:"flex", flexDirection:"column", gap:"6px", margin:"14px 0 4px", padding:"14px 20px",
    borderRadius:"14px", border:"1px solid var(--interactive-accent)", background:"var(--background-secondary)",
    textDecoration:"none", cursor:"pointer", maxWidth:"620px", transition:"transform .12s" });
  add("span", { fontSize:"9px", fontWeight:"700", letterSpacing:".08em", textTransform:"uppercase",
    color:"var(--interactive-accent)" }, a).textContent = "📌 пульт: облако → ПК";
  add("span", { fontSize:"19px", fontWeight:"800", color:"var(--text-normal)" }, a).textContent = IC.bridge + " Studio Bridge";
  add("span", { fontSize:"12px", color: alive ? "var(--text-muted)" : "var(--text-error)", lineHeight:"1.5" }, a).textContent =
    !st ? "статуса нет — мост не запущен"
    : !alive ? `⚠️ мост молчит ${Math.round(age / 60)} мин`
    : `${MODE[(ctl || {}).mode] || ""}  ·  мост ${(ctl || {}).bridge === false ? "off" : "on"}  ·  программ на связи: ${ok} из ${apps.length}`;
  a.href = "#";
  a.addEventListener("mouseenter", () => a.style.transform = "translateY(-1px)");
  a.addEventListener("mouseleave", () => a.style.transform = "none");
  a.addEventListener("click", e => { e.preventDefault(); go("Studio_bridge/Studio_bridge.md"); });
}

const rows = cards.map(f => ({ f, ...info(f) }))
  .sort((a, b) => (b.fm.status === "in-progress") - (a.fm.status === "in-progress") || b.last - a.last);
for (const br of [...new Set(rows.map(r => r.br))]) {
  const row = section(IC.folder, br);
  for (const r of rows.filter(x => x.br === br))
    tile(row, IC.card, r.f.basename, r.n ? r.n + " превью" : "пока пусто",
      () => go(r.f.path), r.fm.status === "in-progress", r.fm.status === "in-progress" ? "в работе" : null);
}

const lib = section(IC.section, "библиотека");
tile(lib, IC.star, "Библиотека", "рефы · туториалы · курсы · скрипты", () => go("Library/Library.md"), true);
tile(lib, IC.assembly, "_Assembly", "отбор в шоурил", () => go("Projects/show reel/_Assembly/_Assembly.md"));

const ag = section(IC.agent, "агенты");
tile(ag, IC.star, "Правила", "всё, что агенты обязаны соблюдать — правишь тут", () => go("Weaver/Правила.md"), true);
tile(ag, IC.note, "Ядро", "грузится в каждую сессию", () => go("weaver_claude/00_start.md"));
tile(ag, IC.note, "Карта ПК", "диски, софт, порты", () => go("weaver_claude/02_map.md"));
tile(ag, IC.section, "Скиллы", "моделинг · анимация · GSG · устройство Weaver", () => go("weaver_claude/skills/weaver-system.md"));
tile(ag, IC.note, "STATE", "снимок задач, генерируется", () => go("Agent/STATE.md"));
if (shell && vault) tile(ag, "⌨️", "Claude Code", "запустить на этом ПК",
  () => shell.openPath(vault + "\\weaver_claude\\cmd_claude\\start_claude.bat"));
```

```
Weaver
├── Projects        задачи: claude · show reel · work · site_portfolio → Context.md · Assets · Passes · Output
├── Library         рефы · туториалы · курсы · материалы · скрипты (+ Eagle)
├── Weaver          эта страница · Правила
└── Studio_bridge   пульт моста: guard · мост · программы

скрыто: weaver_claude (ядро, карта ПК, скиллы, cmd_claude) · код моста · Agent · Eagle_lib · _archive · CLAUDE.md · AGENTS.md
```

Задача = папка + карточка + `Context.md`. Одна задача Todoist = одна папка. Карточка сама собирает превью из `Output`, библиотека — из Eagle. Скрытое не удалено: открывается плитками выше, а для агентов всё на месте.
