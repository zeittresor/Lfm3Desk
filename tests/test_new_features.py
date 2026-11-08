import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from code_artifacts import archive,without_code
from image_intent import requested
from speech_text import for_speech
from tools_local import convert_units
import engine

class CodeTests(unittest.TestCase):
 def test_multiple_code_files_timestamp_manifest_no_execution(self):
  text='Hier:\n```python filename=../../test.py\nprint("Hallo")\n```\n```csharp\nclass Test {}\n```'
  with tempfile.TemporaryDirectory() as d:
   saved=archive(text,d);self.assertEqual(len(saved),2)
   for f in saved:self.assertEqual(Path(f['path']).parent,Path(d)/'output'/'code');self.assertTrue(f['complete'])
   self.assertRegex(Path(saved[0]['path']).name,r'^\d{8}_\d{6}_\d{6}_');self.assertEqual(Path(saved[0]['path']).suffix,'.py');self.assertEqual(Path(saved[1]['path']).suffix,'.cs');self.assertEqual(Path(saved[0]['path']).read_text(),'print("Hallo")\n')
   manifest=json.loads(next(Path(d).rglob('*manifest.json')).read_text());self.assertFalse(manifest['executed']);self.assertIn('app_version',manifest)
 def test_unclosed_code_is_saved_flagged_and_not_spoken(self):
  text='Code:\n```python\nprint("NEVER_SAY")'
  with tempfile.TemporaryDirectory() as d:self.assertFalse(archive(text,d)[0]['complete'])
  self.assertNotIn('NEVER_SAY',for_speech(text))
 def test_tilde_long_fences_inline_opener(self):
  for text in ('Vorher\n~~~~python\nSECRET\n~~~~\nNachher','Vorher ```python\nSECRET\n```\nNachher'):
   self.assertNotIn('SECRET',for_speech(text));self.assertIn('Vorher',for_speech(text));self.assertIn('Nachher',for_speech(text))
 def test_inline_fence_is_saved_but_not_spoken(self):
  text='Code: ```python print("SECRET")``` Fertig.'
  self.assertNotIn('SECRET',for_speech(text));self.assertIn('Fertig',for_speech(text))
  with tempfile.TemporaryDirectory() as d:
   saved=archive(text,d);self.assertEqual(Path(saved[0]['path']).suffix,'.py');self.assertIn('SECRET',Path(saved[0]['path']).read_text())
 def test_single_line_unclosed_fence_is_not_spoken(self):
  self.assertNotIn('SECRET',for_speech('```SECRET'))
 def test_no_code_no_output(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(archive('Hallo',d),[]);self.assertFalse((Path(d)/'output').exists())
 def test_unique_files_do_not_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   a=archive('```py\nprint(1)\n```',d);b=archive('```py\nprint(1)\n```',d);self.assertNotEqual(a[0]['path'],b[0]['path'])
 def test_empty_blocks_do_not_save(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(archive('```\n\n```',d),[])
 def test_worker_archives_code_and_sends_only_prose_to_tts(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[]
  text='Hier ist der Code:\n```python\nprint("SECRET")\n```'
  instance.generate=lambda *args:(text,None);output=io.StringIO()
  with tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)),patch.object(engine,'PROTOCOL',output),patch('audio_pipeline.render',return_value=('audio.wav',False)) as render:
   instance.respond({'input':'Schreibe Python-Code','output':'txt,tts','tools':False})
   self.assertNotIn('SECRET',render.call_args.args[1]);events=[json.loads(x) for x in output.getvalue().splitlines()]
   result=events[-1];self.assertEqual(result['text'],text);self.assertEqual(len(result['code_files']),1);self.assertIn('SECRET',Path(result['code_files'][0]['path']).read_text());self.assertTrue(any(e['type']=='code_saved' for e in events))
 def test_audio_render_boundary_drops_explicit_tts_code(self):
  from audio_pipeline import render
  seen=[]
  fake=types.SimpleNamespace(generate=lambda *a:seen.append(a) or (_ for _ in ()).throw(RuntimeError('captured')))
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(RuntimeError,'captured'):render(fake,'```py\nSECRET\n```','German','female',{},lambda *a,**k:None,d)
  self.assertNotIn('SECRET',seen[0][0][-1]['content']);self.assertIn('Code',seen[0][0][-1]['content'])

class ImageIntentTests(unittest.TestCase):
 def test_clear_image_requests(self):
  for text in ('wie wird das wetter morgen in hamburg und wie würde das aussehen als erstelltes bild?','Erstelle ein Bild eines Leuchtturms','Mach ein Bild von Hamburg','ein Bild von Hamburg erstellen','Create a picture of a cat','draw an image','Visualisiere die Szene'):
   self.assertTrue(requested(text),text)
 def test_negated_explanatory_and_code_requests(self):
  for text in ('Kein Bild erstellen','Bitte ohne Bild','Beschreibe nur ein Bild','Wie erstellt man ein Bild?','How to generate an image?','Write code to create an image','Was zeigt dieses Bild?','Do not generate an image','Bitte nicht als Bild','Do not draw a picture'):
   self.assertFalse(requested(text),text)
 def setup_engine(self,replies):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];instance.image_engine=None;seen=[]
  def generate(conversation,*args):seen.append(json.loads(json.dumps(conversation)));return replies.pop(0),None
  instance.generate=generate;return instance,seen
 def test_prose_fallback_calls_image_then_returns_reply(self):
  instance,seen=self.setup_engine(['Eine Szene am Hafen.','A harbour in Hamburg with clouds.','Hier ist das Bild.']);output=io.StringIO()
  with patch('image_runtime.generate',return_value={'image':'test.png'} ) as generator,patch.object(engine,'PROTOCOL',output):instance.respond({'input':'wie würde Hamburg als erstelltes Bild aussehen?','output':'txt','weather_enabled':False})
  generator.assert_called_once();self.assertEqual(generator.call_args.args[1]['prompt'],'A harbour in Hamburg with clouds.')
  events=[json.loads(x) for x in output.getvalue().splitlines()];self.assertEqual(events[-1]['text'],'Hier ist das Bild.');self.assertTrue(next(e for e in events if e['type']=='tool')['application_fallback'])
 def test_failed_model_image_call_is_not_retried_by_fallback(self):
  instance,_=self.setup_engine(['<tool_call><function=generate_image><parameter=prompt>harbour</parameter></function></tool_call>','Bild fehlgeschlagen.'])
  with patch('image_runtime.generate',side_effect=RuntimeError('fixture error')) as generator,patch.object(engine,'PROTOCOL',io.StringIO()),contextlib.redirect_stderr(io.StringIO()):instance.respond({'input':'Erstelle ein Bild','output':'txt','weather_enabled':False})
  self.assertEqual(generator.call_count,1)
 def test_disabled_tools_never_generate_image(self):
  instance,_=self.setup_engine(['Tools sind deaktiviert.'])
  with patch('image_runtime.generate',side_effect=AssertionError('image generated')),patch.object(engine,'PROTOCOL',io.StringIO()):instance.respond({'input':'Erstelle ein Bild','output':'txt','tools':False})
 def test_failed_fallback_reports_error_and_stops(self):
  instance,_=self.setup_engine(['Stell dir einen Hafen vor.','A harbour.','Fehler bei der Bildgenerierung.']);output=io.StringIO()
  with patch('image_runtime.generate',side_effect=RuntimeError('fixture error')) as generator,patch.object(engine,'PROTOCOL',output),contextlib.redirect_stderr(io.StringIO()):instance.respond({'input':'Erstelle ein Bild','output':'txt','weather_enabled':False})
  self.assertEqual(generator.call_count,1);events=[json.loads(x) for x in output.getvalue().splitlines()];self.assertIn('error',next(e for e in events if e['type']=='tool')['result'])
 def test_weather_evidence_reaches_fallback_prompt(self):
  replies=['<tool_call><function=current_weather><parameter=place>Hamburg</parameter></function></tool_call>','Hafen bei 5 Grad.','A cloudy harbour.','Bild fertig.'];instance,seen=self.setup_engine(replies)
  service=types.SimpleNamespace(schemas=lambda:[],wiki_available=False,online=types.SimpleNamespace(wiki=False,weather=True,web=False),sources=[],run=lambda *a:{'temperature_2m':5,'online_available':True})
  with patch.object(engine,'ToolServices',return_value=service),patch('image_runtime.generate',return_value={'image':'x.png'}),patch.object(engine,'PROTOCOL',io.StringIO()):instance.respond({'input':'Wetter und als erstelltes Bild','output':'txt'})
  self.assertIn('temperature_2m',seen[2][-1]['content'])

