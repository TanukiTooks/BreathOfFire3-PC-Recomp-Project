# Breath of Fire III native-coverage audit

Latest native batch (2026-09-13): [AREA033 animated map tiles](world-native-investigation/README.md), 49 targeted routines / 24,940 bytes total, 4,045 generated identities. All 4,001 prior identities and 67 prior code bodies are preserved. 42 controlled comparisons and 17 copied-save checkpoints pass; all four world-map images match exactly. Sampled camp-to-world interpreter instructions fell from 9.93 million to 1.83 million. These are route-specific fallback counts, not a whole-game completion percentage. The tables below retain the original audit baseline.

2026-09-11. This is the starting baseline for systematic recompilation work. No additional user playthrough is required before beginning the tasks below. The playable executable and normal launch configuration were not changed during this audit.

## Current position

The user has verified smooth opening animation, Bluetooth controller input, the opening battle, controllable Ryu, saving/loading, and resolution of the audio slowdown during card operations. These are tested milestones, not full-game compatibility claims.

| Measure | Current evidence | What it means |
|---|---:|---|
| Main generated C function declarations | 1,479 | Generated implementation functions, not a validated semantic function total |
| Main dispatch addresses | 8,656 | Includes internal continuation/resume addresses |
| Static overlay dispatch addresses | 1,245 | Addresses for which one or more compiled byte variants are available |
| Static overlay address/variant pairs | 2,195 | Separates different code images occupying the same address |
| Generated overlay function prototypes | 2,944 | Includes helpers/fragments; distinct from actual dispatch-table entries |
| Input capture variants used for current overlays | 16 | A limited set from startup and card investigation |
| Ghidra function starts inside the boot image | 1,012 | 1,007 are present in the main dispatch table; this is not a whole-game percentage |

The other 153 Ghidra functions are outside the boot image (PSX helper/GTE analysis space). The five in-image starts absent from the main dispatch table are `0x8014AAAC`, `0x8014AAB8`, `0x801780E8`, `0x8017E128`, and `0x8017E208`. They need inspection; some are startup labels or patch/data artifacts, so blindly adding them as seeds is inappropriate.

**There is no defensible whole-game native percentage yet.** We do not have a validated total of executable code, reachable variants or semantic functions. Likewise, the old `dispatch_stats.miss_total = 0` observation is an unknown-dispatch counter, not proof that no interpreter fallback occurred.

## Disc structure: the main new finding

The disc has 887 files, including **880 EMI archives**. The inferred archive model accounts exactly for all 880 files, with no out-of-bounds sections or unexplained size remainder:

- One 2,048-byte header sector, section count at offset 0, `MATH_TBL` marker at offset 8.
- Sixteen-byte section records begin at offset 16.
- Section payloads follow sequentially, each padded to a 2,048-byte boundary.
- Records include size, a destination-like field, a further word and a low-16-bit type field. The header, record layout, sector padding and type-0 direct RAM handling are now confirmed against the original loader; other type semantics remain under investigation. See [loader verification](loader-verification/README.md).

The result is **6,344 sections**, not 880 flat code overlays. Of these, 2,623 type-0 sections have plausible PSX RAM destinations, representing 1,929 unique destination/size/content combinations. **Many are data; these numbers are not code/function totals.** Audio, graphics and other section types must not be swept as instructions.

RecompOne's whole-file heuristic identified 246 possible raw-code files: 141 battle-magic, 40 bosses, 25 scenario, 19 player-character, 14 miscellaneous, 4 battle and 3 world files. That is a useful search hint, but the section directory is the better foundation. Whole-file guesses are not loader-verified addresses.

### First concrete targets

