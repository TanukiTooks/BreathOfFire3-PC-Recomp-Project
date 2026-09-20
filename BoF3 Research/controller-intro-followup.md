# Controller and intro follow-up, 2026-09-10

The user confirmed the original build reaches the title screen, but reported a slow/choppy Capcom animation and no Bluetooth controller input.

## Controller change

Added `p1_device = "auto"` in game.toml's `[controller]` section and staged the same config beside the executable. The runtime source uses the keyboard by default when the positive `PSX_DEBUG_TOOLS` compile definition is absent. This build enables debug tooling by not defining `PSX_NO_DEBUG_TOOLS`, but does not define the positive symbol; therefore its unconfigured Player 1 defaults to keyboard. Explicit game configuration avoids this ambiguity.

The normal-window diagnostic log now confirms `opened controller for slot: Xbox Series X Controller`. Digital pad mode remains selected. The user subsequently confirmed working controller input in actual play. Normal routing is exclusive to the selected gamepad; keyboard button bindings are not a fallback while auto selects the controller.

Current Xbox mappings: Menu = Start, View = Select, A = Cross/confirm, B = Circle, X = Square, Y = Triangle, D-pad = movement, LB/RB = L1/R1, LT/RT = L2/R2. These are read from the runtime's input.ini. Connect the controller before starting the game.

## Intro change and evidence

Normal-window measurements after startup showed around 60 guest frames/sec and 16.681 ms average frame intervals. During the Capcom animation, an early sample showed 70.91% interpreter attribution and about 92 guest frames over 2.047 seconds. These are limited observations, not a full movie benchmark. That diagnostic window was closed during the intro (`sdl_window_close`), so a complete before/after presentation comparison is unavailable.

A separate headless capture with `overlay_cache = true` recorded four observed executable regions, including the intro code at `0x801CE000`. The stock `compile_overlays.py --static --cps` pipeline compiled those regions successfully into `generated-intro-overlays/`, producing 830 exact function identities across seven translation units. The game CMakeLists.txt now includes them using `GAME_OVERLAY_STATIC_C`. This also includes observed startup/kernel code and a region at `0x8017E000`; it is not exclusively movie-decoder code. Framework source was not changed. Exact-byte guards select compiled variants and fall back when bytes do not match.

The rebuilt game passed a headless startup check: frame 3,055 after 22.718 seconds of monitoring, a visible Breath of Fire III title screen, and 2,794,113 static-overlay hits. This proves native execution and continued boot progress. It does not establish normal-window animation smoothness, Bluetooth button response, or gameplay correctness. The subsequent user playtest below confirms both reported symptoms are resolved in the tested opening sequence.

## Reproduction

The regular `Run-Bof3.ps1 -Tool PSXRecomp` command runs the updated executable and configuration. No user rebuild is required. `Build-Bof3.ps1 -Tool PSXRecomp -Regenerate` now also regenerates the startup overlays from `intro-overlay-captures.json`.

Evidence: `logs/input-timing.stdout.log`, `logs/input-timing.json`, `logs/intro-timing-summary.log` (partial test), `logs/compile-intro-overlays.log`, `logs/intro-native-build.log`, `logs/intro-native-test.json`, and `intro-native-result.png`. The capture configuration was temporary; automatic overlay caching remains disabled in the user's normal game configuration. All diagnostic runtime processes have been closed.

## User playtest confirmation

On 2026-09-10, the user reported that the animation is smooth, controller input works, the intro plays, the intro fight can be completed, and Ryu can then be moved around. These are user-observed milestones in the rebuilt game, beyond the earlier automated headless check.

Status: first playable opening baseline achieved. PSXRecomp remains the working base; RecompOne remains a reference. Broader area transitions, later battles, audio correctness, and saving/reloading have not yet been verified. Next acceptance check: progress through area transitions to an available save point, save, close the game normally, relaunch, and verify the saved position and state load correctly.
