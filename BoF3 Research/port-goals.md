# Breath of Fire III port goals

Recorded from the user's requirements on 2026-09-11. This is the target product scope, not a list of implemented features. The current native baseline and validation evidence remain in [coverage/README.md](coverage/README.md).

## Product direction

Deliver a faithful Breath of Fire III experience with a player-selectable Enhanced gameplay preset. Preserve the original story, characters and recognizable artwork. Players should be able to enjoy presentation and convenience improvements without being forced to use balance changes or cheats.

The requirements below are user-requested. Where an exact design or default has not been specified, proposals are marked as such and remain adjustable. Numerical balance changes will follow analysis and testing rather than being invented in advance.

## Modes and settings

| Area | Target behavior | Default / decision status |
|---|---|---|
| Faithful gameplay | Preserve original combat, growth, skill and master rules as the comparison baseline | Proposed initial gameplay preset |
| Enhanced gameplay | Offer the agreed magic, skill-management and master-system changes | Player opt-in; exact balance values pending |
| Presentation | Resolution, aspect ratio, frame-rate target and separate filtering/smoothing choices | Independent of gameplay preset |
| Loading | Optimise loading while preserving correct game state, audio and events | On by default, requested |
| Autosave | User-selectable on/off | Off initially is a proposal; default not specified by user |
| World-map saving | Save directly from the world map without entering camp | Required convenience feature; available to both gameplay presets is proposed |
| Turbo, auto battle, encounters | Independently configurable conveniences/assists | Normal speed, manual battle and original encounter rate proposed as defaults |
| Boosters / cheats | Explicit optional settings, separate from Enhanced balance | All off by default is proposed |
| 2D artwork | Crisp, pixel-accurate sprite presentation; optional smoothing | Smoothing off by default, requested |

Faithful is the reference for original gameplay mechanics; it need not reproduce loading delays. A preset must clearly show which rules it changes. The exact granularity of individual Enhanced balance toggles remains a design decision. Switching growth rules on an existing save needs an explicit compatibility design before implementation, because prior stat gains may be irreversible.

## Enhanced gameplay requirements

| ID | Requirement | Intended outcome / acceptance evidence |
|---|---|---|
| BAL-01 | Improve Nina's magic and elemental-spell scaling | Magic remains useful into late game. Compare representative early, middle and late-game damage, AP costs, resistances and encounter roles against the faithful baseline; preserve a reason to choose different characters and spells. Exact formulas and tuning are undecided. |
| SKILL-01 | Remove friction from Skill Ink use | Players can freely experiment with party abilities. User-approved direction permits either more accessible Skill Inks or removing the consumable requirement; select the implementation after tracing transfer rules and inventory/save effects. |
| GROW-01 | Remove incentives for deliberately killing Ryu or manipulating progression to avoid undesirable master-related gains | Identify and reproduce the reported incentive using actual EXP, eligibility and master-growth rules. Choose a fix that supports normal party progression without requiring players to withhold levels or incapacitate characters for optimal growth. The underlying mechanics and remedy are not yet verified. |
| MASTER-01 | Overhaul the master experience | Improve understanding and use of the master system alongside any agreed growth-rule changes. Preserve original rules in Faithful. Exact bonuses, penalties and unlock rules require a later design pass. |
| MASTER-02 | Add a Masters section to the menu | Show discovered masters and useful apprenticeship information. Keep undiscovered information hidden initially; support optional hints on finding masters without automatically revealing everything. Reveal conditions and hint wording remain to be designed. |
| UI-01 | Improve and modernise the UI | Make settings and the new systems readable and convenient while retaining the game's visual identity. Validate navigation with a controller and ensure new layouts work across supported resolutions and aspect ratios. |
| UI-02 | Device-aware button prompts | Show Xbox glyphs for Xbox controllers, PlayStation glyphs for PlayStation controllers, and actual configured keyboard controls when using the keyboard. Respect remapping and controller connection changes. Initial common-font implementation is playable: supplied Xbox artwork, keyboard keycaps, effective remaps and device switching. The naming screen is validated in 4:3/16:9, and SDL virtual-device tests cover Xbox/PlayStation detection and disconnect/reconnect. The user confirmed physical Xbox/keyboard glyph visibility and switching. Broader glyph variants remain to be mapped. |

Potential growth solutions must be evaluated rather than silently assumed: changing when master bonuses apply, making growth recoverable, or redesigning penalties have different effects on saves and balance. No particular solution has been selected.

## Presentation requirements

| ID | Requirement | Acceptance target |
|---|---|---|
| VIDEO-01 | Graphics settings and higher resolutions | Expose supported resolution and rendering options in the port's UI, with persistent settings and legible menus. |
| VIDEO-02 | Widescreen | Extend supported gameplay views and adapt UI placement without stretching artwork or breaking framing, culling, transitions or input. Preserve appropriate image proportions. Cutscene/movie handling requires separate validation. |
| VIDEO-03 | 60–120 FPS | Target smooth 60 and 120 FPS presentation while preserving intended movement, battle timing, scripts, animation duration, input behavior and audio. These are development targets, not established capabilities. Implement and validate 60 first, then 120. |
| ART-01 | Improve/filter 3D assets and textures | Provide suitable enhancement/filtering choices for 3D presentation. Exact methods and any replacement-texture scope remain open. |
| ART-02 | Preserve crisp 2D sprites | Keep the original sprite artwork sharp by default, with predictable pixel scaling. A global texture-filter switch must not unintentionally blur sprites or UI. |
| ART-03 | Optional sprite smoothing | Offer a clear opt-in option for players who prefer smoothing; off by default. |

