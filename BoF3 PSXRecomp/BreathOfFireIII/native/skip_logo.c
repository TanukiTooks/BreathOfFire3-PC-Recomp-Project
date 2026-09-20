/* Opt-in Capcom logo skip at the original logo player's Start-button test. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
uint32_t bof3_logo_skip_button(uint32_t buttons) {
    static int enabled = -1;
    static int reported;
    if (enabled < 0) {
        const char *value = getenv("BOF3_SKIP_CAPCOM_LOGO");
        enabled = value && strcmp(value, "1") == 0;
    }
    if (enabled) {
        if (!reported) {
            fprintf(stdout, "bof3: skipping Capcom logo through its normal exit path\n");
            reported = 1;
        }
        buttons |= 0x0800u;
    }
    return buttons;
}
