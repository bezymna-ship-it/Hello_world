## 0. Source, method, accuracy
- File: `Projects/claude/Like_nothing/Output/Refs/ref_mouse.png` (identical size to `Output/Images/nb2_mouse_draft_001.png`, 4 539 259 B). The viewer caps at 2000x1116. Layout: TL = 3/4, TR = straight top (nose LEFT), BL = side (nose LEFT), BR = underside (nose LEFT).
- I cropped each quadrant, contrast-stretched it, put a grid on it and read pixel coordinates. Scale taken from L = 125 mm: top 10.5 px/mm, side 11.16, underside 10.4 (px of a 2x crop).
- Raw proportions in the ref are L:W(hump):H = 125 : 72 : 42. CANONICAL = length unchanged, lateral x0.913, vertical x0.95, which gives the requested 125 x 66 x 40. Reading error is about 1 mm; the views disagree with each other by up to 3 mm.
- Not found: no mouse prompt or notes in the vault. `Prompts/` holds only headphone prompts. `Like_nothing/C4D/src` is empty. No mouse C4D scene exists.
- Project rules from `Agent/Inbox/Claude outputs/handoff_modeling_weaver.md` that apply here: units mm; product face looks to -Z; no logos or names, only digits and Latin letters; no UVs means TriPlanar (object space), UVs only on the glass/pixel matrix; moving parts sit under nulls on their axes; pixel matrix = one `pixel_screen` object with UV at each cell centre (Pixbar_clock trick; Yogo keyboard used 48x42 tiles, tile = 0.813 of pitch); USB-C 8.34 x 2.56 mm is the scale gauge.

## 1. Frame and canonical size
- Y up. Nose = -Z, tail = +Z. Origin on the desk plane under the sensor, so s = distance from nose and Z = s - 62.5. Mouse-LEFT (thumb side, red dot) = +X.
- The C4D "Right" viewport (camera at +X) reproduces the ref side view.
- Canonical size: **125.0 L x 66.0 W (hump, s = 89.5) x 40.0 H** (peak at s = 72, desk to glass top).

## 2. Shell loft
Plan half-width (mm) at s; these are control points for a symmetric plan spline:

| s | 0 | 1.1 | 3.3 | 7.1 | 11.4 | 16.2 | 23 | 36 | 52 | 62 | 71 | 81 | 89.5 | 100 | 109.5 | 115 | 121 | 124 | 125 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| half-w | 8.7 | 14.5 | 19.0 | 23.3 | 25.9 | 27.7 | 28.5 | 28.7 | 29.2 | 29.6 | 30.7 | 32.4 | 33.0 | 32.4 | 30.7 | 27.8 | 21.7 | 14.6 | 6 |

The nose is nearly square (front corner R about 12.5 mm). The sides are almost straight from s = 20 to 62, then flare 3.5 mm to the hump. The tail is a blunt half-ellipse (a = 35, b = 33).

Top silhouette z (mm, side view, centre line) at s:

| s | 0 | 2.7 | 13.4 | 26.9 | 35.8 | 44.8 | 53.8 | 59.1 | 62.7 | 71.7 | 80.7 | 89.6 | 98.6 | 107.5 | 112.9 | 116.5 | 121 | 124.1 | 125 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| z | 13.0 | 15.9 | 21.3 | 28.3 | 33.1 | 36.0 | 38.1 | 39.0 | 39.4 | 40.0 | 39.8 | 38.8 | 36.3 | 31.7 | 27.1 | 21.6 | 16.0 | 11.8 | 7.9 |

- Nose face, rear tail curve: (s, z) = (0.4, 10), (2.7, 6.6), (6.3, 2.4), (9, 0.9). Tail: (124, 4.9), (120, 2.9), (113, 1.3). Bottom corner radius is about 8 mm.
- Front block slope is about 24 degrees, convex (steeper at the nose, flatter by s = 55).

