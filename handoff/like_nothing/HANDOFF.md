# Like_nothing — передача контекста в новую сессию

Дата: 2026-10-02. Пользователь пишет по-русски, любит короткие ответы. Сессия-источник потеряла Bridge (404), поэтому
этот файл написан из облака; всё, что лежит в хранилище Weaver (код `lnk_*`, сцены, картинки), на ПК цело.
Первым делом новая сессия должна **дописать суть этого файла в `Projects/claude/Like_nothing/Context.md`**
(карточка Weaver; в облаке я этого сделать не мог).

## 0. Что просили (крупная задача, "дерзай")

Собрать сцену Cinema 4D 2026.4 + Redshift с набором устройств в стиле Nothing: **наушники (большие, с ободком), телефон,
клавиатура, игровая мышь**. Студийный свет (нужен предмет, не пространство), две расцветки: **A — белый металл**,
**B — графит**.
- Детальность каждой модели, шейдеры высокого качества, уровень Apple close-up. Текстуры 4K (GSG-библиотека или
  генерация; Magnific upscale можно).
- Белая металлическая основа с металлической крошкой, LED вместо кнопок, мелкие тактильные выступы (напр. громкость
  на наушниках — без кнопок), защитное слегка матовое стекло над LED у наушников.
- Всё под SubDiv; "те самые фасочки" (аккуратные микрофаски/скругления) — найти лучший open-source skill
  (результат ресёрча: `scout/skills.md`).
- Процедурность и анимационная иерархия + навигация в сцене.
- Сохранить в Weaver как **BASE-шаблон** (render low/medium; bucket 512; низкий render threshold 0.3; без automatic
  sampling; ориентироваться на то, что пользователь выставлял сам).
- У каждой модели — управляемый "продвинутый" шейдер (ручки), если нельзя — сцены для управления; показать, как с этим работать.
- Сцена **взрыва частиц → последовательность пикселей для шейдера**; сцена **абстрактных кубиков** (приветствие с
  подмигивающими глазками; лоадер-спиннер из вращающихся кубов; стандартный эквалайзер-луп; шейдер анимации, готовый
  к звуку); любая идея визуализации интерфейса.

## 1. Правила Weaver, которые соблюдать
- Ручки только на **одном** корневом null `<NAME>_CONTROL` (§4.12) — тут `LIKE_NOTHING_CONTROL`.
- Python-вывод только ASCII (§4.3). Рендеры делает пользователь; финальные/тяжёлые — спросить (§8.6–8.7);
  превью-рендеры для проверки в этой сессии делались через `render_preview_image` (ок).
- Пастельная палитра §11.8 к белой/графитовой теме не относится.
- Свои ядра с префиксом `lnk_`; **не менять исходники Yogo/Pixbar**; один документ на имя; чужие документы не трогать.
- Показать/сообщать пользователю коротко, по-русски.

## 2. Где что лежит (всё в хранилище `G:\todoist_obsidian_claude\`)
- Проект: `Projects/claude/Like_nothing/` — `Context.md` (карточка), `Output/Images/` (nb2_*: наушники A 4K 5504x3072,
  v2 draft 2K, phone/mouse/keyboard_v2 drafts 2752x1536), `Output/Refs/` (ref_*.png, `site/`), `Prompts/`, `Passes/`,
  `Assets/`, `C4D/`.
- Сцены: `C4D/Like_nothing_v001.c4d` (сохранён один раз после базы — **без** изделий и материалов),
  `C4D/Like_nothing_BASE_v001.c4d` (чистая база). Шаблон: `Agent/Templates/C4D_base_scene/` (`.c4d`, `README.md`, `src/`
  — копии только ранних модулей: geo, kit, c4d, ctl, base, cc, edge, parts; поздние lnk_hs/mats/pixel/hp/ph/ms/scene
  **ещё не скопированы**).
- Код: `Projects/claude/Like_nothing/C4D/src/` (список в §4).
- Yogo (Yogo_pro_keyboard_v008_anim_codex.c4d) — отдельный документ, не трогать без запроса. Там на BACKLIGHT_CONTROL
  74 user data (экраны-смайлики/шум); подсветка стоит в красном тесте. Старые значения: main k0 mode 5 c1 white
  bright 0.52 react on; keyboard1 mode 5 peach (0.65,0.56,0.38) bright 1.0 react off; keyboard2 mode 1 mint
  (0.4,0.79,0.51) bright 1.0 react on; all_bright 0.35. Если пользователь попросит — вернуть.
