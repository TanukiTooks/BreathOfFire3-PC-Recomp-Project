# Breath of Fire III port roadmap

Target scope: [port-goals.md](port-goals.md), recorded 2026-09-11. This roadmap orders work by dependencies. Stages may overlap when their prerequisites are met; they are not time estimates or completion percentages.

## 1. Preserve and expand the faithful baseline — in progress

Continue section-aware native recompilation, exact live-byte checks, Ghidra boundary work and comparison against a preserved executable. Existing progress includes working opening gameplay/save-load, repeatable copied-save probes, the overlay index and 48 additional targeted routines covering 23,384 original instruction bytes. These additions are beyond the existing generated main code; they are not the entire native implementation.

The larger motion-command helper batch is complete, with runtime coverage limited to early exit and extended commands 0xF4 / 0xFF. A follow-up [68-scenario functional suite](coverage/command-scenarios/README.md) exercises all 31 switch entries with explicit callback test doubles. The [party/motion batch](coverage/party-motion-native/README.md) converts 0x801BDBC4 / 0x801A2AE4, with 58 functional scenarios (three using the real motion callee) and full-party camp/world-map comparisons. The [SCENA01 batch](coverage/scenario01-native/README.md) converts both scenario/event dispatchers, initialization, the map/story event selector and the idle event: 134 controlled cases and 17 copied-save checkpoints pass with documented sampling limits. The [first two story-event handlers](coverage/scenario01-events-native/README.md) are now native, with 84 isolated cases and 12 chained steps. The copied-save regression passes but stays on idle event 0; establish a natural story route through events 1/2 next, before treating their external-service integration as validated. Event 3 at 0x801F8F34 is the next conversion candidate. Primary substate-1 movement remains another lead. See [latest validation](coverage/scenario01-events-native/README.md). Keep original memory cards protected and retain tested snapshots.

Success evidence: each native batch retains expected behavior and prior entries, and every selected body has verified code identity and boundaries. Broaden representative gameplay coverage rather than treating one indoor save as whole-game validation.

## 2. Map the systems needed by the product goals — next research expansion

| Workstream | Identify before implementing | Goal IDs |
|---|---|---|
| Battles and rewards | Damage/magic formulas, elemental resistance, HP/AP changes, EXP/money awards, item consumption and battle state transitions | BAL-01, BATTLE-01, CHEAT-01–05 |
| Growth and masters | Master data, apprenticeship conditions, level-up calculations, party EXP eligibility, learned skills and relevant save fields | GROW-01, MASTER-01/02, SKILL-01 |
| Menus and input | Menu state/navigation, draw primitives, fonts, layout, settings persistence and world-map menu entry points | UI-01, MASTER-02, VIDEO-01, SAVE-02 |
| Saves and world flow | Serialization, valid world-map save states, transition boundaries, loading ownership and recovery behavior | SAVE-01/02, LOAD-01 |
| Rendering and timing | Simulation clocks versus presentation, camera/frustum/culling, sprite/UI classification, animation sampling and audio scheduling | VIDEO-01–03, ART-01–03, SPEED-01 |
| Encounters | Random encounter generation and rate state, separation from required story battles | ENCOUNTER-01 |
| Mod support | Existing mod hooks, extension points, asset loading, configuration and save interactions | MOD-01 |

Timing lead established: the packed play clock at 0x80144FC0 uses 30 subticks per second; both comparison builds advance it by one tick per two runtime-frame-counter increments within sample bounds on the current route. Minute rollover is verified. See [timer evidence](coverage/substate-timers-native/README.md). This is a simulation/presentation dependency to preserve, not an implemented 60/120 FPS feature.

Record verified formulas and state layouts separately from hypotheses. The reported master/level optimisation issue needs a reproducible example before changing rules. User playtest checkpoints can then be requested for specific systems, rather than requiring an entire playthrough before further work.

## 3. Establish options and save architecture

Implement the shared settings/menu foundation once its interfaces are understood. Separate gameplay rulesets, presentation, convenience options and cheats. Keep Faithful available as the baseline. Decide and document save metadata/migration before Enhanced progression changes can be stored permanently.

Define the mod-support foundation alongside settings and saves: supported extension points, packaging, author documentation, player management and compatibility behavior. These are design tasks for MOD-01; the existing internal mod system is not yet a completed community-mod feature.

Success evidence: settings persist correctly; defaults match the agreed specification; original saves remain loadable; changing presentation settings does not alter progression; unsupported ruleset conversions are not silently performed.

## 4. Build convenience features and modern presentation

2026-09-13 presentation update: [terrain bounds in the normal widescreen build](coverage/widescreen-terrain-release/README.md), plus [high-resolution title/footer images](coverage/title-footer/README.md). The existing optional 16:9 setting controls terrain widening; 4:3 bounds remain original. This is limited-scene validation, not whole-game widescreen completion.

The basic display-settings launcher is implemented: window/borderless mode, window size, 1x-4x internal resolution, texture filtering and VSync. Crisp defaults keep nearest filtering and 4:3. Actual OpenGL 1x windowed and 2x borderless runs passed load/movement, state and clock comparisons; 3x remains separately untested; a later 16:9 / 4x title and camp/world-map route passed. See [usage and limits](display-settings.md). Optional experimental 16:9 is now included, with a default-off BoF3 mod and one indoor route validated; broad scene, battle and widescreen high-resolution/fullscreen coverage remain. See [widescreen evidence](coverage/widescreen/README.md). In-game settings, strict integer fullscreen scaling and 60/120 FPS remain separate tasks.