Cross-sections (SDS loft stations):
- Front block (s = 10 to 60): rounded-rectangle with a crown of R = 60 mm. Caps drop about 6 mm from the spine to the outer edge. The side wall is vertical down to the skirt.
- Hump (s = 62 to 100): top is a cylindrical dome of R = 43 mm. Edge sag is 8 mm at half-width 25 (z = 32) and 15 mm at half-width 33. The wall is vertical down to z = 16-18, which is the widest point. Below that it tucks in by 3 mm to the skirt at z = 2.5.
- Tail (s > 105): the section shrinks as the table above; keep the dome R = 43 scaled by the half-width ratio.
- Thumb hollow on both side walls: depth 1.5 mm, s = 40-80, z = 8-26.

Underside / skirt:
- Satin skirt ring, 2.5 mm tall, visible from the side.
- Ring width in plan varies: 5.7 mm at the waist (s = 33-53), 2.7 mm at the hump flanks, 6 mm at the tail, 6 mm at the nose.
- Inside the ring: 0.4 mm dark groove, then the base plate. This variable ring width is what gives the underside its S-shaped plate outline.

## 3. Front metal block (s = 0 to 62)
- Silver frame wraps the nose and both sides up to s = 36, 2.1 mm wide, tapering to a point. Nose lip is 3 mm tall (z = 10-13).
- Spine (central channel): half-width 5.2 (10.4 wide), flush with the caps, runs s = 1.4 to 62.
- **Left/right buttons**: caps X from +/-5.2 to +/-26.6 (21.4 wide), s = 1.4 to 61.5 (60 long). Seams 0.35 wide x 1.2 deep, over a dark liner.
  - Corner radii: front-outer 11, rear-outer 3.5, inner 1.0.
  - Surface: shallow dish 0.5 mm in the middle.
  - Split line is the long-axis centre (the spine).
  - Hinge is at the REAR edge: travel 0.8 mm at the nose (about 0.8 degrees), exaggerated to 2 degrees for render.
- **Scroll wheel**: centre s = 26.8 (Z = -35.7), X = 0.
  - D = 24, width 6.0, protrudes 4.5 mm above the spine. Visible chord 18.7 mm, matching the 18.6 measured.
  - Axle at Y = 20.8, axis along X. Slot 21.5 x 8.7, R 2, black recess.
  - Two smooth flanges 0.8 mm each; between them a diamond-pyramid knurl.
  - Knurl: pitch about 0.75 mm, 8 pyramids across the face, about 100 around. Do it as displacement or 4K normal, not geometry.
  - Mechanical detent 24 steps/rev (15 degrees each).
- **DPI button**: s = 49 (Z = -13.5), 11.4 long x 4.6 wide, R 2.3, pillow 1.8 mm above the spine (top about 38.8).
- White shell bridge: caps end at s = 61.5, the glass starts at s = 64.6, so there is a 3.1 mm strip.

## 4. Side buttons and red dot
- Both sides (mirrored), 2 per side: front s = 40-58, rear s = 59.5-78. Each is 18 long x 4.1 high, 1.0 mm proud, 1.0-1.5 mm gap between them, rear tip chamfered.
- Mid line follows the wall: (s, z) = (40, 18.1), (49, 21.0), (58.5, 24.0), (70, 25.2), (78, 24.4).
- Centres: front (X = +/-29.5, Y = 21.0, Z = -13.5); rear (X = +/-30.5, Y = 25.2, Z = +6.0). Travel is 0.5 mm along the wall normal.
- **Red dot**: ONE, on the +X wall behind the side buttons. s = 84 (Z = +21.5), Y = 23.7, X about +32.7, diameter 5.0, flush glossy lens (can be a status LED).
- Optional tiny status pictograms on the same wall at s = 23-30, z about 4, 0.3 mm laser etch, digits/letters only.

