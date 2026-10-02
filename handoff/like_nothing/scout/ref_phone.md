# Smartphone concept: modelling spec for C4D SDS build (from ref_phone.png)

## 0. Source and method
- Real path: `Projects/claude/Like_nothing/Output/Refs/ref_phone.png`. The brief's `Refs/ref_phone.png` is not a file. It is byte-identical in size (4,190,678 B) to `Output/Images/nb2_phone_draft_001.png`. No phone prompt file exists: `Prompts/` holds only `headphones_A_v1.md` and `headphones_v2_draft.md`.
- `view_image` caps at 2000 px wide (~2752x1536 original, inferred). I cropped and pixel-measured the saved copy, assuming body length = 150 mm. Scale is 4.87 px/mm in the back view, 5.55 in the side view, 4.85 in the front view.
- Accuracy: lengths +-0.5 mm, island and matrix +-1 mm, thickness +-1 mm. All mm values are canonical (rounded and symmetrised) unless marked "ref".
- Quadrants: Q1 = 3/4 back, Q2 = straight back (landscape, camera end right), Q3 = side, Q4 = front (landscape).
- Not checked: whether a phone scene already exists in C4D.

## 1. Frame of reference (units mm)
- Origin = body centre. +Y = camera/top end. +X = viewer's right when looking at the BACK, so the lens column is at -X and the LED matrix at +X.
- Screen faces +Z. Back glass faces -Z, so the default C4D Front camera sees the back (lens column on the left, matrix on the right, as in Q1).
- Edge A = +X (roller, slot, key plate). Edge B = -X (two tabs). Bottom end Y=-75 (USB-C). Top end Y=+75 (plain).
- Q2 and Q4 are landscape. Q2 is the portrait back view rotated CCW by 90 degrees.

## 2. Body and profile (canonical)
| Item | Value |
|---|---|
| Body L x W x T | 150.0 (Y) x 72.0 (X) x 8.6 (Z). Ref ratio 2.07 = 150 x 72.3. Ref thickness reads ~10 mm at 150 mm length (see section 11). |
| Plan corner | R 11.0 (ref 10-12), G2 squircle (quarter superellipse n~4, blend patch ~14 mm). |
| Z stack | Z=0 mid-plane. Front glass top +4.3. Back surface -4.3. Island rim -5.3. Island glass -5.1. Lens-ring tops -5.9. Max depth 10.2 mm. |
| Frame wall | Flat vertical, 6.5 mm (Z +3.2 to -3.3), satin, mid-height Z=-0.05. |
| Back-side edge | Polished 45-degree chamfer 1.0 x 1.0 (ref reads ~1.2-1.4 mm, mirror-bright). |
| Front-side edge | Satin round R 1.1. |
| Micro-chamfer | 0.12 on every pocket, key, dome and plate edge. |
| Front glass | 147.2 x 69.2, R 9.6 (inset 1.4 = round 1.1 + lip 0.3). Thickness 0.7, edge R 0.35. Parting gap 0.1. |
| Back plate | Same outline 147.2 x 69.2, R 9.6, thickness 0.8, edge R 0.5. Gap 0.1 groove. Soft pillow edge. |
| Antenna splits (8) | Light-grey polymer inserts 1.4 wide, flush. On both long edges at Y=+-62.4 (ref 11.9-13.3 mm from the end). On both end faces at X=+-21 (ref ~15 mm from the corner). |

## 3. Back: camera island (Q1, Q2)
- Outer 64.0 (X) x 45.0 (Y), R 6.5, centred X=0, Y=+48.5 (Y 26.0-71.0). Margin 4.0 on three sides (ref 3.7-4.5).
- Rim top face 2.3 wide, +1.0 mm above the back plate (rim top Z=-5.3). Outer top chamfer 0.35, inner 0.25.
- Smoked-glass panel 59.4 x 40.4, R 4.2, sunk 0.2 (Z=-5.1). One single pane covers the lenses and the matrix.
- Lens rings x2: OD 14.9, ID 12.9 (ring 1.0), centres X=-19.8, Y=48.5+-8.8 (ref pitch 17.5-17.8; the ref pair sits +1.2 mm toward the end, symmetrised).
  - Rings stand 0.8 above the glass (Z=-5.9) with a 0.2 top chamfer and a 0.15 inner bevel.
  - Inside each ring: a black sapphire disc dia 12.9, recessed 0.25. Dark-grey lens barrel dia 5.4. A blue/magenta AR iris dia 2.4 at the centre.
