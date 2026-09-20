/* Game-owned prompt presentation. Original guest instructions and bindings are
 * unchanged. Every admitted sprite and scratch texture has an exact byte guard. */
#include "gpu.h"
#include "gpu_render.h"
#include "mod_plugins.h"
#include "host_input_prompt.h"
#include "psx_keybinds.h"
#include "button_prompt_assets.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern int bof3_title_sprite(const GpuSpritePresentation *s);

static int prompt_mode = -1; /* 0 auto, 1 original, 2 Xbox, 3 keyboard */
static int prompt_trace, prompt_last_family = -1;
static unsigned prompt_replacements;

static void prompt_init(void) {
    const char *value;
    if (prompt_mode >= 0) return;
    value = getenv("BOF3_BUTTON_PROMPTS");
    prompt_mode = 0;
    if (value && !strcmp(value,"original")) prompt_mode = 1;
    else if (value && !strcmp(value,"xbox")) prompt_mode = 2;
    else if (value && !strcmp(value,"keyboard")) prompt_mode = 3;
    value = getenv("BOF3_TRACE_BUTTON_PROMPTS");
    prompt_trace = value && !strcmp(value,"1");
}

static int xbox_icon(const HostInputPrompt *binding) {
    if (binding->kind == HOST_PROMPT_BUTTON) {
        switch (binding->code) {
        case SDL_CONTROLLER_BUTTON_A: return ICON_A_COLOR;
        case SDL_CONTROLLER_BUTTON_B: return ICON_B_COLOR;
        case SDL_CONTROLLER_BUTTON_X: return ICON_X_COLOR;
        case SDL_CONTROLLER_BUTTON_Y: return ICON_Y_COLOR;
        case SDL_CONTROLLER_BUTTON_BACK: return ICON_VIEW;
        case SDL_CONTROLLER_BUTTON_START: return ICON_MENU;
        case SDL_CONTROLLER_BUTTON_LEFTSHOULDER: return ICON_LB;
        case SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: return ICON_RB;
        case SDL_CONTROLLER_BUTTON_LEFTSTICK: return ICON_LEFT_STICK_PRESS;
        case SDL_CONTROLLER_BUTTON_RIGHTSTICK: return ICON_RIGHT_STICK_PRESS;
        case SDL_CONTROLLER_BUTTON_DPAD_UP: return ICON_DPAD_UP;
        case SDL_CONTROLLER_BUTTON_DPAD_DOWN: return ICON_DPAD_DOWN;
        case SDL_CONTROLLER_BUTTON_DPAD_LEFT: return ICON_DPAD_LEFT;
        case SDL_CONTROLLER_BUTTON_DPAD_RIGHT: return ICON_DPAD_RIGHT;
        default: return -1;
        }
    }
    if (binding->kind == HOST_PROMPT_AXIS) {
        switch (binding->code) {
        case SDL_CONTROLLER_AXIS_TRIGGERLEFT: return binding->direction>0 ? ICON_LT : -1;
        case SDL_CONTROLLER_AXIS_TRIGGERRIGHT: return binding->direction>0 ? ICON_RT : -1;
        case SDL_CONTROLLER_AXIS_LEFTX: return binding->direction>0 ? ICON_LEFT_STICK_RIGHT : ICON_LEFT_STICK_LEFT;
        case SDL_CONTROLLER_AXIS_LEFTY: return binding->direction>0 ? ICON_LEFT_STICK_DOWN : ICON_LEFT_STICK_UP;
        case SDL_CONTROLLER_AXIS_RIGHTX: return binding->direction>0 ? ICON_RIGHT_STICK_RIGHT : ICON_RIGHT_STICK_LEFT;
        case SDL_CONTROLLER_AXIS_RIGHTY: return binding->direction>0 ? ICON_RIGHT_STICK_DOWN : ICON_RIGHT_STICK_UP;
        default: return -1;
        }
    }
    return -1;
}

/* A small code-drawn keycap font. Special keys use familiar compact labels;
 * return/arrow keys have distinct symbols instead of clipped long names. */
static const char key_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-?";
static const char *key_bits[] = {
 "010101111101101","110101110101110","011100100100011","110101101101110",
 "111100110100111","111100110100100","011100101101011","101101111101101",
 "111010010010111","001001001101010","101101110101101","100100100100111",
 "101111111101101","101111111111101","010101101101010","110101110100100",
 "010101101111011","110101110101101","011100010001110","111010010010010",
 "101101101101111","101101101101010","101101111111101","101101010101101",
 "101101010010010","111001010100111","111101101101111","010110010010111",
 "110001010100111","110001010001110","101101111001001","111100110001110",
 "011100111101111","111001010010010","111101111101111","111101111001110",
 "000000111000000","110001010000010"
};

