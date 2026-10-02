## Method and caveats
- `gsg_guide` failed (the vault has no `.claude/skills/gsg-library/SKILL.md`). I read the same guide at `weaver_claude/skills/gsg-library.md` plus `Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_gsg.py`. Both `ykb_gsg.py` and `T_cubes/C4D/src/tc_gsg.py` do the same job: `make(doc,name,code,tile,space,tint,sss,vp)`.
- Disk check via read-only `exec_python`: I listed folders under `E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library\materials` and read pixel widths from the JPG/PNG/TIF headers. Nothing was modified.
- The "_4k_" tag in a file name is not the pixel width. Some data maps are tiny: Sd128/256, Al256, Sc256, Sw128/256.
- Averages below (base sRGB, roughness 0..1) were sampled from the 4K maps. The base sRGB average is the suggested `vp`. Roughness is the map value / 255.
- The only GSG library on E: is Greyscalegorilla_Library. The GSG max is 4096, except TC012 at 8192 (16-bit TIF).
- Pixbar_clock is NOT open in C4D (open: "Untitled 3" and `Yogo_pro_keyboard_v008_anim_codex.c4d`). PXB_* values come from `Pixbar_clock/C4D/src/pxb_mats.py`.
- Web access to help.maxon.net is blocked. The port names of the RS Flakes node are unverified.

## Loader gotchas (ykb_gsg.make)
1. `tint` only multiplies the basecolor map. It is ignored for MC058 (normal-only), MC075 (glass) and MC078 (metal), which have no basecolor map. For those, set `base_color` afterwards with `set_ports(m,{"base_color":lin_rgb,"refl_roughness":x})`.
2. MC058 has only `normal.tif` 4096 and `.gsgm` params: base 0.10, roughness 0.385. Its normal map is a micro-texture source and works fine once you override the colour.
3. MC075 and MC078 are params-only. No texture files exist.
   - MC075 gives `refr_depth` = transmission_depth × 1000 mm (6–50 mm). That is far too thick for 1–2 mm glass, so override it.
   - It also sets `coat` 0.5 with coat roughness 0.45 on many items. Set coat to 0 for clean frosted glass.
4. `make` adds SSS (weight 0.25, radius 0.6 mm) automatically on MC027 (subsurface 0.7) and on materials with Sw maps. Pass `sss=False` for crisp small parts.
5. The user's own tint values are float multipliers, e.g. (0.35,0.51,0.34) on `GSG_MC001_A131_CAluminumBrushed01_Green`. The same material has a roughness-sampler multiplier of 1.5, so the user pushes GSG aluminium rougher. Values above 1 work on the sampler. I did not verify whether the basecolor multiplier clamps.
6. MC005_A002 AnodizedMidnightGreen has only a `.gsgm`, no maps (the index is correct). The MC078 folders hold 4 duplicate `.gsgm` files, which is harmless.
7. MC044 and the MC024/MC054/MC058/MC064/MC067/MC069 maps are TIF/EXR. The loader regex accepts them.

## Candidates
Map legend: B base, M metal, N normal, R rough, H height, E edge colour, Aa/Al aniso angle/level, O opacity, Sw/Sd scatter. All widths are 4096 unless noted.

### 1. White/silver bead-blasted or anodized aluminium, with micro-grain and sparkle
- **MC001_A141 CAluminumPowdered (best white).** B M N R, JPG.
  - Base avg (245,247,246), roughness 0.29, metal 255.
  - Preview shows fine bead-blast sparkle.
  - Suggested: tile 32 mm, `world` for static shells and `object` for moving parts, `vp=(245,247,246)`.
- **MC005_A004 AnodizedSilver.** B M N R, JPG. M is a flat 255. Base (183,183,183), roughness 0.49. Suggested: tile 30 mm, tint (1.2,1.2,1.2) to lift toward white (unverified).
  - The Server_motherboard scene uses it at 120 mm, which is too big for products.
  - MC005_A003 AnodizedRoseGold also has maps. MC005_A005 AnodizedSpaceGrey has B M N R as well (base not sampled).
