## Итог в одной фразе
Нужный движок уже есть и проверен: пиксельный экран на MoGraph (Cloner + Python Effector, цвет клона в RS через атрибут `RSMGColor`) со всеми ручками на корневом нулике. Режимы часы, шарик, выкл, картинка/секвенция и шум уже работают. Не хватает трёх режимов (глазки-приветствие, спиннер, эквалайзер), аудио-входа, сцены взрыва частиц и сцены кубиков. Сохранённого скрипта сборки самого рига экрана в vault НЕТ — он собран «вживую», поэтому перенос = пересборка по описанию ниже.

Ограничения моей проверки: в C4D ничего не менял, активный документ не переключал. Читал открытый документ `Yogo_pro_keyboard_v008_anim_codex.c4d` (C4D 2026.4, версия 2026400). Сцены Pixbar_clock, Cubes_system, T_cubes (v010) не открывал, по ним только Context.md и src.

## (1) Абстрактные анимированные кубы
- Готового «моргающего приветствия», спиннера или эквалайзера из кубов НЕТ нигде в vault.
- `Projects/claude/Cubes_system/C4D/src/cs_build.py` (сцена `C4D/Cubes_system_v003.c4d`): CUBES_RIG > CTRL (User Data + Python-тег `DRIVER`, который каждый кадр переносит значения в клонер, эффекторы, поле и материалы), CUBES (Cloner Grid, 4 куба со скруглением), E_RANDOM, E_WAVE (Formula), E_SCATTER (Random), E_FALL (Plain), поле F_SWEEP (Linear). Без Redshift, сетка 14x14. Это готовая «волна + сборка/рассыпание» с ключом `Progress` 0→1. Внутри есть хелпер `add_ud(obj, name, kind, default, lo, hi, step, cycle, unit, slider)` для int/float/color/cycle — его стоит копировать для новых ручек.
- `T_cubes` (`C4D/src/tc7_native.py`, `tc4_anim.py`, сцена `T_cubes_v010.c4d`): бенто-плитки как обычные объекты с плотными ключами. Словарь движений: flip, lift, slide (бегунки), press (кнопки), bob, tilt. Тейк S16 содержит `CLAUDE_WORD`: слово из MoGraph-кубов. На каждую букву свой Cloner (режим Object/Vertex по точечному объекту 5x7) + Plain Effector, сила которого проявляет букву по ключам. Это единственный готовый пример «кубы как пиксели». В src он не сохранён (собран вживую, 47 МБ сцена).
- Вывод: для кубиков база есть только как идея Cloner Object/Vertex над сеткой точек + эффектор. Сами анимации надо писать.

## (2) Частицы / взрыв, запекаемые в пиксельную картинку
- Сцены с частичным взрывом в C4D или Houdini нет. «Разлёт слоёв» в Yogo — это разнос, а не частицы.
- Ближайшее готовое: `Cubes_system` (E_SCATTER = Random с позицией и вращением, сила — поле F_SWEEP; E_FALL = Plain со схлопыванием; ключ Progress; по MoData проверено, что на кадре 0 всё разлетелось, на кадре 90 собрано). Это уже «explode/assemble» на кубах-частицах.
- Houdini: `Block_frame` (`Houdini/src/bf_build.py`) — сборка из облака деталей функцией прогресса без состояния. По правилам §5 рендер Houdini только через hython, Redshift через мост нельзя.
- `Library/tutorial/Houdini/Particles.md` — только список туториалов, без сима.
- Запекания в картинку нет. Но в Yogo-эффекторе в `md.GetArray(c4d.MODATA_MATRIX)` уже читаются позиции клонов — тот же приём пригоден для сплата частиц в сетку.

