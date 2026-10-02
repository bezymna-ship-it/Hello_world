# Keyboard modelling spec (from ref_keyboard_v2.png)

Source: `Projects/claude/Like_nothing/Output/Refs/ref_keyboard_v2.png`. The path in the task text omits `Output/`. It is the same size (4,819,472 B) as `Output/Images/nb2_keyboard_v2_ledpanel_001.png`. It is a 2x2 AI mosaic: 3/4, top, low side, macro. I upscaled and measured the top view in pixels. Calibration: 1u key pitch = 48.8 px = 19.05 mm, so 0.39 mm/px, error about 3%. The LED pitch measured 8.0-8.14 px, which is 6.0 LED cells per key unit. So the pitch is 3.175 mm (1/8", U/6), and every number below is snapped to that module. Nothing was changed in C4D or the vault. Scratch crops are in the scratchpad only.

## 1. Canonical design
- **Layout:** 5 rows x 16u, 68 keys, ANSI. This is exactly `ykb_layout.ROWS[1:]` (Yogo 75 without the F-row). There is no F-row and no Esc in any view. The full-width LED strip replaces the F-row. This contradicts the brief's "75% with function row".
- **Top of the device:** one black glossy glass panel in a slim white-aluminium bezel. The whole panel is an LED matrix.
- **Skin:** one translucent frosted silicone skin over the key field, with low pillow keys.
- **Controls:** one knurled knob and one red dot at the right end of the strip. No other buttons. The 4 right-column keys are blank soft keys.

## 2. Inconsistencies between views, and the choice
| Issue | Views | Canonical |
|---|---|---|
| Depth and thickness | The ref gives 323x148 outer and 11.4 mm body. The brief hint was 320x120x9. | Use the ref. A 120 mm depth would leave only about 13 mm for the strip, so the strip would have to go. |
| Key height | Brief says 2 mm. Side view shows about 3.5 mm over the glass. | Rise 2.25 mm over the valley floor (skin 1.0 mm + 0.3 mm gap = 3.55 mm over glass). |
| Knob | Top and 3/4 views show about 14 mm diameter. Side view shows about 5 mm. | Ø14 x 6 mm. |
| Legends | Top: thin square pixel/LCD font. 3/4: faint. Macro: glowing white dot-matrix. | Emissive white 5x7 dot-matrix. |
| Skin tint | Top: grey over black. 3/4: near white. Macro: milky with internal glow. | Milky white, light-scattering, glow visible inside the keys. |
| LEDs under the skin | Macro: LEDs glow under every key. Top: black. | The full panel is LEDs. Key zone dim by default, per-key glow on demand. |
| Space bar | Top: 6.1u. 3/4 looks about 7u. | 6.25u. |
| Key shape | Top: soft ring. 3/4: flat boxes. Macro: pillow with flat plateau and flared foot. | Macro shape. |
| Strip content | Rainbow extent differs between views. | Animated content, not geometry. |

The rainbow fades in the outer rows, and "10:28" sits at the right end of the strip.

## 3. Dimensions (mm)
Axes follow Yogo: Y up, X right, front = -Z. Origin is the centre of the bezel footprint. y=0 is the glass top.
- **Bezel:** outer 322.5 x 147.9, plan R8. Top face 2.5 wide. Wall y +0.4 to -7.2 (7.6 high). Measured in the ref: 323.6 x 146.3.
- **Base plate:** black, 320.9 x 146.3 (inset 0.8), 3.8 thick (y -7.2 to -11.0). Bottom edge R1.2. Optional 1.5 mm underside sag.
- **Glass:** 317.5 x 142.875 x 1.1, corner R5.5. Top at y=0, rim at +0.4, edge R0.4.
- **LED matrix:** 100 x 45 cells = 4500. Pitch 3.175, cell 2.54 (0.8 of pitch), emissive plane y=-1.5, black mask grid above it.
  - Margins 2 px on every side.
  - Strip: cols 2-91, rows 2-10 = 90 x 9 px (285.75 x 28.58 mm), x -152.4 to +133.35, z +36.51 to +65.09.
  - Gap: rows 11-12.
  - Key zone: cols 2-97, rows 13-42 (96 x 30 px). Each 1u key covers a 6x6 px block.
- **Key field and skin footprint:** 304.8 x 95.25 (16u x 5u). x ±152.4, z -65.09 to +30.16. Row centres z = +20.64, +1.59, -17.46, -36.51, -55.56. Skin plan corner R4.
- **Knob:** Ø14 x 6 above glass, at x +146.05, z +55.56 (col 96, row 5). Dark recess ring Ø17. Diamond knurl, brushed top.
- **Red dot:** Ø3.5, 0.4 mm dome, at x +146.05, z +42.86 (row 9), directly in front of the knob.
- **Clock "HH:MM":** 3x5-px digits, 1-px gaps, 1-px colon. It spans 18 cols (74-91), rows 4-8.

**Bezel section** (x outward from the glass edge, y up):
1. (0,+0.1) to (0.3,+0.4): inner chamfer 0.3.
2. Top flat to (1.8,+0.4).
3. Outer diamond-cut chamfer 0.7 at 45 degrees to (2.5,-0.3).
4. Vertical wall to (2.5,-6.7).
5. Bottom chamfer 0.5.

Make the chamfer a separate polygon selection with a polished material. Put hold loops of 0.15 mm at each chamfer edge. Sweep the section along a rounded-rect path with 6 or more segments per corner. Glass seats on a ledge at y=-1.1.

## 4. Key layout (u)
- **R1:** 13x1, backspace 2, 1.
- **R2:** 1.5, 12x1, 1.5, 1.
- **R3:** 1.75, 11x1, 2.25, 1.
- **R4:** 2.25, 10x1, 1.75, Up 1, 1.
- **R5:** 1.25 x3, space 6.25, 1 x3, then ← ↓ → (1 each). Up sits above ↓.

Counts: 57 x 1u, 3 x 1.25u, 2 x 1.5u, 2 x 1.75u, 1 x 2u, 2 x 2.25u, 1 x 6.25u = 68 keys. The widths sum to 80u.

**Legends:** 51 keys carry legends (26 letters, 21 dual-legend symbol keys, 4 arrow triangles). 17 keys are blank: backspace, the 4 right-column keys, tab, caps, enter, both shifts, ctrl, opt, cmd, space, rcmd, fn, ropt.
- Dual legends are 5x5 dots at 0.75 mm pitch, symbol above digit.
- Singles are 5x7 dots at 0.9 mm pitch (4.5 x 6.3 mm), taken from a bitmap font.
- Each lit dot is a 0.7 mm quad ray-conformed to the key top. Reuse the approach of `ykb_legend_fit.fit`.

## 5. Skin
One piece. Keys are not separate bodies.

**Key profile.** Distance is measured from the key footprint edge (key footprint = w x 19.05 minus 1.6 mm for the valley; 17.45 x 17.45 for 1u). Heights are above the valley floor, whose top is at y=1.30.

| Point | Inset d | Height h | Role |
|---|---|---|---|
| P0 | -0.80 | 0.00 | valley centreline, shared seam |
| P1 | -0.30 | 0.00 | floor hold |
| P2 | +0.20 | 0.10 | foot flare |
| P3 | +0.80 | 0.95 | wall (about 55 degrees) |
| P4 | +1.30 | 1.85 | shoulder, lower hold |
| P5 | +2.00 | 2.25 | plateau edge |

The plateau interior has a 0.15 mm crown (cylindrical for keys of 2u or more), so the top is at y=3.70. The cage is pre-rounded, so SDS gives about a 1.5 mm shoulder without creases. Plan corner radius grows with height from 3.4 to 4.2 (Yogo KC v3 values). Valley floor is 1.0 mm wide. Underside is flat at y=0.3.

**Approaches compared**
- **Heightfield or displacement from a key mask (100x45 or finer):** fast layout previs. Rejected for the final: not an SDS cage, edges soft, no per-key deform weights, texture swimming.
- **Separate dome per key on a sheet:** visible seam, not one piece.
- **Recommended: ring-loft tiles welded on the valley centreline, one SDS cage.**
- **Fallback:** a global tensor grid, all valence 4, about 45k quads. Use it if shading artifacts appear at valley crossings.

**Algorithm** (reuse the `ykb_geo` kernel: `RR`, `map_norm`, `Mesh.ring/band`, `coons_grid`, `panel`)
1. Lattice L = U/4 = 4.7625 mm. Every key edge is a multiple of 0.25u, so staggered rows share nodes with no T-junction problems.
2. For each key, make 6 rounded-rect rings R0..R5. R0 is the cell rectangle (r=0). R1..R5 are the profile table above, with `outline.offset(-d)`. Use 4w nodes per horizontal side and 4 per vertical side on every ring, via `G.map_ring(norm, outline)`.
3. Bands R0-R1, R1-R2, R2-R3, R3-R4, R4-R5 are quads. Fill R5 with a Coons grid (4w x 4). Set plateau height = 2.25 + crown(rho), using `rr_rho` as in `ykb_parts.keycap_dish`, with the sign flipped.
4. Weld all points by quantised (x,y,z) with tolerance 1e-4. This merges the R0 nodes of neighbouring tiles.
5. Pull the 4 outer corner R0 nodes to the R4 arc.
6. Close the cage: add a 3-ring rolled lip (R0.4) around the outside and a flat underside at y=0.3 from `panel()`. This closed solid keeps subsurface scattering working.
7. Write per-point data: `key_id[v]`, `ring_w[v]` (R5/plateau 1.0, R4 0.85, R3 0.5, R2 0.12, R1/R0 0), planar UV, and a polygon selection per key.
8. Validate with `Mesh.check()`: 0 boundary edges (closed), 0 duplicates, 0 non-manifold.

**Expected counts for the open top sheet:** 7285 points, 7200 quads, 14484 edges, Euler V-E+F = 1. Plateau corners are valence-3 poles on a near-flat area. Valley T-junctions are valence 6 and crossings valence 8, both on the flat floor. The closed solid is about 8.5k quads. Set SDS to OSD_CATMARK, editor 1-2, render 3, no Phong angle limit.

## 6. Hierarchy
```
KB_ROOT   pivot: bezel centre, glass plane
|- CTRL   user data, same schema as BACKLIGHT_CONTROL + KEYS group
|- BODY
|  |- bezel_frame        SDS, bezel_chamfer selection
|  |- base_plate         SDS
|  '- feet x4
|- PANEL
|  |- glass_cover
|  |- led_mask_grid
|  '- LED   led_points(4500) > led_cloner > led_cell ; led_effect (Python effector)
|- KNOB_ASSY   pivot on knob axis, Y-rotation
|  |- knob (SDS lathe, N=48) ; knob_top ; knob_recess
|  '- red_dot
'- SKIN
   |- skin_dent   Python Generator over the child skin_cage, under SDS
   |  '- skin_cage
   '- KEYS
      '- k<r>_<cc>_<label> x68   null at key centre, y=1.30, user data Press 0-1, Glow RGB
         '- legend_N
```

## 7. Materials
- **Bezel:** white anodized or blasted aluminium. Start from `MC005_A068` (Sandblasted Aluminum 01) with the base colour tinted to light silver-white and 4K flake maps added. Alternatives: `MC005_A004` (Anodized Silver), `MC007_A001`. Chamfer: `MC001_A140` (Aluminum Polished).
- **Base plate:** `MC005_A016` (black matte, as in Yogo CLASSIC).
- **Feet:** `MC001_A308` (DRubber).
- **Glass:** custom smoked glossy black. Base about 0.01, roughness 0.05-0.08, IOR 1.52, plus a faint micro-scratch roughness map (library group TC012). GSG `MC075_A031` (Smokey Frosted Glass) is too matte; `MC075_A065` (Tempered Frosted) is the neutral frosted option.
- **LED cell:** black base, emission from RS Color User Data with attribute `RSMGColor` (the Yogo `YKB_screen_cell` recipe, emission weight about 9).
- **Skin:** custom, because `gsg_find "silicone"` returns no match. Suggested start:
  - base 0.92 white, roughness 0.42, IOR 1.43;
  - subsurface weight about 0.8, radius about 2.5 mm, colour (0.95,0.96,1.0), or thin-wall transmission 0.35 with refraction roughness 0.55;
  - fine micro-bump.
  - `MC075_A067` (rough 0.35, IOR 1.77) is a glass reference only.
- **Legends:** black base, white emission (animatable per key).
- **Knob:** `MC005_A038` (Knurl Metal 01) as bump and normal on a brushed aluminium body.
- **Red dot:** red emission over clear glass.

## 8. Animation hooks
- **Press as dent:** `skin_dent` reads Press from the 68 key nulls. For each point, `dy = -1.2 * Press[key_id[v]] * ring_w[v]`, plus a lateral pull toward the key centre of about 0.8% * Press * ring_w * (1 - ring_w). C4D has no Python Deformer. Use a Python Generator, or a Python Tag at Generators priority. Keep the cage under SDS. Fallback for hero close-ups only: a Displacer with a few fields.
- **Per-key glow:** `led_effect` is a Python Effector copied from `ykb_screen_effector.py` (reads grid size from clone positions, controls from a null's user data). It needs zone logic: the strip, and the 6x6 px block of each key (assign a cell to the key containing its centre; the 1.25, 1.75, 2.25 and 6.25u keys fall on half-pixels). The existing `_digits` is the two-line 16x14 layout. A single-line HH:MM at native size is needed. New modes: key glow, rainbow with a row envelope (bright centre rows), equalizer.
- **Pivots:** KB_ROOT, KNOB_ASSY (knob axis), SKIN, each key null, the LED cloner at the panel centre.

## 9. Code and live-scene facts
- Reuse (copy with the `lnk_` prefix): `ykb_layout.ROWS[1:]`, `ykb_geo.py`, `ykb_parts.py` (keycap ring loft, KC r_bot 3.4 / r_top 4.2), `ykb_legend_fit.py`, `ykb_screen_effector.py`, `ykb_gsg.make`.
- The live Yogo scene is open: `Yogo_pro_keyboard_v008_anim_codex.c4d`. In `main_keyboard`, `keyboard1`, `keyboard2` under `YOGO75PRO/MODULE/SCREEN` there are `scr_grid` (16816 pts), `scr_points` (2016 pts), `scr_cloner`, `scr_cell`, `scr_effect`. The 2016 points are a 48 x 42 grid.
- `BACKLIGHT_CONTROL` screen user data is ids 48-74. Mode is id 50 (currently 1 = ball). Intensity 0.55.
- `c4d.documents.GetDocumentList()` does not exist in this build (AttributeError). Use `GetFirstDocument()` and `GetNext()` instead.
- Image resolution is unverified; it is probably about 2752 x 1536. The viewer cap is about 2000 px.
- Open points:
  - The 3.5 mm key height, 14 mm knob and 11.4 mm body thickness are estimated from AI renders, plus or minus 1 mm.
  - The strip column count is 90 plus or minus 2 and the digits are 5 rows plus or minus 1.
  - The pixel under-glow beneath the keys is assumed.

## KEY FACTS
- Reference file is Projects/claude/Like_nothing/Output/Refs/ref_keyboard_v2.png. The task text omits Output/. It matches Output/Images/nb2_keyboard_v2_ledpanel_001.png (4,819,472 B).
- Canonical layout: 5 rows x 16u = 68 keys = ykb_layout.ROWS[1:] of Yogo 75. No F-row; the LED strip replaces it. The brief's '75% with function row' contradicts the ref.
- Key counts: 57x1u, 3x1.25, 2x1.5, 2x1.75, 1x2u, 2x2.25, 1x6.25 = 68. 51 keys carry legends, 17 are blank.
- Calibration: 1u = 48.8 px = 19.05 mm. LED pitch measured 8.0-8.14 px = 6.0 cells per key unit, so pitch 3.175 mm (1/8 inch, U/6).
- Overall size from the ref: bezel outer 322.5 x 147.9 mm, glass 317.5 x 142.875 x 1.1. The brief's 320x120x9 does not match: body is about 11.4 mm thick (Al wall 7.6 + base 3.8), keys reach 14.9 mm.
- Full-panel LED matrix 100 x 45 = 4500 cells, pitch 3.175, cell 2.54. Strip = cols 2-91, rows 2-10 (90 x 9, 285.75 x 28.58 mm). Key zone = 96 x 30 px, a 6x6 px block per 1u key.
- Skin footprint = 16u x 5u = 304.8 x 95.25 mm, x +-152.4, z -65.09 to +30.16. Margin glass to skin about 6.35 mm; plan corner R4.
- Key profile: valley floor top y=1.30 over glass, key rise 2.25 mm + 0.15 crown (top y=3.70), wall about 55 degrees, footprint = w*19.05 - 1.6 mm, corner R 3.4 to 4.2. Brief said 2 mm; side view shows about 3.5 mm total over glass.
- Skin method: ring-loft tiles (6 rings R0..R5, 4w nodes per side on a 0.25u lattice) welded on the valley centreline into one SDS cage. Expected open sheet: 7285 points, 7200 quads, 14484 edges, Euler = 1. Fallback: a global tensor grid (all valence 4, about 45k quads).
- Valley T-junctions come out valence 6 and crossings valence 8, both on the flat valley floor. Plateau corners are valence-3 poles on a near-flat area.
- Knob is a knurled aluminium cylinder Ø14 x 6 mm at x +146.05, z +55.56. Red dot Ø3.5 at x +146.05, z +42.86. The side view shows the knob at about 5 mm; the top and 3/4 views win.
- Clock 'HH:MM' in 3x5 px digits, cols 74-91, rows 4-8. The Yogo effector's _digits is a two-line 16x14 layout, so the single-line strip layout and zone logic are new.
- Bezel section: 2.5 mm top face, 0.7 mm diamond-cut outer chamfer, 0.3 mm inner chamfer, 7.6 mm wall. Base plate is black, inset 0.8 mm, 3.8 mm thick.
- Legends: 5x7 dot-matrix (0.9 mm pitch), emissive white, ray-conformed to the key top. Dual legends 5x5 at 0.75 mm.
- Press-as-dent: a Python Generator (skin_dent) reads Press from 68 key null pivots and applies ring_w weights. C4D has no Python Deformer. Keep it under SDS.
- GSG: no silicone material (gsg_find 'silicone' has no match), so the skin is custom. Bezel: MC005_A068 / A004 / MC007_A001, chamfer MC001_A140, knurl MC005_A038, rubber MC001_A308, black matte MC005_A016, frosted glass MC075_A065-A067.
- Live Yogo scene is open; MODULE/SCREEN has scr_points 2016 pts (48x42), scr_grid 16816 pts, scr_cloner, scr_cell, scr_effect. BACKLIGHT_CONTROL screen user data is ids 48-74.
- c4d.documents.GetDocumentList() does not exist in this C4D build. Use GetFirstDocument() and GetNext() for read-only listing.

## FILES
Projects/claude/Like_nothing/Output/Refs/ref_keyboard_v2.png
Projects/claude/Like_nothing/Context.md
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_layout.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_geo.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_parts.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_legend_fit.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_screen_effector.py
Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_gsg.py
weaver_claude/skills/references/sds-topology-knowledge.md
weaver_claude/skills/gsg-library.md