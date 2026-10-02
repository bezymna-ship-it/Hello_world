# Headphone concept: modelling spec for a C4D Subdivision Surface build

## 0. Sources and method
- Path correction. The sheet is `Projects/claude/Like_nothing/Output/Refs/ref_headphones.png` (there is no `Refs/` at the project root). It is byte-identical in size (4771625 B) to `Output/Images/nb2_headphones_v2_draft_001.png`, so it is the v2 draft, 2752x1536. The older over-ear sheet is `Output/Images/nb2_headphones_A_001.png`.
- `view_image` caps at about 2000 px wide. I split the sheet into 4 views, cropped them 2-4x and counted pixels in the screen.
- Scale is anchored to the cup's long axis = 72 mm (the brief's 62x72 cup; the face-on view measures 1.12:1). Precision is about ±8%. Every number below is an estimate unless it says "measured".
- Sheet layout: Q1 = hero 3/4 (studio lights in frame), Q2 = "side" (cup face-on), Q3 = front (10:28 and waveform), Q4 = folded.
- The old sheet A is an AirPods-Max-like over-ear and is rejected in `Context.md`. Only three ideas from it carry over: a clear window, a roller and paddle on the right edge, and USB-C plus mic holes on the left.

## 1. Inconsistencies between views, and the canonical choice
- **Hinge hardware differs in every view.**
  - Q1: aluminium end cap, a flat slider bar in a slot with a ruler, then a block yoke on a post.
  - Q2: a flat bar with an "L" window and ruler.
  - Q4: a clevis with a pin cap, a tongue, and a vertical cylindrical barrel with a stub into the cup.
  - Canonical: one stack of end cap, slider bar, yoke, vertical swivel barrel, tilt stub, cup (section 3). It uses Q4's barrel/stub and Q1/Q2's slider and ruler.
- **Q2 is not a profile.**
  - The cup is shown lying down, with the long axis horizontal.
  - A flat strap leaves sideways from the cup's top edge and ends in a cut-off rounded end.
  - Use Q2 only for the cup face, bezel, matrix, red tab, "40MM" etch and ruler. Ignore the strap.
- **Screen orientation differs.** Q1 shows the waveform running front-to-back, Q3 shows it vertical with 10:28 rotated 90°, and Q2 is rotated. Canonical: the matrix is 23 columns (front-back) x 27 rows (vertical), so a worn headphone reads upright.
- **Q3 digits and cups.**
  - The "10:28" digits are drawn as a dotted outline while the waveform is solid.
  - The cups are splayed about 45° outward and are not parallel.
  - Only the left cup has hardware (USB-C, mic holes); the right cup front wall is plain.
- **Q4 screens.** They are dark, with only a faint grid, and the cups overlap. The overlap is impossible with the swivel at the cup centre (section 8).
- **Red accent.** It exists only in Q2, as a tab on the hinge. Canonical: one red tab, on `fork_yoke_R`.
- **Labels.** Q2 shows "L" and "40MM" on the waveform cup. Q1 and Q3 show the waveform and "40MM" on the screen-right cup and "L" on the screen-left cup. Canonical: R cup = waveform, red tab, domes, "40MM". L cup = clock, USB-C, mics, "L".
- **Studio.** The softbox and strip lights in Q1 are not part of the product. The knurled dial is visible only in Q1 (cup R bottom edge) and is not readable in other views.
- **Bezel and headband widths drift.** The silver ring is 2.6-3.2 mm in Q2 but about 1.5 mm in Q1. The band is about 22 mm wide in Q1, 27.5 mm in Q2 and wider in Q3.
- **Unlit tiles.** Q2 shows them lighter near the bottom, probably a floor reflection. Use a uniform idle emission instead.

## 2. Global dimensions and axes
Axes: Y up, X lateral (cup_R at +X), wearer faces -Z, cup bottom on Y=0, symmetry plane X=0. Document unit: mm.