## (3) Пиксельные экраны с текстурой/секвенцией
Путь A: Pixbar_clock, «экран-фильтр» (UV на ячейку).
- `Projects/claude/Pixbar_clock/C4D/src/pxb_parts2.py` функция `pixel_screen()` (строка 83): все 832 квадрата (52x16) одним мешем, у каждой точки UV центра своей ячейки `((i+0.5)/NX, (j+0.5)/NY)`, (0,0) = левый верх картинки. Запись UV: `pxb_c4d.to_poly(mesh, name, phong, uvs)` через `UVWTag.SetSlow`.
- Материал `PXB_pixel_screen`: `pxb_mats.screen()` (строка 154) — RS Standard Material (база ~0.004), Emission/Color ← нода Texture, emission_weight 45, путь задаётся через `_texture_node` и `maxon.Url` в порт `tex0/path`. Текстура: `Assets/Textures/display_clock_52x16.png`.
- Минус (из Context Yogo): режимы Animation у RS Texture нельзя узнать/задать из Python, поэтому секвенцию придётся включать руками; цвета и режимы ручками не управляются. Поэтому в Yogo ушли на MoGraph.

Путь B (основной): Yogo, MoGraph.
- Живая сцена `Yogo_pro_keyboard_v008_anim_codex.c4d`, в каждой клавиатуре `YOGO75PRO/MODULE/SCREEN` (проверено чтением): `scr_points` (Polygon, 2016 точек = 48x42, y=3.2, шаг 0.617 мм), `scr_cloner` (режим Object, Object=`scr_points`, Instance Mode=1 Render Instance, список эффекторов = [`scr_effect`]; всего таких 3), `scr_cell` (куб 0.501 x 0.08 x 0.501, тег `YKB_screen_cell`), `scr_effect` (Python Effector, тип 1025800, код 8675 символов, user data 1 = ссылка на пульт), `scr_grid` (решётка `YKB_screen_grid`).
- Материал `YKB_screen_cell`: граф RS из трёх нод — output, standardmaterial, rsuserdatacolor с атрибутом `RSMGColor` (default чёрный); Context: emission_weight 9, `scr_dim` 0.04. Старые `display_leds` и `display_pixels` скрыты.
- Код: `Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_screen_effector.py` (8200 Б). Режимы `scr_mode` (проверено по циклу user data 50): 0 Часы, 1 Шарик (петля), 2 Выкл, 3 Картинка/секвенция, 4 Шум. Сетка 48x42 определяется по позициям клонов; «логический рисунок» 16x14 масштабируется на S = NX//16. Картинка: `c4d.bitmaps.BaseBitmap`, пиксель = центр ячейки, `_grade` (инверсия, контраст, уровни, тон). Секвенция: число в конце имени файла, номер = первый + int(t*fps) mod N, зациклено (длина считается пробингом файлов). Шум: fbm по (i, j, t*speed) с двумя цветами. Цвет пишется в `MODATA_COLOR`.
- Тестовая картинка: `Yogo_pro_keyboard/Assets/Textures/screen_test_48x42.png` (радужный смайлик, глянул — виден).
- Концепт-рефы Like_nothing показывают именно этот контент: на чашках наушников и камере телефона — зелёная/белая волна-эквалайзер и часы `10:28` (`Like_nothing/Output/Refs/ref_headphones.png`, `ref_phone.png`).

## (4) Аудио / звук
- В vault НЕТ ни одного C4D-хука со звуком (поиск по sound, audio, equalizer, Omgsound, xpresso, эквалайзер, звук). Единственное упоминание — Blender-доклад в `Viewport_cheats/Context.md` (Speaker + NLA, не C4D).
- Нативные возможности C4D 2026.4 (проверено по константам `c4d`): Sound Effector `c4d.Omgsound` (`MGSOUNDEFFECTOR_FILE`, `_FREQ`, `_BANDWIDTH`, `_MODE`, `_MULTIPLIER`, `_PLAY`, `_SCRUB`, `_START`, `_MGMODE_STEP`), поле `Fsound`, Xpresso Sound node (`GV_SOUND_FFT_BIN`, `GV_SOUND_FFT_RES_*`), звуковая дорожка `CTsound`. Ни одна сцена пользователя их не использует; поведение в цепочке с Python-эффектором НЕ проверено.

