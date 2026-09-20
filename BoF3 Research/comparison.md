# Breath of Fire III: first generated-build comparison

Date: 2026-09-10. Provisional choice: **PSXRecomp as the working base**, with RecompOne retained for reference. This recommendation is based on observed execution, not generated function counts. Neither build has passed a gameplay acceptance test.

## Subsequent controller and intro work

The user subsequently confirmed reaching the title screen, with choppy intro playback and no Bluetooth input. Explicit gamepad routing and native startup overlays have now been added. The user confirmed smooth animation, working input, completion of the intro fight, and controllable Ryu. See [controller-intro-followup.md](controller-intro-followup.md) for evidence and remaining checks. The results below describe the original comparison build.

## Common input and setup

Both projects use the same USA SLUS-00422 CUE and both BIN tracks. See [input-manifest.json](input-manifest.json) for exact hashes and independently verified boot extraction. Framework snapshots and game folders are separate. Legacy folders were not used as inputs.

Ghidra 12.1.3 has the matching ghidra_psx_ldr installed. The shared boot executable was imported with PsxLoader into `../Ghidra/Projects/BreathOfFireIII_USA.gpr`; automatic analysis and function exports are complete. The automatic SDK identification is PsyQ 3.7.0. All discovered names and boundaries still need review.

## Results

| Milestone | PSXRecomp | RecompOne |
|---|---|---|
| Disc probe | Passed | Passed |
| Code generation | Passed | Full automatic configuration failed with insufficient memory; separate boot configuration passed |
| Native application build | Passed, MSVC Release | Passed, .NET 10 Release, 34 generated-code warnings |
| Runtime initialization | Passed, bundled OpenBIOS | Passed, OpenGL 4.5 initialized |
| Recognizable game image | Confirmed: mine scenes, dialogue, game logo, mural sequence | Not confirmed |
| Input | Start/Cross commands accepted; transitions observed after Start, but menu navigation not established | Not tested |
| Title menu / new game / controllable scene | Not verified | Not verified |
| Audio / save and load / battle overlays | Not verified | Not verified |

### PSXRecomp

Source nightly commit: `ed55299be34710a90fc080484a83e8634bd41fa9`. Project: `../BoF3 PSXRecomp/BreathOfFireIII`. Its `psxrecomp` directory is a junction to the supplied nightly source.

Generated 35 game C shards with 1,479 dispatch entries. Built the two emitters, generated the game and OpenBIOS, and built the runtime. The only compiler adaptation was enabling `/experimental:c11atomics` specifically for the framework's `starvation_ring.c` from the game's CMakeLists.txt; the framework source was not edited. Debug tools are enabled for local testing, with the observed server bound to 127.0.0.1. Netplay, setup wizard and recomp-ui are disabled.

The headless run used the shared game.toml and isolated `run-boot-baseline/saves`. It used HLE boot with recompiled OpenBIOS kernel execution. Runtime framebuffer captures show recognizable mine scenes with characters, dialogue and the game logo, followed by a mural sequence. Graphics correctness has not been compared frame-for-frame with an emulator.

The last observation reached frame 96,743. Dispatch counters reported 55,106,840 static hits and zero dispatch misses in the observed run. This is scoped counter evidence; it does not establish coverage of the entire game.

Start was injected for 3, 60, then 30 frames, and Cross for 10 frames. Captures include transitions and black intermediate frames. No capture establishes a usable title menu or playable control. Headless timing is not a user-facing performance measurement. `psxrecomp-title.png` was an intermediate filename and contains a black frame, not proof of reaching a title menu.

The quit command returned an ambiguous busy response, but the launched process was subsequently confirmed absent. The test is closed.

![PSXRecomp mine scene](psxrecomp-boot.png)

![PSXRecomp mural sequence](psxrecomp-confirm-2.png)

Evidence: `logs/psxrecomp-generate.log`, `logs/psxrecomp-runtime-build-debug.log`, `logs/psxrecomp-boot.*.log`, `logs/psxrecomp-start-test.json`, `logs/psxrecomp-second-start.json`, `logs/psxrecomp-final-state.json` and the PNG captures.