Higher presentation rates and turbo are separate features: raising the frame-rate setting must not act as a speed multiplier. Art classification and renderer timing need investigation before committing to a specific interpolation or filtering implementation. Native compilation alone does not deliver high-frame-rate rendering.

## Convenience and assists

| ID | Requirement | Acceptance target |
|---|---|---|
| LOAD-01 | Loading optimisation by default | Reduce unnecessary loading work/waits while preserving events, resource readiness and stable audio. Measure loading separately from displayed FPS. |
| SAVE-01 | Optional autosaves | User on/off control, clear indication of when a save occurred and reliable recovery after restart. Proposed design: separate autosave slots that do not overwrite manual saves. Safe save points and retention are undecided. |
| SAVE-02 | Direct world-map saves | Access manual saving from the world map without a camp-menu detour. Reuse or validate the original serialization path and preserve relevant location/progression state. Availability during transitions and other unsafe states requires defined rules. |
| SPEED-01 | Turbo settings | User-controlled faster gameplay, independent of render FPS. Initial targets: 2x/4x with hold and on/off toggle. Requested next: keep music at normal tempo during faster gameplay, if practical; the current guest-timed audio path needs separate music-driver work. |
| BATTLE-01 | Auto battle | Optional automatic battle actions. The initial policy (for example simple repeat/basic actions versus more involved tactics), resource use and interruption controls require design. Do not choose a policy implicitly. |
| ENCOUNTER-01 | Encounter-rate control | Include original rate, increased rate and zero random encounters. Proposed safety rule: zero random encounters does not suppress required story/scripted battles. Exact multiplier range remains open. |
| CHEAT-01 | EXP gain booster | Optional increased EXP with clear settings; define how it interacts with master growth and party eligibility. |
| CHEAT-02 | Money gain booster | Optional increased money gains; multipliers remain open. |
| CHEAT-03 | Infinite HP | Optional setting; define treatment of defeat checks, status effects and scripted events before release. |
| CHEAT-04 | Infinite MP/AP | Optional unlimited spell resource; the port should use the game's appropriate terminology in its UI. |
| CHEAT-05 | Infinite item use | Optional non-consumption for supported item use. Define treatment of quest items, exchanges and other progression-dependent consumption separately. |

Keep original-rate/manual/no-cheat choices available. Exact control ranges and defaults not stated by the user above are proposals, not finalized product decisions.

## Mod support

Added at the user's request on 2026-09-13.

| ID | Requirement | Acceptance target |
|---|---|---|
| MOD-01 | Support community-created mods | Players can install and manage optional mods, with documentation for mod authors. Exact supported changes, packaging, authoring interfaces and mod-management UI remain to be designed. |

Mod support is an explicit project goal. Proposed design considerations include enabling/disabling mods, compatibility and dependency reporting, and documenting effects on saves and the Faithful baseline. Existing internal mod hooks are a starting point; they do not by themselves complete this goal.

## Save and configuration design

Preserve existing original memory cards and the tested load path during development. Proposed implementation requirements:

- Record the gameplay ruleset and any persistent enhancement metadata with a port save, without silently rewriting existing original saves.
- Keep presentation preferences independent from character progression data.
- Make Enhanced-to-Faithful save conversion a deliberate design decision; do not promise reversible stat history.
- Test manual save, autosave and world-map save through full process restart, including changed settings and interruption scenarios.
- Clearly separate permanent progression changes from temporary assists in the settings descriptions.

These are implementation proposals to support the requested features, not additional monetisation, online or account features.

## Development scope and open decisions

The current Windows project is the initial implementation environment. Mod support is included in the target scope. Additional platform releases, a distribution model and broad content replacement have not been requested or committed here.

Later design sessions should settle: Skill Ink policy; the actual master/growth remedy; master hints and spoilers; UI direction; autosave defaults/retention; turbo and encounter ranges; auto-battle policy; booster interactions; save migration between rulesets; and mod formats, supported interfaces, compatibility and management. None of these decisions blocks continued identification and faithful native compilation.

Use [port-roadmap.md](port-roadmap.md) to connect these goals to the engineering work. Track faithful compatibility, native coverage and requested enhancements separately; neither generated entry counts nor a completed settings screen constitute a whole-project completion percentage.

## Rendering preference added 2026-09-13

Reduce original PlayStation polygon wobble and affine texture warping in the improved presentation, with an explicit player toggle to retain original PSX wobble. The initial optional correction is implemented and remains experimental; see [current evidence](coverage/geometry-wobble/README.md).