| Item | Value |
|---|---|
| Overall height at rest | 196 mm (outer apex), 208 mm with sliders at +12 |
| Width over cup outer faces | 168 mm |
| Cushion-to-cushion gap | 120 mm at rest; worn clamp adds up to about 15 mm per side |
| Overall depth | 64 mm |
| Cup | outer 72 (Y) x 64 (Z) x 24 (X) |
| Cup thickness | shell 12.5 incl. bezel + cushion 11.5 |
| Headband width | 27 mm |
| Headband thickness | 10 mm |
| Headband centreline | 10 mm legs at X=±72, Y=118-128, then a semi-ellipse a=72, b=63 about (0,128,0), apex centreline Y=191 |

The brief's "span about 170 mm" is matched: 2x72 + 24 = 168.

## 3. Hierarchy (ASCII snake_case) and pivots (mm)
```
HEADPHONES_CONTROL            null at the top, all user data (rule 4.12)
 hp_root
  hp_headband  (0,128,0)      Y translate = slide 0..12, drives both caps
    hb_path (spline a/b/legs) -> hb_sweep: hb_arc_outer, hb_arc_pad
    hb_cap_L/R (±72,118,0): cap_shell, cap_etch_text, cap_torx_screw, cap_pin_led
  asm_L / asm_R (±72,0,0)
    fork_slider_bar_L/R (±72,110,0)
    fork_yoke_L/R (±72,88,0): slider_core_white, red_tab (R only)
      swivel_L/R axis Y at (±72,80,0): swivel_barrel, swivel_pin_cap
        tilt_L/R axis Z at (±72,74,0): tilt_stub
          cup_L/R origin (±72,36,0):
            cup_shell, cup_bezel_ring, cup_glass, cup_screen_grid,
            pixel_screen, cup_pcb_back, cup_cushion, cup_cushion_seat, cup_baffle
            L only: usb_c_pocket, usb_c_tongue, mic_hole_01..04
            R only: tact_capsule, tact_dome_up, tact_dome_play, tact_dome_down, knurled_dial (optional)
```
Build one cup and mirror it. Rule 10.5: pivots sit on the rotation axes.

## 4. Per-part shape spec
- **hb_arc_outer.**
  - Section 27.0 x 3.2 mm with a 1.2 mm outward crown and a fully rolled edge R1.6.
  - Build it as a Sweep of the section along `hb_path`, so the headband lengthens automatically.
  - SDS: 4 longitudinal loops, 2 support loops per edge, about 60 segments around the arc.
- **hb_arc_pad.**
  - Section 24.0 x 5.5 mm, inset 1.5 mm from the edges, 1.0 mm inward crown, edge R2.5.
  - It stops 6 mm short of the caps, ends R4, with a 1.5 mm white leather edge visible around it.
- **hb_cap.**
  - Aluminium sleeve 27.4 x 11.5 x 14, wall 1.6, lower corners R4, edge chamfer 0.4 (second micro-radius 0.15).
  - The parting line to the leather is a convex curve (Q1).
  - A 14.4 x 3.0 slot in the bottom takes the slider.
  - Engraving: "40MM" (R) or "L" (L) on the outer face, about 2.2 mm text height, 0.1 mm deep.
- **fork_slider_bar.**
  - Flat bar 14.0 (Z) x 2.6 (X) x 30 (Y), edge R0.6, travel 12 mm.
  - Ruler: 1.0 mm pitch, a long tick (2.4 mm) every 5 mm, a short tick (1.4 mm) otherwise, 0.12 wide x 0.1 deep. Do it as a bump or alpha mask, not geometry.
  - A 12 x 4.5 x 0.4 recessed window carries the "L"/"R" letter. A white core strip 4 x 2 mm is visible in the yoke slot (Q1).
- **fork_yoke.** Block 22 (Z) x 9 (X) x 22 (Y), R3, chamfer 0.4, slot 14.6 x 3.0, bottom boss for the swivel.
- **swivel_barrel.** Cylinder Ø9 x 17, top chamfer 0.5. The pin cap carries an engraved Ø2.4 power-style icon (0.1 deep). A micro vertical text line runs on the barrel side.
- **tilt_stub.** Ø5 x 4 into a Ø7 x 1.2 recess in the cup edge, chamfer 0.3.
- **cup_shell.**
  - Squircle (G2, exponent about 4.5) outline 72 x 64, outer corner R19.
  - Wall draft 4° toward the back, face-edge fillet R6, a 0.2 x 0.2 parting groove under the bezel, back lip step 1.5.
  - Openings: USB pocket 9.1 x 3.4, mic holes Ø0.8, dome capsule, stub recess.
