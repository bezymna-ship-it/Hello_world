## Result in one line
The user's real render presets live ONLY in the open scene `Yogo_pro_keyboard_v008_anim_codex.c4d` (PREVIEW_3090Ti and FINAL_3090Ti) plus the fresh-document default `My Render Setting` in "Untitled 3". The vault holds no written rule for bucket size / automatic sampling. There is no medium preset anywhere in the user's own work.

Method: vault_search over Weaver/, Agent/, Library/, weaver_claude/, Studio_bridge/ and every Projects/claude/* folder. vault_read of the src scripts. Read-only exec_python (GetFirstDocument -> GetNext; `c4d.documents.GetDocumentList` does NOT exist in 2026.4). Nothing was modified, opened, saved or rendered.

## (c) Live state in Cinema 4D 2026.4 (read via description iteration)
Open documents: "Untitled 3" (empty, unsaved) and `Yogo_pro_keyboard_v008_anim_codex.c4d` (G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D). The active render data in Yogo is PREVIEW_3090Ti. Redshift videopost type 1036219. Both Yogo render datas also carry RS Post-Effects (1040189), Magic Bullet Looks (1054755) and Viewport Renderer (300001061). The fresh doc has Redshift plus Magic Bullet Looks.

| Parameter | Untitled 3 "My Render Setting" | Yogo PREVIEW_3090Ti (active) | Yogo FINAL_3090Ti |
|---|---|---|---|
| Resolution / RD fps / doc fps | 1280x720 / 30 / 30 (range 0-90) | 540x808 / **50** / 30 (range 0-420) | 720x1077 / **50** / 30 |
| SETTING_MODE (60000) | 0 Basic | 1 Advanced (all tabs 1) | 1 Advanced |
| ENABLE_AUTOMATIC_SAMPLING (1107) | **1 (ON)** | 0 | 0 |
| Min / Max samples (1101/1102) | 4 / 32 | 4 / 32 | 8 / 128 |
| UNIFIED_ADAPTIVE_ERROR_THRESHOLD (1103) | 0.01 | **0.6** (BASIC mirror 60002 = 0.6) | 0.04 |
| BLOCK_SIZE (21001) / BLOCK_RENDERING_ORDER (21002) | 512 / 1 Spiral | **512** / Spiral | **256** / Spiral |
| Denoise (DENOISE_ENABLED) / engine | OFF / OIDN(4) | ON / OptiX(3), AOVs on | ON / OptiX(3) |
| GI primary / secondary | BF(4) / IPC(2) | BF(4) / BF(4) | BF / BF |
| BF rays (7101) / secondary bounces (7003) / combined GI bounces | 16 / 1 / 2 | 16 / 1 / 2 | 64 / 1 / 2 |
| Trace depth combined/refl/refr/transp | 6/2/5/16 | 6/2/5/16 | 8/3/4/32 |
| Other | HW RT on, motion blur off, random pattern off, filter Gauss 2.5, IPC/IC mode 3 (Rebuild, don't save), AUTOLIGHT 1 | same, motion blur off, RANDOMIZE_PATTERN 0 | same |
| Frame sequence / save | CURRENTFRAME(1) / SAVEIMAGE on | ALLFRAMES(2) / SAVEIMAGE 0, path `...\Yogo_pro_keyboard\Passes\wip\ykb_render`, PNG | same |

Enum values read from the live description:
- Denoise engine: 1 Altus Single, 2 Altus Dual, 3 OptiX, 4 OIDN.
- GI engines: 0 None, 2 Irradiance Point Cloud, 3 Irradiance Cache, 4 Brute Force.
- Rendering mode: 0 Production, 1 Live.
- Bucket order: 0 Horizontal, 1 Spiral, 2 Hilbert.

Redshift preferences (`%APPDATA%\Maxon\Cinema4d_2026_4_267036B8\Redshift\preferences.xml`): compute devices RTX 3090 Ti plus Threadripper 3960X (both selected), TextureCacheBudgetGB 32.

No saved render presets and no startup.c4d exist in the C4D prefs. `prefs/library` holds only GSG scripts. Of possible use for the base scene: `prefs/library/Scripts/GSG Utility Scripts/scenes/` has RS Studio Camera.c4d, RS Light Rigs.c4d, RS Area Light Rig.c4d, GSG Cyc.c4d, GSG Shaderball.c4d, RS HDRI + BG.c4d; the same folder has RenderCalculator.py and IterateAndRender.py.

## (a) Vault evidence of what the USER tuned
- `Projects/claude/Yogo_pro_keyboard/Passes/wip/step10_b/README.txt`: "second run with the user's settings (Redshift: samples 4/32, threshold 0.6, bucket 512), preset PREVIEW_3090Ti, 540x808". This confirms the user edited PREVIEW_3090Ti himself: threshold 0.6 and bucket 512.
- `Projects/claude/Yogo_pro_keyboard/Context.md`, entry 2026-10-01 Codex: at the user's request the old `My Render Setting` (the user's own: 1080x1615, threshold 0.03; earlier 1080x1440, frames 0-120) and `RS XRAY` (no GI, threshold 0.012, transparency 64) were deleted. In their place Codex created PREVIEW_3090Ti (540x808, 4/32, thr 0.10, GI BF/BF 16 rays, 1 bounce, Production Bucket, bucket 256, OptiX+auto denoise AOVs, HW RT, motion blur off, random pattern off) and FINAL_3090Ti (720x1077, 8/128, thr 0.04, 64 rays, 1 bounce). Originals are recoverable from `C4D/Yogo_pro_keyboard_v008_before_render_presets.c4d` (not opened, per the rules).
- Rule `Weaver/Правила.md` §8.3: preview horizontal up to 960x540, vertical up to 540x960, threshold ~0.02-0.03, sample limit, denoise. Also §8.2 (one frame, up to 2 min), §8.4, §4.4 (never call RenderDocument with Redshift), §4.6 (before saving a scene switch RDATA_SAVEIMAGE off and set RDATA_PATH to Passes/wip), §8.6/8.7 (renders are the user's side; ask before any render). The word bucket/бакет does not appear in Weaver/ or Agent/ rules.
- `Projects/claude/Server_motherboard/Context.md` line 35: "960x540, threshold 0.03, up to 64 samples, OIDN, bucket 512" (user preview rule 27.09). `AI_OS_UI/C4D/src/ui_studio.py` line 14: "medium quality ... OIDN and 512 px buckets (user choice 27.09)".
- `weaver_claude/skills/references/c4d-redshift.md` lines 56-57 (the agent skill): "automatic sampling, threshold 0.008-0.012 final and 0.02 probe, OIDN, refl 6/refr 10", with IRIS timings (1920x1080 thr 0.008 about 9 min, 0.012 about 7 min, 960x540 thr 0.02 about 70 s).

## (b) Scripts that set render data (parameter -> value)
All use `REDSHIFT_RENDERER_*` ids on the video post `vp`.
- `AI_OS_UI/C4D/src/ui_studio.py render_settings()` (the only "medium"/"high" in the vault; 1600x2000): AUTOMATIC_SAMPLING False; medium MIN 16, MAX 256, threshold 0.01 (set on both UNIFIED_ and BASIC_UNIFIED_); high MAX 1024, thr 0.005; BLOCK_SIZE 512; denoise OIDN; GI primary BRUTE_FORCE, secondary IRRADIANCE_POINT_CLOUD; BF rays 256; NUM_GI_BOUNCES 3; INTEGRATION_OPTIONS_DEFAULT_LIGHT False; RDATA_AUTOLIGHT False; RDATA_SAVEIMAGE False; frame sequence CURRENTFRAME; PNG.
- `Server_motherboard/C4D/src/sm_studio.py` (960x540, 25 fps): auto False, 4/64, thr 0.03, BLOCK_SIZE 512, OIDN, BF + IPC, rays 64, bounces 2, DOF on, RDATA_SAVEIMAGE False.
- `Tree_growth/C4D/src/tg_scene.py` line 566+: the same as Server_motherboard (4/64, 0.03, 512, OIDN, BF+IPC, 64 rays, 2 bounces).
- Houdini RS ROP: `Block_frame/Houdini/src/bf_rs.py` EnableAutomaticSampling=0, 8/64, thr 0.05, denoise on, GI on, NumGIBounces2=2. `Tree_growth/Houdini/src/tgh4_rs.py` and `tgh_rs_draft.py`: 4/32, thr 0.05, the same flags.
- `Mebel_stuliya/C4D/scripts/build_mebel_v01.py`: DENOISE on, engine OPTIX, MAX_SAMPLES 256, threshold 0.01 (final) or a parameter (preview). No bucket and no auto-sampling setting.
- `Hasselblad_500 hb_studio.py`, `Logitech_IRIS ir_studio.py`, `Pixbar_clock pxb_studio.py`, `Yogo ykb_studio.py redshift_settings()` (1920x1080, default threshold 0.008): AUTOMATIC_SAMPLING **True**, BASIC_UNIFIED_ADAPTIVE_ERROR_THRESHOLD only, OIDN, depths hb 6/10/14/16, pxb 6/12/16/64, ykb 6/10/14/96. No BLOCK_SIZE, no min/max samples.
- `Pixbar_clock pxb_looks.py` and `Yogo ykb_looks.py` (x-ray look): GI engines 0/0, thr 0.012, transparency depth 64.

## Contradictions with "bucket 512, low threshold 0.3, no automatic sampling"
1. **Bucket**: FINAL_3090Ti = 256 (Codex wrote "per user preference", which contradicts the current 512). Scripts hb/ir/pxb/ykb_studio and Mebel never set BLOCK_SIZE (default applies). Only PREVIEW, the fresh doc and the AI_OS_UI/SM/TG scripts have 512.
2. **Threshold 0.3**: this value occurs nowhere. The user's live PREVIEW is **0.6** (confirmed by the step10_b README); the old My Render Setting had 0.03; Codex's initial value was 0.10; the rule says 0.02-0.03; the fresh doc has 0.01. 0.3 may be a typo for 0.03, or a deliberate intermediate. Confirm with the user. Treat the user's literal "0.3" as the Low preset, while noting that his own live value is 0.6.
3. **Automatic sampling**: the fresh doc default is ON (Basic mode). The scripts hb/ir/pxb/ykb_studio and the skill `c4d-redshift.md` explicitly turn it ON. In the live Yogo presets it is OFF, in Advanced mode. When it is ON the min/max samples are ignored, so the template must set ENABLE_AUTOMATIC_SAMPLING=False AND SETTING_MODE=1 (or the BASIC_* mirrors).
4. **Denoiser**: the live presets use OptiX (3090 Ti); all the vault scripts and the skill use OIDN; the fresh doc has denoise OFF.
5. **GI**: live presets are BF/BF (16 and 64 rays); the scripts use BF + IPC (64-256 rays); the fresh doc is BF + IPC at 16 rays.
6. **Render-data fps 50 vs doc fps 30** in Yogo (both PREVIEW and FINAL): set both to the same value in the template.
7. **Python ids**: `REDSHIFT_RENDERER_BASIC_DENOISE_ENABLED` and `REDSHIFT_RENDERER_RANDOMIZE_PATTERN` do not exist in 2026.4. Use `REDSHIFT_RENDERER_BASIC_DENOISE`=60008 and `REDSHIFT_RENDERER_UNIFIED_RANDOMIZE_PATTERN`=1106. The `_set()` helper silently skips unknown names, so those lines in ui/sm/tg_scene silently did nothing. The Basic mirror of the threshold (60002) does follow the Advanced value in the live doc.

## Missing / must be invented
- **Medium** preset: it does not exist in the user's scenes. The only precedent is AI_OS_UI "medium" (16-256 samples, thr 0.01, BF 256 + IPC, OIDN, 512, 3 bounces), set 27.09 and marked "user choice". Proposed for the template (to be confirmed): 1920x1080 (vertical products 1080x1920), auto OFF, 8-16 / 128-256 samples, threshold 0.03-0.04 (FINAL_3090Ti is 0.04), OptiX, GI BF/BF 64 rays, 1-2 bounces, bucket 512, depths 8/3/6/32 (refraction raised because of the frosted glass).
- **Low**: take the user's PREVIEW_3090Ti with threshold 0.3 (per his word): 540x808 vertical or 960x540, auto OFF, 4/32, OptiX, BF/BF 16 rays, 1 bounce, bucket 512 spiral, depths 6/2/5/16.
- **High / 4K product close-up**: nothing user-made. The only precedent is AI_OS_UI "high" (16-1024, thr 0.005). To invent: 3840x2160, auto OFF, e.g. 32/1024, thr 0.005-0.01, BF/BF 128-256 rays, bucket 512.
- No saved C4D render-preset library and no base scene template for the user exist in the vault (the Like_nothing folder holds only Output/Prompts/Refs, no C4D folder yet).

## Not found
Any vault note with the words "бакет"/"bucket" as a user rule (only code comments and one Context line), "light cache", "irradiance cache" settings by the user (live IC mode 3 = Rebuild don't save, default), and any saved Redshift/C4D render preset files.

## KEY FACTS
- User's real render presets live only in the open scene Yogo_pro_keyboard_v008_anim_codex.c4d: PREVIEW_3090Ti (active) and FINAL_3090Ti; plus the fresh-doc 'My Render Setting' in Untitled 3.
- PREVIEW_3090Ti live: 540x808, Advanced mode, automatic sampling OFF, samples 4/32, threshold 0.6, bucket 512 (Spiral), OptiX denoise, GI Brute Force/Brute Force 16 rays, 1 secondary bounce, depths 6/2/5/16 (combined/refl/refr/transp).
- FINAL_3090Ti live: 720x1077, automatic sampling OFF, 8/128, threshold 0.04, bucket 256 (contradicts 512), OptiX, BF/BF 64 rays, 1 bounce, depths 8/3/4/32.
- Untitled 3 default 'My Render Setting': 1280x720, 30 fps, Basic mode, automatic sampling ON, 4/32, threshold 0.01, bucket 512 Spiral, denoise OFF (OIDN selected), primary BF, secondary Irradiance Point Cloud, 16 rays, depths 6/2/5/16.
- Param ids (c4d 2026.4): BLOCK_SIZE=21001, BLOCK_RENDERING_ORDER=21002 (0 Horizontal,1 Spiral,2 Hilbert), ENABLE_AUTOMATIC_SAMPLING=1107, UNIFIED_MIN/MAX_SAMPLES=1101/1102, UNIFIED_ADAPTIVE_ERROR_THRESHOLD=1103, BASIC_UNIFIED_ADAPTIVE_ERROR_THRESHOLD=60002, SETTING_MODE=60000 (0 Basic,1 Advanced), NUM_GI_BOUNCES=7003, BRUTE_FORCE_GI_NUM_RAYS=7101.
- Enums: denoise engine 1 Altus Single/2 Altus Dual/3 OptiX/4 OIDN; GI engine 0 None/2 Irradiance Point Cloud/3 Irradiance Cache/4 Brute Force; rendering mode 0 Production/1 Live. Redshift videopost type 1036219.
- step10_b/README.txt confirms the user himself set 'samples 4/32, threshold 0.6, bucket 512' on PREVIEW_3090Ti; Codex originally created it with threshold 0.10 and bucket 256.
- The user's threshold 0.3 for low appears nowhere: live PREVIEW=0.6, old user My Render Setting=0.03 (1080x1615), rule Weaver/Правила.md section 8.3 says ~0.02-0.03; 0.3 may be a typo of 0.03, ask/flag.
- Automatic sampling contradiction: fresh doc default is ON; hb_studio/ir_studio/pxb_studio/ykb_studio.py and skill c4d-redshift.md line 56 turn it ON; template must set ENABLE_AUTOMATIC_SAMPLING False and Advanced mode, otherwise min/max samples are ignored.
- Bucket 512 is set by ui_studio.py (AI_OS_UI), sm_studio.py (Server_motherboard), tg_scene.py (Tree_growth); Hasselblad/IRIS/Pixbar/Yogo studio scripts and Mebel never set bucket size.
- Only 'medium' in the vault is AI_OS_UI ui_studio.py: 16-256 samples, thr 0.01, BF 256 rays + IPC, OIDN, bucket 512, 3 bounces, 1600x2000 (marked user choice 27.09); 'high' = 16-1024, thr 0.005. No medium preset exists in the user's own scenes; must be invented.
- Denoiser mismatch: live presets use OptiX (RTX 3090 Ti), scripts and skill use OIDN. GI mismatch: live BF/BF vs scripts BF+Irradiance Point Cloud.
- Yogo render datas have RDATA_FRAMERATE 50 while DOCUMENT_FPS is 30 -- set both consistently in the template; RD path is Passes\wip\ykb_render, SAVEIMAGE 0 (rule 4.6).
- Python ids REDSHIFT_RENDERER_BASIC_DENOISE_ENABLED and ..._RANDOMIZE_PATTERN do not exist; correct are BASIC_DENOISE=60008 and UNIFIED_RANDOMIZE_PATTERN=1106; the _set() helper in ui/sm/tg scripts silently skips missing names. c4d.documents.GetDocumentList does not exist; use GetFirstDocument/GetNext.
- Hardware (Redshift preferences.xml): RTX 3090 Ti + Threadripper 3960X both selected as compute devices, TextureCacheBudgetGB 32.
- Weaver rules relevant to the template: preview resolution horizontal <=960x540, vertical <=540x960 (8.3), one frame <=2 min (8.2), never RenderDocument with Redshift (4.4), set SAVEIMAGE off and path Passes/wip before saving (4.6), controls on one *_CONTROL null at the root (4.12), ask before any render (8.7).
- No saved C4D render presets, no startup.c4d, and no base-scene template exist; Like_nothing vault folder has only Output/Prompts/Refs. Old user settings recoverable from C4D/Yogo_pro_keyboard_v008_before_render_presets.c4d (not opened).

## FILES
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\Context.md
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\Passes\wip\step10_b\README.txt
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\Yogo_pro_keyboard_v008_anim_codex.c4d
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\Yogo_pro_keyboard_v008_before_render_presets.c4d
G:\todoist_obsidian_claude\Weaver\Правила.md
G:\todoist_obsidian_claude\weaver_claude\skills\references\c4d-redshift.md
G:\todoist_obsidian_claude\Projects\claude\AI_OS_UI\C4D\src\ui_studio.py
G:\todoist_obsidian_claude\Projects\claude\Server_motherboard\C4D\src\sm_studio.py
G:\todoist_obsidian_claude\Projects\claude\Tree_growth\C4D\src\tg_scene.py
G:\todoist_obsidian_claude\Projects\claude\Hasselblad_500\C4D\src\hb_studio.py
G:\todoist_obsidian_claude\Projects\claude\Yogo_pro_keyboard\C4D\src\ykb_studio.py
G:\todoist_obsidian_claude\Projects\claude\Mebel_stuliya\C4D\scripts\build_mebel_v01.py
C:\Users\Work_PC\AppData\Roaming\Maxon\Cinema4d_2026_4_267036B8\Redshift\preferences.xml
C:\Users\Work_PC\AppData\Roaming\Maxon\Cinema4d_2026_4_267036B8\prefs\library\Scripts\GSG Utility Scripts\scenes