## 5. LED glass panel
- Plan: front edge s = 64.6 (Z = +2.1), flat for +/-19 with corner R 5.
- Half-width 25.0 up to s = 90, then 23.3 at 95, 21.7 at 100, 19.3 at 109.5, 14.6 at 115, 10.3 at 118, apex at s = 118.8. Size about 54.2 x 50, centre Z = +29.2.
- Convex cover 1.6 mm thick that wraps the shoulder. Its edge line is z = 34.5 (s = 63), 30.5 (s = 90), 26 (s = 100), 22 (s = 116).
- Surround: 1.0 mm satin-aluminium bezel with a 0.3 chamfer.
- Pixel grid: **44 (along Z) x 40 (across X) cells**, pitch 1.25, tile 1.02 (the Yogo ratio 0.813). Cells outside the glass outline are culled. Built as one `pixel_screen` object with a cell-centre UV tag plus a dark `pixel_grid` mask.
- Crosshair glyph: 11 x 11 big pixels, each 2 x 2 cells (pitch 2.5, tile 2.1). Four arms of 5 big pixels, with a 1-pixel gap at the centre (the centre is EMPTY). Span 27.5. Centred at X = 0, Z = +29.2.

## 6. Underside
Nose is left. Coordinates are canonical; X sign assumes the underside image is not mirrored.
- Sensor: stadium collar 22.2 x 15.2, mid ring 16.4 x 9.9, window 13 x 6.8 (dark glass with a visible chip). Centre s = 62, X = 0.
- Slide switch: stadium 10.3 x 4.9 at X = -17 (mouse right), Z = 0. Knurled knob, travel +/-2.2 along Z.
- Front skate: pill s = 8.5-21.8, +/-21.8 across, R 3.5, 0.7 mm thick.
- Rear skate: C-shaped arc following the tail outline offset inward by 5.5, thickness 7.5, rounded ends at s about 93 (X = +/-26), outer radius about 26.
- Label recess: s = 93-107, +/-12.3 across, 0.1 deep, R 2. Laser-etched text rotated 90 degrees: CE mark, WEEE bin, "MODEL" line. The ref text is garbled, so use ASCII digits/letters only.
- Nose port: USB-C (8.34 x 2.56) centred, Y about 6.5, inside a 13 x 4.8 satin shroud recessed 0.8.

## 7. Part hierarchy and materials
```
MOUSE (null, origin = desk, under sensor)
 +- CTRL (null, user data: BTN_L/R, WHEEL, DPI, SIDE_x, SWITCH, LED_MODE, flake, frost)
 +- SHELL_GRP
 |   +- shell_body [SDS]      white matte soft-touch, powder-coat + fine metal flake
 |   +- inner_liner           near-black matte, hides seams
 |   +- skirt_ring [SDS]      satin silver aluminium
 |   +- front_frame [SDS]     satin silver
 |   +- spine [SDS]           bead-blasted aluminium, rough 0.45
 +- BTN_L_PIVOT -> btn_L_cap [SDS]  satin aluminium, anisotropic along Z, rough 0.3
 +- BTN_R_PIVOT -> btn_R_cap [SDS]
 +- WHEEL_PIVOT -> wheel_flanges, wheel_knurl   steel, rough 0.35, knurl displacement/normal
 +- wheel_slot, wheel_axle (fixed)
 +- DPI_PIVOT -> dpi_button [SDS]  satin aluminium
 +- SIDE_L_FWD_PIVOT / SIDE_L_BACK_PIVOT / SIDE_R_FWD_PIVOT / SIDE_R_BACK_PIVOT -> side_btn_x  satin aluminium
 +- LED_GRP: glass_cover (smoked, rough about 0.18, IOR 1.5), glass_bezel (satin aluminium),
 |            pixel_screen (UV per cell centre, emission from texture), pixel_grid, led_backplate
 +- red_dot_lens (glossy red, optional emission)
 +- PORT_GRP: usb_c_shroud, usb_c_cavity
 +- BOTTOM_GRP: base_plate (light bead-blast), skate_front, skate_rear (PTFE, rough 0.55),
                sensor_collar, sensor_window, SWITCH_PIVOT -> switch_knob, label_panel
```
- Shell is one white SDS piece, not separate shells; the silver parts are separate objects.
- Edge radii for SDS: shell silhouette R 2.5-3.5 (soft); silver parts (caps, frame, side buttons, DPI) R 0.4 with a support loop at d = 1.7R and at least 6 segments per 90 degrees; seam gap 0.35 x 1.2; glass bezel chamfer 0.3; wheel flange 0.25; sensor collar 0.2.