- **cup_bezel_ring.**
  - Visible ring about 2.8 mm. Outer edge chamfer 0.5 plus a 0.2 micro-radius, then it rolls over R2.5 and continues 2.0 mm down the side wall.
  - Inner lip chamfer 0.35. Lip top is 0.6 above the glass plane.
- **cup_glass.** 1.0 mm thick, outline offset from the bezel (corner R16), recessed 0.6 mm below the lip, flat.
- **cup_cushion.**
  - Outline = cup outline offset -1.0 mm, 11.5-12 mm thick, outer roll R5.5, inner lip R4, piping seam 1.2.
  - Ear opening 34 (Z) x 46 (Y), R15, with a shallow dished baffle of about 40 mm behind it.
  - Seat ring: white, 1.5 mm.
- **SDS rules.** Quads only, valence <= 4, no n-gons, closed shells (`Weaver/Правила.md` rule 10.4). UVs only on the screen and matrix; all other shaders use TriPlanar (rule 10.6).

## 5. LED window and matrix
- **Measured from Q2.** Pixel pitch 42 px on both axes (autocorrelation), so pixels are square. Tile fill about 0.81 of the pitch, matching the keyboard's 0.813. Pitch is about 2.15 mm and the grid is about 27x23.
- **Window.** Glass opening about 66.4 x 58.4 mm; matrix 58.05 x 49.45 mm. The matrix is centred with a black margin of about 4.2 mm (long axis) and 4.5 mm (short axis).
- **Canonical grid.**
  - 23 cols (Z) x 27 rows (Y), pitch 2.15 mm, tile 1.74 mm (corner radius 0.12), gap 0.41.
  - The corner stair profile measured from Q2 is [4,2,1,1] cells per corner. This removes 32 cells, leaving 589 tiles.
  - An odd column count gives a centred glyph. In the reference the waveform centreline is row 12.
  - Hi-res option: 46 x 54 at pitch 1.075 mm. The keyboard effector's font scale `S = NX//16` then gives 2.
- **Layers, outside to inside.**
  - Frosted smoked glass, 1.0 mm.
  - Black louvre grid `cup_screen_grid`, wall 0.41, depth 1.2.
  - `pixel_screen`: one object, with every tile carrying the UV of its cell centre (Pixbar/Yogo technique). Tile plane 2.0 mm below the glass top.
  - `cup_pcb_back`, matte black.
- **Idle level.** Unlit tiles read about #343434 in Q2. Use a uniform idle emission of about 0.04, as `scr_dim` does on the keyboard.
- **UI states** for the 23x27 matrix: waveform, clock (3x5 font, 17 columns wide), volume bar, play/pause, battery, pairing. This turns the glass into the control surface the brief describes.

## 6. Tactile bumps, ports and micro-details
- **Volume and play, as tactile bumps.**
  - Position: R cup front wall, straight section Y 21-51.
  - `tact_capsule`: silicone pill 7.5 x 30 mm, 0.6 recessed.
  - Three domes at 10.5 mm pitch: vol+ Ø5.0, play Ø6.0 (centre), vol- Ø5.0.
  - Dome height: 0.9 mm for vol+/vol-, 1.1 mm for play. Profile: h·(1-(r/a)²)², blended R3 into the floor.
  - A 0.15 mm cross groove on vol+ and a single groove on vol-.
  - Topology: a square-grid disc with no poles, which suits SDS.
- **Left cup.**
  - USB-C pocket 9.1 x 3.4 with a 0.25 chamfer, centre Y=30, on the front wall, long axis vertical.
  - Mic pinholes Ø0.8: pair at Y=41 and 43.7, pair at Y=20 and 22.
