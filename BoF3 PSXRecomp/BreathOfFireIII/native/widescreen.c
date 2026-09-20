/* BoF3 opt-in presentation mod. Guest instructions and save data are unchanged. */
#include "mod_plugins.h"
#include <stdio.h>
static int bof3_widescreen_active;
extern void bof3_mural_widescreen_vblank(void);
static void bof3_activate_widescreen(void) {
    if (psx_mod_set_fixed_display_aspect(16u, 9u)) {
        bof3_widescreen_active = 1;
        fprintf(stdout, "bof3: experimental 16:9 presentation enabled\n");
    }
}
/* Menu artwork repeats in 64-pixel column pairs. Only the verified 320-wide,
 * 16:9 menu surface is extended; unknown display modes keep original bounds. */
int32_t bof3_menu_background_padding(void) {
    if (!bof3_widescreen_active || psx_mod_display_width() != 320u) return 0;
    /* This plugin fixes the aspect at 16:9. The general culling-margin API
     * includes guard pixels, so it is not the visible presentation margin. */
    psx_mod_note_wide_2d_frame();
    return 64;
}
uint32_t bof3_menu_background_pairs(void) {
    return bof3_menu_background_padding() ? 7u : 5u;
}
PSX_MOD_CONSTRUCTOR(bof3_register_widescreen) {
    psx_mod_register_activation_plugin("bof3.presentation.widescreen", bof3_activate_widescreen);
    psx_mod_register_vblank_plugin("bof3.presentation.widescreen", bof3_mural_widescreen_vblank);
}

/* This package fixes its enabled aspect at 16:9; no live aspect toggle. */
int bof3_widescreen_is_active(void) { return bof3_widescreen_active; }