## (5) «Ручки на корневом нулике»
- Правило `Weaver/Правила.md` §4.12: все User Data на отдельный нуль в корне сцены `<ИМЯ>_CONTROL`, одна вкладка, группы-складки по частям; на объектах рига ручек нет, эффекторы/теги/материалы читают значения с нуля; новая часть сцены = новая группа на том же нуле.
- Реализация в Yogo: нуль `BACKLIGHT_CONTROL` в корне (первый, над `main_keyboard`). User Data (проверено): группа ВСЕ КЛАВИАТУРЫ (id 2-14: вкл, интенсивность, скорость, ореол, свет из-под клавиш, Bloom, туман), КЛАВИАТУРА 1/2/3 (id 15-25, 26-36, 37-47), ЭКРАН ТАБЛО (MODULE) (id 48-74): 49 вкл, 50 режим, 51 цвет часов, 52 цвет шарика, 53 интенсивность, 54 погасшие пиксели, 55 время, 56-60 шарик, 61 файл, 62 секвенция, 63 fps, 64/65 отражение X/Y, 66 инверсия, 67 контраст, 68 тон, 69 уровни, 70-74 шум.
- Связь: у каждого эффектора user data 1 = ссылка на нуль (подпись «Pult»), имена ручек ↔ id зашиты словарём `IDS` прямо в код эффектора (при сборке подставляется). Python-тег `backlight_scene` на нуле (4000 символов, `ykb_backlight_scene.py`) пишет Bloom в RS Post-Effects и туман в RS Environment и «будит» эффекторы: при изменении любой ручки делает `SetDirty(DIRTYFLAGS_DATA)` на объектах `bl_effect`/`scr_effect`. Без этого MoGraph не пересчитывается.
- Старый вариант: `Cubes_system` — CTRL внутри CUBES_RIG + тег DRIVER, пушащий значения в объекты.
- Анимация ручек ключами в Yogo работает во вьюпорте и рендере (по Context v2).

## Что переиспользуется КАК ЕСТЬ
1. `ykb_screen_effector.py`: любой плоский регулярный клонер-экран; нужен только свой нуль, словарь `IDS`, ссылка в user data 1 эффектора. Режимы 0-4 готовы.
2. Материал-образец `YKB_screen_cell` (RS Standard + rsuserdatacolor `RSMGColor`), клонер Object + Render Instance + плоский куб, решётка, `backlight_scene` для Bloom/тумана и wake.
3. `pxb_parts2.pixel_screen` + `pxb_c4d.to_poly(uvs=)` + `pxb_mats.screen` для UV/текстурного пути.
4. `cs_build.add_ud` и пара Cloner + Random/Plain + Linear field с ключом Progress (explode/assemble).
5. `weaver_claude/skills/c4d-animation.md`: функция `seg()` и таблица Quint-касательных для ключей на ручках.
Правило проекта: Yogo/Pixbar — только копировать; код в `Like_nothing/C4D/src` с префиксом `lnk_`.

## Что НЕ готово / подводные камни
- Нет скрипта сборки рига экрана и самих User Data нуля Yogo (в src только эффектор и `ykb_backlight_scene.py`; `AddUserData` в Yogo src не встречается) — писать заново; параметры известны (см. выше).
- Грид эффектора определяется по `round(p.x, 2)`: ломается, если шаг < 0.01 ед. (мелкие экраны телефона/мыши) — заменить на округление по шагу. Арт часов/шарика заточен под 16x14 x S, для другого аспекта нужны нормированные координаты u, v.
- Кэш `_CACHE` (картинки, длина секвенции) не сбрасывается: перезаписанный по тому же пути кадр не обновится без правки кода эффектора. Секвенция читается кадр-за-кадром через BaseBitmap — годится для 48x42, не для HD.
- В Yogo экран «проверен данными, не глазами» (§8.6); также клоны не считаются, пока объект не в анимации/виден (замечено на keyboard1/2 на кадре 160).
- Звук: ничего не опробовано. В C4D Python нет прямого чтения аудио; numpy в Python C4D не проверял.