- Flash: dia 3.0, warm-champagne diffuser, 0.25 metal ring, at X=-12.7, Y=48.5.
- Dot-matrix LED panel: 21 x 21 cells.
  - Pitch 1.6, LED square 1.1, gap 0.5, so 33.6 x 33.6 mm.
  - Centre X=+10.3, Y=48.5. Cell (i along Y, j along X): Y=48.5+(i-10)*1.6, X=10.3+(j-10)*1.6.
  - Ref measured ~32 x 36 mm, pitch 1.6-1.7, 20 columns x 21 rows plus 1-2 dim reflected rows. 21 x 21 is chosen for a centred symmetric glyph.
  - Off-state floor ~6-8 % emission, with a faint centre die dot visible through the glass.
  - Default glyph: symmetric audio waveform with the time axis along X in portrait. This is Q1's horizontal waveform; Q2 shows it rotated.
- Micro-text laser-etched on the island rim facing the body centre (Y=27.2), reading +X:
  - "12MP/24MM" at X -22.1...-12.3.
  - "S88/ADD0059" at X +4.8...+16.1. This one is garbled in the ref.
  - Cap height 1.2, dark grey 0.25. Make it a shader decal, not geometry.

## 4. Red accent
- Dot dia 3.2 (ref 15.5 px = 3.2 mm) at X=+20.0, Y=+22.4. It sits just below the island's matrix-side corner, 2 mm from the rim.
- Flush glossy red enamel dome, 0.15 proud, in a 0.1 seat groove. Sampled lit colour sRGB (182, 29, 29); albedo ~(0.72, 0.04, 0.05). This is the only saturated colour.

## 5. Edge A (+X), Y from the camera end (all centred on wall mid-height)
| Part | Y range | Size | Notes |
|---|---|---|---|
| Key plate | +47.4...+22.7 | 24.7 x 3.6 | See section 8. 3x3 dimple icon (dot 0.35, pitch 0.7, 0.1 deep). |
| Speaker slot | +14.6...-19.8 | 34.4 x 4.1, full-round ends | Black recess 1.2 deep. 3 rows x ~33 columns of square holes, 0.7 at 1.0 pitch. Use an opacity/bump map, not geometry. |
| Wheel pocket | -31.3...-50.8 | 19.5 x 6.8, corner R 1.2, depth 3.0 | Black gap ~0.35 around the wheel. Micro-chamfer 0.12. |
| Roller wheel | centre Y=-41.05 | window 17.4 x 5.2 | See below. |
| Volume glyphs | Y=-28.3 (3 arcs), Y=-54.1 (1 arc) | 3.8 x 2.6 | Engraved speaker icons flanking the wheel, 0.03 deep, grey. |

- Roller wheel (ref window ~17.5 x 6.2, with Z scaled 0.84 for T=8.6): knurled disc, axis Z, R 20.0, thickness 5.2. Centre X=+18.0, Y=-41.05, Z=0.
  - Its top reaches X=+38.0, so it protrudes 2.0 past the wall, with a visible chord of 17.4 at the pocket opening (matches Q3). Q1 shows the same bulge.
  - Knurl: 45-degree diamond cross-hatch, 0.6 pitch, 0.12 deep, edge round 0.5. Full circumference knurled so rotation about Z is seamless.
- Ref evidence for the Z axis: knurl diamonds compress toward the left/right ends in Q3, and the icons flank it left/right.

## 6. Edge B (-X) and ends
- Two flush tabs (Q2; Q4 shows only the long one, ~8 mm shifted):
  - Long: Y +27.9...+47.5 (19.6).
  - Short: Y +9.7...+20.6 (10.9).
  - Z-height 3.4, proud 0.4 in the ref. Canonical = low domes (section 8). Suggested roles: power/lock (long) and action (short).
