from pathlib import Path
import tempfile,tomllib,unittest
import bof3_display_settings as settings
class SettingsTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]/'coverage/display-settings');self.path=Path(self.temp.name)/'settings.toml'
 def tearDown(self):self.temp.cleanup()
 def save(self,**kw):return settings.save(self.path,kw.get('mode','windowed'),kw.get('width',960),kw.get('scale',1),kw.get('filter','nearest'),kw.get('vsync','on'),kw.get('sha'),kw.get('aspect'),kw.get('turbo_speed'),psx_wobble=kw.get('psx_wobble'))
 def test_defaults(self):self.assertEqual(settings.show(self.path)['scale'],1);self.save();self.assertEqual(settings.show(self.path)['filter'],'nearest')
 def test_preserve_other_preferences(self):
  raw=b'# Keep me\n[video]\nwindow_width = 640 # previous\ngeometry_correction = true\n[audio]\nfrequency = 44100\n[controller]\nname = "My pad"\n';self.path.write_bytes(raw);self.save(mode='borderless',scale=2,filter='bilinear',vsync='off');doc=tomllib.loads(self.path.read_text());self.assertTrue(doc['video']['geometry_correction']);self.assertEqual(doc['controller']['name'],'My pad');self.assertEqual(doc['audio']['frequency'],44100);self.assertIn('# Keep me',self.path.read_text());self.assertEqual(self.path.with_name('settings.toml.before-display-settings').read_bytes(),raw)
 def test_stale_window_rejected(self):
  sha=settings.show(self.path)['source_sha'];self.save();before=self.path.read_bytes()
  with self.assertRaises(ValueError):self.save(sha=sha)
  self.assertEqual(self.path.read_bytes(),before)
 def test_invalid_toml_unchanged(self):
  self.path.write_text('[video\n')
  with self.assertRaises(ValueError):self.save()
  self.assertEqual(self.path.read_text(),'[video\n')
 def test_invalid_option_unchanged(self):
  self.save();before=self.path.read_bytes()
  for option in [{'scale':5},{'width':123},{'filter':'unknown'},{'mode':'exclusive'},{'vsync':'unknown'}]:
   with self.assertRaises(ValueError):self.save(**option)
  self.assertEqual(self.path.read_bytes(),before)
 def test_non_table_unchanged(self):
  self.path.write_text('video = 3\n')
  with self.assertRaises(ValueError):self.save()
  self.assertEqual(self.path.read_text(),'video = 3\n')
 def test_reopen_roundtrip(self):
  self.save(mode='borderless',width=1280,scale=4,filter='bilinear',vsync='off');p=settings.show(self.path);self.assertEqual((p['window_mode'],p['width'],p['scale'],p['filter'],p['vsync']),('borderless',1280,4,'bilinear','off'))
 def test_widescreen_and_other_mods(self):
  mod=self.path.parent/'mods/state.toml';mod.parent.mkdir();original='format_version = 2\n# Other mod\n[[package]]\nid = "other"\nversion = "2.0"\n[[feature]]\npackage_id = "other"\nid = "choice"\nenabled = true\n[feature.values]\nquality = "high"\n';mod.write_text(original)
  self.save(aspect='16:9');self.assertEqual(settings.show(self.path)['aspect'],'16:9');self.assertIn('# Other mod',mod.read_text());doc=tomllib.loads(mod.read_text());self.assertEqual(doc['feature'][0]['values'],{'quality':'high'})
  self.save(aspect='4:3');self.assertEqual(settings.show(self.path)['aspect'],'4:3');self.assertEqual(len(tomllib.loads(mod.read_text())['feature']),2);self.assertEqual(mod.with_name('state.toml.before-widescreen').read_text(),original)
 def test_stale_mod_state_rejected(self):
  self.save(aspect='4:3');sha=settings.show(self.path)['source_sha'];self.save(aspect='16:9');before=self.path.read_bytes();mod=self.path.parent/'mods/state.toml';before_mod=mod.read_bytes()
  with self.assertRaises(ValueError):self.save(aspect='4:3',sha=sha)
  self.assertEqual(self.path.read_bytes(),before);self.assertEqual(mod.read_bytes(),before_mod)
 def test_invalid_mod_state_no_partial_save(self):
  self.save();before=self.path.read_bytes();mod=self.path.parent/'mods/state.toml';mod.parent.mkdir();mod.write_text('format_version = 1\n')
  with self.assertRaises(ValueError):self.save(scale=4,aspect='16:9')
  self.assertEqual(self.path.read_bytes(),before);self.assertEqual(mod.read_text(),'format_version = 1\n')
 def test_display_only_preserves_widescreen(self):
  self.save(aspect='16:9');self.save(scale=2);self.assertEqual(settings.show(self.path)['aspect'],'16:9')
 def test_turbo_roundtrip_and_preservation(self):
  self.assertEqual(settings.show(self.path)['turbo_speed'],2);self.path.write_text('[bof3]\nother = "keep"\n[hotkeys]\nfast_forward_pad = 1528\n');self.save(turbo_speed=4);self.assertEqual(settings.show(self.path)['turbo_speed'],4);self.save(scale=2);self.assertEqual(settings.show(self.path)['turbo_speed'],4);self.save(turbo_speed=2);self.assertEqual(settings.show(self.path)['turbo_speed'],2);doc=tomllib.loads(self.path.read_text());self.assertEqual(doc['bof3']['other'],'keep');self.assertEqual(doc['hotkeys']['fast_forward_pad'],1528)
 def test_invalid_turbo_unchanged(self):
  self.save();before=self.path.read_bytes()
  for speed in [0,1,3,16,True,'4']:
   with self.assertRaises(ValueError):self.save(turbo_speed=speed)
  self.assertEqual(self.path.read_bytes(),before)
 def test_wobble_roundtrip_and_custom_preservation(self):
  self.assertTrue(settings.show(self.path)['psx_wobble']);self.save(psx_wobble=False)
  self.assertFalse(settings.show(self.path)['psx_wobble']);v=tomllib.loads(self.path.read_text())['video'];self.assertTrue(v['geometry_correction'] and v['perspective_texturing'])
  self.save(scale=4);self.assertFalse(settings.show(self.path)['psx_wobble']);self.save(psx_wobble=True)
  v=tomllib.loads(self.path.read_text())['video'];self.assertFalse(v['geometry_correction'] or v['perspective_texturing']);self.assertTrue(settings.show(self.path)['psx_wobble'])
  self.path.write_text('[video]\ngeometry_correction = true\nperspective_texturing = false\n');self.assertIsNone(settings.show(self.path)['psx_wobble']);self.save(scale=2);v=tomllib.loads(self.path.read_text())['video'];self.assertTrue(v['geometry_correction']);self.assertFalse(v['perspective_texturing'])
 def test_invalid_wobble_unchanged(self):
  self.save();before=self.path.read_bytes()
  for value in ['off',0,1]:
   with self.assertRaises(ValueError):self.save(psx_wobble=value)
  self.assertEqual(self.path.read_bytes(),before)
if __name__=='__main__':unittest.main()