static int key_label(int sc, int wide, char out[8]) {
    out[0]=0;
    if (sc>=SDL_SCANCODE_A && sc<=SDL_SCANCODE_Z) { out[0]=(char)('A'+sc-SDL_SCANCODE_A);out[1]=0;return 1; }
    if (sc>=SDL_SCANCODE_1 && sc<=SDL_SCANCODE_9) { out[0]=(char)('1'+sc-SDL_SCANCODE_1);out[1]=0;return 1; }
    if (sc==SDL_SCANCODE_0) { strcpy(out,"0"); return 1; }
    if (sc>512 && sc<=517) { out[0]='M';out[1]=(char)('0'+sc-512);out[2]=0;return 1; }
    if (sc>=SDL_SCANCODE_F1 && sc<=SDL_SCANCODE_F12) { snprintf(out,8,"F%d",sc-SDL_SCANCODE_F1+1); return 1; }
    switch(sc) {
    case SDL_SCANCODE_RETURN: case SDL_SCANCODE_KP_ENTER: strcpy(out,wide?"ENT":"<");break;
    case SDL_SCANCODE_SPACE: strcpy(out,"SP");break;
    case SDL_SCANCODE_TAB: strcpy(out,"TB");break;
    case SDL_SCANCODE_ESCAPE: strcpy(out,"ES");break;
    case SDL_SCANCODE_BACKSPACE: strcpy(out,"BS");break;
    case SDL_SCANCODE_DELETE: strcpy(out,"DL");break;
    case SDL_SCANCODE_LSHIFT: strcpy(out,"LS");break;
    case SDL_SCANCODE_RSHIFT: strcpy(out,"RS");break;
    case SDL_SCANCODE_LCTRL: strcpy(out,"LC");break;
    case SDL_SCANCODE_RCTRL: strcpy(out,"RC");break;
    case SDL_SCANCODE_LALT: strcpy(out,"LA");break;
    case SDL_SCANCODE_RALT: strcpy(out,"RA");break;
    case SDL_SCANCODE_UP: strcpy(out,"^");break;
    case SDL_SCANCODE_DOWN: strcpy(out,"v");break;
    case SDL_SCANCODE_LEFT: strcpy(out,"{");break;
    case SDL_SCANCODE_RIGHT: strcpy(out,"}");break;
    default: return 0; /* Unknown binding keeps the original glyph. */
    }
    return 1;
}

static void text_bitmap(uint16_t *pixels, const char *label, int *width, int *height) {
    int len=(int)strlen(label),w=len*4+3,x,y,i;
    *width=w;*height=7;
    memset(pixels,0,32*32*sizeof(uint16_t));
    for(y=0;y<7;y++) for(x=0;x<w;x++)
        pixels[y*32+x]=(x==0||y==0||x==w-1||y==6) ? 0x294a : 0x1084;
    for(i=0;i<len;i++) {
        const char *found=strchr(key_chars,label[i]);
        if(found) {
            const char *bits=key_bits[found-key_chars];
            for(y=0;y<5;y++) for(x=0;x<3;x++) if(bits[y*3+x]=='1') pixels[(y+1)*32+i*4+x+2]=0x7fff;
        } else {
            /* Return and directional arrows are single-cell symbols. */
            const char *bits=label[i]=='<'?"001001111100010":label[i]=='^'?"010111010010010":label[i]=='v'?"010010010111010":label[i]=='{'?"010100111100010":"010001111001010";
            for(y=0;y<5;y++) for(x=0;x<3;x++) if(bits[y*3+x]=='1') pixels[(y+1)*32+i*4+x+2]=0x7fff;
        }
    }
}

static int verified_font(const uint16_t *vram, const GpuSpritePresentation *s,
                         const Bof3PromptGlyph *glyph) {
    int y,x,cx=(s->clut&63)*16;
    if ((s->clut>>6)!=480 || cx>=256) return 0;
    if(memcmp(vram+480*1024+cx,prompt_palettes_original+cx,32)) return 0;
    for(y=0;y<8;y++)
        if(memcmp(vram+(glyph->v+y)*1024+960+glyph->u/4,glyph->original+y*2,4)) return 0;
    for(y=0;y<32;y++) for(x=0;x<32;x++)
        if(vram[y*1024+960+x]!=prompt_scratch_original[y*32+x]) return 0;
    return 1;
}