- Bottom end: USB-C 8.9 x 2.6, R 1.3, centred X=0, depth 3, black cavity with steel tongue. Seen only as a dark slit in Q1 (offset ~0.4 of the end face, treated as perspective).
- No front punch-hole, SIM tray, jack or mic holes are visible.

## 7. Front (Q4)
- Edge-to-edge black glass (sampled 28/255), concentric R 9.6, no visible bezel. Only a 1.4 satin lip and the polished edge show.
- Only UI element: "NOTIFICATIONS" in a monospace pixel font, cap height 2.8, length 24, ~85 % white. In portrait it reads left to right at top-centre (Y=+68.4, X=0). Q4 is read as a flip about the vertical axis; if the flip was horizontal it would sit at the bottom, which is a low-stakes UI texture position.
- Screen off: ~0.011 emission floor plus a soft floor-reflection gradient.

## 8. Tactile bumps (replace buttons)
- No gaps and no clicks. Every control is a soft organic dome: pill/superellipse footprint (n~2.6), apex 0.5 above the wall, G2 blend radius 0.8, 0.08 x 0.12 parting groove.
- Canonical Edge A plate resolves the Q1/Q3 mismatch: the 24.7 plate contains two volume domes plus the dimple icon between them.
  - VOL+ : 10.3 x 3.2, Y +47.4...+37.1.
  - VOL- : 10.3 x 3.2, Y +33.0...+22.7.
  - Gap 4.1 holds the dimple icon.
  - A "Key_Mode" switch (single flat plate, as Q3, or two domes) via two objects with visibility toggled.
- The roller is itself a tactile control (volume/scrub dial, press = mute). The ref's roller glyphs already mean volume, so volume exists twice. Decision: roller = fine dial; domes = volume per the brief.
- Animation press travel: dome 0.3 mm along its own axis.

## 9. Materials per part (RS Standard suggestions)
| Part | Material |
|---|---|
| Frame wall | White-silver bead-blasted aluminium: metalness 1, rough 0.30, albedo ~0.80. Ref wall sampled 176/255. |
| Back chamfer | Polished diamond-cut, rough 0.05. Ref sampled 232 highlight. |
| Back plate | Matte white ceramic/glass-ceramic or white metal: albedo 0.86, rough 0.38, clearcoat rough 0.12, 4K mica/metal flake normal, sparkle at ~27 px/mm close-up. |
| Island rim, lens rings, plate edges | Frame satin plus polished chamfers. |
| Island glass | Smoked: transmission ~6 %, rough 0.10. |
| Matrix | Emission via pixel_screen (white, floor 6-8 %). |
| Lens glass | Black sapphire AR, thin-film iris. |
| Flash | Warm diffuser. |
| Red dot | Red enamel gloss, optional emission. |
| Front glass | Black, rough 0.02, oleophobic. |
| Roller | Satin Al plus knurl bump/displacement (4K). |
| Slot grille | Black anodised 0.02 with 0.15 grey holes. |
| Domes | Frame satin. |
| Splits | Grey polymer 0.65, rough 0.5. |
| Engraving / micro-text | Dark-grey laser etch on satin. |
| USB-C | Black cavity, steel tongue. |