- Telegram-бот (`Studio_bridge/weaver_bridge/watcher/weaver_watcher.py`): запрос последней картинки/видео по меню,
  авто-рассылка выключена (`auto_media` False). Не менять без запроса.
- Спеки изделий и исследования — в этом каталоге `scout/` (в облаке; в хранилище их может не быть — **положить в
  `Projects/claude/Like_nothing/Assets/` или Context.md**): ref_headphones/phone/mouse/keyboard (размеры, профиль,
  материалы), apple_look (свет/материалы), gsg (какие коды материалов брать), render_presets, cubes_particles
  (взрыв частиц и кубики), skills (фасочки).

## 3. Состояние на момент обрыва
Сделано и проверено (в **несохранённом** состоянии открытого документа Like_nothing_v001):
- База: `lnk_base.build(name)` — документ в мм, 30 fps, 0–300; наборы рендера **LNK_LOW/MID/HERO**; слои GEO/STUDIO/NAV/RIG;
  `LIKE_NOTHING_CONTROL` (ручки: colourway, screens_on, screens_bright, studio_gain, dome_mult, NAV); STUDIO (lights
  key/strip L,R/top/dome, `cyc`, cameras CAM_LINEUP/HERO/FRONT/SIDE/TOP/MACRO); PRODUCTS (HEADPHONES/PHONE/KEYBOARD/MOUSE);
  NAV (текстовые сплайны). Порядок: CONTROL, STUDIO, PRODUCTS, NAV; активный LOW.
- Рендер-пресеты (подтверждены пользователем): bucket 512, automatic sampling **OFF**, Advanced mode.
  LOW 960x540, thr 0.3, samples 4/32, BF16, depths 6/2/5/16, OptiX. MID 1920x1080, thr 0.08, 8/96, BF32, 8/4/6/32.
  HERO 3840x2160, thr 0.015, 16/512, BF128, 12/5/8/64, OIDN high.
- Материалы `lnk_mats.build_all(doc, "A"|"B")` → `LNK_<key>_<A|B>`: metal_body, metal_trim, alu_hw, knurl, polymer, leather,
  fabric, rubber, black, red, silicone, silicone_trans, glass_smoked, glass_black, lens, led_tile. A/B (графит) уже
  поддержаны параметрами; существующие имена переиспользуются (перед пересборкой с изменениями удалить материал).
  GSG-коды: MC001_A141 (белый бластед металл), MC001_A140 (полир. отделка), MC005_A069 (hardware), MC005_A041 (knurl),
  MC001_A315 (белый полимер), MC067_A036 (knit), MC001_A308 (резина); нормали MC058_A12/A65. Папка GSG:
  `E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library\materials`.
- Пиксельная система: `lnk_pixel_anim` (режимы 0 часы,1 шарик,2 выкл,3 картинка/секвенция,4 шум,5 глазки+подмигивание,
  6 спиннер,7 эквалайзер (вход `pix_eq_level` под звук/ключи, `pix_eq_mix`), 8 пульс-кольца; петли проверены) +
  `lnk_pixel` (MoGraph Cloner Object/Vertex/RenderInstance + Python Effector → `MODATA_COLOR` → RS Color User Data
  `RSMGColor` → emission; Python-тег "wake" на контрольном null обновляет эффекторы при изменении ручек).
- Наушники (`lnk_hp`, `lnk_hp_scene`) — собраны, экраны на чашках (L часы, R эквалайзер).
- Телефон (`lnk_ph`, `lnk_ph_scene`) — собран, экран-матрица на острове; рендер нормальный, но пересвет.
- Мышь (`lnk_ms`, `lnk_ms_scene`) — **геометрия проверена** (21 деталь, закрыты, только квады), собрана в сцене,
  рендер показал корректную форму. LED-тайлы выровнены по поверхности стекла (параметры `y_fn`, `align` в
  `lnk_pixel.make_screen`). Вид самих пикселей на мыши **не проверен**.
