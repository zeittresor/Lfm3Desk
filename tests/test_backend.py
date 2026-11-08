import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import tools_local as tools
import engine

class ToolsTests(unittest.TestCase):
    def test_arithmetic(self):
        self.assertAlmostEqual(tools.calculate('sqrt(81) + 2**3'),17)
        for bad in ['__import__("os").system("echo BAD")','2**10000','[1]*100000','1e200','True','(1).__class__']:
            with self.assertRaises((ValueError,SyntaxError)): tools.calculate(bad)
    def test_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(tools.dispatch('save_note',{'name':'Test.txt','text':'Grüße'},directory),{'saved':'Test.txt'})
            self.assertEqual(tools.dispatch('read_note',{'name':'Test.txt'},directory),{'text':'Grüße'})
            with self.assertRaises(FileExistsError): tools.dispatch('save_note',{'name':'Test.txt','text':'overwrite'},directory)
            for bad in ['../outside.txt','C:\\x.txt','sub/a.txt']:
                with self.assertRaises(ValueError): tools.dispatch('read_note',{'name':bad},directory)
    def test_model_tool_format(self):
        calls=tools.parse_calls('<tool_call>\n<function=calculate>\n<parameter=expression>\n2 + 4\n</parameter>\n</function>\n</tool_call>')
        self.assertEqual(calls[0]['function']['arguments'],{'expression':'2 + 4'})

class EngineTests(unittest.TestCase):
    def test_complete_model_does_not_contact_network(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'model.safetensors').write_bytes(b'123')
            (p/'download-manifest.json').write_text(json.dumps({'files':{'model.safetensors':3}}))
            fake=types.ModuleType('huggingface_hub')
            fake.HfApi=lambda: self.fail('Network API used')
            fake.snapshot_download=lambda *a,**k:self.fail('Download used')
            with patch.dict(sys.modules,{'huggingface_hub':fake}),patch.object(engine,'MODEL',p),patch.object(engine,'PROTOCOL',io.StringIO()):engine.download()
    def test_tool_loop_uses_result_and_preserves_history(self):
        e=engine.Engine.__new__(engine.Engine);e.history=[];seen=[]
        def generate(conversation,mode,r,tools=None):
            seen.append(json.loads(json.dumps(conversation)))
            if len(seen)==1:return '<tool_call><function=calculate><parameter=expression>6*7</parameter></function></tool_call>',None
            return '42',None
        e.generate=generate
        output=io.StringIO()
        with patch.object(engine,'PROTOCOL',output),tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)):
            e.respond({'input':'Was ist 6*7?','output':'txt','tools':True})
        self.assertEqual(json.loads(output.getvalue().splitlines()[-1])['text'],'42')
        self.assertEqual(seen[1][-1]['role'],'tool')
        self.assertIn('42',seen[1][-1]['content'])
        self.assertEqual(e.history[-1]['content'],'42')
    def test_tool_round_limit(self):
        e=engine.Engine.__new__(engine.Engine);e.history=[]
        e.generate=lambda *a,**k:('<tool_call><function=current_time></function></tool_call>',None)
        with patch.object(engine,'PROTOCOL',io.StringIO()),tempfile.TemporaryDirectory() as d,patch.object(engine,'ROOT',Path(d)):
            with self.assertRaisesRegex(RuntimeError,'limit'):e.respond({'input':'time','tools':True})
    def test_asr_does_not_use_chat_history_or_tools(self):
        e=engine.Engine.__new__(engine.Engine);e.history=[{'role':'assistant','content':'old'}];seen=[]
        def generate(c,m,r,tools=None):seen.append((c,m,tools));return 'Hallo',None
        e.generate=generate
        with patch.object(engine,'PROTOCOL',io.StringIO()):e.respond({'task':'asr','input':'x','output':'txt','input_language':'DE','tools':True})
        self.assertEqual(seen[0][0][0]['content'],'Perform ASR in German.')
        self.assertEqual(len(seen[0][0]),2);self.assertEqual(seen[0][1],'text');self.assertIsNone(seen[0][2])