## 8. Tactile bumps instead of buttons (concept)
- All "buttons" are low organic pillows with no hard bezel: side lozenges 0.8-1.0 mm proud with R of at least 1.2 mm falloff; DPI pillow +1.8 mm; caps keep only a thin split line.
- OPTIONAL, not in the ref: a 2 mm / 0.35 mm tactile index bump on the bridge strip at Z = +0.5, X = +/-12, so the thumb can find the glass.
- The "+" crosshair can double as a D-pad.

## 9. Animation pivots (nulls on axes)
- BTN_L_PIVOT: X = +15.9, Y = 36.0, Z = -2.0, axis X, nose down 0.8 degrees (2 for render).
- BTN_R_PIVOT: X = -15.9, same Y and Z.
- WHEEL_PIVOT: X = 0, Y = 20.8, Z = -35.7, axis X, 15 degrees per detent.
- DPI_PIVOT: X = 0, Y = 37.0, Z = -13.5, translate -Y 0.5.
- SIDE_*: centres from section 4; translate 0.5 along the wall normal.
- SWITCH_PIVOT: X = -17, Y = 0.7, Z = 0, slide +/-2.2 along Z.
- Check the rotation sign in C4D (left-handed).

## 10. Inconsistencies and canonical decisions
1. **3/4 vs the other three views.** The 3/4 view shows the glass running from the nose to the hump and replacing the left button (one cap only, an asymmetric front). Top, side and underside all show two caps and the glass only behind them. CANONICAL: top view. In the 3/4 the glass also gets a visible silver bezel, hence the 1.0 mm bezel.
2. **Red dot count.** The top view shows two dots (the side one at s = 84 and a second on the tail centre line at s about 123). The 3/4 and side views show only the side dot. CANONICAL: one dot on the +X wall; the tail dot is dropped.
3. **Side buttons.** Top and underside show them on both sides; 3/4 and side see only one side. CANONICAL: 2 per side, 4 total (the right pair can be dropped).
4. **Proportions.** W:L is 0.58 in the top view and 0.56 in the underside; H:L is 0.34-0.35 in the side view. CANONICAL: 125 x 66 x 40.
5. **Glass vs shoulder.** The plan footprint (half-width 24.3) and the side view (black down to z = 32 at s = 72) do not fit a flat panel. CANONICAL: the crown R = 43 dome with half-width 25.
6. **Wheel.** Looks bigger and thicker in the 3/4 than in the top view. CANONICAL: D = 24 x 6 wide.
7. **Plan waist.** The underside plate outline is S-shaped, while the top outline is almost straight. CANONICAL: straight plan plus a variable skirt ring width.
8. **Text and engravings** are garbled in every view. CANONICAL: replace with ASCII only. Three tick marks at the rear side of the glass (s about 91, z 36-38) appear only in the side view: optional.
9. **Underside mirroring** cannot be verified; the switch is placed on the mouse right.

