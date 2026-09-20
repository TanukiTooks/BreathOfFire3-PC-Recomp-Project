cmake_minimum_required(VERSION 3.20)
set(PSXRECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/psxrecomp" CACHE PATH
    "Path to psxrecomp")
if(NOT EXISTS "${PSXRECOMP_ROOT}/runtime/runtime.cmake")
    message(FATAL_ERROR
        "PSXRecomp runtime is missing: ${PSXRECOMP_ROOT}/runtime/runtime.cmake\n"
        "This project expects the psxrecomp framework checkout at ${PSXRECOMP_ROOT}.\n"
        "Run: git submodule update --init --recursive\n"
        "If psxrecomp/ is not a submodule, set -DPSXRECOMP_ROOT=<path-to-psxrecomp>.")
endif()

project(BreathOfFireIII LANGUAGES C CXX)

# --- Opt-in product surfaces (OFF by default in the framework) -------------
# Scaffold prompts / flags fill these. Without recomp-ui, PSX_RECOMP_UI is OFF.
# Setup-host CI requires WIZARD_CMAKE_BLOCK / ENABLE_SETUP_WIZARD (FORCE_SETUP_HOST
# alone does not open first-run / Generate & rebuild).
set(PSX_RECOMP_UI OFF CACHE BOOL "Initial comparison without launcher" FORCE)
set(PSX_NETPLAY OFF CACHE BOOL "Single-player comparison" FORCE)
set(PSX_SETUP_WIZARD OFF CACHE BOOL "Local generated build" FORCE)
include("${PSXRECOMP_ROOT}/runtime/runtime.cmake")

# This project's own mod catalog. The FRAMEWORK stages it -- together with its
# builtin psx.* packages -- into <exe-dir>/mods/bundled, and refuses to
# configure if a catalog exists here but is not declared. Never copy it by
# hand: five titles did, and framework 4cc04be3's rename of the staged
# directory broke all five silently (bead beads-eio.3.101).
set(PSX_PRELOADED_MODS "${CMAKE_CURRENT_SOURCE_DIR}/mods/preloaded")
if(NOT IS_DIRECTORY "${PSX_PRELOADED_MODS}")
    set(PSX_PRELOADED_MODS "NONE")
endif()

psxrecomp_add_game_runtime(psx-runtime
    # Preserve precise projected coordinates; correction remains optional.
    PGXP
    PRELOADED_MODS_DIR "${PSX_PRELOADED_MODS}"



    WINDOW_TITLE "Breath of Fire III - PSXRecomp"
    DEFAULT_GAME_CONFIG_PATH "game.toml"
    MAX_PLAYERS 1


    GAME_OVERLAY_STATIC_C "${CMAKE_CURRENT_SOURCE_DIR}/generated-scenario01-events-overlays/overlays_static.c"
    GEN_MARKER "generated/SLUS_004.22_dispatch.c"
    GEN_FULL_GLOB "generated/SLUS_004.22_full_*.c"

)

# Stage runtime configs next to the exe for direct build/ launches. Only copy
# files that exist â€” never fail POST_BUILD when game_options.toml is absent.
foreach(_PSX_RUNTIME_CONFIG game.toml game_options.toml)
    if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}")
        add_custom_command(TARGET psx-runtime POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${CMAKE_CURRENT_SOURCE_DIR}/${_PSX_RUNTIME_CONFIG}"
                "$<TARGET_FILE_DIR:psx-runtime>/${_PSX_RUNTIME_CONFIG}"
            COMMENT "Staging ${_PSX_RUNTIME_CONFIG}"
            VERBATIM)
    endif()
endforeach()

# MSVC requires an explicit opt-in for the runtime's C11 atomic operations.
if(MSVC)
    set_property(SOURCE "${PSXRECOMP_ROOT}/runtime/src/starvation_ring.c"
        APPEND PROPERTY COMPILE_OPTIONS /experimental:c11atomics)
endif()



# Keep regeneration reproducible: instrument only the generated dispatcher symbol.
# Its original code-match guard still decides whether a native variant may run.
set_property(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/generated-scenario01-events-overlays/overlays_static.c"
    APPEND PROPERTY COMPILE_DEFINITIONS psx_overlay_dispatch=bof3_generated_overlay_dispatch)
target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/card_selection_trace.c")

target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/widescreen.c")

target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/skip_logo.c")

target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/mural.c")
target_compile_definitions(psx-runtime PRIVATE BOF3_HOST_CONTROLS=1)

target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/button_prompts.c")

# Preserve user-supplied high-resolution title assets as separate PNG resources.
target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/title_artwork.c")
add_custom_command(TARGET psx-runtime POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "$<TARGET_FILE_DIR:psx-runtime>/assets/title"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/title/bofiii_upscaled.png"
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/title/subtitle.png"
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/title/press-start.png"
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/title/copyright-japan.png"
        "${CMAKE_CURRENT_SOURCE_DIR}/assets/title/copyright-usa.png"
        "$<TARGET_FILE_DIR:psx-runtime>/assets/title"
    VERBATIM)

target_sources(psx-runtime PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/native/terrain_widescreen.c")