## Предлагаемая минимальная архитектура
Принцип: один модуль чистых функций анимации, два выхода (цвет экрана, высота/масштаб кубов), один пульт.

A. `lnk_pixel_anim.py` (ASCII, без `import c4d` на верхнем уровне, тестируется обычным python3 как `ykb_geo`; превью — ASCII-арт как `pxb_pixels.ascii_preview`). Функция `cell(mode, i, j, t, nx, ny, P)` в нормированных координатах. Режимы 0-4 сохранить с теми же id (совместимость), добавить:
- 5 Greeting eyes: два глаза (скруглённые прямоугольники) в (0.3, 0.5) и (0.7, 0.5); моргание — сжатие высоты по cos-колоколу, подмигивание — один глаз раз в N периодов; ручки: цвет, размер, зазор, период, сторона подмигивания.
- 6 Loading spinner: N точек по кругу, голова = 2*pi*u, хвост exp(-k*dtheta), направление, радиус, количество.
- 7 Equalizer: B столбцов, уровень = lerp(процедурный(t, b), `scr_level`, `scr_audio_mix`), опционально спектр из внешней картинки/секвенции; режимы «снизу вверх» и «зеркальная волна» (как на телефоне в рефе), пик-холд.
- 8 Explosion: N частиц с сидом, p = p0 + v*tau - drag, закрытая форма, сплат в сетку.
Все периодические: u = (t/period) % 1, целое число циклов, период в секундах (напр. 72 кадра / 30 fps = 2.4 с) — тест замыкания `frame(t) == frame(t+period)`.

B. Пульт `LIKE_NOTHING_CONTROL` в корне (§4.12): группа «PIXEL SCREEN» с теми же именами/id, что в Yogo, плюс новые ручки режимов 5-8, `scr_level` (float, ключуется — вход для будущего Sound Effector/Xpresso/baked audio), `scr_audio_file`, `scr_period`, `scr_phase`. Для каждого устройства (чашки наушников, телефон, клавиатура, мышь) — свой `SCREEN` (points + cloner + effector), все читают один пульт; индивидуальные on/off в своей группе.

C. `lnk_pixel_rig.py`: `make_screen(parent, nx, ny, pitch, name)` собирает scr_points, cloner (Object, Render Instance), плоский cube (0.813 шага), решётку, материал (RS Standard + `rsuserdatacolor` `RSMGColor`), эффектор (код = `lnk_pixel_anim` + обвязка, `IDS` подставляется, ссылка в user data 1) и тег-«будильник» по образцу `backlight_scene`. Копировать живую группу из открытой сцены Yogo через merge не надо — пересборка проще и безопаснее (§3.7, §4.5).

D. a) Контролируемый «шейдер»: ответ пользователю честно — чистый RS-шейдер для глаз/спиннера/эквалайзера не нужен и тяжёл; практический «шейдер анимации» = нулик + эффектор + RS-эмишен через `RSMGColor`; работа: выбрать Режим в цикле, подкрутить ручки, ключи на ручках (Quint по умолчанию, §9.1), положить `scr_audio_file`/анимировать `scr_level`. Для чистого рендера без Python — запечь секвенцию (`lnk_pixel_bake.py`, те же функции, PNG nx x ny через `c4d.bitmaps` или PIL) и подать на UV-путь Pixbar.

