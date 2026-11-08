import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock,patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from audio_pipeline import chunks,combine,render,RATE
from chat_context import model_history,strip_refusals
import engine

class AudioTests(unittest.TestCase):
 def test_chunks_decimals_abbreviations_and_long_sentence(self):
  result=chunks('Dr. Meier misst ca. 7.1 Grad. Danach folgt Satz zwei!')
  self.assertEqual(len(result),2);self.assertIn('7.1',result[0])
  long=' '.join(['Langwort']*60)+'.';result=chunks(long)
  self.assertTrue(all(len(part)<=140 for part in result));self.assertEqual(' '.join(result),long)
 def test_join_normalizes_and_adds_pause_without_clipping(self):
  wave=np.sin(np.arange(RATE)*2*np.pi*220/RATE).astype(np.float32)
  joined=combine([wave*.8,wave*.05])
  self.assertEqual(len(joined),RATE*2+round(RATE*.12));self.assertLessEqual(float(np.abs(joined).max()),.95001)
  self.assertTrue(np.isfinite(joined).all());self.assertTrue(np.all(joined[RATE:RATE+round(RATE*.12)]==0))
  with self.assertRaises(ValueError):combine([np.array([np.nan])])
 def test_render_restarts_each_sentence_and_saves_fragments(self):
  seen=[];wave=MagicMock();wave.squeeze.return_value.float.return_value.cpu.return_value.numpy.return_value=np.sin(np.arange(2400)*.08).astype(np.float32)*.2
  out=types.SimpleNamespace(audio_codes=MagicMock(),audio_lengths=[20])
  def generate(conversation,mode,request):seen.append((conversation,mode,request));return '',out
  fake=types.SimpleNamespace(generate=generate,torch=types.SimpleNamespace(inference_mode=contextlib.nullcontext),codec=types.SimpleNamespace(decode=lambda _:types.SimpleNamespace(audio_values=[wave])))
  with tempfile.TemporaryDirectory() as temp:
   path,temporary=render(fake,'**Max:** ≈ 4,5 °C. **Nebelchance:** 0 %. Satz drei.','German','female',{},lambda *a,**k:None,Path(temp))
   self.assertFalse(temporary);self.assertTrue(Path(path).is_file());self.assertEqual(len(seen),3)
   self.assertEqual(seen[0][0][-1]['content'],'maximal: etwa vier Komma fünf Grad Celsius.')
   self.assertEqual(seen[1][0][-1]['content'],'Nebelwahrscheinlichkeit: null Prozent.')
   for conversation,mode,r in seen:self.assertEqual(len(conversation),2);self.assertEqual(mode,'audio');self.assertLessEqual(r['max_tokens'],512)
   manifests=list(Path(temp).rglob('manifest.json'));self.assertEqual(len(manifests),1)
   manifest=json.loads(manifests[0].read_text());self.assertIn('**Max:**',manifest['source_text']);self.assertNotIn('°C',manifest['prepared_text']);self.assertEqual(manifest['fragments'][0]['text'],seen[0][0][-1]['content']);self.assertEqual(manifest['app_version'],'1.5.1');self.assertEqual(len(list(manifests[0].parent.glob('*.wav'))),3)
 def test_save_disabled_keeps_only_final_temporary_wave(self):
  wave=MagicMock();wave.squeeze.return_value.float.return_value.cpu.return_value.numpy.return_value=np.sin(np.arange(240)*.1).astype(np.float32)*.1
  out=types.SimpleNamespace(audio_codes=MagicMock(),audio_lengths=[2])
  fake=types.SimpleNamespace(generate=lambda *a:('',out),torch=types.SimpleNamespace(inference_mode=contextlib.nullcontext),codec=types.SimpleNamespace(decode=lambda _:types.SimpleNamespace(audio_values=[wave])))
  with tempfile.TemporaryDirectory() as temp:
   path,temporary=render(fake,'Hallo.','German','male',{'save_audio':False},lambda *a,**k:None,Path(temp))
   self.assertTrue(temporary);self.assertIn('/temp/',path.replace('\\','/'));self.assertEqual(len(list(Path(temp).rglob('*.wav'))),1);self.assertFalse(list(Path(temp).rglob('manifest.json')))

class ContextTests(unittest.TestCase):
 def test_stale_refusal_removed_only_for_currently_available_tool(self):
  old='Leider kann ich das Wetter nicht abrufen, da ich kein Wetterdiensttool zur Verfügung habe.'
  self.assertEqual(strip_refusals(old,{'current_weather'}),'');self.assertEqual(strip_refusals(old,set()),old)
  self.assertEqual(strip_refusals('Es gibt keinen Niederschlag.\n\nMorgen 6 Grad.',{'current_weather'}),'Es gibt keinen Niederschlag.\n\nMorgen 6 Grad.')
  history=[{'role':'assistant','content':old}];self.assertEqual(model_history(history,{'current_weather'}),[]);self.assertEqual(history[0]['content'],old)
 def test_multiple_sequential_tool_calls(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  replies=['<tool_call><function=current_time></function></tool_call>','<tool_call><function=calculate><parameter=expression>6*7</parameter></function></tool_call>','42']
  def generate(conversation,*args):seen.append(json.loads(json.dumps(conversation)));return replies[len(seen)-1],None
  instance.generate=generate;output=io.StringIO()
  with tempfile.TemporaryDirectory() as temp,patch.object(engine,'ROOT',Path(temp)),patch.object(engine,'PROTOCOL',output):instance.respond({'input':'Zeit und 6 mal 7','output':'txt'})
  events=[json.loads(line) for line in output.getvalue().splitlines()];self.assertEqual([e['name'] for e in events if e['type']=='tool'],['current_time','calculate']);self.assertEqual(events[-1]['text'],'42')
  self.assertTrue(any(m['role']=='tool' and '42' in m['content'] for m in seen[-1]))
 def test_explicit_history_keeps_chats_isolated(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  def generate(conversation,*args):seen.append(json.dumps(conversation));return 'Antwort',None
  instance.generate=generate
  with patch.object(engine,'PROTOCOL',io.StringIO()):
   instance.respond({'input':'ChatAlice','history':[],'output':'txt','tools':False});alice=instance.history
   instance.respond({'input':'ChatBob','history':[],'output':'txt','tools':False})
   self.assertNotIn('ChatAlice',seen[-1])
   instance.respond({'input':'WeiterAlice','history':alice,'output':'txt','tools':False});self.assertNotIn('ChatBob',seen[-1]);self.assertIn('ChatAlice',seen[-1])
 def test_successful_weather_drops_contradictory_inability_claim(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];calls=[]
  old='Leider kann ich das Wetter nicht abrufen, da ich kein Wetterdiensttool zur Verfügung habe.'
  service=types.SimpleNamespace(schemas=lambda:[{'function':{'name':'current_weather'}}],wiki_available=False,online=types.SimpleNamespace(wiki=False,weather=True,web=False),sources=[],run=lambda *a:{'current':{'temperature_2m':6}})
  def generate(conversation,*args):calls.append(json.dumps(conversation));return ('<tool_call><function=current_weather><parameter=place>Hamburg</parameter></function></tool_call>' if len(calls)==1 else old+' Es sind 6 Grad.'),None
  instance.generate=generate;output=io.StringIO()
  with patch.object(engine,'ToolServices',return_value=service),patch.object(engine,'PROTOCOL',output):instance.respond({'input':'Versuche es nochmal','output':'txt','history':[{'role':'assistant','content':old}]})
  self.assertNotIn('Wetterdiensttool',calls[0]);self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['text'],'Es sind 6 Grad.')