class ImageIntegrationTests(unittest.TestCase):
    def test_image_tool_result_reaches_model_and_gui(self):
        e=engine.Engine.__new__(engine.Engine);e.history=[];e.image_engine=types.SimpleNamespace(generate=lambda **kw:{'image':'test.png','seed':12});seen=[]
        def generate(c,*a,**k):
            seen.append(json.loads(json.dumps(c)))
            if len(seen)==1:return '<tool_call><function=generate_image><parameter=prompt>a red boat</parameter></function></tool_call>',None
            return 'Bild erzeugt.',None
        e.generate=generate
        output=io.StringIO()
        with patch.object(engine,'PROTOCOL',output):e.respond({'input':'Zeichne ein Boot','output':'txt'})
        events=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertTrue(any(x['type']=='image' and x['path']=='test.png' for x in events))
        self.assertIn('test.png',seen[-1][-1]['content'])

    def test_tokenizer_utf8_with_windows_ansi_default(self):
        import tiny_sd
        original=Path.read_text
        def windows_read(path,encoding=None,errors=None):return original(path,encoding=encoding or 'cp1252',errors=errors)
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            (folder/'vocab.json').write_text(json.dumps({'a</w>':42,'ā':100},ensure_ascii=False),encoding='utf-8')
            (folder/'merges.txt').write_text('#version: 0.2\nā x\n',encoding='utf-8')
            with self.assertRaises(UnicodeDecodeError):(folder/'vocab.json').read_bytes().decode('cp1252')
            with patch.object(Path,'read_text',windows_read):
                tokenizer=tiny_sd.Tokenizer(folder);ids,_=tokenizer.encode('a')
            self.assertEqual(ids[:3],[49406,42,49407]);self.assertIn(('ā','x'),tokenizer.ranks)

    def test_image_tool_failure_has_diagnostics(self):
        e=engine.Engine.__new__(engine.Engine);e.history=[]
        def fail(**kwargs):raise ValueError('Tiny-SD width/height: 256, 384 or 512')
        e.image_engine=types.SimpleNamespace(generate=fail);calls=[]
        def generate(*args,**kwargs):
            calls.append(1)
            if len(calls)==1:return '<tool_call><function=generate_image><parameter=prompt>a book</parameter><parameter=height>768</parameter></function></tool_call>',None
            return 'Bildgenerierung fehlgeschlagen.',None
        e.generate=generate;protocol=io.StringIO();errors=io.StringIO()
        with patch.object(engine,'PROTOCOL',protocol),contextlib.redirect_stderr(errors):e.respond({'input':'Ein Buchcover','output':'txt'})
        events=[json.loads(line) for line in protocol.getvalue().splitlines()]
        result=next(item for item in events if item['type']=='tool')
        self.assertEqual(result['arguments']['height'],768);self.assertEqual(result['result']['error_type'],'ValueError')
        self.assertIn('768',errors.getvalue());self.assertIn('Traceback',errors.getvalue());self.assertIn('256, 384 or 512',result['result']['error'])

    def test_tiny_model_reuses_verified_files_without_rehash_or_network(self):
        import tiny_sd
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.bin').write_bytes(b'123')
            h=tiny_sd.sha256(p/'test.bin');st=(p/'test.bin').stat()
            (p/'verified.json').write_text(json.dumps({'test.bin':[3,st.st_mtime_ns,h]}))
            with patch.object(tiny_sd,'MODEL',p),patch.object(tiny_sd,'MANIFEST',{'files':[{'path':'test.bin','size':3,'sha256':h,'url':'https://invalid.test'}]}),patch.object(tiny_sd,'sha256',side_effect=AssertionError('unexpected rehash')),patch('urllib.request.urlopen',side_effect=AssertionError('unexpected network')):
                tiny_sd.prepare()

class InterpreterIsolationTests(unittest.TestCase):
    def test_real_private_venv_probe(self):
        import subprocess
        import venv
        probe=Path(__file__).resolve().parents[1]/'backend'/'probe_python.py'
        with tempfile.TemporaryDirectory(prefix='lfm venv spaces ') as folder:
            environment=Path(folder)/'.venv'
            venv.EnvBuilder(with_pip=False).create(environment)
            python=environment/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
            result=json.loads(subprocess.check_output([str(python),str(probe)],text=True))
            self.assertTrue(result['is_venv'])
            self.assertEqual(Path(result['prefix']).resolve(),environment.resolve())
    def test_doctor_refuses_foreign_environment_before_imports(self):
        import subprocess
        import venv
        doctor=Path(__file__).resolve().parents[1]/'backend'/'doctor.py'
        with tempfile.TemporaryDirectory(prefix='lfm foreign env ') as folder:
            environment=Path(folder)/'.venv'
            venv.EnvBuilder(with_pip=False).create(environment)
            python=environment/('Scripts/python.exe' if sys.platform=='win32' else 'bin/python')
            result=subprocess.run([str(python),str(doctor)],text=True,capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('.venv/Scripts/python.exe',result.stderr)

if __name__=='__main__':unittest.main()
