# Weaver Bridge

Новый мост из облачного Claude к ПК (вместо `Studio_bridge/test_claude_v02…/studio-bridge`). Пульт — карточка [[Studio_bridge/Studio_bridge|Studio_bridge]] (эта папка с кодом в Obsidian скрыта).

```
claude.ai ──HTTPS──► туннель (cloudflared / ngrok) ──► шлюз 127.0.0.1:8765
                                                        ├─ c4d__     Cinema 4D (не 2026.4): плагин cinema4d-mcp, порт 5555
                                                        ├─ c4d26__   Cinema 4D 2026.4: встроенный MCP Maxon, порт 5556
                                                        ├─ houdini__ Houdini, порт 19876
                                                        ├─ nuke__    Nuke, порт 54321
                                                        ├─ fusion__  Fusion Studio
                                                        └─ weaver__  хранилище + библиотека GSG
supervisor.py ────────── держит шлюз, туннель, бота; guard следит за программами; читает control.json
бот weaver_watcher ───── Telegram: рендер (RenderWatch 2.0 внутри), мост, кнопки
```

## Что нового по сравнению со Studio Bridge

- **Cinema 4D 2026.4** — подключается к встроенному MCP Maxon (HTTP, Bearer-токен). Остальные версии — плагин на 5555. Две Cinema могут быть открыты одновременно.
- **Само подключается при открытии программы**: C4D (плагин поднимает сокет-сервер сам), Houdini (`scripts/123.py`, `456.py`), Nuke (`menu.py`). Кнопки MCP Start больше не нужны.
- **Инструменты не пропадают**, пока программа закрыта: Claude видит их и получает ответ «программа не запущена».
- **Guard с тремя режимами** (пульт, кнопка 🛡 Guard в боте, Claude `bridge_control`):
  - ⏸ `off` — ничего не трогает;
  - 🛡 `on` — программа **упала** → закрывает окно ошибки (WerFault, «has stopped working», bug report) и открывает её снова со сценой. Закрыла сама — не трогает. Когда ты за компом;
  - 🔒 `keep` — держит программы открытыми: запускает закрытые, поднимает после падения и зависания (зависла > 5 мин — перезапуск) — когда тебя нет.
  Падение от обычного закрытия guard отличает по метке, которую ставит хук внутри программы при нормальном выходе.
  После падения программа **сама открывает сцену**, которая была открыта (не больше 3 раз за 15 минут).
- **Telegram-бот `weaver_watcher`** — RenderWatch 2.0 + рендеры Houdini/Nuke/Fusion по папкам `Passes`, новые mp4 из `Output/Videos`, статус моста и кнопки.
- **Секреты вне хранилища**: токен шлюза, токен C4D 2026.4, токен бота — в `C:\weaver_bridge\secrets.json`. Облако их прочитать не может.

## Установка (один раз, на ПК)

Нужны Windows, Python 3.11+ (`py`), Git. Если нет: `winget install Python.Python.3.12` и `winget install Git.Git`.

1. **Cinema 4D 2026.4**: *Edit → Preferences → MCP* → галочка **Allow MCP Server**; в *Clients* выбрать **Claude Code** → **Update Selected Client** (токен попадёт в `~/.claude.json`, установщик возьмёт его оттуда). Выставь там же, какие группы инструментов и Python разрешены.
2. Открой папку моста в Проводнике (`G:\todoist_obsidian_claude\Studio_bridge\weaver_bridge`), в адресной строке набери `cmd`, Enter, в чёрном окне:
   ```
   py install.py
   ```
   Установщик найдёт программы, поставит всё в `C:\weaver_bridge`, положит хуки в C4D/Houdini/Nuke, остановит старый Studio Bridge и RenderWatch (их бот заменяет новый), запустит мост и скопирует **адрес коннектора** в буфер. Бот: возьмёт токен из `RenderWatch\watchdog\config.json`, если он там заполнен, иначе спросит (Enter — пропустить).
3. claude.ai → Settings → Connectors: **удали старый коннектор** и добавь новый адрес (*Add custom connector*, без авторизации). Новая сессия Claude → `bridge_status`.
4. Перезапусти Cinema 4D, Houdini, Nuke — с этого момента MCP поднимается в них сам.

Повторный `py install.py` безопасен: обновит серверы, сохранит токены и настройки. `py install.py --telegram` — заново ввести бота. `py install.py --dry-run` — только показать, какие программы нашлись.

## Каждый день

Ничего: мост стартует вместе с Windows (пульт → **с windows: on/off** или `autostart_off.cmd`). Guard — на пульте или кнопкой в боте.