## KEY FACTS
- Ref file: Projects/claude/Like_nothing/Output/Refs/ref_mouse.png (2x2: TL 3/4, TR top, BL side, BR underside); viewer returns 2000x1116 max; no mouse prompt note exists in the vault and Like_nothing/C4D/src is empty
- Canonical size 125.0 L x 66.0 W (hump at s=89.5 from nose) x 40.0 H (peak s=72); ref raw proportions 125:72:42, scaled lateral x0.913 and vertical x0.95
- Axes: Y up, nose -Z, tail +Z, origin on desk under sensor (Z = s - 62.5), mouse-left (red dot side) = +X; C4D Right viewport reproduces the ref side view; units mm
- Plan half-width (s mm: half-w): 0:8.7, 3.3:19, 11.4:25.9, 23:28.5, 52:29.2, 71:30.7, 89.5:33.0, 109.5:30.7, 121:21.7, 125:6; nose nearly square R~12.5
- Top silhouette z (s: z): 0:13.0, 26.9:28.3, 44.8:36.0, 59.1:39.0, 71.7:40.0, 89.6:38.8, 107.5:31.7, 116.5:21.6, 124.1:11.8; hump top is a dome R=43, front block crown R=60
- Front block: 2 caps X 5.2..26.6 (21.4 wide), s 1.4..61.5, spine 10.4 wide, frame 2.1 wide ending at s=36, seams 0.35 x 1.2; button hinge at rear edge, travel 0.8 mm at nose (~0.8 deg; 2 deg for render)
- Scroll wheel: centre s=26.8 (Z=-35.7), D=24, width 6.0, protrudes 4.5, axle Y=20.8 axis X; diamond-pyramid knurl pitch ~0.75 mm (~8 across, ~100 around, via displacement/normal), 24 detents/rev; slot 21.5x8.7
- DPI button: s=49 (Z=-13.5), 11.4 x 4.6, pillow +1.8 mm above spine (pivot Y=37.0, press -0.5 mm)
- Side buttons: 2 per side mirrored, front s=40-58, rear s=59.5-78, each 18 x 4.1, 1.0 mm proud, 0.5 mm travel along wall normal; centres (X=+/-29.5,Y=21,Z=-13.5) and (+/-30.5,25.2,+6)
- Red dot: ONE, +X wall, s=84 (Z=+21.5), Y=23.7, diameter 5.0 flush glossy lens; the tail dot in the top view is dropped
- LED glass: s=64.6..118.8 (Z +2.1..+56.3), half-width 25.0, 1.6 mm convex cover with 1.0 mm aluminium bezel; pixel_screen grid 44 x 40 cells, pitch 1.25, tile 1.02 (0.813 ratio as in Yogo keyboard)
- Crosshair glyph: 11 x 11 big pixels (2x2 cells each, pitch 2.5, tile 2.1), four arms of 5 plus an EMPTY centre pixel, span 27.5 mm, centred X=0, Z=+29.2
- Underside: sensor stadium collar 22.2x15.2 / window 13x6.8 at s=62; slide switch at X=-17 Z=0 (travel +/-2.2); front skate pill s 8.5-21.8 x 43.6 across; rear skate C-arc 7.5 thick R~26; label recess s 93-107, 24.6 across; USB-C 8.34x2.56 on the nose in a 13x4.8 shroud
- Underside outline S-shape comes from a variable satin skirt ring (5.7 mm at waist, 2.7 at hump flanks, 6 at tail/nose); skirt 2.5 mm tall; skates 0.7 mm proud
- Biggest inconsistency: the 3/4 view shows the glass from nose to hump replacing the left button; top/side/underside show two caps with glass only behind them. Canonical follows the top view
- Other flags: red dot count (2 in top view), side buttons on both sides (top/underside) vs one side (3/4, side), glass shoulder wrap vs plan footprint, wheel size, garbled text (use ASCII only)
- SDS edge numbers: shell R 2.5-3.5; silver parts R 0.4 with support loop d=1.7R and 6+ segments per 90 deg; glass bezel chamfer 0.3; wheel flange 0.25; sensor collar 0.2
- Materials: shell white matte soft-touch with fine metal flake; caps/frame/side buttons/DPI satin aluminium anisotropic rough 0.3; spine bead-blasted rough 0.45; wheel steel knurl; glass smoked rough ~0.18 IOR 1.5; skates PTFE rough 0.55; liner near-black; TriPlanar except UV on glass/pixel_screen

## FILES
Projects/claude/Like_nothing/Output/Refs/ref_mouse.png
Projects/claude/Like_nothing/Context.md
Agent/Inbox/Claude outputs/handoff_modeling_weaver.md
weaver_claude/skills/references/c4d-cases.md
weaver_claude/skills/c4d-modeling.md
Projects/claude/Yogo_pro_keyboard/Context.md
Projects/claude/Pixbar_clock/Context.md