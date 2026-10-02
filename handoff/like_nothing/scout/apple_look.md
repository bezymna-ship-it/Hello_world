# Apple close-up look in Redshift terms: recipe sheet for Like_nothing

Tags: [V] verified in this C4D 2026.4 or vault, [W] web-search snippet, [R] my recommendation, needs a test render.

## 0. Read first

- **INCIDENT.** I ran a pure-Python 512x512 pixel-loop benchmark in `exec_python` (in-memory only, nothing inserted or saved). It hung C4D for more than 60 s.
  - The c4d26 `session_id` then changed from `6012a5d34d1a` to `05e5d5625822`. The new session started 11:20:42 local, so C4D or its plugin was restarted.
  - The empty "Untitled 3" document is gone. `Yogo_pro_keyboard_v008_anim_codex.c4d` was reloaded from disk: changed=False, file mtime 10:50:32.
  - Before the restart that doc reported changed=True, so any unsaved in-memory edits may be lost. I only read values, but a read-only RS Light description enumeration had triggered an "exec_python: document changed" warning.
  - Do not run per-pixel Python loops inside `exec_python`.
- **Web access was mostly blocked.** WebFetch returned EGRESS_BLOCKED for apple.com, help.maxon.net, docs.redshift3d.com, greyscalegorilla.com, artivoxa, xo3d, lightmap and petapixel.
  - Only WebSearch snippets and raw.githubusercontent.com worked.
  - Everything marked [V] below comes from the live install (`F:\Cinema4d_2026_4\Redshift\res\core\Data\Strings\en-US\rscore.json`, node assets, doc settings, vault).
- **Apple facts [W, snippets only]:**
  - AirPods Max: "anodized aluminum cups", stainless-steel frame wrapped in soft-to-the-touch material, breathable knit-mesh canopy.
  - AirPods Max 2 (March 2026): Midnight, Starlight, Blue, Purple, Orange.
  - iPhone 17 Pro: 7000-series aluminium unibody, anodized, matte and fingerprint-resistant, Ceramic Shield 2 on front and back.
  - Bead-blast Ra: fine 0.8-1.6 um, standard 1.6-3.2, coarse 3.2-6.3. Type II anodize film is 5-25 um.
  - **Not found:** Magic Keyboard/Mouse finish, and any Apple statement about micro-blasting.

## 1. Verified environment facts