static int bof3_draw_button_prompt(const GpuSpritePresentation *s) {
    const Bof3PromptGlyph *glyph=NULL;
    const uint16_t *vram;
    HostInputPrompt binding;
    uint16_t texture[32*32];
    int i,x,y,w=0,h=0,area[4],preference,icon_index,wide,dw,dh,ox,oy;
    if(bof3_title_sprite(s)) return 1;
    prompt_init();
    if(prompt_mode==1 || s->width!=8 || s->height!=8 || s->draw_width!=8 ||
       s->texture_window || (s->texpage&0x19f)!=0x00f) return 0;
    for(i=0;i<(int)(sizeof(prompt_glyphs)/sizeof(prompt_glyphs[0]));i++)
        if(prompt_glyphs[i].u==s->u && prompt_glyphs[i].v==s->v) {glyph=&prompt_glyphs[i];break;}
    if(!glyph) return 0;
    vram=gpu_get_vram();
    if(!verified_font(vram,s,glyph)) return 0;
    preference=prompt_mode==2?2:prompt_mode==3?1:0;
    if(!host_input_prompt_binding(1,glyph->logical,preference,&binding)) return 0;
    if(prompt_mode==2) binding.family=HOST_PROMPT_XBOX;
    if(binding.family!=HOST_PROMPT_XBOX && binding.family!=HOST_PROMPT_KEYBOARD) return 0;
    if(prompt_trace && prompt_last_family!=binding.family) {
        fprintf(stdout,"bof3 prompts: family=%s logical=%d kind=%d source=%d\n",binding.family==HOST_PROMPT_XBOX?"Xbox":"keyboard",glyph->logical,binding.kind,binding.code);
        fflush(stdout);prompt_last_family=binding.family;
    }
    wide=glyph->logical==PSX_KB_START?16:glyph->logical==PSX_KB_SELECT?24:0;
    memset(texture,0,sizeof(texture));
    if(binding.kind==HOST_PROMPT_UNBOUND) text_bitmap(texture,"-",&w,&h);
    else if(binding.family==HOST_PROMPT_KEYBOARD) {
        char label[8];
        if(!key_label(binding.code,wide,label)) return 0;
        text_bitmap(texture,label,&w,&h);
    } else {
        const Bof3PromptIcon *icon;
        icon_index=xbox_icon(&binding);
        if(icon_index<0) return 0;
        icon=&prompt_icons[icon_index];w=icon->w;h=icon->h;
        for(y=0;y<h;y++) memcpy(texture+y*32,icon->pixels+y*w,w*sizeof(uint16_t));
    }
    /* Reuse a guarded font subrectangle transiently as a 16-bit texture. Flush
     * queued draws before each write and before restoration. The guest cannot
     * observe the temporary contents; CPU VRAM is restored within this
     * callback, and the backend receives the restoring upload before return.
     * OpenGL may defer that upload until its next texture use. */
    gr_get_draw_area(&area[0],&area[1],&area[2],&area[3]);
    gr_set_draw_area(area[0],area[1],area[2],area[3]);
    gr_vram_transfer_in(960,0,32,32,texture);
    gr_set_semi_transparency(0,0);
    if(wide) {
        /* START/SELECT span two/three 8-pixel tiles. Clip each tile of
         * one centered prompt, preserving the original menu spacing. */
        int full_x=s->x-glyph->part*8;
        dw=binding.family==HOST_PROMPT_KEYBOARD?16:8;dh=binding.family==HOST_PROMPT_KEYBOARD?7:8;
        ox=full_x+(wide-dw)/2;oy=s->y;
        gr_set_draw_area(s->x>area[0]?s->x:area[0],area[1],s->x+7<area[2]?s->x+7:area[2],area[3]);
    } else {
        dw=8;dh=8;ox=s->x;oy=s->y;
        if(binding.family==HOST_PROMPT_KEYBOARD) {dw=w<8?w:8;dh=7;ox+=(8-dw)/2;}
        if(binding.family==HOST_PROMPT_XBOX && w>h) {dh=(h*8+w/2)/w;oy+=(8-dh)/2;}
    }
    gr_draw_textured_rect_scaled(ox,oy,dw,dh,0,0,w,h,0,0,0x10f);
    gr_set_draw_area(area[0],area[1],area[2],area[3]);
    gr_vram_transfer_in(960,0,32,32,prompt_scratch_original);
    gr_set_semi_transparency(s->semi_transparent,(s->texpage>>5)&3);
    if(prompt_trace && prompt_replacements++<12) {fprintf(stdout,"bof3 prompts: replaced logical=%d uv=%d,%d xy=%d,%d\n",glyph->logical,s->u,s->v,s->x,s->y);fflush(stdout);}
    return 1;
}
PSX_MOD_CONSTRUCTOR(bof3_register_button_prompts) {
    gpu_set_sprite_presentation_hook(bof3_draw_button_prompt);
}
