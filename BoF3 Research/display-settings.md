# Display settings

Open **Breath of Fire III - Display Settings.cmd** in the project root. Choose your options, then **Save and play**. Use **Save** to keep your choices for the next launch.

Alternatively:

```powershell
& '.\BoF3 Research\scripts\Run-Bof3.ps1' -Tool PSXRecomp -DisplaySettings
```

| Control | What it changes |
|---|---|
| Window mode | Windowed or borderless fullscreen at the desktop resolution |
| Aspect ratio | Original 4:3 or optional experimental 16:9; restart to apply |
| Window width | Dimensions follow the selected aspect; the runtime fits oversized requests to the display |
| Internal resolution | 1x original, or 2x/3x/4x higher rendering resolution; separate from window size |
| Texture filtering | Nearest keeps texture pixels crisp; bilinear smooths them and can soften sprites too |
| PSX polygon wobble | On restores original PSX rendering; Off enables experimental subpixel geometry and perspective-correct textures. Use 2x or higher internal resolution; restart to apply |
| VSync | Requests synchronised presentation; normal speed remains limited when Off. Turbo temporarily uses its own limiter and restores VSync when switched off |
| Skip Capcom logo | Optional startup skip; leaves the scrolling mural and title intact. Off by default; restart through the project launcher to apply |
| Turbo speed | 2x or 4x target for the next launch; F9 toggles, Tab holds. Actual speed depends on runtime/host performance |

**Crisp defaults** selects windowed 960 x 720, 1x internal resolution, nearest filtering and VSync On. Click Save to apply. OpenGL and unfiltered presentation are used. Original 4:3 is the default; the optional widescreen mod selects 16:9. Changes apply on the next game launch.

Preferences persist in `BoF3 PSXRecomp/BreathOfFireIII/build-release/settings.toml`, so the normal launcher also uses them. Unrelated preferences and controller bindings are preserved. When an existing settings file is first edited, its original content is retained as `settings.toml.before-display-settings`. Widescreen is stored separately as the default-off BoF3 feature in `build-release/mods/state.toml`; other mod choices are preserved and its first edit is backed up as `state.toml.before-widescreen`. A stale settings window detects changes to either file and asks you to reopen it rather than overwrite newer changes.

This is a launcher settings window; it is not yet a replacement for the game's in-game options menu. Strict integer scaling in fullscreen and new 60/120 FPS modes are still separate work. Borderless fits the selected aspect. Experimental 16:9 passed one indoor copied-save route at 1x, nearest and VSync On; wider scene, battle, fullscreen and higher-resolution validation remains. See [widescreen evidence and limits](coverage/widescreen/README.md). 1x windowed and 2x borderless have passed copied-save gameplay tests; 3x/4x are available within the renderer's limits but have not separately been playtested.

See [validation evidence](coverage/display-settings/README.md).


Turbo starts off on every launch. Controller toggle: **Select/Back + L3** (left-stick click); hold **Select/Back + L1/LB** for a temporary boost. The selected speed applies through the project launcher or Save and play. Normal-tempo music during Turbo requires separate work; current Turbo affects audio too. See [Turbo usage, measured rates and limits](coverage/turbo/README.md).

Experimental 16:9 now extends the original tiled menu background across the width, including character naming and all four background patterns. Text, panels and portraits keep their original layout. It follows the existing widescreen toggle; 4:3 is unchanged. See [menu background implementation and checks](coverage/widescreen-menu-background/README.md).

**Skip Capcom logo** is saved with the launcher preferences. Enable it, then choose **Save and play**. Turning it off restores original logo playback. It also applies through the normal `Run-Bof3.ps1` launcher; launching the executable directly bypasses this launcher-owned preference. [Implementation and checks](coverage/skip-capcom-logo/README.md).

The scrolling mural now uses 16:9 too, revealing more of the original painting at its original scale and timing. Its dark outer edges and entrance/exit against black remain part of the artwork. The title returns to its original framing after the mural fades. [Artwork, drawing routine and checks](coverage/mural/README.md).

Button prompts now automatically use Xbox icons or configured keyboard keys for identified common-font glyphs. Press a mapped control on the device you want to use; disconnecting the controller returns to keyboard prompts. PlayStation controllers retain original glyphs. This works with either aspect ratio and does not require a display-settings change. Some unclassified artwork can still show original buttons. [Coverage and checks](coverage/button-prompts/README.md).

The supplied title logo and overlapping subtitle now render at display resolution with OpenGL, even at 1x internal resolution. They remain centred and proportional in 4:3/16:9. This artwork uses its own smooth sampling while the existing sprite filtering choice stays unchanged. Press Start and both copyright lines now use the supplied high-resolution artwork, retaining their pulse/fade. [Footer artwork and checks](coverage/title-footer/README.md). [Title artwork and checks](coverage/title-artwork/README.md).

The normal 16:9 build now includes the terrain-culling fix for the reproduced Yrall world-map voids. It follows the existing widescreen option and retains original bounds at 4:3. OpenGL 16:9 / 4x passed the camp/world-map route; denser maps and other object-culling paths still need coverage. [Terrain implementation and comparisons](coverage/widescreen-terrain-release/README.md).

Optional corrected 3D is now built into the normal executable. The current user profile selects wobble Off; Crisp defaults restore On. This correction improves geometry/texture precision and does not fix missing scenery. [Wobble controls, measurements and limits](coverage/geometry-wobble/README.md).
