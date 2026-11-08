import asyncio
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from knowledge import Wikipedia,plain_html
from online_tools import OnlineTools,public_https
from tool_services import ToolServices
import wiki_setup

class PermissionTests(unittest.TestCase):
 def test_default_no_network(self):
  with patch('knowledge.Wikipedia',side_effect=FileNotFoundError('No fixture ZIM')):service=ToolServices('.',{'weather_enabled':False})
  names=[item['function']['name'] for item in service.schemas()]
  self.assertNotIn('wikipedia_lookup',names);self.assertNotIn('web_search',names);self.assertNotIn('current_weather',names)
  with patch('online_tools.download',side_effect=AssertionError('Network used')):
   for name,args in [('web_search',{'query':'test'}),('web_read',{'url':'https://example.com'}),('current_weather',{'place':'Hamburg'}),('wikipedia_online_lookup',{'query':'Test'}),('wikipedia_online_read',{'title':'Test'})]:
    with self.assertRaises(PermissionError):service.run(name,args)
 def test_independent_permissions(self):
  self.assertNotIn('current_weather',[t['function']['name'] for t in ToolServices('.',{'web_enabled':True,'weather_enabled':False}).schemas()])
  self.assertNotIn('web_search',[t['function']['name'] for t in ToolServices('.',{'weather_enabled':True}).schemas()])
  with self.assertRaises(PermissionError):ToolServices('.',{'wiki_enabled':False}).run('wikipedia_lookup',{'query':'x'})
 def test_public_read_boundaries(self):
  with self.assertRaises(ValueError):OnlineTools(True).web_read('https://example.com')
  with self.assertRaises(ValueError):public_https('http://example.com')
  with self.assertRaises(ValueError):public_https('https://127.0.0.1')
 def test_html_is_data(self):
  self.assertEqual(plain_html('<style>secret</style><p>Hallo <b>Welt</b></p><script>danger</script>'),'Hallo Welt')
 def test_weather_location_units_attribution(self):
  answers=[{'results':[{'name':'Hamburg','latitude':53.5,'longitude':10,'country':'Deutschland'}]}, {'current':{'temperature_2m':12},'current_units':{'temperature_2m':'°C'},'daily':{'time':['2026-11-05']},'timezone':'Europe/Berlin'}]
  with tempfile.TemporaryDirectory() as folder,patch('online_tools.json_url',side_effect=answers) as http:
   result=OnlineTools(weather=True,root=folder).current_weather('Hamburg','DE')
  self.assertEqual(result['units']['temperature_2m'],'°C');self.assertIn('Open-Meteo',result['attribution']);self.assertEqual(http.call_count,2)
 def test_private_notes_explained(self):
  with tempfile.TemporaryDirectory() as folder:
   result=ToolServices(folder,{}).run('list_notes',{})
   self.assertIn('not general knowledge',result['scope'])

