import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import image_runtime
import image_setup
import tiny_sd

class ProviderTests(unittest.TestCase):
 def ort(self,available=True,silent_cpu=False):
  calls=[]
  def session(path,sess_options,providers):
   calls.append((path,sess_options,providers))
   return types.SimpleNamespace(get_providers=lambda:['CPUExecutionProvider'] if silent_cpu else ['DmlExecutionProvider','CPUExecutionProvider'])
  return types.SimpleNamespace(disable_telemetry_events=lambda:None,get_available_providers=lambda:['DmlExecutionProvider'] if available else ['CPUExecutionProvider'],SessionOptions=types.SimpleNamespace,ExecutionMode=types.SimpleNamespace(ORT_SEQUENTIAL='sequential'),InferenceSession=session),calls
 def test_cpu_default_provider(self):
  ort,calls=self.ort()
  with patch.dict(sys.modules,{'onnxruntime':ort}),patch.object(tiny_sd,'Tokenizer'):
   tiny_sd.TinySD(lambda *a,**k:None)
  self.assertEqual(len(calls),3);self.assertTrue(all(c[2]==['CPUExecutionProvider'] for c in calls))
 def test_directml_configuration(self):
  ort,calls=self.ort()
  with patch.dict(sys.modules,{'onnxruntime':ort}),patch.object(tiny_sd,'Tokenizer'):
   tiny_sd.TinySD(lambda *a,**k:None,'directml',1)
  for _,options,providers in calls:
   self.assertFalse(options.enable_mem_pattern);self.assertEqual(options.execution_mode,'sequential');self.assertEqual(providers[0],('DmlExecutionProvider',{'device_id':'1'}));self.assertEqual(providers[1],'CPUExecutionProvider')
 def test_no_gpu_provider_is_explicit_error(self):
  ort,_=self.ort(False)
  with patch.dict(sys.modules,{'onnxruntime':ort}):
   with self.assertRaisesRegex(RuntimeError,'unavailable'):tiny_sd.TinySD(lambda *a,**k:None,'directml')
 def test_automatic_ort_cpu_downgrade_is_detected(self):
  ort,_=self.ort(silent_cpu=True)
  with patch.dict(sys.modules,{'onnxruntime':ort}),patch.object(tiny_sd,'Tokenizer'):
   with self.assertRaisesRegex(RuntimeError,'fell back'):tiny_sd.TinySD(lambda *a,**k:None,'directml')
 def test_invalid_index(self):
  ort,_=self.ort()
  with patch.dict(sys.modules,{'onnxruntime':ort}):
   with self.assertRaises(ValueError):tiny_sd.TinySD(lambda *a,**k:None,'directml',-1)

class RuntimeTests(unittest.TestCase):
 def test_cpu_does_not_start_gpu_process(self):
  cpu=MagicMock();cpu.generate.return_value={'backend':'ONNX CPU'}
  with patch.object(image_runtime,'generate_gpu',side_effect=AssertionError('GPU process')):
   self.assertEqual(image_runtime.generate(types.SimpleNamespace(image_engine=cpu),{'prompt':'test'},{},lambda *a,**k:None)['backend'],'ONNX CPU')
 def test_gpu_success_does_not_construct_cpu(self):
  emit=MagicMock();result={'image':'test.png','backend':'directml'}
  with patch.object(image_runtime,'generate_gpu',return_value=result) as gpu,patch.object(tiny_sd,'TinySD',side_effect=AssertionError('CPU')):
   self.assertEqual(image_runtime.generate(types.SimpleNamespace(image_engine=None),{'prompt':'test'},{'image_backend':'directml','image_gpu':2},emit),result)
   gpu.assert_called_once_with({'prompt':'test'},2,emit)
 def test_gpu_failure_cpu_fallback_and_saved_diagnostics(self):
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/'test.png';cpu=MagicMock();cpu.generate.return_value={'image':str(path),'backend':'ONNX CPU'};emit=MagicMock()
   with patch.object(image_runtime,'generate_gpu',side_effect=RuntimeError('no device')),contextlib.redirect_stderr(io.StringIO()):
    result=image_runtime.generate(types.SimpleNamespace(image_engine=cpu),{'prompt':'test'},{'image_backend':'directml'},emit)
   self.assertEqual(result['backend'],'ONNX CPU');self.assertIn('no device',result['fallback_reason']);self.assertEqual(json.loads(path.with_suffix('.json').read_text())['requested_backend'],'directml');self.assertTrue(emit.called)
 def test_missing_gpu_environment(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(FileNotFoundError,'Settings'):image_runtime.generate_gpu({},0,MagicMock(),d)
 def test_gpu_subprocess_protocol_progress_result_and_isolation(self):
  process=MagicMock();process.__enter__.return_value=process;process.stdout=iter([json.dumps({'type':'image_progress','step':1,'steps':2})+'\n',json.dumps({'type':'result','result':{'image':'x.png'}})+'\n']);process.wait.return_value=0;process.poll.return_value=0
  with tempfile.TemporaryDirectory() as d,patch.object(Path,'is_file',return_value=True),patch('subprocess.Popen',return_value=process) as start,patch.dict('os.environ',{'PYTHONPATH':'global packages'}):
   emit=MagicMock();self.assertEqual(image_runtime.generate_gpu({'prompt':'test'},1,emit,d),{'image':'x.png'});emit.assert_called_once_with('image_progress',step=1,steps=2)
   self.assertNotIn('PYTHONPATH',start.call_args.kwargs['env']);self.assertIn('.venv-image',start.call_args.args[0][0]);self.assertIn('test',process.stdin.write.call_args.args[0])
 def test_gpu_process_error_cannot_return_success(self):
  process=MagicMock();process.__enter__.return_value=process;process.stdout=iter(['{"type":"error","message":"DML failed"}\n']);process.wait.return_value=1;process.poll.return_value=1
  with tempfile.TemporaryDirectory() as d,patch.object(Path,'is_file',return_value=True),patch('subprocess.Popen',return_value=process):
   with self.assertRaisesRegex(RuntimeError,'DML failed'):image_runtime.generate_gpu({},0,MagicMock(),d)

class SetupTests(unittest.TestCase):
 def test_wheels_reused_without_download(self):
  with tempfile.TemporaryDirectory() as d:
   calls=[]
   def run(args):calls.append(args);return 0,''
   image_setup.collect(d,run=run)
   self.assertEqual(len(calls),1);self.assertIn('--no-index',calls[0])
 def test_only_missing_wheel_downloaded(self):
  with tempfile.TemporaryDirectory() as d:
   calls=[]
   def run(args):
    calls.append(args)
    return (1,'No matching distribution found for onnxruntime-directml==1.23.0') if len(calls)==1 else (0,'')
   image_setup.collect(d,run=run)
   self.assertEqual(len(calls),3);self.assertIn('--no-deps',calls[1]);self.assertIn('onnxruntime-directml==1.23.0',calls[1]);self.assertIn('--no-index',calls[2])
 def test_offline_missing_is_clear_and_no_download(self):
  with tempfile.TemporaryDirectory() as d:
   run=MagicMock(return_value=(1,'No matching distribution found for onnxruntime-directml==1.23.0'))
   with self.assertRaisesRegex(RuntimeError,'Offline'):image_setup.collect(d,True,run)
   self.assertEqual(run.call_count,1)

if __name__=='__main__':unittest.main()
