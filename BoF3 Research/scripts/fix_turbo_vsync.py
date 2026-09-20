"""Pinned PSXRecomp bounded-Turbo/VSync correction; actual hotkey rate tests in coverage/turbo.
Pace every guest frame at the selected multiplier, present near normal host cadence,
and suspend driver VSync only while manual Turbo is active. Guest audio is unchanged.
"""
from pathlib import Path
import hashlib
path=Path(__file__).resolve().parents[2]/'BoF3 PSXRecomp/psxrecomp-src-nightly-20260910-ed55299be3/runtime/src/main.cpp'
raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
BEFORE='b63bd01de31064dccd7ae037a475a536432d3e97218133e3dea168ce0d521f8c'
AFTER='5b97adfc2dc3ef22ba26ccca1de170069974bc3964f116a08356780682ae6a1e'
# Verified additive read-only prompt bridge; removing its three insertions
# reproduces AFTER byte-for-byte. Cadence implementation is unchanged.
PROMPT_BRIDGE='0cc3dda225dc9bc723cf6b1732fe6af58060271d6e83a8898dbeaff5063ef818'
# Adds the game-scoped F1 dialog and initial loading gate; manual Turbo is unchanged.
STARTUP_PAUSE='4d3b0c5ddc147b7e58ea4ffddf3c64e3b4cb183bc585f76c2eca925a9ee2b967'
REPLACEMENTS=[(b'const int present_every = (mult < 0) ? 4 : (mult <= 4 ? 2 : 4);', b'const int present_every = (mult < 0) ? 4 : mult;'), (b'static double        g_frame_period_ms = PSX_FRAME_PERIOD_MS;', b'static double        g_frame_period_ms = PSX_FRAME_PERIOD_MS;\n/* Manual Turbo owns wall pacing; restore the chosen VSync when released. */\nstatic bool          g_manual_fast_forward_active = false;'), (b'static int present_vsync_owns_cadence(void) {\n', b'static int present_vsync_owns_cadence(void) {\n    if (g_manual_fast_forward_active) return 0;\n'), (b'            manual_turbo_active = true;\n', b'            manual_turbo_active = true;\n            if (!g_manual_fast_forward_active) {\n                g_manual_fast_forward_active = true;\n                apply_present_cadence();\n            }\n'), (b'        } else {\n            turbo_skip = 0;\n            turbo_was_down = 0;', b'        } else {\n            if (g_manual_fast_forward_active) {\n                g_manual_fast_forward_active = false;\n                apply_present_cadence();\n            }\n            turbo_skip = 0;\n            turbo_was_down = 0;')]
if sha in (AFTER,PROMPT_BRIDGE,STARTUP_PAUSE):print('Turbo VSync cadence fix already applied.')
elif sha==BEFORE:
 for old,new in REPLACEMENTS:
  assert raw.count(old)==1
  raw=raw.replace(old,new)
 assert hashlib.sha256(raw).hexdigest()==AFTER
 path.write_bytes(raw);print('Applied bounded Turbo VSync cadence fix.')
else:raise RuntimeError('Runtime source changed. Review the Turbo cadence fix against this source before building.')