1. **LOGO/LOGO.EXE:** its PS-X header supplies load address `0x801CE000`. The new startup probe still found a heavy interpreter entry at `0x801D7578` (about 28.6 million reported interpreted instructions). A captured 64-byte sequence matches the original logo executable at that address, and the current static-overlay entry table lacks it. Start here for a small, measurable coverage improvement; performance no longer being visibly bad does not imply complete native coverage.
2. **GAME.EMI section 0:** begins at file offset `0x800`, has size `0x38158`, and declares destination `0x80195800`. Three separated captured regions match its bytes exactly. The earlier whole-file anchor translation was `0x80195000`; that is the hypothetical address of file byte zero, **not** the section's load address. RecompOne's whole-file guess was `0x80197000`. The loader's type-0 handling is now verified, and the full section matches live RAM byte for byte at both title and load menu. Code/data boundaries still need analysis.
3. **Shared START/STATUS section:** START.EMI section 8 and STATUS.EMI section 0 contain exactly the same 117,986 bytes, destined for `0x801D0C00`. They should be analyzed once and associated with both archives. Their identical contents explain why a runtime capture matched more than one file.

Extracted, hash-checked inputs and an explicit import plan are under `ghidra-input/` and [ghidra-import-plan.json](ghidra-import-plan.json). No inferred code labels or guessed flat-file imports were applied to the existing Ghidra project.

## Repeatable runtime evidence

A new bounded recorder launches an isolated headless process, copies the memory cards into its run directory, saves captures there, samples execution-phase and interpreter counters, and closes its own process. It does not change the normal game configuration or original saves.

```powershell
& '.\BoF3 Research\scripts\Measure-Bof3Coverage.ps1' -Seconds 35
```

The first run completed with 36 samples and advanced from frame 14 to frame 5,989. Each run stores raw JSONL samples, interpreter hotspots, capture history, logs, and a final framebuffer image under `coverage/runs/`. The audited run path and executable/config hashes are in [audit-manifest.json](audit-manifest.json).

Headless throughput is not displayed FPS, and it cannot verify sound quality. Interpreter tables are bounded; a PC can host different code images, so an address alone does not identify an overlay. Captured bytes and checksums must accompany any decision to compile it. `phase_profile` measures sampled execution time, not percent of the game's content compiled.

## Work queue and acceptance checks

| Priority | Work | Completion evidence |
|---|---|---|
| 1 | Validate the EMI loader and promote the section index into a code/data manifest | Destination, size, type semantics and loader path documented for the first mapped sections |
| 2 | Close the known LOGO interpreter gap | Correct code-image entry compiled; startup probe shows reduced fallback; visual startup remains correct |
| 3 | Analyze GAME and the shared START/STATUS section in Ghidra | Validated function boundaries, branch targets, jump tables and loader entry points |
| 4 | Build a section-aware compilation pipeline | Uses validated section images, retains byte guards, deduplicates shared images and rejects unknown section types |
| 5 | Expand to battle/scenario/character sections in evidence-backed batches | Native dispatch observed for each added image; scripted checkpoints and user gameplay remain correct |
| 6 | Broader compatibility validation | Longer story progression, later battles, menus, audio and save/load verified across representative checkpoints |

The existing Ryu save and previously established startup/load sequence provide the initial checkpoints. A whole-game playthrough is eventual validation, not a prerequisite for the section analysis and compilation work.

## Reproduce the static audit

Run `scripts/audit_native_coverage.py`, then `scripts/audit_emi_layout.py`, using the bundled modern Python runtime. The first pass independently checks the extracted boot bytes against the raw disc sectors, hashes all indexed files, counts generated tables and matches runtime byte anchors. The second validates all EMI section boundaries and hashes each payload. Large generated sources and the original disc remain unchanged.

Primary machine-readable outputs: [summary.json](summary.json), [disc-inventory.tsv](disc-inventory.tsv), [capture-disc-matches.json](capture-disc-matches.json), [emi-layout-summary.json](emi-layout-summary.json), [emi-sections.json](emi-sections.json), and [emi-ram-image-groups.json](emi-ram-image-groups.json).

## First identification pass completed

Separate GAME and shared START/STATUS Ghidra programs now contain 18 inspected function names and eight identified byte variables. The broader inventory remains provisional, with function-boundary conflicts explicitly recorded. See [identification report](identification/README.md).

## Card-selection native addition validated

The identified 388-byte routine at 0x801E5320 is now in the normal build. Native dispatch was observed and card-selection/cancel/confirm behavior matched the preserved baseline; the copied save also loaded into gameplay. All prior generated overlay identities and original memory-card hashes were preserved. See [native integration report](card-native/README.md).

