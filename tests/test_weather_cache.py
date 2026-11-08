import copy
import datetime as dt
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
import urllib.error
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from online_tools import OnlineTools
from tool_services import ToolServices
from weather_cache import WeatherCache
import engine

NOW=dt.datetime(2026,11,6,12,tzinfo=dt.timezone.utc)
GEO={'results':[{'name':'Norderstedt','country_code':'DE','country':'Deutschland','latitude':53.7,'longitude':9.99}]}
DATA={'current':{'time':'2026-11-06T13:00','temperature_2m':7,'relative_humidity_2m':80},'current_units':{'temperature_2m':'°C','relative_humidity_2m':'%'},'daily':{'time':['2026-11-03','2026-11-04','2026-11-05','2026-11-06','2026-11-07','2026-11-08'],'temperature_2m_min':[2,3,4,5,6,7],'temperature_2m_max':[5,6,7,8,9,10],'precipitation_sum':[2,1,0,0,0,1]},'daily_units':{'temperature_2m_min':'°C','precipitation_sum':'mm'},'timezone':'Europe/Berlin','utc_offset_seconds':3600}

class WeatherTests(unittest.TestCase):
 def populate(self,folder):
  client=OnlineTools(weather=True,root=folder);client.weather_cache.clock=lambda:NOW
  with patch('online_tools.json_url',side_effect=[copy.deepcopy(GEO),copy.deepcopy(DATA)]) as http:result=client.current_weather('Norderstedt','DE')
  return client,result,http
 def test_live_caches_three_previous_days_separate_from_forecast(self):
  with tempfile.TemporaryDirectory() as folder:
   client,result,http=self.populate(folder)
   self.assertTrue(result['online_available']);self.assertEqual([row['time'] for row in result['recent_history']],DATA['daily']['time'][:3]);self.assertEqual(result['forecast']['time'],DATA['daily']['time'][3:])
   self.assertIn('past_days=3',http.call_args_list[-1].args[0]);self.assertEqual(len(list((Path(folder)/'data/weather').glob('*.json'))),1)
 def test_offline_mode_returns_only_past_data_without_network(self):
  with tempfile.TemporaryDirectory() as folder:
   self.populate(folder);offline=OnlineTools(weather=True,offline=True,root=folder);offline.weather_cache.clock=lambda:NOW+dt.timedelta(days=1)
   with patch('online_tools.json_url',side_effect=AssertionError('No network permitted')) as http:result=offline.current_weather('Norderstedt','DE')
   http.assert_not_called();self.assertFalse(result['online_available']);self.assertEqual(result['status'],'offline_cached');self.assertEqual(result['cache_age_hours'],24)
   self.assertNotIn('current',result);self.assertNotIn('forecast',result);self.assertTrue(result['can_offer_estimate']);self.assertIn('uncertain',result['message']);self.assertIn('cache_retrieved_at',result)
   self.assertTrue(all(row['time']>='2026-11-04' for row in result['recent_history']))
 def test_network_failure_returns_cache_and_explicit_failure(self):
  with tempfile.TemporaryDirectory() as folder:
   client,_,_=self.populate(folder)
   with patch('online_tools.json_url',side_effect=urllib.error.URLError('certificate verification failed')):result=client.current_weather('Norderstedt','DE')
   self.assertEqual(result['status'],'offline_cached');self.assertIn('certificate',result['online_error']);self.assertFalse(result['online_available'])
 def test_offline_without_cache_does_not_invent_values(self):
  with tempfile.TemporaryDirectory() as folder:
   client=OnlineTools(weather=True,offline=True,root=folder)
   with patch('online_tools.json_url',side_effect=AssertionError('No network')):result=client.current_weather('Hamburg')
   self.assertEqual(result['status'],'offline_no_cache');self.assertFalse(result['can_offer_estimate']);self.assertEqual(result['recent_history'],[]);self.assertNotIn('current',result)
 def test_expired_reports_not_returned_or_deleted(self):
  with tempfile.TemporaryDirectory() as folder:
   client,_,_=self.populate(folder);client.offline=True;client.weather_cache.clock=lambda:NOW+dt.timedelta(days=3,seconds=1)
   result=client.current_weather('Norderstedt','DE');self.assertEqual(result['status'],'offline_no_cache');self.assertEqual(len(list((Path(folder)/'data/weather').glob('*.json'))),1)
 def test_region_matching_and_country_ambiguity(self):
  with tempfile.TemporaryDirectory() as folder:
   client,result,_=self.populate(folder);cache=client.weather_cache
   self.assertIsNone(cache.find('Hamburg','DE'));self.assertIsNotNone(cache.find('  NORDERSTEDT  ','DE'))
   for code,lat in [('DE',52.5),('US',44.0)]:
    report=copy.deepcopy(result);report['location'].update(name='Berlin',country_code=code,latitude=lat);cache.save(report,'Berlin',code)
   self.assertIsNone(cache.find('Berlin'));self.assertEqual(cache.find('Berlin','US')[-1]['location']['country_code'],'US')
 def test_rolling_daily_reports_keep_three_dates_and_latest_per_day(self):
  with tempfile.TemporaryDirectory() as folder:
   client,result,_=self.populate(folder);cache=client.weather_cache
   for day in range(5):
    when=NOW+dt.timedelta(days=day);cache.clock=lambda when=when:when
    report=copy.deepcopy(result);report['retrieved_at']=when.isoformat();cache.save(report,'Norderstedt','DE')
   reports=cache.find('Norderstedt','DE');self.assertEqual(len(reports),3)
   when=NOW+dt.timedelta(days=4,hours=1);cache.clock=lambda:when;report['retrieved_at']=when.isoformat();report['current']['temperature_2m']=99;cache.save(report,'Norderstedt','DE')
   reports=cache.find('Norderstedt','DE');self.assertEqual(len(reports),3);self.assertEqual(reports[-1]['current']['temperature_2m'],99)
 def test_disabling_weather_blocks_network_and_cache(self):
  with tempfile.TemporaryDirectory() as folder:
   client=OnlineTools(weather=False,root=folder)
   with patch('online_tools.json_url',side_effect=AssertionError('Network used')):
    with self.assertRaises(PermissionError):client.current_weather('Hamburg')
 def test_global_offline_blocks_other_online_tools_but_keeps_weather_cache_tool(self):
  with tempfile.TemporaryDirectory() as folder:
   service=ToolServices(folder,{'offline':True,'web_enabled':True,'wiki_online_enabled':True})
   self.assertFalse(service.online.web);self.assertFalse(service.online.wiki);self.assertTrue(service.online.weather)
   with patch('online_tools.json_url',side_effect=AssertionError('Network used')):result=service.run('current_weather',{'place':'Hamburg'})
   self.assertFalse(result['online_available'])
 def test_cache_write_failure_does_not_discard_live_report(self):
  with tempfile.TemporaryDirectory() as folder:
   client=OnlineTools(weather=True,root=folder)
   with patch('online_tools.json_url',side_effect=[GEO,DATA]),patch.object(client.weather_cache,'save',side_effect=OSError('disk full')):result=client.current_weather('Norderstedt','DE')
   self.assertTrue(result['online_available']);self.assertIn('disk full',result['cache_write_warning'])
 def test_model_receives_offline_status_and_legitimate_failure_is_preserved(self):
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];calls=[];output=io.StringIO()
  service=types.SimpleNamespace(schemas=lambda:[{'function':{'name':'current_weather'}}],wiki_available=False,online=types.SimpleNamespace(wiki=False,weather=True,web=False),sources=[],run=lambda *a:{'online_available':False,'status':'offline_no_cache','message':'No live data and no recent local records'})
  text='Ich kann das Wetter aktuell nicht abrufen, da der Online-Zugriff nicht verfügbar ist.'
  def generate(conversation,*args):calls.append(json.dumps(conversation));return ('<tool_call><function=current_weather><parameter=place>Hamburg</parameter></function></tool_call>' if len(calls)==1 else text),None
  instance.generate=generate
  with patch.object(engine,'ToolServices',return_value=service),patch.object(engine,'PROTOCOL',output):instance.respond({'input':'Wetter Hamburg','output':'txt'})
  self.assertIn('online_available',calls[-1]);self.assertIn('false',calls[-1]);self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['text'],text)

 def test_corrupt_cached_reports_are_skipped_safely(self):
  with tempfile.TemporaryDirectory() as folder:
   client,_,_=self.populate(folder);path=next((Path(folder)/'data/weather').glob('*.json'))
   record=json.loads(path.read_text());record['reports']+=[None,{'retrieved_at':123},{'retrieved_at':NOW.isoformat(),'location':None}];path.write_text(json.dumps(record))
   client.offline=True;result=client.current_weather('Norderstedt','DE');self.assertEqual(result['status'],'offline_cached');self.assertEqual(len(result['historical_reports']),1)
