# Breath of Fire III shared baseline

This folder records the common input for the PSXRecomp/RecompOne comparison and Ghidra analysis. Created 2026-09-10.

## Verified input

- Game: Breath of Fire III (USA), SLUS-00422.
- Shared CUE: `../iso/Breath of Fire III (USA)/Breath of Fire III (USA).cue`.
- Preserve both referenced BIN tracks. Track 1 is MODE2/2352; track 2 is audio.
- Both BIN track hashes match the [TASVideos version record](https://tasvideos.org/Games/774/Versions/View/1813), which attributes its dump metadata to Redump. No separate revision suffix is specified there; hashes identify the exact input.
- Boot file: `SLUS_004.22`, 1,445,888 bytes. Its SHA-256 is `0af39fb1ffcf25e4bdf2730173f397b5b5f6c44989114fe9b59b92ab7c0eb21a`.
- Load address: `0x80096800`; entry PC: `0x8014AA0C`; payload size: `0x00160800`; initial GP in the header: zero.
- The header's stack address is `0x801FFFF0`; SYSTEM.CNF specifies `0x801FFF00`. Preserve both observations; they are different inputs to the startup path.
- Boot bytes extracted by PSXRecomp were independently checked against the LBA and size reported by RecompOne and match byte for byte.

Full hashes and source fingerprints are in `input-manifest.json`. Re-run `scripts/record_baseline.py` after the two probes to verify them again.

## Tool baselines

- PSXRecomp: user-supplied nightly source, commit `ed55299be34710a90fc080484a83e8634bd41fa9`. The disc probe succeeded with no reported warnings. It found 526 first-pass seeds (entry plus in-image direct JAL targets); these are heuristic seeds, not a validated function count. Game generation and the MSVC runtime build now pass; a headless run renders recognizable opening scenes. See comparison.md for evidence and limits.
- RecompOne: user-supplied `RecompOne-master` source archive. Exact upstream commit is unavailable because this is not a Git checkout; `recompone-source-files.json` fingerprints the source snapshot. Built successfully using .NET SDK 10.0.302, with four upstream warnings and no errors. Its independent disc probe succeeded. Full automatic generation failed with insufficient memory. A separate boot-only configuration generates and builds successfully; recognizable game output is not yet verified. See comparison.md.
- Ghidra: 12.1.3, matching installed `ghidra_psx_ldr`. Project: `../Ghidra/Projects/BreathOfFireIII_USA.gpr`. Imported the exact shared boot executable using `PsxLoader`. Initial automatic analysis completed successfully in 130 seconds and the project was saved. The plugin detected PSY-Q 3.7.0 and Ghidra identified 1,165 functions; both are automatic analysis results requiring review. Analysis warnings are recorded in `logs/ghidra-analysis.log`; exported results are `ghidra-baseline.txt` and `ghidra-functions.tsv`.

## Disc structure and uncertainties

RecompOne inventories 887 files: 2 PS-X executables, 246 possible raw-code files, 4 media files, and 635 data files. The second executable is `LOGO/LOGO.EXE`, with header load address `0x801CE000`; a copy is in `input/LOGO/LOGO.EXE` for later analysis.

The 246 raw-code classifications are heuristics. Many lack a load address; others have guessed addresses. Do not import them all at guessed addresses or treat them as confirmed overlays. In particular, battle and scenario files deserve targeted investigation when startup reaches their loading paths.

The first Ghidra analysis reports p-code decoding warnings at `0x8014AAB8` and `0x801F2C00`. The corresponding original file words are `0x00200000` and `0x0000000E`. The cause has not been established; these warnings are not evidence of disc corruption. Automatic function names, boundaries, and SDK matches need review before they become shared recompiler configuration.

## Comparison results and next stage

The first generation/build/run comparison is complete. **PSXRecomp is the provisional working base.** Read [comparison.md](comparison.md) for observed milestones, reproducible commands and remaining uncertainties. Separate game projects now exist for both tools.
Initial configurations, generation logs and runtime evidence are preserved. Guessed overlay locations remain unvalidated.
User playtest now confirms smooth animation, working controller input, completion of the intro fight, and movement of Ryu. The first playable opening baseline is achieved. Next, verify area transitions, audio, and saving followed by loading after a full restart. See [controller-intro-followup.md](controller-intro-followup.md).
Use targeted Ghidra analysis for the first reproducible failure and feed confirmed discoveries back into the two configurations.

## Open in Ghidra

In the Project Manager, use **File > Open Project** and choose `../Ghidra/Projects/BreathOfFireIII_USA.gpr`, then open `SLUS_004.22`. This is a newly created project; the Legacy work was not used as input.




## Save/load follow-up

The user confirmed successful saving and loading. Slowdown and crackling during card access were reproduced as an interpreter-heavy path; additional native routines are now built and loading the copied save passed. Normal-window save/load audio still needs a retest. See [memory-card-followup.md](memory-card-followup.md).


## Systematic native-coverage work — 2026-09-11

The user confirmed that card-operation slowdown and associated audio crackling are resolved. The next development baseline is the [native-coverage audit and work queue](coverage/README.md): all 880 EMI archive layouts have been indexed, runtime coverage recording is repeatable, and the first section-level Ghidra targets are extracted. Further manual playthrough is not a prerequisite for this work.


## Port goals and roadmap

The user-defined target now includes a faithful gameplay preset and optional Enhanced balance/master changes, independent presentation settings, modern save/loading conveniences and optional assists. See [port goals](port-goals.md) for the complete requirements, defaults and open decisions, and [port roadmap](port-roadmap.md) for implementation dependencies. These are target features, not claims of current implementation.

## Display settings available

A game-specific display-settings launcher now offers window/fullscreen mode, window size, 1x-4x internal resolution, optional texture smoothing and VSync. Crisp defaults keep 4:3 and smoothing off. See [how to open and use it](display-settings.md) and [validation](coverage/display-settings/README.md).


## Experimental widescreen — 2026-09-11

The display launcher now offers default-off 16:9 through a game-owned mod. The Legacy prototype provided the initial configuration; its textured-edge expansion was disabled after comparison because it distorted scenery. The selected native-wide configuration passed the copied-save route, state/timing checks and sprite-proportion comparison. All 12 default 4:3 captures match the prior build. Scene/battle/high-resolution/fullscreen widescreen coverage remains limited. See [implementation, evidence and playtest scope](coverage/widescreen/README.md).


## Turbo controls — 2026-09-11

2x/4x targets are available through Display Settings, with F9 on/off and controller Select + L3 toggle. Starts at normal speed. A small pinned framework presentation fix addresses the original 4x/VSync ceiling; measured room rates are about 1.94x/3.32x, with normal-speed restoration verified. Independent normal-tempo music remains separate work. Native routine count remains 39. See [usage and validation](coverage/turbo/README.md).

## Normal widescreen terrain and title footer — 2026-09-13

The earlier 54-pixel terrain allowance now ships in the normal 16:9 build, with native/interpreter agreement and original 4:3 bounds. The supplied text sheet is separated into Press Start and two copyright images, drawn at display resolution with the original pulse/fades. [Terrain evidence](coverage/widescreen-terrain-release/README.md) · [Title footer evidence](coverage/title-footer/README.md).