class WikipediaFallbackTests(unittest.TestCase):
 def test_retry_recovers_on_second_attempt(self):
  with tempfile.TemporaryDirectory() as temp,patch('wiki_setup.ROOT',Path(temp)),patch('wiki_setup.prepare',side_effect=[OSError('temporary failure'),None]) as prepare:
   self.assertTrue(wiki_setup.prepare_optional());self.assertEqual(prepare.call_count,2)
   state=json.loads((Path(temp)/'data/wikipedia/status.json').read_text());self.assertTrue(state['ready']);self.assertEqual(state['attempts'],2)
 def test_two_failures_do_not_raise_or_enable_online(self):
  with tempfile.TemporaryDirectory() as temp,patch('wiki_setup.ROOT',Path(temp)),patch('wiki_setup.prepare',side_effect=OSError('certificate rejected')) as prepare:
   self.assertFalse(wiki_setup.prepare_optional());self.assertEqual(prepare.call_count,2)
   self.assertFalse(json.loads((Path(temp)/'data/wikipedia/status.json').read_text())['ready'])
  with patch('knowledge.Wikipedia',side_effect=FileNotFoundError('missing')):service=ToolServices('.',{})
  names=[s['function']['name'] for s in service.schemas()];self.assertNotIn('wikipedia_lookup',names);self.assertNotIn('wikipedia_online_lookup',names)
 def test_online_wikipedia_independent_from_web_and_offline(self):
  service=ToolServices('.',{'wiki_enabled':False,'wiki_online_enabled':True})
  names=[s['function']['name'] for s in service.schemas()];self.assertIn('wikipedia_online_lookup',names);self.assertNotIn('web_search',names);self.assertNotIn('wikipedia_lookup',names)
  response={'query':{'pages':[{'title':'Eiffelturm','fullurl':'https://de.wikipedia.org/wiki/Eiffelturm','extract':'Aus Eisenteilen vernietet.'}]}}
  with patch('online_tools.json_url',return_value=response) as request:
   result=service.run('wikipedia_online_lookup',{'query':'Eiffelturm'})
   self.assertIn('de.wikipedia.org/w/api.php?',request.call_args.args[0]);self.assertIn('gsrsearch=Eiffelturm',request.call_args.args[0])
  self.assertIn('vernietet',result['results'][0]['text']);self.assertEqual(len(service.sources),1)
 def test_online_wikipedia_reads_only_fixed_hosts(self):
  online=OnlineTools(wiki=True)
  with patch('online_tools.json_url',return_value={}) as request:
   online.wikipedia_online_read('Eiffelturm','en');self.assertTrue(request.call_args.args[0].startswith('https://en.wikipedia.org/w/api.php?'))
  with self.assertRaises(ValueError):online.wikipedia_online_lookup('test','evil.example')
  with self.assertRaises(PermissionError):OnlineTools(web=True).wikipedia_online_lookup('test')

