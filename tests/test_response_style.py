import sys
from pathlib import Path
import unittest
import io
import json
import types
from unittest.mock import patch
import engine
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from response_style import STYLE,image_result,deduplicate,spoken_answer

class ResponseStyleTests(unittest.TestCase):
 def test_image_metadata_hidden_from_default_model_result(self):
  result={'image':'x.png','backend':'ONNX CPU','seed':3,'steps':20,'prompt':'test'}
  visible=image_result(result,'Zeig mir Hamburg')
  self.assertEqual(visible['image'],'x.png');self.assertNotIn('backend',visible);self.assertNotIn('seed',visible);self.assertEqual(result['seed'],3)
 def test_explicit_technical_question_keeps_details(self):
  result={'image':'x.png','seed':3}
  self.assertEqual(image_result(result,'Welches Modell wurde verwendet?'),result)
 def test_real_errors_retained(self):
  result={'error':'GPU failed'};self.assertEqual(image_result(result,'Ein Bild'),result)
 def test_exact_duplicate_paragraph(self):
  self.assertEqual(deduplicate('Morgen 5 °C.\n\n**Morgen 5 °C.**\n\nÜbermorgen 6 °C.'),'Morgen 5 °C.\n\nÜbermorgen 6 °C.')
 def test_distinct_days_values_and_caveats_preserved(self):
  text='Morgen 5 °C.\n\nÜbermorgen 5 °C.\n\nMorgen 6 °C.\n\nOffline: keine aktuellen Daten.'
  self.assertEqual(deduplicate(text),text)
 def test_technical_narration_omitted_from_speech(self):
  text='Hier ist das Bild. Das Bild wurde mit Tiny-SD auf der CPU erstellt. Es zeigt Hamburg.'
  self.assertEqual(spoken_answer(text,'Ein Bild',True),'Hier ist das Bild. Es zeigt Hamburg.')
 def test_speech_cleanup_preserves_list_boundaries(self):
  text='Wetter:\n- **Temperaturmin:** 5 °C\n- **Wind:** 9 km/h'
  self.assertEqual(spoken_answer(text,'Ein Wetterbild',True),text)
 def test_explicit_explanation_can_be_spoken(self):
  text='Das Bild wurde mit Tiny-SD erstellt.'
  self.assertEqual(spoken_answer(text,'Wie wurde das Bild erstellt?',True),text)
 def test_failures_and_scene_not_suppressed(self):
  text='Das Bild konnte mit dem Modell nicht erstellt werden. Das Bild zeigt einen Computer mit GPU.'
  self.assertEqual(spoken_answer(text,'Ein Bild',True),text)
 def test_engine_uses_style_and_sanitized_image_result_but_logs_full_metadata(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];instance.image_engine=None;seen=[]
  replies=['<tool_call><function=generate_image><parameter=prompt>Hamburg</parameter></function></tool_call>','Hier ist das Bild.\n\nHier ist das Bild.']
  def generate(conversation,*args):seen.append(json.loads(json.dumps(conversation)));return replies[len(seen)-1],None
  instance.generate=generate;output=io.StringIO()
  result={'image':'test.png','backend':'ONNX CPU','seed':123,'steps':20}
  with patch('image_runtime.generate',return_value=result),patch.object(engine,'PROTOCOL',output):
   instance.respond({'input':'Ein Bild von Hamburg','output':'txt','weather_enabled':False})
  self.assertIn('each weather fact once',seen[0][0]['content'])
  tool=next(m for m in seen[-1] if m['role']=='tool')
  self.assertNotIn('ONNX',tool['content']);self.assertNotIn('seed',tool['content'])
  events=[json.loads(line) for line in output.getvalue().splitlines()]
  self.assertEqual(next(e for e in events if e['type']=='tool')['result']['seed'],123)
  self.assertEqual(events[-1]['text'],'Hier ist das Bild.')
 def test_configured_assistant_name_reaches_chat_prompt(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  def generate(conversation,*args):seen.append(conversation);return 'Hallo.',None
  instance.generate=generate
  with patch.object(engine,'PROTOCOL',io.StringIO()):
   instance.respond({'input':'Wie heißt du?','assistant_name':' Mira\nNova ','output':'txt','tools':False})
  self.assertIn('"Mira Nova"',seen[0][0]['content'])
 def test_blank_assistant_name_uses_default(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  def generate(conversation,*args):seen.append(conversation);return 'Hallo.',None
  instance.generate=generate
  with patch.object(engine,'PROTOCOL',io.StringIO()):
   instance.respond({'input':'Hallo','assistant_name':'  ','output':'txt','tools':False})
  self.assertIn('"LFM3"',seen[0][0]['content'])
 def test_style_preserves_offline_caveats(self):
  self.assertIn('offline/cache',STYLE);self.assertIn('each weather fact once',STYLE)

if __name__=='__main__':unittest.main()