Адрес quick-туннеля Cloudflare **меняется при каждом старте моста** — бот пришлёт «адрес изменился», сам адрес: кнопка 🔗 Адрес в боте или `url.cmd`. Чтобы не менять коннектор, поставь постоянный адрес ngrok: `winget install ngrok.ngrok`, `ngrok config add-authtoken <токен>`, в `config.json` → `"tunnel": {"type": "ngrok", "ngrok_domain": "имя.ngrok-free.app"}`.

## Файлы

| Где | Что |
|---|---|
| `../Studio_bridge.md` | пульт в Obsidian (все кнопки) |
| `control.json` | переключатели (guard, программы, мост, запуск с Windows) — меняют пульт, бот, Claude |
| `status.json` | что сейчас работает (пишет supervisor) |
| `config.json` | пути к программам, порты, туннель, папки рендеров (`watch_render_dirs`). Создаёт установщик; можно править руками |
| `supervisor.py` | держит мост и guard; `status.cmd`, `stop.cmd`, `start.cmd`, `url.cmd` |
| `gateway/gateway.py` | шлюз MCP |
| `watcher/weaver_watcher.py` | Telegram-бот (+ `render_watchdog_base.py` — копия RenderWatch 2.0) |
| `hooks/` | то, что ставится внутрь программ (плагин C4D, `weaver_hook.py`) |
| `weaver-server/` | сервер хранилища и GSG (`weaver__…`); `weaver_context` грузит `weaver_claude/00_start.md` |
| `C:\weaver_bridge\` | venv, серверы программ, cloudflared, `logs\`, `state\`, **`secrets.json`**, `connector-url.txt` |

## Telegram

Всё кнопками внизу чата, печатать ничего не нужно: 🔌 Мост (что открыто; там же мост on/off) · 🛡 Guard · 🧩 Программы · 🚀 Запустить · 🎞 Рендер · 🖼 Превью · 🎬 Видео · ⚙️ Настройки · 🔗 Адрес. Пропали кнопки — ☰ Меню → «Кнопки» (/menu). Любая кнопка заодно выключает тревогу.

Мост сообщает: падение (со сценой), перезапуск, зависание, «закрылась, но падение не подтверждено» (с кнопкой «Запустить»), много падений подряд (пауза), смена адреса туннеля.

## Безопасность

- Через мост выполняется **любой Python** в программах — то есть на ПК. Защита — случайный токен в адресе. Адрес никому не показывать. Утёк — удали `gateway_token` из `C:\weaver_bridge\secrets.json` и запусти `py install.py`.
- Код моста лежит в хранилище и правится из облака (`weaver__vault_write`) — после правки он выполняется на ПК при перезапуске моста. Секреты в хранилище не попадают.
- Встроенный MCP Cinema 2026.4: права групп инструментов и Python — в её настройках MCP; журнал вызовов — в папке настроек Cinema, подпапка `mcp`.

## Если что-то не так

`status.cmd` — что работает. Логи — `C:\weaver_bridge\logs\` (`supervisor.log`, `gateway.log`, `tunnel.log`, `watcher.log`, `<программа>.log`).

| Симптом | Что проверить |
|---|---|
| `c4d26: DOWN` | открыта ли Cinema 2026.4; *Preferences → MCP → Allow MCP Server*; токен (`py install.py` перечитает) |
| `c4d: DOWN` | открыта ли Cinema с плагином; окно *Socket Server Control* должно показать Online |
| `houdini: DOWN` | статусная строка Houdini «Weaver Bridge: Houdini MCP on localhost:19876»; лог `houdini.log` |
| guard не поднял программу | guard `off`? «guard следит» у программы на пульте; `supervisor.log`; «пауза: много падений» сбрасывает 🚀 Запустить |
| бот молчит | `secrets.json` (telegram_token, telegram_chat_id); не запущен ли старый RenderWatch с тем же ботом (`watcher.log`: 409 Conflict) |

## Что проверено, а что нет

Проверено в облаке (Linux, без программ): шлюз (stdio + HTTP с Bearer, кеш инструментов, переподключение, `bridge_control`), логика guard (падение / обычное закрытие / keep / запрос `/run` / улики падения / `stop` не трогает программы), бот на заглушке Telegram, установщик — частично (блоки `pythonrc.py`/`menu.py`, токен из `.claude.json`), патч автозапуска C4D, JS карточки (`node --check`). **Не проверено на Windows и в самих программах** — первый запуск `py install.py` покажет; присылай вывод, поправлю.
