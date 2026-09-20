/* GAME.EMI section 1: reveal the existing mural strips at native scale.
 * No game state writes, texture stretching, scroll or fade timing changes. */
#include "mod_plugins.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "mdec.h"
static const uint32_t mural_draw_code[130] = {
    0x27BDFFC8u, 0x3C038014u, 0x24633C31u, 0xAFBF0030u, 0xAFB5002Cu, 0xAFB40028u,
    0xAFB30024u, 0xAFB20020u, 0xAFB1001Cu, 0xAFB00018u, 0x90620000u, 0x00000000u,
    0x1040006Bu, 0x00008821u, 0x2470FFF1u, 0x24150001u, 0x2474FFF3u, 0x24120140u,
    0x3C028014u, 0x94423C22u, 0x24030140u, 0x24420002u, 0x00629823u, 0x3C018014u,
    0xA4223C22u, 0x3C046666u, 0x96030000u, 0x34846667u, 0x00031C00u, 0x00031403u,
    0x00440018u, 0x00031FC3u, 0x00004010u, 0x00081203u, 0x00431023u, 0x00021400u,
    0x00021403u, 0x0222102Au, 0x1440004Cu, 0x00000000u, 0x9203000Fu, 0x00000000u,
    0x1475000Eu, 0x24020003u, 0x96020002u, 0x00000000u, 0x24420001u, 0xA6020002u,
    0x00021400u, 0x00021403u, 0x28420080u, 0x14400012u, 0x24020080u, 0xA6020002u,
    0x24020002u, 0x08074684u, 0xA202000Fu, 0x1462000Bu, 0x24020080u, 0x96020002u,
    0x00000000u, 0x2442FFFFu, 0xA6020002u, 0x00021400u, 0x1C400005u, 0x00000000u,
    0xA6000002u, 0x08074684u, 0xA200000Fu, 0xA6020002u, 0x3C028014u, 0x90423C31u,
    0x00000000u, 0x10400029u, 0x00000000u, 0x0C05ECADu, 0x00000000u, 0x10550006u,
    0x324203FFu, 0x0C05ECADu, 0x00000000u, 0x24030002u, 0x14430004u, 0x324203FFu,
    0x00021183u, 0x08074697u, 0x34470200u, 0x00021183u, 0x34470080u, 0x00002821u,
    0x3C048014u, 0x8C84598Cu, 0x00003021u, 0x0C05F0B6u, 0xAFA00010u, 0x24040002u,
    0x0C053968u, 0x2405000Cu, 0x00132400u, 0x00042403u, 0x24050018u, 0x2626000Bu,
    0x30C600FFu, 0x24070002u, 0x0C0745F6u, 0xAFA00010u, 0x96830000u, 0x00000000u,
    0xA0430004u, 0x96830000u, 0x00000000u, 0xA0430005u, 0x96830000u, 0x00000000u,
    0xA0430006u, 0x267300FFu, 0x26310001u, 0x2A220004u, 0x1440FFA2u, 0x26520080u,
    0x8FBF0030u, 0x8FB5002Cu, 0x8FB40028u, 0x8FB30024u, 0x8FB20020u, 0x8FB1001Cu,
    0x8FB00018u, 0x27BD0038u, 0x03E00008u, 0x00000000u,
};
/* The same RAM address is reused by unrelated overlays. Verify the complete
 * drawing body on each active-frame check rather than caching an address match. */
static int mural_ready(void) {
    const uint8_t phase = psx_mod_read_byte(0x80143C31u);
    if (phase < 1u || phase > 3u) return 0;
    for (uint32_t i = 0; i < 130u; ++i)
        if (psx_mod_read_word(0x801D18F8u + i * 4u) != mural_draw_code[i]) return 0;
    return 1;
}

/* Only the initial black loading interval is unpaced. Do not write guest RAM
 * or bypass CD/overlay initialization; normal logo/mural timing resumes once
 * the corresponding player is ready. The frame bound fails closed. */
int bof3_startup_turbo_active(uint64_t frame) {
    static int finished;
    static int skip = -1;
    if (finished) return 0;
    if (skip < 0) {
        const char *value = getenv("BOF3_SKIP_CAPCOM_LOGO");
        skip = value && strcmp(value, "1") == 0;
    }
    if (frame >= 1800 || (!skip && mdec_get_decode_count() != 0) || mural_ready()) {
        finished = 1;
        fprintf(stdout, "bof3: startup loading complete at frame %llu; normal speed restored\n",
                (unsigned long long)frame);
        fflush(stdout);
        return 0;
    }
    return 1;
}

void bof3_mural_widescreen_vblank(void) {
    if (psx_mod_display_width() != 320u) return;
    if (!mural_ready()) return;
    psx_mod_note_wide_2d_frame();
}