- Раскладка по X: HEADPHONES −480, PHONE −170 (лежит на фронт. стекле, `pose(root, flat=True, floor_y=4.3)`),
  KEYBOARD 120 (пусто), MOUSE 430 (floor_y 0.7).

## 4. Модули (`Projects/claude/Like_nothing/C4D/src/`), порядок reload
`lnk_geo, lnk_kit, lnk_c4d, lnk_ctl, lnk_cc, lnk_edge, lnk_parts, lnk_hs, lnk_gsg, lnk_mats, lnk_pixel_anim, lnk_pixel,
lnk_scene, lnk_base, lnk_hp, lnk_hp_scene, lnk_ph, lnk_ph_scene, lnk_ms, lnk_ms_scene`.
`sys.path.insert(0, r"G:\todoist_obsidian_claude\Projects\claude\Like_nothing\C4D\src")`.
- Ядро: чисто-питоновское квад-ядро (копия Logitech_IRIS `ir_geo/ir_kit/ir_c4d` → `lnk_geo/lnk_kit/lnk_c4d`): RR/RR4,
  `profile_solid`, `plate_sds`, sweep, lathe, knurl. `lnk_cc` — G2 клотоида-дуга-клотоида угол; `lnk_edge` — fit_stack/
  fillet/chamfer, устойчивые к SDS кольца рёбер. `lnk_hs`: `slab_hs, ring_solid, rounded_section, disc_hs, pill, squircle,
  edge_report, to_wall, louvre_xz`. `lnk_parts`: dome, knurl_wheel, slot_section, blend_band, hold_poly, smootherstep.
- `lnk_scene.build(doc, root_name, NODES, all_parts, mats)` — универсальный сборщик: null-узлы с пивотами + SDS-объекты
  с кейджем (editor 2 / render 3, Phong на кейдже, материал на SDS).
- `lnk_ph_scene.build(doc, mats, panel=None, root_name="PHONE")`, `lnk_ms_scene.build(doc, mats, panel=None,
  root_name="MOUSE")`, `lnk_hp_scene.build/add_screens` (сигнатуры смотреть в файле).
- Панель: `lnk_ctl.Panel(null)`: `.group(name,key)`, `.add(key,name,kind,default,lo,hi,step,cycle=…)`, `.id(key)`,
  `.get/.set`. Kinds: float,int,bool,color,cycle,string,file. Эффекторы получают `IDS` (ключ → user-data id) внутри кода.
- `lnk_pixel.add_controls(P, [(key,label,default_mode,(r,g,b)), ...])` добавляет общую группу `pix_*` + группу каждого экрана
  (`<key>_on/_mode/_col/_bright`). Для мыши группу добавлял вручную (`mouse_on/_mode/_col/_bright`, режим 8).
  `make_screen(doc,panel,key,parent,nx,ny,pitch,cells,mat,tile_frac,depth,flipx,name,y_fn,align)`; `place(scr,O,U,V,N)`.
- Мышь: `lnk_ms.NODES` (btn_L/R, wheel, dpi, side_*, ms_led), экран 40x44 pitch 1.25, `led_cells/tile_y`; `place` с
  `O=(0,0,c)`, `U=(-1,0,0)`, `V=(0,0,-1)`, `N=(0,1,0)`, `c = GLASS_S0+2-S0+(NROW-1)/2*PITCH`.

## 5. Как восстановить сцену, если документ потерян
1. Открыть `Like_nothing_v001.c4d` (база) или `lnk_base.build("Like_nothing_v001")`.
2. `mats = lnk_mats.build_all(doc,"A")`; `P = lnk_ctl.Panel(doc.SearchObject("LIKE_NOTHING_CONTROL"))`;
   если нет `P.id("pix_time")` — `lnk_pixel.add_controls(P, screens)` (hpL, hpR, phone, kb, mouse).
3. `lnk_hp_scene.build(...)` + `add_screens`; `lnk_ph_scene.build(doc,mats,P)` + `pose`; `lnk_ms_scene.build(doc,mats,P)` + `pose`.
   Корни: HEADPHONES.x=−480, PHONE.x=−170, KEYBOARD.x=120, MOUSE.x=430.
4. Камеры tmp_cam*/tmp_cam2/tmp_cam_ms — только временные; перед сохранением удалить. `RDATA_SAVEIMAGE` должен быть off.