@unittest.skipUnless(importlib.util.find_spec('libzim'),'libzim required for real ZIM integration')
class ZimTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from libzim.writer import Creator,Item,StringProvider,Hint
  cls.temp=tempfile.TemporaryDirectory();cls.path=Path(cls.temp.name)/'wikipedia_de_all_mini_2026-10.zim'
  class Article(Item):
   def get_path(self):return 'Eiffelturm'
   def get_title(self):return 'Eiffelturm'
   def get_mimetype(self):return 'text/html'
   def get_contentprovider(self):return StringProvider('<html><head><title>Eiffelturm</title></head><body><h1>Eiffelturm</h1><p>Der Eiffelturm wurde 1887 bis 1889 aus vorgefertigten Eisenteilen gebaut. Die Teile wurden vernietet.</p></body></html>')
   def get_hints(self):return {Hint.FRONT_ARTICLE:True}
  with Creator(cls.path).config_indexing(True,'deu') as creator:
   creator.add_metadata('Language','deu');creator.add_metadata('Title','Test Wikipedia');creator.add_item(Article());creator.set_mainpath('Eiffelturm')
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_real_search_and_article(self):
  wiki=Wikipedia(str(self.path));result=wiki.lookup('Eiffelturm')
  self.assertIn('vernietet',result['results'][0]['text']);self.assertEqual(wiki.search('Eisenteilen')[0]['title'],'Eiffelturm')
  self.assertEqual(wiki.search('no_such_subject_abcdef'),[])
 def test_reuse_no_network(self):
  with patch('wiki_setup.ROOT',Path(self.temp.name)),patch('urllib.request.urlopen',side_effect=AssertionError('Must reuse')):
   wiki_setup.prepare(path=str(self.path),offline=True)
 def test_sources_and_excerpt_bound(self):
  service=ToolServices('.',{'wiki_path':str(self.path)})
  service.run('wikipedia_lookup',{'query':'Eiffelturm'});service.run('wikipedia_lookup',{'query':'Eiffelturm'})
  self.assertEqual(len(service.sources),1);self.assertEqual(service.sources[0]['url'],'https://de.wikipedia.org/wiki/Eiffelturm')
  self.assertLessEqual(len(service.wikipedia.read('Eiffelturm',limit=200)['text']),200)
 def test_prelookup_evidence_reaches_model_answer(self):
  import engine,io
  instance=engine.Engine.__new__(engine.Engine);instance.history=[];seen=[]
  def generate(conversation,mode,request,tools=None):
   seen.append(json.loads(json.dumps(conversation)))
   return ('Eiffelturm',None) if len(seen)==1 else ('Er wurde aus Eisenteilen gebaut und vernietet.',None)
  instance.generate=generate;protocol=io.StringIO()
  with patch.object(engine,'PROTOCOL',protocol):instance.respond({'input':'Wie wurde der Eifelturm gebaut?','output':'txt','wiki_auto':True,'wiki_path':str(self.path)})
  self.assertIn('vernietet',seen[1][-1]['content'][-1]['text'])
  result=json.loads(protocol.getvalue().splitlines()[-1]);self.assertEqual(result['sources'][0]['title'],'Eiffelturm')
 def test_mini_default_resumes_and_validates_download(self):
  import io
  data=self.path.read_bytes();filename='wikipedia_de_all_mini_2026-10.zim'
  class Response(io.BytesIO):
   def __init__(self,body=b'',status=200,headers=None):super().__init__(body);self.status=status;self.headers=headers or {}
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)/'data'/'wikipedia';folder.mkdir(parents=True)
   split=len(data)//2;(folder/(filename+'.part')).write_bytes(data[:split])
   def network(request,**kwargs):
    if isinstance(request,str):return Response(filename.encode())
    if request.get_method()=='HEAD':return Response(headers={'Content-Length':str(len(data))})
    self.assertEqual(request.get_header('Range'),f'bytes={split}-')
    return Response(data[split:],206,{'Content-Range':f'bytes {split}-{len(data)-1}/{len(data)}'})
   with patch('wiki_setup.ROOT',Path(temp)),patch('urllib.request.urlopen',side_effect=network):wiki_setup.prepare()
   self.assertEqual((folder/filename).read_bytes(),data);self.assertFalse((folder/(filename+'.part')).exists())
   with patch('wiki_setup.ROOT',Path(temp)),patch('knowledge.ROOT',Path(temp)),patch('urllib.request.urlopen',side_effect=AssertionError('Repeated download')):wiki_setup.prepare()
 def test_full_edition_can_be_downloaded_alongside_mini(self):
  import io
  data=self.path.read_bytes();filename='wikipedia_de_all_nopic_2026-10.zim'
  class Response(io.BytesIO):
   status=200
   headers={'Content-Length':str(len(data))}
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp)/'data'/'wikipedia';folder.mkdir(parents=True)
   mini=folder/self.path.name;mini.write_bytes(data)
   def network(request,**kwargs):
    if isinstance(request,str):return Response(filename.encode())
    if request.get_method()=='HEAD':return Response()
    return Response(data)
   with patch('wiki_setup.ROOT',Path(temp)),patch('knowledge.ROOT',Path(temp)),patch('urllib.request.urlopen',side_effect=network):wiki_setup.prepare('nopic',select_flavour=True)
   self.assertTrue(mini.exists());self.assertTrue((folder/filename).exists())
 @unittest.skipUnless(importlib.util.find_spec('mcp'),'MCP SDK required')
 def test_real_mcp_stdio_and_revocation(self):
  from mcp import ClientSession,StdioServerParameters
  from mcp.client.stdio import stdio_client
  settings=Path(self.temp.name)/'settings.json';settings.write_text(json.dumps({'McpEnabled':True,'WikiPath':str(self.path)}))
  driver=Path(self.temp.name)/'driver.py';driver.write_text('import sys\nsys.path.insert(0,'+repr(str(Path(__file__).resolve().parents[1]/'backend'))+')\nfrom mcp_server import create_server\ncreate_server('+repr(str(settings))+').run(transport="stdio")\n')
  async def exercise():
   async with stdio_client(StdioServerParameters(command=sys.executable,args=[str(driver)])) as streams:
    async with ClientSession(*streams) as session:
     await session.initialize();listing=await session.list_tools();self.assertIn('chat_with_model',[t.name for t in listing.tools])
     result=await session.call_tool('wikipedia_lookup',{'query':'Eiffelturm'});self.assertFalse(result.isError);self.assertIn('vernietet',result.content[0].text)
     result=await session.call_tool('web_search',{'query':'test'});self.assertTrue(result.isError);self.assertIn('disabled',result.content[0].text)
     settings.write_text(json.dumps({'McpEnabled':False}))
     result=await session.call_tool('wikipedia_lookup',{'query':'Eiffelturm'});self.assertTrue(result.isError);self.assertIn('disabled',result.content[0].text)
  asyncio.run(exercise())