- **Knurled dial.** Optional, cup R bottom wall near the front. Ø7.5 x 4.5, diamond knurl done as a bump (not geometry). Q1 only; drop it if volume is carried by the domes.
- **Red tab.** `red_tab` on `fork_yoke_R` outer face, 5.7 x 8.5 x 0.8 mm, R1.2, inlaid, Y 90-95.7. Q2 measures it at about 5.7 x 8.5 mm. It is the single red accent.
- **Small details.**
  - Torx T3 screw (Ø1.6) and a Ø0.8 pinhole LED on the R cap.
  - Icons on the pin caps and barrel tops.
  - "40MM" etch.
  - The headband's pebbled-leather grain.

## 7. Materials (colours sampled from the sheet)
- **cup_shell:** white metal with fine metal flake (about 0.06 mm), roughness about 0.42, base about #E9E9E7 (lit sample #ECECEC).
- **cup_bezel_ring:** bright silver, polished satin.
- **cap, yoke, barrel, bar:** bead-blasted aluminium, base about #A1A1A1 in the render, roughness about 0.38.
- **hb_arc_outer:** white pebbled leather (grain about 0.7 mm), about #EDEDEB.
- **hb_arc_pad:** grey felt, about #B9B9B7.
- **cup_cushion:** grey microfibre/knit with sheen and slight crease displacement, about #B4B4B2.
- **cup_glass:** frosted smoked glass, etched outer surface at roughness about 0.22, IOR 1.52, transmission about 9%.
- **Black parts** (grid, PCB, mic holes): matte black about #0B0B0C.
- **Domes and red_tab:** white silicone with SSS; the red tab is #C8202B (sampled about #AF1E27 in shadow), roughness 0.45.
- **Texture scale:** 4K per the new brief.

## 8. Animation ranges and control
- **Slide.** 0-12 mm (Y translate of `hp_headband`).
- **Fold (swivel).** 0-90°, mirrored for R and L. The screen normal turns from lateral to forward.
  - Q4 shows about 80-90°. With the axis at the cup centre the cups sit 80 mm apart and do not collide.
  - To reproduce Q4's overlap, offset the barrel about 22 mm toward the cup rear.
- **Tilt.** ±10° about Z, for ear fit.
- **Clamp.** X-scale of `hb_path`, 1.0-1.21.
- **Control null `HEADPHONES_CONTROL`.** One user-data tab. Parameters: slide, fold L/R, tilt L/R, clamp, screen mode, screen intensity.

## 9. Not found / unverified
- No true side profile exists in the sheet. Cup depth and shell thickness are inferred, not measured.
- Whether the glass is flat or domed is unclear in the render.
- The cushion's inner geometry is only partly visible (Q1, left cup).
- The knurled dial and the swivel offset are Q1 and Q4 only.
- Suggested v3 render prompt: true orthographic side profile, light sources never in frame, screens lit in every view.