E. b) Сцена `PARTICLES_TO_PIXELS`: 3D-взрыв на базе Cubes_system (мелкие кубы в Cloner, E_SCATTER, ключ Explode/Progress с Quint, пульт в корне) + `lnk_particles_bake.py`: покадрово читает MoData клонов, сплатит вид сверху (ортогонально) в сетку 48x42 и пишет PNG-секвенцию `Assets/Textures/seq/<name>_0001.png`; режим 3 экрана её проигрывает. Это быстрее и безопаснее, чем рендер вида сверху: рендерить не нужно (§4.4 — RenderDocument пачкой/с Redshift запрещён). Если нужен именно рендер, только асинхронно по одному кадру (§8.2).

F. c) Сцена `ABSTRACT_CUBES`: сетка кубов (Cloner Object над точками, напр. 16x14), вариант эффектора `lnk_cubes_effector.py` пишет в `MODATA_MATRIX` (масштаб/высота) и `MODATA_COLOR` те же значения `cell()`. Три анимации (глаза, спиннер, эквалайзер) = те же режимы 5-7, никакого второго кода. Для эквалайзера — нативный вариант на Sound Effector (`Omgsound`, режим STEP по клонам) с флагом «не проверено».

G. Аудио, ступенями: (1) ключуемая ручка `scr_level`; (2) офлайн-запекание спектра в PNG-полоску (ffmpeg + python, строки = полосы, столбцы = кадры), читается как секвенция, рендер-безопасно; (3) нативный Sound Effector/Xpresso Sound node с записью в `scr_level` — сначала прототип и проверка данными (§8.6).

Порядок: `lnk_pixel_anim.py` + тесты ASCII и замыкания петли → `lnk_pixel_rig.py` на одном экране → режимы 5-8 → bake → сцены E и F → аудио. Каждый шаг проверять данными (ASCII-превью, значения `MODATA_COLOR` на кадрах 0/N/2N), один начальный рендер при создании сцены (§8.6а).

