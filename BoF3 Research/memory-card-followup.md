# Memory-card performance follow-up — 2026-09-10

The user confirmed that saving and loading work, but reported crackling audio and slow game speed while reading/checking files during save/load. Save/load functionality is now a user-verified milestone; audio during these operations needed further work.

## Reproduction and change

Tested headlessly with copies of both memory-card files in `BoF3 PSXRecomp/BreathOfFireIII/run-card-probe/saves`. Original card SHA-256 hashes were checked before and after and remained identical. No framework code or card protocol behavior was changed.

The old build reproduced the slowdown on **Checking memory card**: approximately 26.5 guest frames/sec across the stable sampled interval, despite headless execution, with about 73–78% interpreter attribution. Card reads themselves use an in-memory copy in memcard.c, making repeated host disk reads an unlikely explanation for the read-side symptom. Save writes do flush files; this pass does not rule out separate write-side costs.

Captured the executable variants used by card checking, file listing and loading. Combined them with the working startup captures, preserving exact byte-image variants and unioning observed execution/entry lists for identical images. `startup-card-overlay-captures.json` contains 16 variants. The stock static CPS overlay pipeline compiled 7 and skipped 9 regions with no walk-root seeds; none failed. Output includes 2,944 exact function identities in 20 translation units.

CMake now links `generated-startup-card-overlays/overlays_static.c`. The regeneration script consumes the combined capture file. The earlier `generated-intro-overlays` source remains available, and the previous executable is preserved as `build-release/Breath_of_Fire_III___PSXRecomp.before-card-fix.exe`.

## Verification

The new headless run passed through Checking memory card to the card-selection screen, then Checking file to the saved-game list. A sample during the reading stage advanced 69 guest frames in 0.765 seconds (about 90 fps), with interpreter attribution about 6–9% in the sampled reading interval. These are observational samples from the same menu path, not a synchronized frame-for-frame benchmark or a measure of presentation FPS.

The copied Ryu save (level 1, displayed time 00:09) appeared correctly, was selected and loaded, and the game returned to the saved indoor area. Evidence: `card-native-loaded.png` and `logs/card-native-loaded.json`. The diagnostic process was then closed.

Normal-window audio was not assessed in the headless test. The user should repeat saving and loading with the updated build and confirm whether the crackling and slow motion are resolved. A full post-change save/write and reload cycle remains a user retest; this automated pass exercised the read/load path only.

## Evidence

- Before: `logs/card-load-stage1.json`, `logs/card-file-check.json`, `logs/card-load-stage2.json` and `card-load-19.png`.
- Native generation/build: `logs/compile-card-overlays.log`, `logs/card-native-build.log`.
- After: `logs/card-native-reading.json`, `logs/card-native-file-check.json`, `logs/card-native-loaded.json`, `card-native-reading-8.png`, `card-native-slots.png`, `card-native-loaded.png`.
- `logs/card-native-stage1.json` is an initial input attempt that remained on the title menu; it is excluded from the card-performance comparison.
- Original card preservation: `logs/card-probe-original-hashes.json`.

Use the usual `Run-Bof3.ps1 -Tool PSXRecomp` command; the rebuilt executable is already installed.
