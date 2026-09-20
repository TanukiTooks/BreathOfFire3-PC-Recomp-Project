/* Replace only identified title/logo/footer sprites; guest texture data stays intact. */
#include "gpu.h"
#include "gpu_gl_renderer.h"
#include "mod_plugins.h"
#include "psx_sdl.h"
#define STBI_NO_STDIO
#include "../psxrecomp/runtime/third_party/stb_image.h"
#include "title_artwork_guard.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
extern uint64_t s_frame_count;
static unsigned char *title_pixels[2];
static int title_w[2],title_h[2],title_load_state,title_mode=-1;
static uint64_t title_seen[2];
static float title_opacity[2];
static uint64_t label_seen[2][2];
static uint32_t label_color[2][2];
static unsigned char label_pixels[2][2][144*16*4];
static int label_front[2];
static unsigned char *footer_pixels[3];
static int footer_w[3],footer_h[3],footer_state,footer_mode=-1;
static uint64_t footer_seen[2][3];
static float footer_opacity[2][3];
static int title_enabled(void) {
    if(title_mode<0){const char *s=getenv("BOF3_TITLE_ARTWORK");title_mode=!(s&&!strcmp(s,"original"));}
    return title_mode;
}
/* Distinct complete body/table guards for the overlay reused after Start. */
static int title_guard(void) {
    uint32_t i;uint8_t phase=psx_mod_read_byte(0x80143c32u);
    if(!title_enabled() || psx_mod_display_width()!=320u || psx_mod_display_height()!=240u)return 0;
    if(psx_mod_read_half(0x80143b92u)==1u) {
        for(i=0;i<sizeof(menu_title_code)/sizeof(menu_title_code[0]);i++)
            if(psx_mod_read_word(0x801e7514u+i*4u)!=menu_title_code[i])return 0;
        for(i=0;i<sizeof(menu_title_table)/sizeof(menu_title_table[0]);i++)
            if(psx_mod_read_word(0x801ed1fcu+i*4u)!=menu_title_table[i])return 0;
        return 2;
    }
    if(phase!=1 && phase!=2)return 0;
    for(i=0;i<sizeof(title_code_and_table)/sizeof(title_code_and_table[0]);i++)
        if(psx_mod_read_word(0x801d1b00u+i*4u)!=title_code_and_table[i])return 0;
    return 1;
}
static int title_load(void) {
    int i;
    if(!title_load_state) {
        const char *names[2]={"bofiii_upscaled.png","subtitle.png"};
        const char *base=SDL_GetBasePath();title_load_state=-1;
        if(!base)return 0;
        for(i=0;i<2;i++) {
            char path[4096];size_t size=0;void *file;int channels;
            snprintf(path,sizeof(path),"%sassets/title/%s",base,names[i]);
            file=SDL_LoadFile(path,&size);
            if(file && size<16*1024*1024)title_pixels[i]=stbi_load_from_memory(file,(int)size,&title_w[i],&title_h[i],&channels,4);
            SDL_free(file);
        }
#if !defined(PSX_SDL3)
        SDL_free((void*)base);
#endif
        if(title_pixels[0]&&title_pixels[1]&&title_w[0]==1939&&title_h[0]==811&&title_w[1]==2146&&title_h[1]==732)title_load_state=1;
        else {fprintf(stderr,"bof3: title PNGs unavailable or unexpected size; keeping original title\n");return 0;}
    }
    if(title_load_state!=1)return 0;
    for(i=0;i<2;i++)if(!gl_renderer_prepare_artwork(i,title_pixels[i],title_w[i],title_h[i]))return 0;
    return 1;
}
/* Lossless RGB crops retain their black backdrop. The presentation shader
 * removes near-black and uses max(RGB) coverage, preserving source colours on
 * black while allowing the mural/fades to show through between the letters. */
static int footer_load(void) {
    int i;
    if(footer_mode<0){const char *s=getenv("BOF3_TITLE_FOOTER");footer_mode=!(s&&!strcmp(s,"original"));}
    if(!footer_mode)return 0;
    if(!footer_state) {
        const char *names[3]={"press-start.png","copyright-japan.png","copyright-usa.png"};
        const char *base=SDL_GetBasePath();footer_state=-1;if(!base)return 0;
        for(i=0;i<3;i++) {
            char path[4096];size_t size=0;void *file;int channels;
            snprintf(path,sizeof(path),"%sassets/title/%s",base,names[i]);file=SDL_LoadFile(path,&size);
            if(file && size<16*1024*1024)footer_pixels[i]=stbi_load_from_memory(file,(int)size,&footer_w[i],&footer_h[i],&channels,4);
            SDL_free(file);
        }
#if !defined(PSX_SDL3)
        SDL_free((void*)base);
#endif
        if(footer_pixels[0]&&footer_pixels[1]&&footer_pixels[2]&&footer_w[0]==1058&&footer_h[0]==69&&footer_w[1]==810&&footer_h[1]==62&&footer_w[2]==1541&&footer_h[2]==61)footer_state=1;
        else {fprintf(stderr,"bof3: title footer PNGs unavailable; keeping original footer\n");return 0;}
    }
    if(footer_state!=1)return 0;
    for(i=0;i<3;i++)if(!gl_renderer_prepare_artwork(4+i,footer_pixels[i],footer_w[i],footer_h[i]))return 0;
    return 1;
}
/* Existing New Game / Load Game image labels must remain in front of the
 * new host logo. Decode their exact 4bpp sprite source, retaining nearest
 * sampling, colour modulation, placement and current selection brightness. */