## KEY FACTS
- Рабочий движок экрана уже есть: Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_screen_effector.py (8200 Б, Python Effector, MODATA_COLOR, режимы 0 Часы, 1 Шарик, 2 Выкл, 3 Картинка/секвенция, 4 Шум).
- В живой сцене Yogo_pro_keyboard_v008_anim_codex.c4d (C4D 2026.4, 30 fps, 0-420) в каждой из 3 клавиатур MODULE/SCREEN: scr_points (2016 точек = 48x42, шаг 0.617 мм) -> scr_cloner (Object, Instance Mode=Render Instance) -> scr_cell (куб 0.501x0.08x0.501) + scr_effect (Python Effector, user data 1 = ссылка на пульт) + scr_grid.
- Материал YKB_screen_cell = RS Standard Material + нода rsuserdatacolor с атрибутом RSMGColor на Emission (проверено дампом графа); emission_weight 9, scr_dim 0.04 по Context.
- Пульт BACKLIGHT_CONTROL в корне сцены; группа ЭКРАН ТАБЛО = user data id 48-74 (49 вкл, 50 режим, 61 файл, 62 секвенция, 63 fps, 64-74 пост-обработка/шум); IDS (имя -> id) зашит в код эффектора; тег backlight_scene будит эффекторы через SetDirty при любой смене ручки.
- Правило §4.12 Weaver/Правила.md: все ручки на нуле <ИМЯ>_CONTROL в корне, одна вкладка, группы-складки; на объектах рига ручек нет.
- Скрипта сборки рига экрана и User Data пульта в vault НЕТ (ищу scr_cloner/AddUserData по Yogo src - пусто): рига придётся пересобрать скриптом lnk_pixel_rig.py; единственный готовый add_ud() - в Cubes_system/C4D/src/cs_build.py.
- Режимов глаза-приветствие, спиннер, эквалайзер, взрыв частиц в эффекторе НЕТ; их надо добавить как чистые функции lnk_pixel_anim.py (периодические, замыкание петли).
- Pixbar_clock UV-путь: pxb_parts2.pixel_screen() (строка 83, 52x16 = 832 квадрата, UV центра ячейки), pxb_c4d.to_poly(uvs=), pxb_mats.screen() (строка 154, RS Emission <- Texture, weight 45). Минус: режимы Animation RS Texture нельзя задать из Python.
- Cubes_system_v003.c4d + cs_build.py: Cloner Grid + E_RANDOM/E_WAVE/E_SCATTER/E_FALL + линейное поле F_SWEEP + ключ Progress; по MoData кадр 0 разлетелось, кадр 90 собрано - готовая база explode/assemble.
- T_cubes_v010 S16: CLAUDE_WORD = на букву свой Cloner (Object/Vertex по 5x7 точкам) + Plain Effector с ключами - единственный пример кубов как пикселей; в src не сохранён.
- Сцены со взрывом частиц (C4D/Houdini) и запеканием в пиксельную секвенцию в vault не существует; ближайшее - Cubes_system scatter и Houdini Block_frame (прогресс-функция).
- Аудио-хуков в vault нет вообще (поиск sound/audio/Omgsound/xpresso/эквалайзер пуст). В C4D 2026.4 существуют c4d.Omgsound (Sound Effector, MGSOUNDEFFECTOR_*), Fsound, Xpresso Sound node GV_SOUND_FFT_BIN - нигде не использованы и в цепочке с Python-эффектором не проверены.
- Подводные камни эффектора: грид по round(p.x,2) ломается при шаге <0.01; арт часов/шарика заточен под 16x14*S; _CACHE картинок и длины секвенции не сбрасывается; экран проверен данными, не глазами (§8.6).
- Концепт-рефы Like_nothing (ref_headphones.png, ref_phone.png) уже показывают на экранах волну-эквалайзер и часы 10:28; тестовая картинка экрана - радужный смайлик Yogo/Assets/Textures/screen_test_48x42.png.
- Рекомендация: один модуль lnk_pixel_anim.py, два выхода (цвет экрана / высота кубов), один пульт LIKE_NOTHING_CONTROL; сплат частиц из MoData вместо рендера вида сверху (§4.4 запрещает RenderDocument с Redshift); аудио ступенями: ключуемая ручка scr_level, запечённый спектр-PNG, затем Sound Effector/Xpresso.
- Ограничения моей проверки: в C4D ничего не менял/не активировал, Pixbar_clock, Cubes_system v003 и T_cubes v010 не открывались (по ним только Context.md и src); Yogo-код читал из vault и живого документа.

## FILES
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_screen_effector.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_backlight_scene.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_backlight_effector.py
Projects/claude/Yogo_pro_keyboard/Context.md
Projects/claude/Yogo_pro_keyboard/C4D/Yogo_pro_keyboard_v008_anim_codex.c4d
Projects/claude/Yogo_pro_keyboard/Assets/Textures/screen_test_48x42.png
Projects/claude/Pixbar_clock/C4D/src/pxb_parts2.py
Projects/claude/Pixbar_clock/C4D/src/pxb_mats.py
Projects/claude/Pixbar_clock/C4D/src/pxb_c4d.py
Projects/claude/Pixbar_clock/C4D/src/pxb_pixels.py
Projects/claude/Pixbar_clock/Assets/Textures/display_clock_52x16.png
Projects/claude/Cubes_system/C4D/src/cs_build.py
Projects/claude/Cubes_system/C4D/Cubes_system_v003.c4d
Projects/claude/T_cubes/C4D/src/tc7_native.py
Projects/claude/T_cubes/C4D/src/tc4_anim.py
Projects/claude/T_cubes/C4D/T_cubes_v010.c4d
Projects/claude/T_cubes/Context.md
Projects/claude/Like_nothing/Context.md
Projects/claude/Like_nothing/Output/Refs/ref_phone.png
Projects/claude/Like_nothing/Output/Refs/ref_headphones.png
Weaver/Правила.md
weaver_claude/skills/c4d-animation.md
Projects/claude/Block_frame/Context.md