class UnitTests(unittest.TestCase):
 def test_temperature_and_speed(self):
  self.assertEqual(convert_units(0,'C','F')['value'],32);self.assertEqual(convert_units(36,'km/h','m/s')['value'],10)
 def test_lengths_and_weights(self):
  self.assertEqual(convert_units(2,'km','m')['value'],2000);self.assertEqual(convert_units(1,'kg','g')['value'],1000)
 def test_invalid_quantities(self):
  for args in ((1,'kg','m'),(-1,'K','C'),(float('nan'),'C','F')):
   with self.assertRaises(ValueError):convert_units(*args)

@unittest.skipUnless(importlib.util.find_spec('reportlab') and importlib.util.find_spec('pypdf'),'PDF test packages required')
class PdfTests(unittest.TestCase):
 def test_pagination_unicode_and_code(self):
  from pdf_export import export
  from pypdf import PdfReader
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'chat.pdf';text='Du: Grüße aus Köln.\nMira: Höchsttemperatur 8 °C.\n```python\nprint("Hallo")\n'+('print("long_code")\n'*130)+'```\n'+('Eine weitere Zeile mit Umlauten äöü.\n'*110)
   export({'title':'Wetter in Hamburg','text':text,'assistant_name':'Mira'},path)
   pdf=PdfReader(path);self.assertGreater(len(pdf.pages),1);all_text='\n'.join(p.extract_text() for p in pdf.pages);self.assertIn('Grüße aus Köln',all_text);self.assertIn('print("Hallo")',all_text);self.assertIn('Höchsttemperatur',all_text)

if __name__=='__main__':unittest.main()