## 10. Hierarchy and pivots (prefix PH_, code in `C4D/src` as `lnk_*`)
```
LNK_PHONE (root null, origin body centre, Y-up, mm)
├─ PH_CTRL (UD: Explode 0-1, Gap mm, WheelAngle, WheelRPM, DomeUp/Dn/Pwr/Act 0-1, LED_Mode, LED_Bright, RedDot 0-1, Key_Mode)
├─ PH_GEO
│  ├─ L7_FrontGlass   pivot (0,0,+3.95)  explode +3G
│  ├─ L6_Display      pivot (0,0,+3.0)   explode +2G  (OLED, ink, UI plane)
│  ├─ L4_Internals    pivot (0,0,-0.5)   explode +1G  (PCB/battery/speaker box/wheel carrier)
│  ├─ L5_Frame        pivot (0,0,0) stays (pockets, slot, USB-C, 8 splits)
│  ├─ L3_BackPlate    pivot (0,0,-3.9)   explode -1.5G
│  ├─ L2_IslandStack  pivot (0,48.5,-5.1) explode -3G (glass, Matrix_pixel_screen @X+10.3, PCB)
│  ├─ L1_IslandRim    pivot (0,48.5,-5.3) explode -4G
│  │   ├─ Lens_A/B_pivot  (X-19.8, Y39.7/57.3) rings, glass, barrel, iris; Flash (X-12.7)
│  ├─ Wheel_pivot (X+18,Y-41.05,Z0, axis Z) → Wheel_disc (explode +X 1.5G)
│  ├─ Dome_VolUp/Dn pivots (press -X 0.3), Dome_Pwr/Act pivots (press +X 0.3)
│  ├─ RedDot, Text_decals
└─ PH_NAV (nulls: Back, SideA, SideB, Front, IslandClose, WheelClose, MatrixClose)
```
Default Gap G = 12 mm. Reuse the `pixel_screen()` approach: one quad per LED with a per-cell centre UV (21 x 21 texture, nearest sampling, UV (0,0) = top-left).

## 11. Inconsistencies and chosen canon
1. **Thickness:** the ref reads ~10 mm at 150 mm length (14.6:1) vs the brief's ~8. Canonical is 8.6 as a compromise; the roller/pocket height needs the wall. Expose it as a parameter.
2. **Key plate:** Q3 shows one 24.7 pill with a dot grid. Q1 shows two ~10 mm pills spanning the same length. Solved with two domes in one plate.
3. **Opposite edge:** Q2 shows two tabs. Q4 shows one tab shifted ~8 mm. Q2 is canonical.
4. **Roller:** protrudes in Q1, flush-looking in Q3, axis ambiguous. Solved with the R20 Z-axis disc.
5. **Glass tone:** Q1 shows mid-grey glass with a LED grid visible everywhere. Q2/Q4 are near black. Treated as reflection; grid exists only in the matrix area.
6. **Lens pair** offset by +1.2 mm and the island edge sloping in Q3 (perspective): symmetrised to a vertical wall.
7. **Text** is garbled (ref); replaced by generic strings. No logos.
8. **Front:** no front camera. Label orientation depends on the assumed flip.

## 12. Build notes
- Quad-only SDS cells with holding loops of 0.1-0.15 at every hard edge. Editor 1-2, render 3.
- Reuse the vault builder: `Pixbar_clock/C4D/src/pxb_geo.py`, `pxb_parts.py` (Face and `feature(kind=hole|pocket|cut)` at line 391, `box_final` at line 200), validated by `tools/check_parts.py`. A domed "boss" feature is not in it and must be written.
- Pockets, slot, USB-C and wheel window are `pocket`/`cut` features.

