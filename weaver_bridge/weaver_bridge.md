---
cssclasses:
  - weaver-card
weaver: bridge-control
status: in-progress
tools: c4d, houdini, nuke, fusion, weaver
width: 1100
---

```dataviewjs
// ============ ПУЛЬТ WEAVER BRIDGE ============
// Переключатели пишутся в control.json рядом с карточкой. Сторож (supervisor.py) читает его каждые
// 5 секунд; тот же файл меняют Telegram-бот (/mode, /apps) и Claude (bridge_control).
// Статус — status.json рядом (его пишет сторож; секретов в нём нет).
const p    = dv.current();
const base = p.file.folder;
const CTRL = base + "/control.json";
const STAT = base + "/status.json";

const view = dv.container.closest(".markdown-preview-view, .markdown-source-view");
if (view) view.style.setProperty("--file-line-width", `min(${Number(p.width) || 1100}px, 100%)`);

const box = document.createElement("div");
dv.container.appendChild(box);
const add = (tag, styles, parent) => {
  const e = document.createElement(tag);
  if (styles) Object.assign(e.style, styles);
  (parent || box).appendChild(e);
  return e;
};
const IC = { folder:"📁", section:"🗂", card:"📄", note:"📝", link:"🔗", home:"🏠",
             video:"▶", image:"🖼", star:"⭐" };
const LBL = { fontSize:"10px", fontWeight:"700", letterSpacing:".09em",
  textTransform:"uppercase", color:"var(--text-faint)", minWidth:"74px" };
const BTN = { display:"inline-flex", alignItems:"center", gap:"9px", padding:"10px 16px",
  borderRadius:"10px", background:"var(--background-secondary)",
  border:"1px solid var(--background-modifier-border)", color:"var(--text-normal)",
  textDecoration:"none", fontSize:"13.5px", fontWeight:"600", lineHeight:"1",
  cursor:"pointer", transition:"background .12s, border-color .12s, transform .12s" };
const ON = { borderColor:"var(--interactive-accent)",
  background:"color-mix(in srgb, var(--interactive-accent) 16%, var(--background-secondary))" };

const readJson = async (path) => {
  try { return JSON.parse(await app.vault.adapter.read(path)); } catch (e) { return null; }
};
const pad = n => String(n).padStart(2, "0");
const stamp = () => { const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`; };
const writeCtrl = async (change) => {
  const c = (await readJson(CTRL)) || { mode: "off", bridge: true, apps: {} };
  change(c);
  c.updated = stamp(); c.updated_by = "obsidian";
  await app.vault.adapter.write(CTRL, JSON.stringify(c, null, 2));
  await draw();
};