- Scene unit is 1 mm (display cm). RS values (`refr_depth`, `ms_radius_scale`, TriPlanar scale = 1/tile_mm) follow scene mm. Round Corners radius 0.3 means 0.3 mm. This is not yet render-tested.
- Standard Material port ids (82 read from a live graph, prefix `...nodes.core.standardmaterial.`):
  - Base and reflection: `base_color`, `metalness`, `refl_color`, `refl_roughness`, `refl_ior`, `refl_aniso`, `refl_aniso_rotation`, `refl_enablemultiscattercomp`.
  - Diffuse and sheen: `diffuse_model` (Oren-Nayar, d'Eon, EON), `diffuse_roughness`, `sheen_weight`, `sheen_roughness`, `sheen_color`.
  - Coat and film: `coat_weight`, `coat_roughness`, `coat_ior`, `coat_color`, `coat_bump_input`, `thinfilm_thickness` (nm), `thinfilm_ior`.
  - Refraction and SSS: `refr_weight`, `refr_color`, `refr_roughness` (labelled "Extra Roughness"), `refr_thin_walled`, `refr_depth`, `refr_abbe`, `ms_amount`, `ms_radius`, `ms_radius_scale`, `ms_color`, `ms_mode`, `ms_include_mode`.
  - Output: `emission_weight` (labelled "Radiance W/sr/m^2"), `emission_color`, `opacity_color`, `bump_input`, `overall_color`.
- Other port ids:
  - `bumpmap`: `input`, `inputtype` (0 height, 1 tangent normal), `scale`, `factorinobjscale`, `flipy`, `unbiasednormalmap`. Output `out`.
  - `triplanar`: `imagex`, `scale`, `projspacetype` (1 = object), `blendamount`.
  - `texturesampler`: `tex0`, `scale`, `mip_bias`, `filter_enable_type`.
  - `bumpblender`: `baseinput`, `bumpinput0..2`, `bumpweight0..2`, `additive`. Output `outdisplacementvector`.
  - `roundcorners` (from `Mebel_stuliya/C4D/scripts/rs_nodes.py`): `radius`, `out`. Strings also list `numSamples`, `sameObjectOnly`.
- **RS Flakes exists** (`com.redshift3d.redshift4c4d.nodes.core.flakes`, "RS Flakes").
  - Inputs: Scale, Density, Randomize, Seed, Pattern (Voronoi/Dots), Flakes Size, Size Variance, Coord Space (World/Object/UV), 3D Flakes (Depth, Step Size, IOR), Distance Behavior (Blend Minimum/Maximum).
  - Outputs: `outNormal`, `outAlpha`, `outFlakesBlend`, `outFlakesID`. Only `inseed` and `outnormal` were confirmed by a string scan of the plugin binary.
  - The other port ids are inferred as lowercase labels. Introspect them on a scratch material before building.
- Other nodes present:
  - `carpaint`, which has a Metallic Flakes group (flake_color/weight/gloss/density/scale/decay/strength).
  - `openpbrmaterial`, which has `fuzz_*`, `thin_film_*` (um) and `coat_darkening`.
  - `curvature` (Convex/Concave, radius), `maxonnoise` (types include "Sparse convolution", "Dents", "Voronoi 1-3"), `rsnoise`, `jitter`, `tiles`, `rscolorrange`, `rsmathmix`.
- **User presets** (`FINAL_3090Ti`, `PREVIEW_3090Ti`): automatic sampling OFF, denoise engine 3 = OptiX (OIDN quality 1), GI Brute Force/Brute Force, Gauss filter 2.5, Max Subsample Intensity 4.0, Bump Bias -2.0. OCIO is ACEScg, sRGB, "ACES 1.0 SDR-video". RS Dome multiplier is 0.394.
- **Pitfall in existing code:** `ykb_studio.redshift_settings()` sets `ENABLE_AUTOMATIC_SAMPLING=True` and OIDN, which contradicts the user's rule. The base-scene code must set it to False explicitly.

## 2. Material recipes

Colours are linear (ACEScg, so neutrals are identical). Convert chromatic colours with `ykb_gsg.lin()`/`srgb8()`. Library codes below are GSG.

| Material | Recipe |
|---|---|
| **WHITE_METAL_BLAST** (cups, case, mouse shell, phone frame) | base 0.88/0.885/0.89 (Al F0 is 0.913/0.922/0.924, and 0.86-0.90 is the user's `YKB_alu_*` range); metalness 1; `refl_color` 1,1,1 (edge tint); `refl_ior` 1.5. Roughness 0.40 mean, +/-0.035 mottling from Maxon Noise (Object coords, ~18 mm feature size), dimple floors -0.045. Coat 0.35, IOR 1.6, roughness 0.45 for an anodic sheen (0 for raw aluminium). Normal 4K via TriPlanar (object space, scale 1/25 or 1/40), Bump Map `inputtype` 1, `scale` 0.4-0.8. Cross-check, GSG roughness means: SandblastedAluminum01/02 (MC005_A068/069) 0.41/0.42 with specks 0.17-0.20 and metallic 0.88; AnodizedSilver (MC005_A004) flat 0.485 at normal strength 0.4. |
| **CHAMFER_POLISH** (diamond-cut edge line) | base 0.92, metalness 1, roughness 0.07-0.12, no bump. Either a separate face selection or a Curvature mask (Convex, radius 0.4 mm) that mixes roughness 0.40 to 0.09. Optional film: `thinfilm_thickness` 120-180 nm, ior 1.5. |
| **GRAPHITE** (2nd colourway) | base 0.05/0.05/0.055, metalness 1, roughness 0.38 (user's anod_port base 0.13). |
| **RED_ACCENT** | Anodised: base ~0.58/0.013/0.010, metalness 1, roughness 0.36, coat 0.5. Lacquer tab: base 0.62/0.012/0.010, metalness 0, roughness 0.30, coat 1.0 (roughness 0.06, IOR 1.5). |
| **GLASS_FROST_COVER** (over the LED matrix, 1-1.2 mm) | `refl_ior` 1.52, `refl_roughness` 0.12-0.18 (etched top), `refr_weight` 1, `refr_color` 0.96/0.97/0.98, `refr_roughness` 0.30-0.40 (diffuses pixels), `refr_thin_walled` ON (keeps pixels aligned and is cheaper). Glass `refr_samples` 16-32. Add TC012_A005 / A011 / A019 (Subtle* smudge maps) at 0-0.04 roughness. Reference for a solid slab: GSG MC075_A031 SmokeyFrostedGlass has roughness 0.35, transmission 1, depth 6 mm, transmission colour 0.679/0.687/0.700, scatter 0.095/0.087/0.067, coat 0.5 / 0.45 / IOR 1.3. |
| **SMOKED_GLASS** (black panel) | As GLASS_FROST_COVER but `refr_color` 0.16-0.30, `refl_roughness` 0.08-0.12. |
| **LED_PIXEL** | base 0.005; `emission_color` 1/0.93/0.82; `emission_weight` 2.4 (the Pixbar `pixel_screen` value; 4.0 for `display_led`). Red glyph: colour 1/0.02/0.01, weight at most 3 (ACES shifts hue on saturated bright reds). Off pixels are 0.02x. Use the UV-of-cell-centre trick (`pixel_screen`). |
| **SILICONE_SOFT_TOUCH** (tactile bumps, mouse grips, keyboard skin) | base 0.80 white or 0.045 black; `diffuse_model` EON, `diffuse_roughness` 0.55; `refl_ior` 1.43, `refl_weight` 0.7, `refl_roughness` 0.60; sheen 0.25 (roughness 0.45, colour ~base). SSS `ms_amount` 0.20, `ms_radius_scale` 0.8 mm, radius colour 1/0.75/0.65, mode Random Walk. For a translucent bump over an LED: `ms_amount` 0.5, radius scale 1.5-2, `refr_weight` 0.35 thin-walled. Bump: micro-skin normal at 10 mm tile, scale 0.10-0.15. |
| **PU_LEATHER_PEBBLE** (headband, cushions) | base 0.78 white or 0.035 black; roughness 0.50 +/-0.06, IOR 1.45, coat 0.12 (roughness 0.35), sheen 0.10. Pebble normal 4K at 40 mm tile, scale 0.45. Library: HeadphonePad01 MC005_A030 (sheen colour 0.955/0.981/1.0), LeatherSoftWhite MC024_A002. |
| **KNIT_FABRIC** (canopy) | GSG WhiteJerseyKnitCottonFabric MC067_A036 (4K TIFs, thin_walled), tile 10-14 mm. `diffuse_roughness` 0.8, roughness 0.65, sheen 0.6 (roughness 0.35). Alternative: OpenPBR `fuzz_weight` 0.6. |
| **SPEAKER_GRILLE** | GSG SpeakerMesh01 MC005_A072 (basecolor, height, normal, opacity, roughness; sheen 0.25), or a generated hex perforation (hole 0.9 mm, pitch 1.2 mm, 6 mm tile) over black foam (0.035 / roughness 0.95). |

## 3. Metal flake and sparkle (strongest first)

1. **Baked into the maps.** The GSG sandblasted maps already carry sparkle: roughness specks at 0.17-0.20 against a 0.41 mean, and metallic dips and peaks. My generator reproduces this (see section 7).
2. **RS Flakes into the bump chain.** `flakes.outnormal` goes to `bumpblender.bumpinput1`, weight 0.35-0.6, additive, into `bump_input`. Never feed it through a Bump Map node.
   - Pattern Voronoi, Coord Space Object, Density 0.2-0.35, Randomize 0.9, unique seed per material.
   - Scale: start near 12-20 and judge at 100 mm macro. The original OSL default is 0.2 with a 0-25 range, so verify the semantics.
   - Blend Min/Max is a distance fade: fade out beyond ~800-1500 mm to avoid shimmer in motion.
3. **Thin-coat gating.** `coat_weight` = `rscolorrange(flakes.outFlakesBlend or outAlpha)` peaking at 0.8; `coat_roughness` 0.06, `coat_ior` 1.6. Only the flakes get a glossy layer over a matte base.
4. **RS Car Paint node's Metallic Flakes group**, blended in through a Material Blender. This is cheaper but less controllable.
5. **Render caveat.** Max Subsample Intensity 4.0 (both presets) mutes glints. Use 8-12 for HERO and watch fireflies.

## 4. Edges

- **Round Corners:** radius = 0.5x the geometry bevel width, i.e. 0.15-0.25 mm for a 0.3-0.5 mm chamfer. `numSamples` 8 for LOW, 16-32 for HERO. `sameObjectOnly` ON.
- It only softens real creases and cannot make wide bevels. Disable it on parts thinner than 2R.
- The SDS bevel stays the primary highlight carrier.
- Feed it through the bump chain: `roundcorners.out` goes to `bumpinput0` with weight 1.

## 5. Studio lighting and camera

Let S be the product's largest dimension. All lights are RS Light type 3 (Area), Units Image (the user's convention). Hide dome and lights from the camera: `CAMERA_RAY_CONTRIBUTION_SCALE` 0.

| Light | Size | Placement | Intensity |
|---|---|---|---|
| KEY | ~3S x 2S, spread 1 | 45 deg off-axis, 35 deg up, distance 2.2S | 1.0 reference |
| STRIP L/R | 0.35S x 3S (~1:8) | +/-110-125 deg, 10 deg up, distance 1.6S | 2.5-4x KEY (edge highlight on chamfers) |
| TOP scrim | 3S x 3S | overhead, distance 1.8S | 0.6x |
| Black flags | n/a | in front of glass | negative fill, so LEDs and black reflections read |
| Dome | n/a | HDRI | 0.15-0.30 (user 0.394 is the ceiling) |

- Area-light textures (GSG): HC010_A018 SoftBoxGradient, A025 SoftBoxSoftEdge, A019 SoftBoxGridLarge, A010 LEDPanel, A009 KinoBank.
- HDRIs (GSG, picked by eye from the contact sheets): HC006_A002 (two tall panels), HC006_A035/A037 (strip pairs), HC005_A025 / A069 / A073 (single strip or ring on black), HC005_A064-066 (twin strips on grey).
- Light samples: area 16 -> 32-64 for HERO; dome 64 default.
- Backdrop: seamless cyclorama via `ykb_studio.cyclorama` (r=700 mm), 0.80 / roughness 0.75 white or 0.004 black.
- Target scene-linear values: white diffuse 0.7-0.8, strip reflection peaks 3-6, glass blacks 0.002-0.01.
- View transform: keep "ACES 1.0 SDR-video". For a pure-white Apple cyc use the "Un-tone-mapped" view per `c4d-redshift.md`, or push the cyc to linear 8-16.
- **RS Camera (type 1057516)**: `RSCAMERAOBJECT_SENSOR_SIZE` 36x24, ISO 100, EV 0, vignetting 0 (0.05-0.1 for moody shots), focus distance in mm, f/8 default, Bokeh off. Focal length 100 mm (hero) to 135 mm (macro).
- DOF is about 2Nc(1+m)/m^2 with c = 0.03 mm:
  - m = 0.2, f/8 gives ~12 mm; f/11 gives ~17 mm.
  - m = 0.5, f/8 gives ~3 mm; f/16 gives ~5.8 mm.
  - RS has no diffraction, so f/11-16 stays sharp.
- Bloom, glare and streaks off. LED glow comes from a halo card (the `YKB_BL_halo` approach). If post bloom is unavoidable: threshold at least 1.0, intensity at most 0.05 (RS PostFX `BLOOM_*` exist, defaults unread). PostFX colour-management params are deprecated in 2026, so use the OCIO view instead.

## 6. Render presets (all: auto sampling OFF, bucket 512, GI Brute Force/Brute Force)

| | LOW | MID | HERO 4K |
|---|---|---|---|
| Resolution | 960x540 | 1920x1080 | 3840x2160 |
| Threshold | **0.30** | 0.08 | 0.01-0.02 |
| Samples min/max | 4/32 | 8/96 | 16/512 |
| BF GI rays | 16 | 32 | 128-256 |
| Depth combined/refl/refr/transp | 6/2/5/16 | 8/4/6/32 | 12/5/8/64 |
| Denoise | OptiX, Balanced | OptiX or OIDN Balanced | OIDN High (OptiX is also acceptable) |
| Max subsample intensity | 4 | 4 | 8-12 |

- The user's FINAL_3090Ti used refraction depth 4 and reflection 3. That is too low for metal-in-glass-in-metal, hence the higher HERO depths.
- Render time scales with pixels. IRIS at 1080p / 0.012 took about 7 min, so 4K is roughly 4x, around 28 min, as a scene-dependent estimate.
- Keep Bump Bias -2.0 and the Gauss filter (2.0-2.5). EXR 16-bit with DWA 45.
- Texture cache: the doc has GPU Texture Cache Max 256 MB, 15 % free memory, CPU 4096 MB. Raise the GPU cache to 1-2 GB for ~30 4K maps (not benchmarked).

## 7. Textures to generate and how

**4K maps needed** (16-bit PNG, Raw colour space for everything except colour maps):

- `blast_normal`, `blast_rough`, `flake_normal` and flake ID/mask: 40 mm tile = 102 px/mm, so an 80 um dimple is 8 px. Use a 25 mm tile on small parts.
- `anod_cloud`: 2K at 120 mm.
- `silicone_skin_normal`: 10 mm.
- `pebble_leather` height + normal: 40 mm. The proven `hb_textures.leather()` is 2048 at 40 mm and needs about 4x the memory at 4096.
- `hex_perf` alpha: 6 mm.
- Library: knit is MC067_A036. Glass imperfections are TC012_A005 / A011 / A019.

**Where to generate.** C4D's Python 3.11.4 has no numpy, PIL, cv2, scipy or imageio. Use external `python3` + numpy + PIL, as `Hasselblad_500/C4D/tools/hb_textures.py` does, writing to `Assets/Textures`. Its tileable `value_noise`, `voronoi`, `blur_wrap` and `leather` are reusable. For micro-grain without bitmaps, use RS nodes: Maxon Noise "Sparse convolution" or "Dents" plus RS Flakes.

**Tested in the sandbox** (numpy 2.4.6; sketch at `/tmp/claude-0/-home-user-Hello-world/55ecca3a-582f-59d9-86bf-be34a7db2932/scratchpad/lnk_tex_sketch.py`). The full 4096 blast set (normal, rough, flake normal) takes 14 s and 1.06 GB of RAM, with 1.9 % flake coverage and roughness 0.19-0.55 (mean 0.396). Core of the method:

```python
def band_noise(n, wl_px, bw=0.5, seed=1):   # tileable band-pass noise
    f=np.fft.rfftfreq(n)[None,:]; g=np.fft.fftfreq(n)[:,None]
    r=np.sqrt(f*f+g*g)+1e-9; w=np.exp(-0.5*(np.log(r*wl_px)/bw)**2); w[0,0]=0
    a=np.fft.irfft2(np.fft.rfft2(np.random.RandomState(seed).randn(n,n).astype(np.float32))*w,s=(n,n))
    return (a-a.mean())/a.std()
# height = band_noise(wl=2*grain_px) + 0.35*band_noise(wl*0.4); normal via np.roll gradients (tileable)
```

- Flakes: stamp about 24k random discs (r 1.4-2.6 px) with a 4-18 deg random tilt, roughness 0.16-0.22.
- **Calibration needed:** my normal strength 0.55 gives R/G spanning 29-222, while GSG Sandblasted spans 85-186. Use strength ~0.30.
- The knit generator in the sketch is crude (a zigzag). Use the GSG fabric instead.

## 8. Open items

- Introspect the Flakes, Round Corners and Curvature graph port ids on a scratch material.
- Test-render the Round Corners unit (mm) and the Flakes Scale semantics.
- Check the DOF-enable behaviour on the RS Camera.
- Confirm the Apple-specific finishes visually in the first hero shot.

## KEY FACTS
- INCIDENT: a pure-Python 512x512 pixel-loop benchmark via exec_python hung C4D >60 s; c4d26 session_id changed 6012a5d34d1a -> 05e5d5625822 (restart ~11:20:42 local); 'Untitled 3' gone, Yogo_pro_keyboard_v008_anim_codex.c4d reloaded from disk (changed=False, mtime 10:50:32); it had changed=True before, so unsaved edits may be lost. Never run per-pixel Python loops in exec_python.
- Web access: WebFetch EGRESS_BLOCKED for apple.com, help.maxon.net, docs.redshift3d.com, greyscalegorilla.com, artivoxa, xo3d, lightmap, petapixel; only WebSearch snippets and raw.githubusercontent.com worked. Magic Keyboard/Mouse finish and any Apple micro-blast statement NOT found.
- Apple facts from search snippets: AirPods Max anodized aluminum cups + stainless frame with soft-touch wrap + knit-mesh canopy; AirPods Max 2 (Mar 2026) colours Midnight/Starlight/Blue/Purple/Orange; iPhone 17 Pro 7000-series aluminium unibody, anodized matte, Ceramic Shield 2 front+back; bead-blast Ra fine 0.8-1.6 um / std 1.6-3.2 / coarse 3.2-6.3; Type II anodize 5-25 um.
- RS Flakes node EXISTS: com.redshift3d.redshift4c4d.nodes.core.flakes ('RS Flakes'). Inputs inScale, inDensity, inRandomize, inSeed, inPattern(Voronoi|Dots), inFlakeSize, inVariance, inCoordinateSpace(World|Object|UV), inDepth/inStepSize/inIOR (3D flakes), inFlakesMinimum/Maximum (distance fade); outputs outNormal, outAlpha, outFlakesBlend, outFlakesID. Only 'inseed' and 'outnormal' confirmed as graph strings in redshift4c4d.xdl64; the rest inferred, need introspection. Source: Redshift/res/core/Data/Strings/en-US/rscore.json.
- Flakes outNormal goes to bumpblender.bumpinput* (additive) -> standardmaterial.bump_input, never through a Bump Map node. Also present: carpaint node (Metallic Flakes group), openpbrmaterial (fuzz_*, thin_film_*), curvature, roundcorners (radius, numSamples, sameObjectOnly, out), maxonnoise (Sparse convolution, Dents, Voronoi types), rsnoise, jitter, tiles.
- Standard Material port ids verified (82 ports): base_color, metalness, refl_color/refl_roughness/refl_ior/refl_aniso, coat_weight/roughness/ior/color/bump_input, sheen_*, thinfilm_thickness(nm)/thinfilm_ior, refr_weight/color/roughness/thin_walled/depth/abbe, ms_amount/radius/radius_scale/color/mode/include_mode, emission_weight (Radiance W/sr/m^2), diffuse_model (Oren-Nayar, d'Eon, EON), bump_input. bumpmap: input, inputtype(0 height,1 tangent normal), scale, factorinobjscale, flipy. triplanar: imagex, scale, projspacetype(1 object), blendamount.
- Scene unit is 1 mm (display cm), so Round Corners radius 0.15-0.25 for a 0.3-0.5 mm chamfer (about 0.5x bevel width), numSamples 8 LOW / 16-32 HERO, sameObjectOnly ON. Unit assumption not yet render-tested.
- WHITE_METAL_BLAST: base 0.88/0.885/0.89 linear, metalness 1, refl_color white, roughness 0.40 +/-0.035 (GSG MC005_A068/069 means 0.41/0.42 with specks 0.17-0.20; AnodizedSilver MC005_A004 flat 0.485, normal strength 0.4), coat 0.35 IOR 1.6 rough 0.45, 4K grain normal via TriPlanar object-space scale 1/25-1/40, Bump scale 0.4-0.8. Sparkle: bake into maps, or RS Flakes via bump blender, or flake-gated coat (rough 0.06), or Car Paint node flakes.
- Max Subsample Intensity 4.0 and Max Secondary Ray Intensity 4.0 in the user's presets mute metal glints; raise to 8-12 for HERO only. ykb_studio.redshift_settings() sets automatic sampling True and OIDN, contradicting the user's rules; base-scene preset code must set ENABLE_AUTOMATIC_SAMPLING False explicitly.
- User presets read from the Yogo doc: PREVIEW_3090Ti 540x808, thr 0.6, 4/32, BF 16 rays, depth 6/2/5/16, bucket 512; FINAL_3090Ti 720x1077, thr 0.04, 8/128, BF 64, depth 8/3/4/32, bucket 256. Both auto-sampling OFF, GI BF/BF, OptiX denoise (engine 3, Balanced), Gauss 2.5, bump bias -2.0, OCIO ACEScg/sRGB/'ACES 1.0 SDR-video'. Proposed LOW thr 0.30 4/32 bucket 512; MID 0.08 8/96; HERO 4K 0.01-0.02 16/512, BF 128-256, depth 12/5/8/64.
- Glass: GLASS_FROST_COVER = refl_ior 1.52, refl_roughness 0.12-0.18, refr_weight 1, refr_roughness 0.30-0.40, refr_thin_walled ON, refr_color 0.96-0.98; smoked variant refr_color 0.16-0.30. GSG MC075_A031 SmokeyFrostedGlass: rough 0.35, depth 6 mm, trans colour 0.679/0.687/0.700, scatter 0.095/0.087/0.067, coat 0.5/0.45/IOR 1.3. Imperfection maps TC012_A005/A011/A019.
- LED pixels: emission_weight 2.4 (Pixbar pixel_screen), 4.0 (YKB display_led); red glyph colour 1/0.02/0.01 weight <=3 to avoid ACES hue shift; no post bloom, use halo-card glow (YKB_BL_halo approach); bloom if unavoidable threshold >=1.0, intensity <=0.05.
- Soft-touch silicone: base 0.80 white / 0.045 black, diffuse_model EON, diffuse_roughness 0.55, IOR 1.43, roughness 0.60, sheen 0.25, SSS ms_amount 0.20 radius_scale 0.8 mm (translucent bump over LED: ms_amount 0.5, scale 1.5-2, refr_weight 0.35 thin-walled). Leather: HeadphonePad01 MC005_A030, LeatherSoftWhite MC024_A002; knit: MC067_A036 (thin_walled, 4K tif); grille: MC005_A072 SpeakerMesh01 or generated hex perforation (0.9/1.2 mm, 6 mm tile).
- Lighting (S = largest product dimension, Units Image): KEY 3S x 2S at 45 deg/35 deg up/2.2S = 1.0; two vertical STRIP lights 0.35S x 3S at +/-110-125 deg = 2.5-4x for chamfer edge lines; TOP scrim 3S x 3S = 0.6x; black flags in front of glass; dome 0.15-0.30 hidden from camera (CAMERA_RAY_CONTRIBUTION_SCALE 0). GSG light maps HC010_A018/A025/A019/A010; HDRIs HC006_A002/A035/A037, HC005_A025/A069/A073.
- RS Camera object (type 1057516) params verified: RSCAMERAOBJECT_SENSOR_SIZE (36,24), EXPOSURE (EV), ISO, VIGNETTING, FOCUS_DISTANCE (mm), FNUMBER_VALUE, BOKEH_ENABLED, APERTURE_BLADES. Recommendation: 100-135 mm, f/8 default, ISO 100, EV 0; DOF ~ 2Nc(1+m)/m^2 with c=0.03 mm (m 0.2 f/8 ~12 mm; m 0.5 f/8 ~3 mm).
- Texture generation: C4D Python 3.11.4 has NO numpy/PIL/cv2/scipy/imageio; use external python3+numpy+PIL like Hasselblad_500/C4D/tools/hb_textures.py (reusable value_noise, voronoi, blur_wrap, leather) writing 16-bit PNG to Assets/Textures. Sandbox-tested FFT band-pass generator: 4096^2 blast normal+rough+flake set in 14 s, 1.06 GB RAM, 1.9 % flake coverage, roughness 0.19-0.55 mean 0.396; normal strength must be ~0.30 to match GSG (R/G 85-186). The crude knit generator is not usable; use GSG fabric.
- Texture cache in the Yogo doc: GPU Texture Cache Max 256 MB, 15 % free memory, CPU 4096 MB; consider raising GPU cache to 1-2 GB for ~30 4K maps (not benchmarked).

## FILES
G:\todoist_obsidian_claude\Projects\claude\Like_nothing\Context.md
G:\todoist_obsidian_claude\weaver_claude\skills\references\c4d-redshift.md
G:\todoist_obsidian_claude\weaver_claude\skills\gsg-library.md
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\src\ykb_gsg.py
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\src\ykb_mats.py
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\src\ykb_studio.py
G:\todoist_obsidian_claude\Projects\claude\Mebel_stuliya\C4D\scripts\rs_nodes.py
G:\todoist_obsidian_claude\Projects\claude\Hasselblad_500\C4D\tools\hb_textures.py
G:\todoist_obsidian_claude\Projects\claude\Server_motherboard\C4D\tools\sm_pcb_art.py
F:\Cinema4d_2026_4\Redshift\res\core\Data\Strings\en-US\rscore.json
E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library\materials\GSG_MC005_A068_SandblastedAluminum01
E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library\materials\GSG_MC005_A004_AnodizedSilver
E:\assets\Greyscalegorilla Studio\assets\Greyscalegorilla_Library\materials\GSG_MC075_A031_SmokeyFrostedGlass
G:\todoist_obsidian_claude\Agent\gsg_sheets\hdris\HC006_00.jpg
/tmp/claude-0/-home-user-Hello-world/55ecca3a-582f-59d9-86bf-be34a7db2932/scratchpad/lnk_tex_sketch.py