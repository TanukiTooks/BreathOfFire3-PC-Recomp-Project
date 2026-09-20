"""Record the shared BoF3 inputs and cross-check two independent disc readers."""
from pathlib import Path
import collections
import hashlib
import json
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'BoF3 Research'
DISC = ROOT / 'iso' / 'Breath of Fire III (USA)'
PSX = ROOT / 'BoF3 PSXRecomp' / 'psxrecomp-src-nightly-20260910-ed55299be3'
RECOMP = ROOT / 'BoF3 Recomp1' / 'RecompOne-master'

def hashes(path):
    digests = {name: hashlib.new(name) for name in ('md5', 'sha1', 'sha256')}
    crc = 0
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            for digest in digests.values():
                digest.update(chunk)
            crc = zlib.crc32(chunk, crc)
    return dict(path=str(path.relative_to(ROOT)), size=path.stat().st_size,
                crc32=f'{crc & 0xffffffff:08x}',
                **{name: digest.hexdigest() for name, digest in digests.items()})

psx = json.loads((OUT / 'psxrecomp-disc-probe.json').read_text())
recomp = json.loads((OUT / 'recompone-disc-probe.json').read_text(encoding='utf-8-sig'))
assert psx['boot_exe'] == recomp['boot']
track = DISC / psx['bin_name']

def extract(entry):
    result = bytearray()
    with track.open('rb') as stream:
        for lba in range(entry['lba'], entry['lba'] + (entry['size'] + 2047) // 2048):
            stream.seek(lba * 2352)
            sector = stream.read(2352)
            assert len(sector) == 2352 and sector[:12] == b'\x00' + b'\xff' * 10 + b'\x00'
            assert sector[15] == 2 and not sector[18] & 0x20, 'Expected Mode 2 Form 1'
            result.extend(sector[24:2072])
    return bytes(result[:entry['size']])

boot_entry = next(f for f in recomp['files'] if f['path'] == recomp['boot'])
boot = extract(boot_entry)
assert boot == (OUT / 'input' / psx['boot_exe']).read_bytes(), 'Disc reader extraction mismatch'
assert hashlib.sha256(boot).hexdigest() == psx['boot_exe_sha256']
assert boot[:8] == b'PS-X EXE'
header = dict(zip(('entry_pc', 'initial_gp', 'load_address', 'text_size'),
                  (f'0x{x:08X}' for x in struct.unpack_from('<4I', boot, 0x10))))
assert int(header['load_address'], 16) == int(boot_entry['baseAddress'], 16)
assert int(header['entry_pc'], 16) == int(psx['entry_pc'], 16)
assert len(boot) >= 0x800 + int(header['text_size'], 16)
for file_path in ('SYSTEM.CNF', 'LOGO/LOGO.EXE'):
    entry = next(f for f in recomp['files'] if f['path'] == file_path)
    destination = OUT / 'input' / file_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(extract(entry))

files = [hashes(path) for path in sorted(DISC.iterdir()) if path.is_file()]
expected_sha1 = {
 'Breath of Fire III (USA) (Track 1).bin': '5745d9dde965ed0ec673ba071deb762355fa3e1a',
 'Breath of Fire III (USA) (Track 2).bin': 'd9f92af296360772e62caa4cb276de3fa74f5538',
}
for file in files:
    expected = expected_sha1.get(Path(file['path']).name)
    if expected:
        assert file['sha1'] == expected, 'Disc hash differs from reference record'

source_files = []
for path in sorted(RECOMP.rglob('*')):
    relative = path.relative_to(RECOMP)
    if path.is_file() and not any(p in ('.git', 'bin', 'obj') for p in relative.parts):
        source_files.append({'path': relative.as_posix(), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
source_json = json.dumps(source_files, indent=2) + '\n'
(OUT / 'recompone-source-files.json').write_text(source_json, encoding='utf-8')
manifest = {
 'game': 'Breath of Fire III (USA)', 'serial': psx['serial'],
 'revision_note': 'USA release; no separate revision suffix in reference record. Identify exact input by hashes.',
 'reference': 'https://tasvideos.org/Games/774/Versions/View/1813',
 'reference_match': 'Both BIN track SHA-1 hashes match the TASVideos record sourced from Redump.',
 'disc_files': files, 'boot_executable': hashes(OUT / 'input' / psx['boot_exe']),
 'boot_header': header, 'boot_file_lba': boot_entry['lba'],
 'independent_extraction_matches': True,
 'disc_file_counts': dict(collections.Counter(f['kind'] for f in recomp['files'])),
 'overlay_note': 'rawcode labels and guessed bases are RecompOne heuristics, not validated overlays.',
 'psxrecomp_commit': (PSX / 'NIGHTLY_COMMIT').read_text().strip(),
 'recompone_source': {'provenance': 'User-supplied master source archive; exact upstream commit unavailable.',
                     'files': len(source_files), 'manifest_sha256': hashlib.sha256(source_json.encode()).hexdigest()},
 'ghidra_version': '12.1.3',
 'ghidra_psx_loader_jar': hashes(ROOT / 'Ghidra' / 'ghidra_12.1.3_PUBLIC' / 'Ghidra' / 'Extensions' / 'ghidra_psx_ldr' / 'lib' / 'ghidra_psx_ldr.jar'),
}
(OUT / 'input-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k: manifest[k] for k in ('serial', 'reference_match', 'boot_header', 'independent_extraction_matches', 'disc_file_counts')}, indent=2))
print('SYSTEM.CNF:', (OUT / 'input' / 'SYSTEM.CNF').read_text().strip())