- **MC001_A130 CAluminumBase.** B M N R. Base (238,238,240), roughness 0.33. MC001_A140 CAluminumPolished: base (245,247,246), no roughness sampled.
- **MC007_A001 Aluminum01.** B M N R E, JPG. Base (239,241,241), roughness 0.26, coat 0.48. Tile 60 mm. The E map gives the edge tint, which is good for chamfers. Magnesium MC007_A047: base (229,229,229), roughness 0.28.
- **MC005_A069 SandblastedAluminum02.** B M N R. Base (135,135,137), roughness 0.42. M avg 0.85, so the micro-pits show. Tile 30 mm. A068 is the graphite version (base 75).
- **Sparkle accent: MC002_A021 SilverSparkled.** B M N R. Base (251,250,245), roughness 0.20, coat_roughness 0.01.
  - Preview is coarse salt-and-pepper glitter, too strong alone.
  - Use it at about 10–20% through a Material Blender or Bump Blender over MC001_A141.
  - Also available: MC002_A018 SilverBumpy (roughness 0.29), MC002_A019 SilverMatte (0.33).
- **MC078_A016 AluminumBasicMetal.** Params only: (0.981,0.985,0.984), metal 1, roughness defaults to 0.4. Flat.
- **MC005_A047 MetallicPlastic01.** B H M N R. Base (164,165,167), M 0.92, roughness 0.47. MC005_A011 BrushedMetallicPlastic: base (176,175,180), M 0.75.

### 2. Titanium
- **MC007_A105 Titanium01.** B M N R E. Base (180,175,171), roughness 0.34. Params: coat 0.48, coat_roughness 0.31, coat_IOR 3.0. Tile 60 mm.
- **MC007_A106 TitaniumClean01.** Base (226,222,219), roughness 0.09 (polished).
- **MC078_A002 TitaniumBasicMetal.** Params only: (0.903,0.868,0.848), roughness 0.3, metal 1.

### 3. Brushed/knurled for scroll wheels and knobs
- **MC005_A038 / A039 / A040 / A041 KnurlMetal01–04.** B H M N R, JPG.
  - Base avg: 167, 151, 22 (A040 is black), 164. Roughness: 0.33, 0.42, n/a, 0.44.
  - Cycle count per 4096 px: A039/A040/A041 ≈ 64–72; A038 has 64×32.
  - For a pitch of about 0.4 mm, use tile ≈ 26 mm, `object` space. This is an estimate, so check it visually.
  - Previews: A038 is a diamond knurl, A039 a fine pyramid knurl.
- **MC044_A015 EmbossedMetalKnurl.** Aa Al B H(exr) M N R, TIF. Large pyramid knurl. A035 is gold, A055 black.
- **MC007_A064 SteelBrushedPattern01.** Aa B M N R E, anisotropy 0.85, base (178,178,178), coat 0.49. The preview is an overlapping-disc "engine-turned" pattern, so it is decorative (dial or cap), not subtle brushing. Server_motherboard used it at 120 mm.
- **MC001_A131 / A132 / A133 CAluminumBrushed01–03.** B M N R, base ≈ 220, roughness 0.32, anisotropy 0.3 in params (no angle map). Already in the Yogo scene.
- MC005_A020 ColoredChromeSilver: base 192. The user has used it as a chrome ring at 40 mm `object`.

### 4. Matte soft-touch white polymer
- **MC001_A315 DWhitePlasticDull.** B N R. Base (204,204,204), roughness 0.42. Tile 45 mm.
  - Warning: MC001_A313 DWhitePlastic (already used by the user) is glossy, roughness 0.06.
- **MC005_A057 Plastic02.** B M N R. Base (199,199,198), roughness 0.38. The user used it at 30 mm.
- **MC005_A035 KeyboardKey01.** Base (201,201,193), roughness 0.34, M map all 0. The user used it at 40–45 mm.
- **MC027_A024 P5PlasticPlainFineWrinkle.** B N R plus Sd256. Base (178,178,178), roughness 0.25, subsurface 0.7. A002 (stripe) is white 209, roughness 0.31.
- **For a true soft-touch micro-grain:** MC058_A12 FineMistMoldedPlastic (also A15 Grit, A18 HeavyMist, A73 Stipple). Normal only. Set white base (~0.85 linear) and roughness 0.45–0.55 manually. Tile 30–40 mm, to be checked by eye.
- MC025_A014 PolystyreneFoamSoftWhite is not polymer.