static int title_label(const GpuSpritePresentation *s,int buffer,int which) {
    const uint16_t *vram=gpu_get_vram();
    unsigned char *rgba=label_pixels[which][1-label_front[which]];
    const unsigned char *previous=label_pixels[which][label_front[which]];
    int x,y,w=s->width,cx=(s->clut&63)*16,cy=s->clut>>6;
    for(y=0;y<16;y++)for(x=0;x<w;x++) {
        uint16_t packed=vram[(s->v+y)*1024+896+(s->u+x)/4];
        uint16_t color=vram[cy*1024+cx+((packed>>(((s->u+x)%4)*4))&15)];
        unsigned char *p=rgba+(y*w+x)*4;
        p[0]=(unsigned char)((color&31)*255/31);p[1]=(unsigned char)(((color>>5)&31)*255/31);
        p[2]=(unsigned char)(((color>>10)&31)*255/31);p[3]=color?255:0;
    }
    if(memcmp(rgba,previous,(size_t)w*16*4))label_front[which]=1-label_front[which];
    if(!gl_renderer_prepare_artwork(which+2,label_pixels[which][label_front[which]],w,16))return 0;
    label_seen[buffer][which]=s_frame_count;label_color[buffer][which]=s->color;
    return 1;
}
/* Original logo layers 2/3,4/5,15/16 and TM tile 1. Double-buffered at y=0/240. */
int bof3_title_sprite(const GpuSpritePresentation *s) {
    int y=s->y,buffer=0,match=0,page=s->texpage&0x1f,which=-1,footer=-1,kind;
    if(!title_enabled() || s->texture_window || s->draw_width!=s->width)return 0;
    if(y>=240){buffer=1;y-=240;}
    if(s->x==26 && y==24 && s->u==0 && s->v==0 && s->width==240 && s->height==160 && page==0x1b && s->clut==(485<<6))match=1;
    if(s->x==266 && y==136 && s->u==0 && s->v==160 && s->width==48 && s->height==48 && page==0x1b && s->clut==(485<<6))match=1;
    if(s->x==-6 && y==28 && s->u==0 && s->v==0 && s->width==224 && s->height==128 && (page==0x19||page==9) && (s->clut==(484<<6)||s->clut==(491<<6)))match=2;
    if(s->x==218 && y==28 && s->u==0 && s->v==128 && s->width==96 && s->height==128 && (page==0x19||page==9) && (s->clut==(484<<6)||s->clut==(491<<6)))match=1;
    if(s->x==262 && y==130 && s->u==96 && s->v==60 && s->width==12 && s->height==10 && page==15 && s->clut==(480<<6))match=1;
    if((s->texpage&0x19f)==14 && s->clut==0x78c2 && s->height==16 && s->u==0) {
        if(s->x==96 && y==80 && s->width==128 && s->v==0)which=0;
        if(s->x==92 && y==112 && s->width==144 && s->v==16)which=1;
    }
    if((s->texpage&0x19f)==0x9d && s->clut==(486<<6) && s->height==16 && s->u==0) {
        if(s->x==48 && y==184 && s->v==0 && s->width==224)footer=0;
        if(s->x==12 && y==200 && s->v==16 && s->width==160)footer=1;
        if(s->x==12 && y==212 && s->v==32 && s->width==160)footer=2;
        if(s->x==172 && y==212 && s->v==48 && s->width==144)footer=2;
    }
    if((!match && which<0 && footer<0) || !(kind=title_guard()) || !title_load())return 0;
    if(footer>=0) {
        if(kind!=1 || !footer_load())return 0;
        footer_seen[buffer][footer]=s_frame_count;footer_opacity[buffer][footer]=(s->color&255)/128.f;return 1;
    }
    if(which>=0)return kind==2 ? title_label(s,buffer,which) : 0;
    if(match==2 && s->clut==(484<<6)){title_seen[buffer]=s_frame_count;title_opacity[buffer]=(s->color&255)/128.f;}
    return 1;
}
static int title_layers(GlArtworkLayer *out,int capacity) {
    GpuDisplayInfo di;int b,kind,count=2;gpu_get_display_info(&di);
    if(capacity<5 || !(kind=title_guard()) || di.disabled || di.depth24 || di.display_x!=0 || (di.display_y!=0 && di.display_y!=240))return 0;
    b=di.display_y==240;
    /* Original title draws at 30 Hz into alternating buffers. Displayed buffer
     * is normally 3-4 VBlanks older than its last draw, not 1-2. */
    if(!title_seen[b] || s_frame_count<title_seen[b] || s_frame_count-title_seen[b]>4)return 0;
    out[0]=(GlArtworkLayer){0,24,28,272,272.f*811/1939,title_opacity[b],1,1,1,0};
    out[1]=(GlArtworkLayer){1,96,106,128,128.f*732/2146,title_opacity[b],1,1,1,0};
    if(kind==2)for(int i=0;i<2;i++) {
        uint32_t color=label_color[b][i];
        if(label_seen[b][i] && s_frame_count>=label_seen[b][i] && s_frame_count-label_seen[b][i]<=4)
            out[count++]=(GlArtworkLayer){i+2,i?92.f:96.f,i?112.f:80.f,i?144.f:128.f,16,1,
                (color&255)/128.f,((color>>8)&255)/128.f,((color>>16)&255)/128.f,1};
    }
    if(kind==1)for(int i=0;i<3;i++) {
        if(footer_seen[b][i] && s_frame_count>=footer_seen[b][i] && s_frame_count-footer_seen[b][i]<=4) {
            const float widths[3]={208,160,304},xs[3]={56,12,12},ys[3]={184,200,214};
            out[count++]=(GlArtworkLayer){4+i,xs[i],ys[i],widths[i],widths[i]*footer_h[i]/footer_w[i],footer_opacity[b][i],1,1,1,0,1};
        }
    }
    return count;
}
PSX_MOD_CONSTRUCTOR(bof3_register_title_artwork) {gl_renderer_set_artwork_hook(title_layers);}