## KEY FACTS
- Real ref path: Projects/claude/Like_nothing/Output/Refs/ref_phone.png (brief's Refs/ref_phone.png is wrong); same file size (4,190,678 B) as Output/Images/nb2_phone_draft_001.png; no phone prompt file exists (Prompts/ only has headphones_A_v1.md, headphones_v2_draft.md)
- Canonical body 150.0 x 72.0 x 8.6 mm (ref pixel ratio 2.07; ref reads ~10 mm thick at 150 mm length, so 8.6 compromise), plan corner R 11 G2 squircle, flat 6.5 mm wall, 1.0 polished 45-degree back chamfer, R1.1 satin front round
- Local axes: +Y camera/top end, +X = viewer right looking at back (lens column -X, matrix +X, roller edge = Edge A +X), screen +Z, back faces -Z
- Camera island 64.0 x 45.0 mm R6.5 centred (X0, Y+48.5), +1.0 mm over back plate, 2.3 rim, one smoked-glass pane 59.4 x 40.4 R4.2 sunk 0.2
- Two lens rings OD 14.9 / ID 12.9, stand 0.8 above glass, centres X-19.8, Y 39.7 and 57.3; flash dia 3.0 at (X-12.7, Y48.5); black sapphire disc, barrel dia 5.4, AR iris dia 2.4
- LED matrix 21x21 cells, pitch 1.6, LED 1.1 sq, gap 0.5 = 33.6 mm sq, centre (X+10.3, Y48.5); ref counted ~20x21; off-state floor 6-8 %; default glyph symmetric waveform; build as pixel_screen() single mesh with per-cell UV (as Pixbar_clock)
- Red dot dia 3.2 at (X+20.0, Y+22.4), glossy red enamel, lit sRGB (182,29,29); only saturated colour
- Edge A (+X) from camera end: key plate Y+47.4..+22.7 (24.7 x 3.6), speaker slot Y+14.6..-19.8 (34.4 x 4.1, ~3x33 square holes 0.7 @1.0 pitch), wheel pocket Y-31.3..-50.8 (19.5 x 6.8), glyph icons at Y-28.3 / -54.1
- Roller wheel canonical: Z-axis knurled disc R20, thickness 5.2, centre (X+18, Y-41.05), 2.0 mm protrusion giving 17.4 mm visible chord (matches Q3 ~17.5 window and Q1 bulge); 45-degree diamond knurl 0.6 pitch, 0.12 deep; pivot for rotation at the disc centre
- Edge B (-X) tabs: long Y+27.9..+47.5 (19.6) and short Y+9.7..+20.6 (10.9), proud 0.4 in ref; canonical = low organic domes (apex 0.5, G2 blend 0.8, 0.08 x 0.12 parting groove)
- Tactile rule: Edge A plate = two volume domes 10.3 x 3.2 (VOL+ Y+47.4..+37.1, VOL- Y+33.0..+22.7) with 3x3 dimple icon in the 4.1 gap; Key_Mode switch for single plate (Q3) vs two domes (Q1)
- USB-C 8.9 x 2.6 centred on bottom end Y=-75; 8 antenna-split polymer inserts 1.4 wide at Y=+-62.4 on long edges and X=+-21 on end faces
- Front: edge-to-edge black glass 147.2 x 69.2 R9.6, no front camera; only UI element 'NOTIFICATIONS' mono pixel text, cap 2.8, length 24, top-centre in portrait
- Micro-text on island rim at Y=27.2: '12MP/24MM' X-22.1..-12.3 and 'S88/ADD0059' X+4.8..+16.1 (ref garbled), cap 1.2; make as shader decal
- Explode pivots: L7 front glass +3G, L6 display +2G, L4 internals +1G, L5 frame 0, L3 back plate -1.5G, L2 island stack -3G, L1 rim -4G, G=12 mm default; wheel +X 1.5G; PH_NAV nulls for camera takes
- Main inconsistencies resolved: thickness 10 vs 8 mm; one 24.7 key (Q3) vs two ~10 mm pills (Q1); Q2 two tabs vs Q4 one tab shifted ~8 mm; roller flush vs protruding; glass tone grey (Q1) vs black (Q2/Q4); roller icons mean volume so volume is duplicated by domes (decision: roller = fine dial, domes = volume)
- Reusable vault code: Projects/claude/Pixbar_clock/C4D/src/pxb_geo.py, pxb_parts.py (feature(kind=hole|pocket|cut) line 391, box_final line 200), pxb_parts2.py pixel_screen() line 83, tools/check_parts.py; no domed boss feature exists, must be written. Pixbar Context documents Takes incl. EXPLODE
- Not checked in this task: C4D document state (no exec_python used), GSG library; accuracy of dimensions is +-0.5 mm length, +-1 mm island/matrix/thickness

## FILES
Projects/claude/Like_nothing/Output/Refs/ref_phone.png
Projects/claude/Like_nothing/Output/Images/nb2_phone_draft_001.png
Projects/claude/Like_nothing/Context.md
Projects/claude/Like_nothing/Prompts/headphones_A_v1.md
Projects/claude/Pixbar_clock/Context.md
Projects/claude/Pixbar_clock/C4D/src/pxb_parts2.py
Projects/claude/Pixbar_clock/C4D/src/pxb_parts.py
Projects/claude/Pixbar_clock/C4D/src/pxb_geo.py
Projects/claude/Pixbar_clock/C4D/tools/check_parts.py