from pathlib import Path
import subprocess,struct,hashlib,json,os
R=Path('BoF3 Research').resolve();O=R/'coverage/mural';G=R.parent/'BoF3 PSXRecomp/BreathOfFireIII';F=R.parent/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3';b=(O/'GAME-section-01-801D0C00.bin').read_bytes();assert hashlib.sha256(b).hexdigest()=='4085bb55d18007389e57c8400eeb51be7026e17a10b33af1ae8a5665d5d381af';data=','.join(hex(x)+'u' for x in struct.unpack('<130I',b[0xcf8:0xf00]))
s='''#include <stdint.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "mod_plugins.h"
static uint32_t ram_code[130];
static unsigned width=320,phase=1,notes=0;
static uint32_t decoded=0;
uint32_t mdec_get_decode_count(void) { return decoded; }
int bof3_startup_turbo_active(uint64_t frame);
uint32_t psx_mod_display_width(void) { return width; }
uint8_t psx_mod_read_byte(uint32_t p) { assert(p==0x80143C31u);return (uint8_t)phase; }
uint32_t psx_mod_read_word(uint32_t p) { assert(p>=0x801D18F8u && p<0x801D1B00u && !(p&3)); return ram_code[(p-0x801D18F8u)/4]; }
void psx_mod_note_wide_2d_frame(void) { ++notes; }
void bof3_mural_widescreen_vblank(void);
static const uint32_t original[]={'''+data+'''};
int main(int argc, char **argv) {
 memcpy(ram_code,original,sizeof(original));
 phase=0;assert(bof3_startup_turbo_active(10)==1);
 if(argc>1 && strcmp(argv[1],"timeout")==0) {
  assert(bof3_startup_turbo_active(1800)==0);
 } else {
  decoded=1;
  if(argc>1 && strcmp(argv[1],"skip")==0) {
   assert(bof3_startup_turbo_active(555)==1);
   phase=1;ram_code[0]^=1;assert(bof3_startup_turbo_active(1060)==1);
   ram_code[0]^=1;assert(bof3_startup_turbo_active(1063)==0);
  } else assert(bof3_startup_turbo_active(555)==0);
 }
 phase=0;decoded=0;assert(bof3_startup_turbo_active(0)==0);
 for(phase=0;phase<256;++phase){notes=0;bof3_mural_widescreen_vblank();assert(notes==(phase>=1 && phase<=3));}
 phase=2;
 for(unsigned i=0;i<130;++i){ram_code[i]^=1u;notes=0;bof3_mural_widescreen_vblank();assert(notes==0);ram_code[i]^=1u;}
 width=640;notes=0;bof3_mural_widescreen_vblank();assert(notes==0);
 width=0;bof3_mural_widescreen_vblank();assert(notes==0);
 width=320;bof3_mural_widescreen_vblank();assert(notes==1);
 puts("PASS: all 256 phase values, each of 130 mutated code words, unsupported widths, and valid restoration");return 0;
}
'''
(O/'guard-test.c').write_text(s)
args=['cl','/nologo','/TC','/W3','/I'+str(F/'runtime/include'),str(O/'guard-test.c'),str(G/'native/mural.c'),'/Fo:'+str(O)+'/','/Fe:'+str(O/'guard-test.exe'),'/link','/INCREMENTAL:NO'];r=subprocess.run(args,cwd=O,capture_output=True,text=True);(O/'guard-test-build.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stdout+r.stderr;r=subprocess.run([str(O/'guard-test.exe')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;(O/'guard-test.json').write_text(json.dumps({'passed':True,'result':r.stdout.strip(),'scope':'Actual native/mural.c, original binary guard bytes, mocked display/RAM/notification services.'},indent=2));print(r.stdout)
for mode in ('logo','skip','timeout'):
 r=subprocess.run([str(O/'guard-test.exe'),mode],capture_output=True,text=True,env=dict(os.environ,BOF3_SKIP_CAPCOM_LOGO='1' if mode=='skip' else '0'))
 assert r.returncode==0,r.stdout+r.stderr
 print('PASS: startup',mode,'and completed startup stays inactive')