## KEY FACTS
- Real path of the sheet: Projects/claude/Like_nothing/Output/Refs/ref_headphones.png (not Refs/ at project root); byte-identical in size (4771625 B) to Output/Images/nb2_headphones_v2_draft_001.png (2752x1536, 2x2). Older over-ear sheet: Output/Images/nb2_headphones_A_001.png (AirPods-Max-like, rejected in Context.md).
- view_image caps at about 2000 px wide; analysis done on quadrant crops (2-4x) of that copy; dimensions have about ±8% error, anchored to cup long axis = 72 mm (face-on aspect measured 1.12:1).
- Canonical size: cup 72 (Y) x 64 (Z) x 24 (X); overall 196 mm tall (208 with sliders +12), 168 mm over cup faces (matches the brief's ~170 mm span), cushion gap 120 mm at rest. Headband 27 wide x 10 thick, centreline legs 10 mm at X=±72 then a semi-ellipse a=72, b=63 about (0,128,0).
- LED matrix measured in Q2: square pixels, pitch 42 px both axes (autocorrelation), about 27x23 grid, pitch about 2.15 mm, tile fill about 0.81 of the pitch (same as the keyboard's 0.813), rounded-corner stair mask [4,2,1,1] per corner.
- Canonical matrix: 23 cols (front-back) x 27 rows (vertical), upright when worn; 589 tiles after masking (23x27 minus 32); hi-res option 46x54 at pitch 1.075 mm reuses the keyboard effector's S = NX//16 font scale.
- Glass opening about 66.4 x 58.4 mm; matrix 58.05 x 49.45 mm with about 4.2-4.5 mm black margin; glass 1.0 mm frosted smoked, recessed 0.6 mm below the bezel lip; tile plane 2.0 mm below the glass top; idle tile emission about 0.04 (Q2 unlit tile samples about #343434).
- Mechanism chosen: end cap -> slider bar (Y travel 12 mm, 1 mm ruler ticks) -> yoke -> vertical swivel barrel (fold 0-90 degrees) -> tilt stub (±10 degrees about Z) -> cup. Pivots: cap (±72,118,0), slider (±72,110,0), yoke (±72,88,0), swivel axis Y at (±72,80,0), tilt axis Z at (±72,74,0), cup origin (±72,36,0).
- Inconsistencies flagged: hinge hardware differs in Q1/Q2/Q4; Q2 is not a profile (cup lying down, headband strap leaves sideways from the cup edge); screen orientation differs per view; Q3 digits rotated 90 degrees and drawn as a dotted outline, cups splayed about 45 degrees; Q4 screens dark and cups overlap; red tab only in Q2; L/R labels contradict between Q2 and Q1/Q3.
- Cup assignment chosen: R cup = waveform, red tab, tactile domes, '40MM'; L cup = clock, USB-C and mic pinholes, 'L'. One red accent only: silicone tab 5.7 x 8.5 x 0.8 mm on fork_yoke_R.
- Tactile instead of buttons: silicone capsule 7.5 x 30 mm on the R cup front wall (Y 21-51) with 3 domes at 10.5 mm pitch: vol+ Ø5.0 / h0.9 (cross groove), play Ø6.0 / h1.1, vol- Ø5.0 / h0.9 (single groove); profile h*(1-(r/a)^2)^2, pole-free square-grid disc topology. Knurled dial (Ø7.5 x 4.5, bump-map knurl) is Q1-only and optional.
- Left cup ports: USB-C pocket 9.1 x 3.4 with a 0.25 chamfer, centre Y=30 on the front wall, long axis vertical; mic pinholes Ø0.8 at Y=41 / 43.7 and Y=20 / 22.
- Colours sampled from the render: cup shell white about #ECECEC lit, cushion about #B4B4B2, headband pad about #B9B9B9, aluminium about #A1A1A1, red tab about #AF1E27 (use about #C8202B).
- Chamfer language: 0.5 mm 45 degree chamfer plus a 0.15-0.2 micro-radius on bezel/cap edges, bezel inner lip 0.35, parting groove 0.2 x 0.2, bezel rolls R2.5 and continues 2 mm down the side wall; corner R19 squircle (G2, exponent about 4.5) on the cup outline, glass corner R16.
- Weaver rules to apply: 10.4 (quads only, valence <= 4, closed shells), 10.5 (pivots on the rotation axes), 10.6 (TriPlanar; UVs only on the screen/matrix), 10.3 (no brand text, ASCII letters/digits only, so '40MM', 'L', 'R'), 4.12 (all controls up the hierarchy, e.g. HEADPHONES_CONTROL).
- Headband should be a Sweep over a parametric spline (hb_path with a/b/legs) so length follows the slider/clamp parameters; cup built once and mirrored.
- Not available: no true orthographic side profile in the sheet, shell thickness and cushion inner geometry are inferred; recommended v3 prompt change: true orthographic side profile, light sources never in frame, screens lit in every view.

## FILES
Projects/claude/Like_nothing/Output/Refs/ref_headphones.png
Projects/claude/Like_nothing/Output/Images/nb2_headphones_v2_draft_001.png
Projects/claude/Like_nothing/Output/Images/nb2_headphones_A_001.png
Projects/claude/Like_nothing/Prompts/headphones_v2_draft.md
Projects/claude/Like_nothing/Prompts/headphones_A_v1.md
Projects/claude/Like_nothing/Context.md
Projects/claude/Like_nothing/Output/Refs/site_sheet.png
Projects/claude/Yogo_pro_keyboard/Context.md
Projects/claude/Pixbar_clock/Context.md
Weaver/Правила.md