const button = (row, icon, label, active, onClick, title) => {
  const a = add("a", Object.assign({}, BTN, active ? ON : {}), row);
  add("span", { fontSize:"19px", lineHeight:"1" }, a).textContent = icon;
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
const row = (label) => {
  const r = add("div", { display:"flex", alignItems:"center", gap:"10px", flexWrap:"wrap", margin:"0 0 12px" });
  add("span", LBL, r).textContent = label;
  return r;
};

const MODES = [
  ["off",   "⏸", "Выключен",          "ничего не запускает и не трогает"],
  ["crash", "🩹", "После падения",     "я за компом: поднимает программу, только если она упала"],
  ["keep",  "🔒", "Держать открытыми", "меня нет: запускает, поднимает после падения и зависания"],
];
const STATE_RU = { "ok":"🟢 работает", "running, MCP off":"🟡 открыта, MCP не отвечает", "starting":"🟡 запускается",
  "waiting":"⏳ скоро запущу", "hung":"🧊 зависла", "closed":"⚪ закрыта", "parked":"⚪ закрыта вручную",
  "paused":"🛑 пауза: много падений", "no exe":"❌ не найден exe" };

async function draw() {
  box.replaceChildren();
  const c = (await readJson(CTRL)) || { mode: "off", apps: {} };
  const s = await readJson(STAT);

  // ---------- заголовок ----------
  const head = add("div", { display:"flex", alignItems:"center", gap:"11px", margin:"0 0 3px" });
  add("span", { fontSize:"27px", lineHeight:"1" }, head).textContent = "🎛";
  add("span", { fontSize:"25px", fontWeight:"800", letterSpacing:"-.01em" }, head).textContent = "Weaver Bridge";
  add("div", { fontSize:"11.5px", color:"var(--text-faint)", margin:"0 0 13px" })
    .textContent = "Weaver  ›  " + base.split("/").join("  ›  ");

  const nav = row("переход");
  button(nav, IC.home, "Weaver", false, () => app.workspace.openLinkText("Weaver.md", "", false));
  button(nav, IC.section, "weaver_claude", false, () => app.workspace.openLinkText("weaver_claude/weaver_claude.md", "", false));
  button(nav, IC.note, "Инструкция", false, () => app.workspace.openLinkText(base + "/README.md", "", false));

  // ---------- состояние ----------
  const meta = add("div", { fontSize:"11.5px", color:"var(--text-muted)", margin:"0 0 14px", lineHeight:"1.6" });
  if (!s) {
    meta.textContent = "Сторож ещё не писал статус: мост не установлен или не запущен (README → установка).";
  } else {
    const age = Math.round(Date.now() / 1000 - (s.time || 0));
    const stale = age > 120;
    meta.innerHTML = "";
    add("span", { color: stale ? "var(--text-error)" : "var(--text-muted)" }, meta).textContent =
      (stale ? `⚠️ статус не обновлялся ${Math.round(age/60)} мин — сторож не работает?` : `обновлено ${age} с назад`) +
      `  ·  шлюз: ${s.gateway}  ·  туннель: ${s.tunnel}  ·  бот: ${s.watcher}`;
  }

  // ---------- режим ----------
  const mr = row("сторож");
  for (const [m, icon, label, hint] of MODES)
    button(mr, icon, label, c.mode === m, () => writeCtrl(x => { x.mode = m; }), hint);
  add("div", { fontSize:"11px", color:"var(--text-faint)", margin:"-4px 0 14px 84px" }).textContent =
    (MODES.find(x => x[0] === c.mode) || MODES[0])[3];

  // ---------- программы ----------
  const ar = row("программы");
  const order = ["c4d", "c4d26", "houdini", "nuke", "fusion"];
  const keys = Object.keys(c.apps || {}).sort((a, b) => (order.indexOf(a) + 99) % 99 - (order.indexOf(b) + 99) % 99);
  for (const k of keys) {
    const info = (s && s.apps && s.apps[k]) || {};
    const st = STATE_RU[info.state] || (info.state ? info.state : "");
    button(ar, c.apps[k] ? "✅" : "▫️", info.label || k, !!c.apps[k],
           () => writeCtrl(x => { x.apps[k] = !x.apps[k]; }), (c.apps[k] ? "под сторожем" : "не под сторожем") + (st ? " · " + st : ""));
  }
  if (s && s.apps) {
    const list = add("div", { fontSize:"12px", color:"var(--text-muted)", margin:"-2px 0 14px 84px", lineHeight:"1.7" });
    for (const k of keys) {
      const a = s.apps[k]; if (!a) continue;
      const port = a.port === true ? " · MCP ✅" : (a.port === false ? " · MCP ❌" : "");
      add("div", null, list).textContent = `${STATE_RU[a.state] || a.state} — ${a.label}${port}`;
    }
  }

  // ---------- мост и автозапуск ----------
  const br = row("мост");
  button(br, "🌐", c.bridge === false ? "Мост выключен" : "Мост включён", c.bridge !== false, () => {
    if (c.bridge !== false && !confirm("Выключить шлюз и туннель? Claude из облака потеряет доступ к ПК, пока не включишь обратно (здесь или в боте).")) return;
    writeCtrl(x => { x.bridge = x.bridge === false; });
  }, "шлюз + туннель: доступ Claude из облака к программам");
  button(br, "🪟", c.windows_autostart === false ? "Без автозапуска" : "Запуск с Windows", c.windows_autostart !== false,
         () => writeCtrl(x => { x.windows_autostart = x.windows_autostart === false; }),
         "запускать мост и сторожа при входе в Windows");
  button(br, "🔄", "Обновить", false, () => draw());

  add("div", { fontSize:"11px", color:"var(--text-faint)", margin:"6px 0 0" }).textContent =
    `control.json: изменено ${c.updated || "?"} (${c.updated_by || "?"}) · Telegram: /bridge /mode /apps /run · Claude: bridge_status, bridge_control`;
}

await draw();
const timer = setInterval(() => { if (!box.isConnected) { clearInterval(timer); return; } draw(); }, 15000);
```

## Что это

Пульт моста Weaver Bridge: облачный Claude ↔ программы на этом ПК. Кнопки выше пишут `control.json`, сторож подхватывает за 5 секунд.

- **Сторож** — что делать с программами: ничего · поднимать после падения · держать открытыми.
- **Программы** — какие из них под сторожем.
- **Мост** — шлюз и туннель (без них облако не видит ПК). **Запуск с Windows** — стартовать всё это при входе в систему.

Подробно — [[Studio_bridge/weaver_bridge/README|README]].