## Card drawing helpers validated

Three drawing helpers (2,328 original instruction bytes) are now in the normal native build. All eight baseline states and seven screenshots match exactly; the remaining image difference is the pulsing save-slot outline. Both builds load the copied save into the same indoor scene. Prior native entries and original card hashes were preserved. See [drawing-helper integration](card-drawing-native/README.md).

## Panel-border helpers validated

Two more routines, at 0x801AEBA0 in GAME and 0x801DF410 in the shared START/STATUS image, are now in the normal native build. All eight baseline states matched and the copied save loaded successfully; seven screenshots matched exactly, with only the animated selection outline differing in the eighth. All prior native identities and original card hashes were preserved. This brings the targeted additions to six routines covering 3,884 original instruction bytes. See [panel-border integration](panel-border-native/README.md). The audit table above remains the original baseline snapshot.

## Lower-level drawing helpers validated

Four GAME helpers for textured panels, colored lines, tile descriptors and tile drawing are now integrated and observed executing natively. All eight baseline states matched; seven screenshots were identical and one differed only in the animated selection outline. Copied-save loading passed and original cards were preserved. Ten targeted additions now cover 5,880 original instruction bytes. Their remaining direct callees have entries in the main native table; this is not proof of all downstream runtime paths. See [drawing primitives report](drawing-primitives-native/README.md).

## Logo decoder hotspot removed

A fresh profile and full-range live byte match identified the 832-byte logo video decoder at 0x801D7578. It is now native: its entry-attributed interpreter counter fell from 28,592,486 to zero. All 23 frame-exact logo samples matched, and the menu/copied-save regression passed. Eleven targeted additions now cover 6,712 original instruction bytes. See [logo decoder integration](logo-decoder-native/README.md) and [remaining fallback analysis](remaining-fallback/README.md).

## Gameplay loops and return continuations validated

Three GAME loop bodies now execute natively, including the corrected flag-loading prefix at 0x801A06D8. The three observed resume-PC interpreter hotspots are zero. Twelve state checkpoints pass; eleven screenshots match exactly and the remaining difference is the known selection-outline animation. The full 4,560-byte scene-record buffer matches after extended idle/directional-input checks. Fourteen targeted additions cover 8,124 original instruction bytes. See [gameplay-loop report](gameplay-loops-native/README.md).

## Scene callbacks and switch dispatch validated

Three further GAME callbacks now execute natively: the scene frame pipeline, active gameplay-state handler and scene-record motion/state update. All twelve logical-state checkpoints matched, eleven screenshots were identical and one differed only in the known selection outline. Nine final record bytes differed within verified animation fields at checkpoints 28 frames apart; all other record bytes matched. All ten switch targets have guarded native variants, but only case 0 was exercised. Seventeen targeted additions now cover 9,916 original instruction bytes. See [scene-callback integration](scene-callbacks-native/README.md).

## Frame-sequence helpers validated

Three more GAME helpers now execute natively: primary-record updates, palette adjustments and the smaller-record scan. All twelve logical-state checkpoints matched, with eleven identical screenshots and the known selection-outline difference. Four controlled active palette cases also matched expected outputs in both builds. The natural smaller-record pool was inactive, so its callbacks remain untested. Record-buffer differences were confined to verified timing fields. Twenty targeted additions cover 11,076 original instruction bytes. See [frame-helper integration](frame-helpers-native/README.md).

## Primary-state and motion dispatch validated

Three GAME bodies now execute natively: the primary-record state dispatcher, motion-command dispatcher and eight-record sequence scan. All twelve states and twelve screenshots matched; the four active palette regressions also passed. Traces confirm primary callback returns and the motion 0xF0 helper path. Sequence records were inactive, so their active updates remain untested. Twenty-three targeted additions cover 11,896 original instruction bytes. See [primary/motion integration](primary-motion-native/README.md).

## Product-directed research

The [port goals](../port-goals.md) and [roadmap](../port-roadmap.md) now guide expansion beyond the current scene: prioritise battle formulas/rewards, master and level-up rules, skill transfer, save/world-map paths, encounter generation, UI and rendering/timing. Continue the current verified native queue while recording these subsystem entry points. Faithful comparisons remain the reference; requested enhancements are tracked separately from native-coverage measurements.