### RecompOne

Source: supplied `RecompOne-master` archive, fingerprinted in `recompone-source-files.json`; exact upstream commit unavailable. Project: `../BoF3 Recomp1/BreathOfFireIII`.

The original autoconfiguration is preserved as `config/breathoffireiii.json`, with its generated function maps. It includes 37 overlay entries, many with heuristic load addresses. Generation produced very large boss-overlay files and repeated unknown-instruction diagnostics, then failed in `StringBuilder.ToString()` from `OverlayWriter.EmitOverlayFile`. The original log is about 463 MB; partial files remain in `generated/` for investigation and are excluded from the game build. The precise cause of the output expansion has not been established.

A separate `config/boot-baseline.json` retains the same main configuration and only the header-addressed `LOGO/LOGO.EXE` overlay. It generates into `generated-boot/`, leaving the original experiment intact. It produced 1,277 functions and 53 SDK replacements. Two unsupported SPECIAL words were reported. This reduced configuration deliberately lacks the raw game overlays and cannot establish general gameplay coverage.

A minimal runner built successfully. An optional `BOF3_SMOKE_SECONDS` mode in Program.cs adds observations without changing generated game behavior, then terminates the test process at the end of the observation window. During the 20-second test, VSync event counts advanced from 105 to 560, only the main overlay was active, and the sampled return address was `0x8014AB18`, the caller of the generated VSync wrapper. VSync events prove VSync continued returning; this is not evidence of a VSync deadlock. Every sampled CPU VRAM shadow had zero nonzero words. That shadow is not an OpenGL framebuffer capture, so visual success or a black screen cannot be conclusively claimed from it alone. No recognizable game image has been verified. The smoke process exited as configured.

Evidence: `logs/recompone-autoconfigure.log`, `logs/recompone-generate.log`, `logs/recompone-generate-boot.log`, `logs/recompone-game-smoke-build.log`, `logs/recompone-smoke.stdout.log`, `logs/recompone-smoke.stderr.log`.

## Repeat the comparison

Run from this workspace in PowerShell. Both scripts resolve the workspace from their own location. Current game configs still contain absolute disc paths; update those if moving the workspace.

```powershell
& '.\BoF3 Research\scripts\Build-Bof3.ps1' -Tool PSXRecomp
& '.\BoF3 Research\scripts\Build-Bof3.ps1' -Tool RecompOne
& '.\BoF3 Research\scripts\Run-Bof3.ps1' -Tool PSXRecomp
& '.\BoF3 Research\scripts\Run-Bof3.ps1' -Tool RecompOne -SmokeSeconds 20
```

Add `-Regenerate` to the build script to rerun the respective generation path; RecompOne uses the bounded boot configuration. The unbounded original autoconfiguration is preserved but is not the default rebuild. PSXRecomp requires Visual Studio C++ tools, CMake and modern Python for generation; RecompOne requires .NET 10. PSXRecomp CMake may fetch missing build dependencies. Interactive runs use the same isolated test-state directories. RecompOne's test settings currently mute audio.

For PSXRecomp diagnostic work, run with `-Headless -DebugPort 4381`; its framework provides `tools/raw_tcp.py` for commands such as `gpu_state`, `dispatch_stats` and `screenshot_file`. Stop the test after collecting evidence.

## Next work

1. Establish PSXRecomp title-menu and New Game navigation at normal presentation speed, then verify the first controllable scene and audio.
2. Investigate the first reproducible failure using shared original bytes and the Ghidra project. Record any confirmed names, function boundaries and overlay load addresses with evidence.
3. Use RecompOne's main loop around `0x8014AB10` and its SDK replacements as a comparison target; determine why no game image has yet been established before expanding overlay scope.
4. Validate raw overlay load addresses and code boundaries individually before reintroducing them to RecompOne. Preserve stock generation results and keep changes reproducible.

The current toolset is sufficient for this next stage; no extra download from the PlayStation decomp.wiki list is required yet.


