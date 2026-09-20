"""Compile the real menu gate and plugin with isolated display/frame inputs."""
from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parents[1];F=R.parent/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';O=R/'coverage/widescreen-menu-background';source=(F/'runtime/src/gpu.c').read_text(encoding='utf-8')
lo=source.index('static uint32_t ws_wide_2d_stamp =');hi=source.index('/* Squash applies only',lo)
actual=source[lo:hi]
pre=r'''
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include "mod_plugins.h"
uint64_t s_frame_count=100;
static int engaged=1, gameplay=0, only2d=1, mdec=0, depth=0;
typedef struct { int depth24; } GpuDisplayInfo;
static int ws_engaged(void) { return engaged; }
static int ws_game_mode(void) { return gameplay; }
static int ws_2d_only_scene(void) { return only2d; }
static int mdec_recently_active(uint32_t n) { (void)n; return mdec; }
static void gpu_get_display_info(GpuDisplayInfo *di) { di->depth24=depth; }
#define WS_FMV_HYSTERESIS 30
'''
post=r'''
/* Mural behavior has its own complete-code-guard test. */
void bof3_mural_widescreen_vblank(void) {}
int psx_mod_register_vblank_plugin(const char *id, PSXModVBlankCallback cb) { (void)id; assert(cb); return 1; }
static PSXModActivationCallback activate;
static uint32_t width=320;
static int allow_activation=0;
int psx_mod_register_activation_plugin(const char *id, PSXModActivationCallback cb) { (void)id; activate=cb; return 1; }
int psx_mod_set_fixed_display_aspect(uint32_t n,uint32_t d) { assert(n==16 && d==9);return allow_activation; }
uint32_t psx_mod_display_width(void) { return width; }
void psx_mod_note_wide_2d_frame(void) { gpu_ws_note_wide_2d_frame(); }
extern int32_t bof3_menu_background_padding(void);
extern uint32_t bof3_menu_background_pairs(void);
int main(void) {
 assert(gpu_ws_present_native_43()==1);
 gpu_ws_note_wide_2d_frame();assert(gpu_ws_present_native_43()==0);
 s_frame_count+=2;assert(gpu_ws_present_native_43()==0);
 ++s_frame_count;assert(gpu_ws_present_native_43()==1);
 gpu_ws_note_wide_2d_frame();++s_frame_count;mdec=1;assert(gpu_ws_present_native_43()==1);
 ++s_frame_count;mdec=0;depth=1;assert(gpu_ws_present_native_43()==1);
 ++s_frame_count;depth=0;gameplay=1;only2d=0;assert(gpu_ws_present_native_43()==0);
 gameplay=0;only2d=1;assert(gpu_ws_present_native_43()==1);
 engaged=0;gpu_ws_note_wide_2d_frame();assert(gpu_ws_present_native_43()==0);engaged=1;
 assert(activate && bof3_menu_background_padding()==0 && bof3_menu_background_pairs()==5);
 activate();assert(bof3_menu_background_padding()==0);
 allow_activation=1;activate();s_frame_count+=10;
 assert(gpu_ws_present_native_43()==1);
 assert(bof3_menu_background_padding()==64 && bof3_menu_background_pairs()==7);
 assert(gpu_ws_present_native_43()==0);
 width=640;s_frame_count+=10;assert(bof3_menu_background_padding()==0 && bof3_menu_background_pairs()==5);
 assert(gpu_ws_present_native_43()==1);
 width=0;assert(bof3_menu_background_padding()==0);
 puts("PASS: expiry, FMV precedence, existing 3D path, disabled/failed activation, supported and unknown widths");return 0;
}
'''
h=O/'gate-test.c';h.write_text(pre+actual+post,encoding='utf-8')
cmd=['cl','/nologo','/TC','/W3','/I'+str(F/'runtime/include'),str(h),str(G/'native/widescreen.c'),'/Fe:'+str(O/'gate-test.exe'),'/Fo:'+str(O)+'/','/link','/INCREMENTAL:NO']
r=subprocess.run(cmd,cwd=O,capture_output=True,text=True);(O/'gate-test-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr
r=subprocess.run([str(O/'gate-test.exe')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
(O/'gate-test.json').write_text(json.dumps({'passed':True,'result':r.stdout.strip(),'gpu_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'scope':'Actual extracted GPU presentation gate and actual game plugin compiled with mocked frame/display inputs.'},indent=2));print(r.stdout)
