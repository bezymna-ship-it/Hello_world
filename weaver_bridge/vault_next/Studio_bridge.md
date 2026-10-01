---
cssclasses:
  - weaver-card
weaver: bridge-control
width: 1100
---

```dataviewjs
// ============ ПУЛЬТ STUDIO BRIDGE ============
// Все кнопки моста здесь. Код моста — в скрытой папке weaver_bridge/ рядом.
// Кнопки пишут weaver_bridge/control.json; supervisor читает его каждые 5 секунд
// (тот же файл меняют кнопки бота и Claude через bridge_control). Статус — weaver_bridge/status.json.
const base = dv.current().file.folder;
const B    = base + "/weaver_bridge";
const CTRL = B + "/control.json", STAT = B + "/status.json", CONF = B + "/config.json";
const fs   = window.require ? window.require("fs") : null;
const shell = window.require ? window.require("electron").shell : null;

const view = dv.container.closest(".markdown-preview-view, .markdown-source-view");
if (view) view.style.setProperty("--file-line-width", "min(1100px, 100%)");
const box = document.createElement("div");
dv.container.appendChild(box);
const add = (tag, styles, parent) => { const e = document.createElement(tag);
  if (styles) Object.assign(e.style, styles); (parent || box).appendChild(e); return e; };

const LBL = { fontSize:"10px", fontWeight:"700", letterSpacing:".09em", textTransform:"uppercase",
  color:"var(--text-faint)", minWidth:"84px" };
const BTN = { display:"inline-flex", alignItems:"center", gap:"9px", padding:"10px 16px", borderRadius:"10px",
  background:"var(--background-secondary)", border:"1px solid var(--background-modifier-border)",
  color:"var(--text-normal)", textDecoration:"none", fontSize:"13.5px", fontWeight:"600", lineHeight:"1",
  cursor:"pointer", transition:"background .12s, border-color .12s, transform .12s" };
const ON = { borderColor:"var(--interactive-accent)",
  background:"color-mix(in srgb, var(--interactive-accent) 16%, var(--background-secondary))" };
const HINT = { fontSize:"11.5px", color:"var(--text-faint)", margin:"-4px 0 16px 94px", lineHeight:"1.5" };

const readJson = async p => { try { return JSON.parse(await app.vault.adapter.read(p)); } catch (e) { return null; } };
const pad = n => String(n).padStart(2, "0");
const stamp = () => { const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
const writeCtrl = async change => {
  const c = (await readJson(CTRL)) || { mode:"off", bridge:true, apps:{} };
  change(c); c.updated = stamp(); c.updated_by = "obsidian";
  await app.vault.adapter.write(CTRL, JSON.stringify(c, null, 2));
  await draw();
};
const button = (row, icon, label, active, onClick, title) => {
  const a = add("a", Object.assign({}, BTN, active ? ON : {}), row);
  add("span", { fontSize:"18px", lineHeight:"1" }, a).textContent = icon;
  add("span", null, a).textContent = label;
  if (title) a.title = title;
  a.href = "#";
  a.addEventListener("mouseenter", () => { a.style.transform = "translateY(-1px)";
    if (!active) a.style.borderColor = "var(--interactive-accent)"; });
  a.addEventListener("mouseleave", () => { a.style.transform = "none";
    if (!active) a.style.borderColor = "var(--background-modifier-border)"; });
  a.addEventListener("click", e => { e.preventDefault(); onClick(); });
  return a;
};
const row = label => { const r = add("div", { display:"flex", alignItems:"center", gap:"10px", flexWrap:"wrap", margin:"0 0 10px" });
  add("span", LBL, r).textContent = label; return r; };
const open = p => app.workspace.openLinkText(p, "", false);

const GUARD = [
  ["off",  "⏸", "off",  "ничего не запускает и не трогает"],
  ["on",   "🛡", "on",   "я за компом: программа упала — закрывает окно ошибки и открывает её снова с той же сценой; закрыла сама — не трогает"],
  ["keep", "🔒", "keep", "меня нет: держит программы открытыми — запускает закрытые, поднимает после падения и зависания"],
];
const STATE_RU = { "ok":"🟢 работает", "running, MCP off":"🟡 открыта, MCP не отвечает", "starting":"🟡 запускается",
  "waiting":"⏳ скоро запущу", "hung":"🧊 зависла", "closed":"⚪ закрыта", "parked":"⚪ закрыта вручную",
  "paused":"🛑 пауза: много падений подряд", "no exe":"❌ не найден exe" };
const ORDER = ["c4d26", "c4d", "houdini", "nuke", "fusion"];

async function launch(k) {
  const cfg = (await readJson(CONF)) || {};
  const dir = (cfg.home || "C:\\weaver_bridge") + "\\state\\requests";
  if (!fs) { new Notice("Запуск отсюда недоступен — нажми 🚀 Запустить в боте"); return; }
  try { fs.mkdirSync(dir, { recursive:true }); fs.writeFileSync(dir + "\\launch_" + k + ".txt", "");
        new Notice("Запускаю " + k + " (до 10 с)"); }
  catch (e) { new Notice("Не получилось: " + e.message); }
}

async function draw() {
  box.replaceChildren();
  const c = (await readJson(CTRL)) || { mode:"off", bridge:true, apps:{} };
  if (c.mode === "crash") c.mode = "on";
  const s = await readJson(STAT);
  const cfg = (await readJson(CONF)) || {};

  const head = add("div", { display:"flex", alignItems:"center", gap:"11px", margin:"0 0 3px" });
  add("span", { fontSize:"27px", lineHeight:"1" }, head).textContent = "🎛";
  add("span", { fontSize:"25px", fontWeight:"800", letterSpacing:"-.01em" }, head).textContent = "Studio Bridge";
  add("div", { fontSize:"11.5px", color:"var(--text-faint)", margin:"0 0 12px" })
    .textContent = "облачный Claude ↔ программы на этом ПК  ·  Telegram-бот weaver_watcher";

  const nav = row("переход");
  button(nav, "🏠", "Weaver", false, () => open("Weaver/Weaver.md"));
  button(nav, "⭐", "Правила", false, () => open("Weaver/Правила.md"));
  button(nav, "📝", "Инструкция", false, () => open(B + "/README.md"));
  if (shell) button(nav, "📁", "Логи", false, () => shell.openPath((cfg.home || "C:\\weaver_bridge") + "\\logs"));

  // ---------- состояние ----------
  const meta = add("div", { fontSize:"12px", margin:"4px 0 16px", lineHeight:"1.6" });
  if (!s) meta.textContent = "Статуса нет: мост не запущен (start.cmd в weaver_bridge) или не установлен.";
  else {
    const age = Math.round(Date.now() / 1000 - (s.time || 0));
    meta.style.color = age > 120 ? "var(--text-error)" : "var(--text-muted)";
    meta.textContent = (age > 120 ? `⚠️ мост молчит ${Math.round(age/60)} мин — не запущен?` : `обновлено ${age} с назад`) +
      `  ·  шлюз ${s.gateway}  ·  туннель ${s.tunnel}  ·  бот ${s.watcher}`;
  }

  // ---------- guard ----------
  const gr = row("guard");
  for (const [m, icon, label, hint] of GUARD)
    button(gr, icon, label, c.mode === m, () => writeCtrl(x => { x.mode = m; }), hint);
  add("div", HINT).textContent = (GUARD.find(x => x[0] === c.mode) || GUARD[0])[3];

  // ---------- программы ----------
  add("div", Object.assign({}, LBL, { margin:"4px 0 8px" })).textContent = "программы";
  const grid = add("div", { display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(240px, 1fr))", gap:"10px", margin:"0 0 6px" });
  const keys = [...new Set([...ORDER.filter(k => k in (c.apps || {})), ...Object.keys(c.apps || {})])];
  for (const k of keys) {
    const a = (s && s.apps && s.apps[k]) || {};
    const t = add("div", { padding:"12px 14px", borderRadius:"12px", background:"var(--background-secondary)",
      border:"1px solid " + (c.apps[k] ? "var(--interactive-accent)" : "var(--background-modifier-border)"),
      display:"flex", flexDirection:"column", gap:"7px" }, grid);
    add("div", { fontSize:"14.5px", fontWeight:"700" }, t).textContent = a.label || k;
    add("div", { fontSize:"11.5px", color:"var(--text-muted)" }, t).textContent =
      (STATE_RU[a.state] || a.state || "—") + (a.port === true ? " · MCP ✅" : a.port === false ? " · MCP ❌" : "");
    const r = add("div", { display:"flex", gap:"7px", flexWrap:"wrap" }, t);
    const small = { padding:"6px 10px", fontSize:"12px" };
    Object.assign(button(r, c.apps[k] ? "🛡" : "▫️", c.apps[k] ? "guard следит" : "guard не следит", !!c.apps[k],
      () => writeCtrl(x => { x.apps[k] = !x.apps[k]; }), "нажми, чтобы переключить").style, small);
    if (s && !(a.pids && a.pids.length) && a.state !== "no exe")
      Object.assign(button(r, "▶", "Запустить", false, () => launch(k), "открыть программу").style, small);
  }

  // ---------- мост ----------
  add("div", { height:"10px" });
  const br = row("мост");
  button(br, "🌐", c.bridge === false ? "off" : "on", c.bridge !== false, () => {
    if (c.bridge !== false && !confirm("Выключить мост? Claude из облака перестанет видеть программы, пока не включишь обратно (здесь или в боте). Guard и бот продолжат работать.")) return;
    writeCtrl(x => { x.bridge = x.bridge === false; });
  }, "доступ Claude из облака к программам на ПК");
  add("div", HINT).textContent = c.bridge === false
    ? "выключен: Claude из облака не видит ПК. Guard и бот работают."
    : "включён: Claude из облака видит Cinema, Houdini, Nuke, Fusion и файлы хранилища.";

  const wr = row("с windows");
  button(wr, "🪟", c.windows_autostart === false ? "off" : "on", c.windows_autostart !== false,
    () => writeCtrl(x => { x.windows_autostart = x.windows_autostart === false; }), "запускать мост при входе в Windows");
  add("div", HINT).textContent = c.windows_autostart === false
    ? "после перезагрузки ПК мост сам не запустится — только start.cmd"
    : "после перезагрузки ПК мост, guard и бот запускаются сами";

  const fr = row("");
  button(fr, "🔄", "Обновить", false, () => draw());
  add("span", { fontSize:"11px", color:"var(--text-faint)" }, fr).textContent =
    `изменено ${c.updated || "?"} (${c.updated_by || "?"})`;
}

await draw();
const timer = setInterval(() => { if (!box.isConnected) { clearInterval(timer); return; } draw(); }, 15000);
```

- **Guard** — что делать с программами, за которыми он следит: `off` ничего · `on` поднять после падения · `keep` держать открытыми.
- **Мост** — шлюз + туннель: через них Claude из облака работает с программами и файлами на ПК.
- **С Windows** — запускать мост, guard и бота сами после включения ПК.

То же самое — кнопками в Telegram-боте (🔌 Мост · 🛡 Guard · 🧩 Программы · 🚀 Запустить).