Start with supported loading improvements and direct world-map save access, then safe optional autosaves. Implement resolution/filtering controls and widescreen with sprite/UI fidelity checks. Treat 60 FPS and subsequently 120 FPS as dedicated timing/rendering work, with fixed-duration movement, scripted sequences, battles and audio comparisons. Develop turbo independently.

Success evidence: restart-tested saves, correct event/resource ordering, crisp default sprites, correctly framed widescreen scenes and unchanged normal-speed game behavior at each supported presentation rate. Keep existing native-regression checks active.

## 5. Develop and tune the Enhanced ruleset

After baseline rules are mapped, choose the Skill Ink policy and master/growth remedy with the user. Prototype magic scaling against representative early/middle/late encounters. Add the Masters menu and progression-aware hints. Implement the selected auto-battle policy, encounter controls and optional boosters once the relevant battle/world boundaries are known.

Success evidence: Faithful reproduces original mechanics; Enhanced achieves the stated player outcomes; settings and descriptions are clear; hints respect discovery state; required story battles and progression items behave as intended; save/reload retains the intended rules.

Do not postpone every enhancement until all code is native, but do require an understood, tested implementation boundary for each feature. Fixes and tuning should use verified game-owned hooks instead of accumulating unrelated edits to the shared recompiler framework.

## 6. Broader compatibility and release readiness

Validate representative story areas, battle types, masters, party configurations, menus and save histories in both rulesets. Exercise normal and zero/increased encounters, autosave/manual save, turbo/auto battle, supported frame rates and graphics choices. Investigate failures using reproducible checkpoints.

Success evidence: the agreed gameplay routes and feature matrix pass; remaining limitations are documented; native coverage and fallback dependencies are reported accurately. Release scope and additional platform support will be decided separately.

## How progress will be reported

Maintain three separate views:

- Faithful compatibility: which gameplay routes and systems have been tested.
- Native coverage: identified/compiled code images and observed fallback, with explicit denominator limits.
- Product features: requested options implemented, validated and still pending.

The earlier informal 5–10% estimate was not measured coverage. This expanded product scope should be tracked through the above milestones until the remaining systems and acceptance work are sufficiently mapped to estimate effort.


## Turbo prototype — 2026-09-11

The launcher offers 2x/4x targets with existing hold/toggle controls and a new controller toggle binding. A pinned manual-Turbo/VSync runtime correction removes the prior 2x ceiling on the 4x setting. Copied-save tests measured about 1.94x and 3.32x, both returning to 1x; uncapped execution in the tested room reaches about 3.38x. Full 4x therefore depends on further performance work. The requested independent normal-tempo music needs music-driver identification or separate playback and is deferred from this rudimentary implementation. See [Turbo evidence](coverage/turbo/README.md).

## Widescreen investigation checkpoint — 2026-09-13

The user completed a broad full-party gameplay playtest. Reported terrain edge gaps were reproduced and causally traced to the game's cached terrain culling bounds. Two reversible RAM-bound experiments filled the gaps; the normal build retains experimental widescreen without that fix. Integrate aspect-aware bounds when the rendering workstream reaches this code, including geometry-pool and separate object checks. See [checkpoint](coverage/widescreen-culling/README.md).

## Tiled menu backgrounds — 2026-09-13

VIDEO-02 now includes repeating menu backgrounds across 16:9, with the original artwork scale and centered menu layout. All four themes on card selection and character naming have real-renderer checks; 4:3 is compared against the pre-change build. This is an enhancement of an existing native routine, so the targeted count stays 48 / 23,384 bytes. Other menu paths and higher-resolution combinations remain for broader playtesting. The terrain-culling fix remains checkpointed. See [implementation and evidence](coverage/widescreen-menu-background/README.md).

## Scrolling mural — 2026-09-13

Identified the GAME.EMI intro/mural routines and matched the complete texture atlas plus palettes to DEMO.EMI. The optional 16:9 mode now reveals the existing offscreen mural strips at native artwork scale, preserving original scroll and fade behavior. Title and menu transitions are covered by the mural regression. This adds no newly converted guest routine. Fishing and fairy village widescreen checks are deferred until those minigames are reached; the separate terrain-culling checkpoint remains open. [Mural evidence](coverage/mural/README.md).

## Device-aware button prompts: initial implementation — 2026-09-13

UI-02 now has a playable common-font implementation. The six supplied exports provide 39 losslessly imported Xbox icons. Verified face, shoulder, START/SELECT tiles and duplicate small-text face glyphs use effective host bindings; mapped input activity selects Xbox or keyboard presentation, with original art for PlayStation and unidentified devices. Naming-screen rendering, remaps, original fallback and font restoration are tested; SDL virtual devices exercise classification and hotplug. The user confirmed physical Xbox/keyboard switching; broader glyph coverage remains. This presentation work adds no semantic native routines: the targeted total remains 48 routines / 23,384 bytes. Larger title/options/save-management changes remain deferred. See [implementation and evidence](coverage/button-prompts/README.md).

## High-resolution title artwork — 2026-09-13

The main title now uses the supplied PNG with a smaller subtitle overlapping the lower blue III, following the user's reference. The replacement is drawn at display resolution in both 4:3 and 16:9 and also follows the dimmed New Game/Load Game screen, with its original image labels in front. Press Start and copyright were identified as pre-rendered images and are deferred to a separate text/artwork pass. Physical Xbox/keyboard glyph switching is user-confirmed. The previous terrain-culling experiment remains checkpointed; its changes were never shipped. See [title implementation and checks](coverage/title-artwork/README.md).
