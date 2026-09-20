/* Preserve the terrain builder's own safety margin at native 16:9.
 * No guest instruction writes: generated and interpreted execution share this policy. */
#include "mod_plugins.h"
#include "dirty_ram_interp.h"
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
extern int bof3_widescreen_is_active(void);
static int terrain_enabled=-1;
static int terrain_margin(void) {
    if(terrain_enabled<0){const char *s=getenv("BOF3_TERRAIN_WIDESCREEN");terrain_enabled=!(s&&!strcmp(s,"original"));}
    if(!terrain_enabled || !bof3_widescreen_is_active() || psx_mod_display_width()!=320u)return 0;
    /* ceil((320*(16/9)/(4/3)-320)/2) = ceil(320/6) = 54.
     * Preserve original 50-pixel allowance; do not add generic guard pixels. */
    return (int)((psx_mod_display_width()+5u)/6u);
}
static int terrain_words_match(void) {
    return psx_mod_read_word(0x801533ecu)==0x24420032u &&
           psx_mod_read_word(0x801533f0u)==0x3042ffffu &&
           psx_mod_read_word(0x801533f4u)==0x2c4201a5u &&
           psx_mod_read_word(0x801533f8u)==0x10400009u;
}
static int terrain_immediate(uint32_t pc,uint32_t insn,int32_t *out) {
    int margin;pc&=0x1fffffffu;
    if(!((pc==0x001533ecu && insn==0x24420032u)||(pc==0x001533f4u && insn==0x2c4201a5u)))return 0;
    margin=terrain_margin();if(!margin || !terrain_words_match())return 0;
    *out=(int16_t)insn+(pc==0x001533ecu?margin:margin*2);return 1;
}
int32_t bof3_terrain_immediate(uint32_t pc,uint32_t insn) {
    int32_t value=(int16_t)insn;terrain_immediate(pc,insn,&value);return value;
}
/* The camera/zoom trim skips outer grid columns before screen culling.
 * In 16:9 those columns contain visible terrain and objects. Use the existing
 * zero-trim path: all 28 columns, unchanged row count, culls and 1024-slot pool.
 * The shared trim byte also feeds the object dispatcher at 0x80155B40. */
static int grid_enabled=-1;
static const struct {uint32_t pc,word;} grid_guard[]={
    {0x80153218u,0x3c038015u},{0x8015321cu,0x9063933bu},
    {0x80153220u,0x24020023u},{0x80153224u,0x14620003u},
    {0x80153228u,0x0000b021u},{0x8015322cu,0x3c011f80u},
    {0x80153230u,0xac20000cu},{0x80153234u,0x3c0b8010u},
    {0x80153238u,0x356b4000u},{0x8015323cu,0x3c021f80u},
    {0x80153260u,0x8c420000u},{0x80153274u,0xa0229341u},
    {0x801532bcu,0x2402001cu}
};
int bof3_terrain_grid_branch(uint32_t pc,uint32_t insn,int taken) {
    unsigned i;
    if((pc&0x1fffffffu)!=0x00153224u || insn!=0x14620003u)return taken;
    if(!bof3_widescreen_is_active() || psx_mod_display_width()!=320u)return taken;
    if(grid_enabled<0){const char *s=getenv("BOF3_TERRAIN_GRID");grid_enabled=!(s&&!strcmp(s,"original"));}
    if(!grid_enabled)return taken;
    for(i=0;i<sizeof(grid_guard)/sizeof(grid_guard[0]);i++)
        if(psx_mod_read_word(grid_guard[i].pc)!=grid_guard[i].word)return taken;
    return 0; /* Fall through; original delay slot and store execute normally. */
}
PSX_MOD_CONSTRUCTOR(bof3_register_terrain_widescreen) {
    dirty_ram_set_immediate_hook(terrain_immediate);
    dirty_ram_set_bne_hook(bof3_terrain_grid_branch);
}