## 6. Что осталось (по приоритету)
1. **Мышь:** крупный план LED (режим 8/1/5 — видно ли пиксели), корпус перевести на `metal_body` (по спеку:
   белый матовый soft-touch с тонкой металлической крошкой), стыки/швы (зазор 0.35x1.2 между крышками уже в габаритах,
   пояс/шов основания не сделан).
2. **Свет:** сильный пересвет. Нужно dome ≈0.5 (ручка `dome_mult`), top ≈0.35, key ≈1.0; polymer tint 1.0. Обновить
   дефолты в `lnk_base`. Рецепт студийного света — `scout/apple_look.md`.
3. **Клавиатура** (не построена): 75% раскладка ~320x120x9 мм; **весь LED-экран под одной силиконовой шкурой**, клавиши очень низкие
   (2 мм купола) — как у панелей для саунд-дизайнеров; большая пиксельная сетка (~128x44), ручка, красная точка. Спек —
   `scout/ref_keyboard.md`. Ориентировать вперёд −Z (§4.11).
4. **Расцветка B (графит):** материалы уже есть (`build_all(doc,"B")`); нужны Takes COLOURWAY_A/B с подменой Texture-тегов
   и использование ручки `colourway`.
5. **Ручки/анимация:** на `LIKE_NOTHING_CONTROL` группы по изделиям (слайды/раскладка наушников, наклон/складка, колёсико,
   нажатия куполов, взрыв); навигация (Takes/камеры по изделиям, слои), `flipx` для L-чашки — в `lnk_hp_scene.add_screens` до сих пор
   `flipx=(side<0)`, должно быть False.
6. **Сцены-дополнения:** PARTICLES_TO_PIXELS (взрыв → запечь PNG-секвенцию из MoData splat; режим 3 проигрывает), ABSTRACT_CUBES
   (глазки с подмигиванием, спиннер, эквалайзер с `pix_eq_level` под звук). Идеи — `scout/cubes_particles.md`.
7. **Сохранение:** `Like_nothing_v002.c4d`; скопировать все новые `lnk_*` в `Agent/Templates/C4D_base_scene/src`; обновить
   README шаблона и Context.md (состояние, решения, правила рендера, GSG, пиксельная система, как пользоваться ручками).
8. Magnific/Seedream: Seedream 5 нода так и не запускалась; идеи по концептам (без студийных ламп в кадре, настоящий профиль,
   экраны включены) не заказывались. Magnific в облачной сессии был недоступен (403 прокси) — пользователь запускает у себя.

## 7. Грабли C4D / API, уже пойманные
- Не гонять в `exec_python` попиксельные циклы (подвесили C4D, guard перезапустил, Yogo перегрузился с диска).
- Всегда искать документ по имени и `SetActiveDocument`; рендер идёт по активному документу. `render_preview_image`:
  `renderer="redshift"`, `quality="final"`; запустить → сразу вернуть активным Yogo → собрать картинку повторным вызовом.
- **Эйлеры камеры C4D:** `H = atan2(-f.x, f.z)`, `P = asin(f.y)` (взгляд вниз — отрицательный pitch). Иначе камера смотрит в сторону.
- `SetMl`, не `SetRelMatrix`. Созданные через `c4d.BaseObject` cloner/effector — вызывать `Message(c4d.MSG_MENUPREPARE, doc)`.
- MoData cloner доступна только после `doc.ExecutePasses(...)`.
- Cloner Object mode с `MG_OBJECT_ALIGN`: клон выравнивает **ось Z** по нормали вершины; у точек-объекта должны быть полигоны,
  нормаль вверх (порядок `CPolygon(a,b,c,d)` для сетки с x вправо, z вниз по j). Куб клона тонкий по Z.
- Redshift Node Material: `maxon.GraphDescription.ApplyDescription` + прямые правки графа (`AddChild/Connect`). Bump Blender
  через метки Description не создаётся — только `AddChild` с id портов.
- Эквалайзер/часы L-чашки отображались зеркально при `flipx=True` → FLIPX=False.
- Освещение: dome слишком сильный, заднюю грань телефона пересвечивает.
- LED: emission weight 40, `glass_smoked` refr_color 0.34, refr_rough 0.12, refl_rough 0.10.