### 5. Frosted/satin glass (MC075, params only)
- **MC075_A065 TemperedFrostedGlass.** IOR 1.52, roughness 0.35, depth 40 mm, coat 0.5/0.45. Override coat to 0.
- **MC075_A073 BorosilicateFrostedGlass.** IOR 1.49, roughness 0.35, nearly clear. Also A066 SodaLimeFrosted, A072 CrownFrosted, A067 SapphireFrosted (IOR 1.77; the user's CLASSIC style uses it).
- The user's live frosted glass: `YKB_CLASSIC_display` (IOR 1.77, roughness 0.117, refr 1) and `YKB_display_cover` (IOR 1.49, roughness 0.287, refr 0.95). The user clearly prefers lighter frost (0.12–0.29) than the GSG 0.35.

### 6. Smoked black glass: none in GSG
- The darkest is MC075_A031 SmokeyFrostedGlass, with transmission_color (0.68,0.69,0.70) and depth 6 mm. It is light grey. A004 SmokeyGlass is the same colour, clear.
- Use the user's recipes:
  - `PXB_front_smoked`: base (0.015,0.015,0.017), roughness 0.04, transmission 1.0, `refr_color` (0.24,0.24,0.25), IOR 1.58, `refr_depth` 2.0 mm.
  - `IR_glass_black` (Logitech_IRIS): base 0.003, roughness 0.10, coat 1.0/0.03, plus `scratches.png` bump 0.012 at 40 mm (tri_bump).
- For the frosted-smoke LED window, add `refr_roughness` 0.2–0.35.

### 7. Translucent frosted silicone: none in GSG
- The GSG has no silicone. MC054 3D-printed plastic shows visible layer lines, and MC040 soap is marbled.
- Use `YKB_silicone` (base 0.92, roughness 0.45, refr 0.55), `YKB_sw_rubber` and `PXB_silicone_clear` (roughness 0.5, transmission 0.6, `refr_roughness` 0.4, `refr_depth` 1.0 mm).
- Add a MC058 micro-normal for grain.

### 8. Woven fabric/knit mesh
- **MC067_A036 WhiteJerseyKnit** (B N R Sw S): base 179, roughness 0.83. Also A038 Black (base 59), A001 HeatherGreyRibbed (162), A034 BlackRibbed, A032 DarkGreyJersey.
- **MC032_A011 PlushGridFabricWhite.** B N R Sw plus Hx. Base (210,208,203). Good for ear cushions or a headband.
- **MC032_A019 PerforatedFabricWhite.** B N R O Sw, base (199,201,204), O = opacity. A020 is black (base 49).
- **MC005_A072 SpeakerMesh01.** B H N O R, base 23, sheen 0.25, hex mesh with opacity (48×27 cycles per tile, so tile ≈ 58 mm for a 1.2 mm pitch). A073 is orange, not usable.
- MC032_A006 DiamondRipstopBlack, MC032_A026 CoatedNylonBlack, MC069_A019 WhiteWashedLinen. The user's `Hitech_cloth` project has no ready GSG fabric table.
- Fabric tiles to be set by eye (30–60 mm). Cycle counts on knits were unreliable.

### 9. Pebble-grain leatherette
- **MC058_A65 / A66 PebbleMoldedPlastic01/02, A54 LinearPebble.** Normal only, base 0.10, roughness 0.385. Override the colour. LeatherMoldedPlastic01–31 are A20–A50. All TIF 4096.
- **MC024 true leather** (B H(exr) N R, TIF): A002 SoftWhite (187,184,171, roughness 0.51), A022 LightGray (138), A024 Charcoal (84), A023 BlackSmudge (63), A030 WarmWhite (180,171,156; has M).
  - Tile ≈ 35 mm. Params: subsurface_scale 0.005, randomwalk.
  - A027 LeatherBlack is only 2048.
- **MC005_A030 HeadphonePad01.** B N R. Base 23, roughness 0.45, sheen colour (0.96,0.98,1.0). A ready black pad.
- MC001_A257 DLeatherWhite (231,221,210) and A239 DLeatherBlack (33).

### 10. Black rubber/foam
- **MC001_A308 DRubber.** B N R S. Base (37,37,37), roughness 0.33, stipple pattern, IOR 1.4. Used by the user at 60 mm (Server, sheen 0.2) and 30 mm (Yogo feet). Tile 25–30 mm for small parts.
- **MC005_A013 CameraGrip01.** B H N R, base 28. MC034_A002 RecycledRubberYogaMatBlack (base 70).
- **Foam:** MC025_A011 / A012 PolystyreneFoamBlack (B Hx N R Sd256 Sw256), MC041_A010 CraterFoamCharcoal.

### 11. Red signal paint/plastic
- **MC001_A303 DRedPlastic.** B N R. Base (231,31,31), roughness 0.09 (glossy).
- **MC001_A305 DRedPlasticDull.** Base (185,19,19), roughness 0.93. Too matte, so scale the roughness sampler ×0.5.
- A301 DPlasticResin (170,0,0). A306 has a bump map.
- MC005_A026 GlossyPlastic04: base (142,35,40), roughness 0.07, subsurface 0.3.
- The emissive red dot is not GSG. Base it on `PXB_dot_glow` / `PXB_knob_orange` (0.93,0.26,0.04, with SSS).

### 12. Metal flake / sparkle / pearl / glitter / micro-crystal maps
- **Available:** MC002_A012 CopperSparkled, MC002_A016 GoldSparkled, MC002_A021 SilverSparkled. MC005_A076/A077/A078 SpeckledPlastic01–03 (A076 is dark, base 46). MC027 *Speckled* plastics. MC038_A008 RecycledPlasticPinkFlakes (150,136,142). MC064_A044 / A045 MetallicSplatterAbstractPaint (blue / pink with M maps, coloured). MC054_A007 SpeckledChampaign (3D-print look).
- **Texture kind (all imperfection maps, no flakes):**
  - TC001 Scratches (50, JPG).
  - TC002 Smudges (JPG).
  - TC003 Crust.
  - TC005 Dust.
  - TC008 Frost01–10 (4096, 16-bit TIF): good for frosted-glass roughness.
  - TC012 Subtle* (20 maps, 8192 16-bit TIF): AlmostClean, DustyBits, FingerMarked, Gritty, Worn and others. These are the best product-grade imperfection maps. TC012_A001 is 132 MB.
  - HC011_A036 "ALM2Sparkle" is an area-light map, not a material.

## Reuse of the user's existing materials
**Live Yogo doc (59 materials):**
- **White metal parts:**
  - YKB_alu_knob (0.90,0.91,0.91, metal 1, roughness 0.24)
  - YKB_alu_bottom (0.86,0.87,0.87, metal 1, roughness 0.40)
  - YKB_knob_cap (0.88,0.89,0.89, metal 1, roughness 0.18)
  - These have no textures. Upgrade them to MC001_A141 / MC005_A004 maps.
- **Other metals:**
  - YKB_anod_port (0.13,0.14,0.14, metal 1, roughness 0.36): black anodized.
  - YKB_steel (0.76 grey), YKB_nickel, YKB_tin, YKB_gold, YKB_copper, YKB_screw_black, YKB_battery.
- **Soft translucents:**
  - YKB_silicone, YKB_sw_rubber, YKB_film_pet, YKB_sw_muffler: translucent silicone/rubber.
  - YKB_silicone_feet: black rubber (0.035, roughness 0.75).
  - YKB_foam_black (0.04, roughness 0.95), YKB_foam_gray, YKB_foam_ixpe, YKB_foam_poron.
- **Plastics:**
  - YKB_plastic_white (0.90, roughness 0.40), YKB_plastic_black, YKB_keycap.
  - GSG_MC001_A313_DWhitePlastic: tile 45 mm, `object`.
  - GSG_MC005_A056_Plastic01 (black) and GSG_MC005_A035_KeyboardKey01: tile 40 mm, world.
- **Glass:** YKB_display_cover and YKB_CLASSIC_display (frosted, see item 5). YKB_sw_lightguide and YKB_led_lens are light-pipe glass.
- **Screens:** YKB_display_pixels (emission 125, `display_clock_16x14.png`), YKB_screen_cell (emission 9), YKB_display_led, YKB_BL_core and YKB_BL_halo (backlight) are pixel-screen candidates.
- **Not reusable as shipped:** the pastel A313 copies, the orange/green D plastics, and the green-tinted CAluminumBrushed01. The last one is re-tintable.

**Pixbar `pxb_mats.py` recipes** (not live):
- housing_white (0.885,0.88,0.865, roughness 0.36, diffuse roughness 0.3, SSS 0.08): good soft white.
- front_smoked: the smoked-glass recipe from item 6.
- frosted_pc, clear_pc, light_pipe, silicone_clear, silicone_grey.
- pixel_screen (`screen()`): emission ← Texture, weight 45. Use it as the screen material, with a `display_clock_52x16.png`-style image.
- Others: knob_orange, dot_glow, collar_metal, bar_black.

**Other user assets:**
- `Logitech_IRIS/Assets/Textures`: scratches.png 2048, spun_corner.png 1024 (concentric lathe rings), pad_speckle.png 1024, sensor_mesh.png 512. Recipes in `ir_mats.py`: black_anod, rubber_pad, glass_black, lens_pupil with thin film at 380 nm / IOR 1.4.
- `Server_motherboard/Assets/Textures`: brushed_2k, cloud_2k, grain_2k (all 2048). Generator: `C4D/tools/sm_textures.py` (pure python3, takes a seed). Documented tiles: brushed 30–120 mm, grain 8–40 mm, cloud 30–200 mm (roughness ±0.1 via Change Range).
- The thin-film wiring is documented in `weaver_claude/skills/references/c4d-redshift.md`: Maxon Noise → rsmathrange → `thinfilm_thickness`.

## Missing in GSG, to author procedurally
- **True metal flakes.** RS node IDs exist in this C4D 2026.4 (`list_graph_node_assets`):
  - `com.redshift3d.redshift4c4d.nodes.core.flakes`
  - `…core.carpaint` and `carpaintmaterial@c7ec42b9-…`
  - `…core.maxonnoise`, `rsnoise`
  - `…core.bumpblender`, `materialblender`
  - `…core.curvature`, `roundcorners`, `sprite`
  - The Flakes port names are unverified. Plan: Flakes or cell noise drives a fine bump plus a roughness modulation at 0.02–0.05 mm over MC001_A141.
  - `roundcorners` gives edge-shading rounding, which helps the chamfer look.
- **Pearl/iridescent.** No such maps; use thin film as in the user's recipes.
- **Smoked black glass**, **frosted silicone** and the **red LED / signal dot**: author from the PXB/YKB/IR recipes above.
- **4K procedural textures.** The user's own are 2K. Re-run `sm_textures.py` / `ir_textures.py` at 4096 with a flake generator added. Magnific upscaling was NOT used.
- **Tactile bumps (volume).** Modelled geometry under SDS, not shader work.

## Suggested stack
1. White body: MC001_A141, 32 mm.
2. Titanium trim: MC007_A105.
3. Scroll wheel/knob: MC005_A041 or A038, 26 mm, `object`.
4. Soft-touch parts: MC001_A315 or MC058_A12 with a white override.
5. Frosted window: MC075_A065 with edits.
6. Smoked window: PXB_front_smoked recipe.
7. Fabric: MC067_A036.
8. Cushion pad: MC005_A030.
9. Black rubber: MC001_A308.
10. Red: MC001_A303.

## KEY FACTS
- gsg_guide tool fails (no .claude/skills/gsg-library/SKILL.md in vault); equivalent guide is weaver_claude/skills/gsg-library.md. Loader: Projects/claude/Yogo_pro_keyboard/C4D/src/ykb_gsg.py (same copy tc_gsg.py in T_cubes). GSG library on E:\ is the only texture library; all verified 4K maps are real 4096x4096 (some data maps are tiny: Sd128/256, Al256, Sc256).
- Best white bead-blast aluminium: MC001_A141 CAluminumPowdered (B/M/N/R 4096 JPG, base avg 245,247,246, roughness 0.29, metal 1); runner-up MC005_A004 AnodizedSilver (base 183, roughness 0.49, flat metal); MC007_A001 Aluminum01 has specular edge colour map (base 239, roughness 0.26).
- Sparkle accent: MC002_A021 SilverSparkled (4096 B/M/N/R, base 251,250,245, roughness 0.20, coat_roughness 0.01) - coarse glitter, blend 10-20% over MC001_A141; also MC002_A012 Copper / A016 Gold Sparkled. No pearl/iridescent/glitter/micro-crystal maps exist in GSG (confirmed by name search); TC textures are only scratches/smudges/dust/frost/subtle imperfection.
- Titanium: MC007_A105 Titanium01 (B/M/N/R/E, base 180,175,171, roughness 0.34, coat 0.48) and A106 TitaniumClean01 (polished, roughness 0.09); MC078_A002 TitaniumBasicMetal is params-only (0.903,0.868,0.848, roughness 0.3).
- Knurl for scroll wheel/knob: MC005_A038-A041 KnurlMetal01-04 (B/H/M/N/R 4096; ~64-72 cycles per tile, so tile ~26 mm gives ~0.4 mm pitch, estimate), MC044_A015 EmbossedMetalKnurl (TIF 4096 with aniso maps); MC007_A064 is a decorative engine-turned disc pattern, not plain brushing.
- MC058 molded-plastic family (A65/A66 Pebble, A20-A50 LeatherMolded, A12 FineMist, A15 Grit, A73 Stipple) has ONLY a 4096 normal.tif + params (base 0.10, roughness 0.385): usable as pebble/soft-touch micro-texture but base colour must be overridden manually (make() tint is ignored without a basecolor map).
- Soft-touch white with real maps: MC001_A315 DWhitePlasticDull (base 204, roughness 0.42), MC005_A057 Plastic02 (199, 0.38), MC005_A035 KeyboardKey01 (201,201,193; 0.34); WARNING MC001_A313 DWhitePlastic (already used by user) is glossy (roughness 0.06). MC027_A024 P5 FineWrinkle (178, 0.25, SSS).
- Glass is params-only (MC075, no textures): frosted = A065 TemperedFrostedGlass (IOR 1.52, rough 0.35), A073 BorosilicateFrosted, A067 SapphireFrosted (IOR 1.77); loader sets refr_depth 6-50 mm (too thick, override) and coat 0.5/0.45 (set 0). User's live frosted glass YKB_CLASSIC_display uses roughness 0.117, IOR 1.77.
- No truly dark smoked glass in MC075 (darkest neutral is SmokeyGlass transmission_color 0.68). Use the user's own recipe PXB_front_smoked (base 0.015, rough 0.04, transmission 1, refr_color 0.24, IOR 1.58, refr_depth 2 mm) or IR_glass_black (base 0.003, rough 0.10, coat 1/0.03 + scratches bump 0.012 @40 mm).
- No silicone in GSG: reuse YKB_silicone / YKB_sw_rubber (live in Yogo scene) or PXB_silicone_clear (roughness 0.5, transmission 0.6, refr_roughness 0.4, depth 1 mm) + MC058 micro-normal.
- Fabric/leather/rubber picks: MC067_A036 WhiteJerseyKnit (B/N/R/Sw/S 4096), MC032_A011 PlushGridFabricWhite, MC032_A019 PerforatedFabricWhite (opacity), MC005_A072 SpeakerMesh01 (opacity hex mesh, black); leather MC024_A002/A022/A024/A023 (4096 TIF + height EXR); MC005_A030 HeadphonePad01 (black pad); rubber MC001_A308 DRubber (4096 B/N/R/S, roughness 0.33); foam MC025_A011/A012 black.
- Red: MC001_A303 DRedPlastic (231,31,31, roughness 0.09, glossy), A305 Dull (185,19,19, roughness 0.93 too matte), A301 resin (170,0,0), MC005_A026 GlossyPlastic04 (142,35,40, SSS 0.3); emissive red dot must be authored (PXB_dot_glow / PXB_knob_orange recipes).
- Live Yogo doc (59 mats) reusable: YKB_alu_knob/alu_bottom/knob_cap (flat white metal 0.86-0.90, roughness 0.18-0.40), YKB_anod_port, YKB_silicone*, YKB_sw_rubber, YKB_foam_*, YKB_display_cover (frosted: IOR 1.49, rough 0.287, refr 0.95), YKB_display_pixels/screen_cell/BL_* (emissive pixel screen), GSG_MC001_A313_DWhitePlastic (45 mm object), GSG_MC005_A056/A035 (40 mm world). Pixbar_clock is NOT open: PXB_* values come from Pixbar_clock/C4D/src/pxb_mats.py (pixel_screen emission<-Texture weight 45, front_smoked, frosted_pc, housing_white).
- Redshift nodes confirmed in C4D 2026.4 via list_graph_node_assets: nodes.core.flakes, carpaint (+carpaintmaterial), maxonnoise, rsnoise, bumpblender, materialblender, curvature, roundcorners, sprite - procedural metal-flake path is available; Flakes port names unverified (help.maxon.net blocked).
- User's own authored textures are only 2K/1K (Server_motherboard brushed/cloud/grain_2k.png via sm_textures.py; Logitech_IRIS scratches.png 2048, spun_corner.png 1024, pad_speckle 1024); 4K versions need re-running generators at 4096 (no Magnific used). Product-grade imperfection maps in GSG: TC012 Subtle* (8192 16-bit TIF), TC008 Frost (4096 16-bit TIF).
- Tile conventions from user's scenes: Yogo plastics 40-45 mm, case world 90 mm, knob/object 30-40 mm; Server scene used 100-200 mm for big metal parts (too coarse for small products). User tint = float RGB multiplier (e.g. 0.35,0.51,0.34); user also ran roughness sampler multiplier 1.5 on CAluminumBrushed01, i.e. GSG aluminium is too glossy for his taste.

## FILES