## State boundaries and flag helper validated

The primary state-1 callback, corrected mode dispatcher and newly identified flag leaf now execute natively. All twelve states and screenshots matched; retained palette cases passed. The missing 52-byte leaf and split 76-byte dispatcher are corrected in the research Ghidra project. Twenty-six targeted additions cover 12,100 original instruction bytes. See [state-boundary integration](state-boundaries-native/README.md), including observed callback pointers and timing/coverage limits.

## Substate actions, motion and timer routines validated

Three more GAME bodies now execute natively after two checked prefix merges. All twelve states matched, eleven screenshots were identical and the remaining difference was the known selection outline. Palette tests passed. New timer observations preserve the play-clock cadence and minute rollover in both builds; active countdowns remain untested. Twenty-nine targeted additions cover 13,712 original instruction bytes. See [substate/timer validation](substate-timers-native/README.md).

## Position-action and idle checks validated

Two action wrappers, their shared position/state helper and the corrected idle-transition routine now execute natively. All twelve states matched, eleven screenshots were identical and the known selection outline accounted for the remaining difference. Palette and clock tests passed. The shared helper was observed at least 1,024 times; its successful direction-search path remains untested. Thirty-three targeted additions cover 14,560 original instruction bytes. See [action-check validation](action-checks-native/README.md).

## Position attributes and record dispatch validated

Four more GAME routines now execute natively: position-attribute selection, fractional-cell attribute checks, reverse primary-record processing and secondary scene-mode dispatch. All twelve states matched, eleven screenshots were identical and the known selection outline accounted for the remaining difference. Palette and clock checks passed. Selector zero, one primary record and secondary mode 1 were observed; alternate branches remain untested. Thirty-seven targeted additions cover 15,280 original instruction bytes. See [position/record validation](position-records-native/README.md).

## Larger motion-command helpers integrated

Two larger GAME command interpreters now execute natively, with all 31 switch targets and 41 call-return entries guarded. The current route observes control-helper early exit and extended commands 0xF4 / 0xFF; other commands need targeted scenarios. All twelve states, screenshot criteria, palette and clock checks passed. Eight generated BREAK no-ops were corrected to use the existing interpreter trap handler through a repeatable game-owned step. Thirty-nine targeted additions cover 18,824 original instruction bytes. See [motion-command validation](motion-commands-native/README.md).

## Controlled motion-command scenarios

68 isolated scenarios now compare the generated helpers against original MIPS execution, with exact memory/register/callback-argument checks and fixture-specific expected results. All 31 switch entries were observed, including three reachable division-error paths. External callees are explicit test doubles; timing, graphics and real story-script behavior remain separate validation work. An EPC discrepancy in the reference interpreter is recorded. The game executable and original cards are unchanged. See [command-scenario report](command-scenarios/README.md).

## Basic display settings validated

The new launcher persists display options through the existing runtime settings file. Real OpenGL tests at crisp 1x windowed and smooth 2x borderless passed copied-save load/movement, twelve logical-state comparisons, palette tests and clock cadence checks. The production executable and original cards are unchanged. See [display-settings report](display-settings/README.md).


## Experimental widescreen — 2026-09-11

The display launcher now offers default-off 16:9 through a game-owned mod. The Legacy prototype provided the initial configuration; its textured-edge expansion was disabled after comparison because it distorted scenery. The selected native-wide configuration passed the copied-save route, state/timing checks and sprite-proportion comparison. All 12 default 4:3 captures match the prior build. Scene/battle/high-resolution/fullscreen widescreen coverage remains limited. See [implementation, evidence and playtest scope](widescreen/README.md).


## Turbo controls — 2026-09-11

2x/4x targets are available through Display Settings, with F9 on/off and controller Select + L3 toggle. Starts at normal speed. A small pinned framework presentation fix addresses the original 4x/VSync ceiling; measured room rates are about 1.94x/3.32x, with normal-speed restoration verified. Independent normal-tempo music remains separate work. Native routine count remains 39. See [usage and validation](turbo/README.md).
