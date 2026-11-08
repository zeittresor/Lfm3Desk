import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from prepare_wheels import collect,missing_requirement,native_run

class WheelReuseTests(unittest.TestCase):
    def fixture(self,folder):
        root=Path(folder);(root/'backend').mkdir();(root/'wheelhouse').mkdir()
        (root/'backend'/'requirements.txt').write_text('lfmfixture-root==1.0.0\n')
        return root
    def wheel(self,folder,name,dependency=None):
        stem=name.replace('-','_')+'-1.0.0';dist=stem+'.dist-info'
        metadata='Metadata-Version: 2.1\nName: '+name+'\nVersion: 1.0.0\n'
        if dependency:metadata+='Requires-Dist: '+dependency+'\n'
        with zipfile.ZipFile(folder/(stem+'-py3-none-any.whl'),'w') as z:
            z.writestr(dist+'/METADATA',metadata+'\n');z.writestr(dist+'/WHEEL','Wheel-Version: 1.0\nGenerator: fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n');z.writestr(dist+'/RECORD','')
    def test_real_pip_resolves_existing_wheels_without_index(self):
        with tempfile.TemporaryDirectory(prefix='lfm wheels spaces ') as folder:
            root=self.fixture(folder);self.wheel(root/'wheelhouse','lfmfixture-root','lfmfixture-dep==1.0.0');self.wheel(root/'wheelhouse','lfmfixture-dep')
            calls=[]
            def run(arguments):
                calls.append(arguments)
                self.assertIn('--no-index',arguments)
                return native_run(arguments)
            with contextlib.redirect_stdout(io.StringIO()):collect(root,'lfmfixture-root==1.0.0','lfmfixture-dep==1.0.0','https://invalid.test',True,run)
            self.assertEqual(len(calls),1);self.assertEqual(len(list((root/'wheelhouse').glob('*.whl'))),2)
    def test_only_missing_requirement_downloaded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);(root/'wheelhouse'/'existing.whl').write_bytes(b'fixture');calls=[]
            def run(arguments):
                calls.append(arguments)
                return (1,'ERROR: Could not find a version that satisfies the requirement requests>=2.0 (from root) (from versions: none)') if len(calls)==1 else (0,'OK')
            with contextlib.redirect_stdout(io.StringIO()):collect(root,'torch==2.11.0+cu128','torchvision==0.26.0+cu128','https://download.pytorch.org/whl/cu128',False,run)
            online=[a for a in calls if '--no-index' not in a]
            self.assertEqual(len(online),1);self.assertEqual(online[0][-1],'requests>=2.0');self.assertIn('--no-deps',online[0])
    def test_offline_missing_never_downloads(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);calls=[]
            def run(arguments):calls.append(arguments);return 1,'No matching distribution found for torch==2.11.0+cu128'
            with self.assertRaises(RuntimeError):collect(root,'torch==2.11.0+cu128','torchvision==0.26.0+cu128','https://invalid.test',True,run)
            self.assertEqual(len(calls),1);self.assertIn('--no-index',calls[0])
    def test_conflict_does_not_trigger_broad_update(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);(root/'wheelhouse'/'existing.whl').write_bytes(b'fixture');calls=[]
            def run(arguments):calls.append(arguments);return 1,'ERROR: ResolutionImpossible: conflicting package requirements'
            with self.assertRaisesRegex(RuntimeError,'No broad package update'):collect(root,'torch','torchvision','https://invalid.test',False,run)
            self.assertEqual(len(calls),1)
    def test_pip_environment_marker_from_mcp_log(self):
        message='ERROR: Could not find a version that satisfies the requirement pydantic<3.0.0,>=2.11.0; python_version < "3.14" (from mcp) (from versions: none)'
        self.assertEqual(missing_requirement(message),'pydantic<3.0.0,>=2.11.0')
        self.assertEqual(missing_requirement('ERROR: No matching distribution found for pydantic<3.0.0,>=2.11.0; python_version < "3.14"'),'pydantic<3.0.0,>=2.11.0')
        for value in ['https://invalid.test/a.whl','pkg @ https://invalid.test/a.whl','../../pkg','requests; invalid marker','requests && echo unsafe']:
            self.assertIsNone(missing_requirement('ERROR: No matching distribution found for '+value))
    def test_only_marked_missing_dependency_downloaded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=self.fixture(folder);(root/'wheelhouse'/'existing.whl').write_bytes(b'fixture');calls=[]
            def run(arguments):
                calls.append(arguments)
                if len(calls)==1:return 1,'ERROR: No matching distribution found for pydantic<3.0.0,>=2.11.0; python_version < "3.14"'
                return 0,'OK'
            with contextlib.redirect_stdout(io.StringIO()):collect(root,'torch','torchvision','https://invalid.test',False,run)
            self.assertEqual(len(calls),3);self.assertIn('--no-index',calls[0]);self.assertIn('--no-index',calls[2]);self.assertEqual(calls[1][-1],'pydantic<3.0.0,>=2.11.0');self.assertIn('--no-deps',calls[1])
    def test_real_pip_marked_dependency_recovery(self):
        with tempfile.TemporaryDirectory(prefix='lfm marker wheels ') as folder:
            root=self.fixture(folder);self.wheel(root/'wheelhouse','lfmfixture-root','lfmfixture-dep==1.0.0; python_version < "4.0"');online=[]
            def run(arguments):
                if '--no-index' in arguments:return native_run(arguments)
                online.append(arguments);self.assertEqual(arguments[-1],'lfmfixture-dep==1.0.0');self.wheel(root/'wheelhouse','lfmfixture-dep');return 0,'Local fixture supplied instead of network'
            with contextlib.redirect_stdout(io.StringIO()):collect(root,'lfmfixture-root==1.0.0','lfmfixture-root==1.0.0','https://invalid.test',False,run)
            self.assertEqual(len(online),1)
    def test_missing_parser(self):
        self.assertEqual(missing_requirement('ERROR: No matching distribution found for torch==2.11.0+cu128'),'torch==2.11.0+cu128')
        self.assertIsNone(missing_requirement('ERROR: No matching distribution found for https://invalid.test/model.whl'))

if __name__=='__main__':unittest.main()
