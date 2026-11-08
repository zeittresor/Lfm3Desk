import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from speech_text import for_speech
import engine

class SpeechTextTests(unittest.TestCase):
 def test_image_caption_preserved_and_windows_path_removed(self):
  text=r'Hier ist dein Bild: ![Wetter in Kaltenkirchen](E:\Debug Enviroment\Lfm3Desk\output\images\bild (1).png) Es zeigt eine Straße.'
  self.assertEqual(for_speech(text),'Hier ist dein Bild: Wetter in Kaltenkirchen Es zeigt eine Straße.')
 def test_url_labels_and_raw_links(self):
  self.assertEqual(for_speech('Siehe [Wikipedia](https://de.wikipedia.org/wiki/Eiffelturm_(Paris)). Weiter.'),'Siehe Wikipedia. Weiter.')
  self.assertNotIn('https',for_speech('Quelle: https://example.org/a?x=1&y=2.'))
  self.assertEqual(for_speech('Siehe (https://example.org/test).'),'Siehe.')
  self.assertEqual(for_speech('www.example.com und example.de/wiki/Test'),'und')
 def test_quoted_and_known_paths_with_spaces(self):
  path=r'E:\Debug Enviroment\output\a nice image.png'
  self.assertEqual(for_speech('Bild: '+path+' ist fertig.',[path]),'Bild: ist fertig.')
  self.assertNotIn('Debug',for_speech('Datei: "'+path+'".'))
  self.assertNotIn('output',for_speech('Datei: /home/user/output/bild.png'))
  self.assertNotIn('server',for_speech(r'Datei: \\server\share\bild.png'))
 def test_units_and_ordinary_prose_not_removed(self):
  text='Morgen 7,1 °C, 95 % Feuchtigkeit und 5,3 km/h. Ein Verhältnis von 1/2, C++ und 10:30 Uhr.'
  self.assertEqual(for_speech(text),text)
 def test_references_and_only_url(self):
  self.assertEqual(for_speech('[Wikipedia][wiki]\n\n[wiki]: https://de.wikipedia.org/wiki/Test'),'Wikipedia')
  self.assertEqual(for_speech('https://example.org/image.png'),'')
 def test_generated_tts_is_clean_but_display_text_preserved(self):
  for tools_enabled,task in ((False,'chat'),(True,'chat'),(False,'translate'),(False,'asr')):
   with self.subTest(tools=tools_enabled,task=task),tempfile.TemporaryDirectory() as temp:
    instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
    original=r'Hier ist [dein Bild](E:\output\bild.png). Mehr: https://example.org/details.'
    audio=types.SimpleNamespace(audio_codes=MagicMock(),audio_lengths=[1])
    def generate(conversation,mode,request,tools=None):
     seen.append((mode,json.loads(json.dumps(conversation))))
     return (original,None) if mode=='text' else ('',audio)
    instance.generate=generate;instance.torch=types.SimpleNamespace(inference_mode=contextlib.nullcontext)
    wave=MagicMock();wave.squeeze.return_value.float.return_value.cpu.return_value.numpy.return_value=[0.0]
    instance.codec=types.SimpleNamespace(decode=lambda _:types.SimpleNamespace(audio_values=[wave]))
    protocol=io.StringIO()
    with patch.object(engine,'ROOT',Path(temp)),patch.object(engine,'PROTOCOL',protocol),patch.dict(sys.modules,{'soundfile':types.SimpleNamespace(write=lambda *args,**kwargs:None)}):
     instance.respond({'input':'Zeig das Bild','output':'txt,tts','tools':tools_enabled,'task':task})
    self.assertEqual(seen[0][0],'text');self.assertTrue(all(mode=='audio' for mode,_ in seen[1:]))
    spoken=' '.join(conversation[-1]['content'] for mode,conversation in seen if mode=='audio');self.assertIn('dein Bild',spoken);self.assertNotIn('E:',spoken);self.assertNotIn('example.org',spoken)
    self.assertEqual(json.loads(protocol.getvalue().splitlines()[-1])['text'],original)

 def test_explicit_verbatim_tts_is_not_filtered(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  original='Bitte https://example.org vorlesen.'
  def generate(conversation,mode,request,tools=None):
   seen.append((mode,conversation))
   raise RuntimeError('Stop after capturing TTS input')
  instance.generate=generate
  with self.assertRaisesRegex(RuntimeError,'Stop after capturing'):
   instance.respond({'input':original,'task':'tts','output':'tts'})
  self.assertEqual(seen[0][0],'audio');self.assertEqual(seen[0][1][-1]['content'],original)
