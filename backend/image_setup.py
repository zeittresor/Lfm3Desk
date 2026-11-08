"""Opt-in DirectML runtime; reuse shared wheels, no changes to the main venv."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import venv
from app_version import VERSION
from prepare_wheels import missing_requirement,native_run

ROOT=Path(__file__).resolve().parents[1]

def collect(root,offline=False,run=native_run):
    root=Path(root);wheels=root/'wheelhouse';wheels.mkdir(exist_ok=True)
    req=root/'backend'/'requirements-image.txt'
    args=['download','--no-index','--find-links',str(wheels),'--dest',str(wheels),'-r',str(req)]
    fetched=set()
    for _ in range(40):
        code,output=run(args)
        if not code:return
        if offline:raise RuntimeError('Offline image GPU wheel set incomplete. '+output[-2500:])
        missing=missing_requirement(output)
        if not missing or missing in fetched:raise RuntimeError('Image GPU wheel resolution failed. '+output[-2500:])
        fetched.add(missing)
        print('[MISSING] Image GPU dependency: '+missing,flush=True)
        code,output=run(['download','--no-deps','--index-url','https://pypi.org/simple','--dest',str(wheels),missing])
        if code:raise RuntimeError('Image GPU dependency download failed. '+output[-2500:])
    raise RuntimeError('Image GPU dependency limit reached')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--offline',action='store_true');args=parser.parse_args()
    if os.name!='nt':raise RuntimeError('DirectML image setup requires Windows.')
    if sys.prefix==sys.base_prefix or Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise RuntimeError('Run with this app\'s main .venv interpreter.')
    print(f'LFM3 Desk {VERSION} | optional image GPU setup',flush=True)
    collect(ROOT,args.offline)
    target=ROOT/'.venv-image';python=target/'Scripts'/'python.exe'
    if not python.exists():
        print('[STEP] Creating private .venv-image (no PyTorch or model copies)',flush=True)
        venv.EnvBuilder(with_pip=True).create(target)
    env=dict(os.environ,PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_NO_CACHE_DIR='1',PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
    subprocess.run([str(python),'-m','pip','--no-cache-dir','install','--no-index','--find-links',str(ROOT/'wheelhouse'),'-r',str(ROOT/'backend'/'requirements-image.txt')],env=env,check=True)
    check=subprocess.run([str(python),'-c',"import onnxruntime as o,json; print(json.dumps({'version':o.__version__,'providers':o.get_available_providers()})); assert 'DmlExecutionProvider' in o.get_available_providers()"],env=env,capture_output=True,text=True,check=True)
    record={'app_version':VERSION,'runtime':check.stdout.strip(),'note':'Provider import check only; actual device/model execution is checked at generation.'}
    folder=ROOT/'output'/'logs';folder.mkdir(parents=True,exist_ok=True)
    (folder/'image-gpu-runtime.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    print('[OK] Optional image GPU runtime ready. '+check.stdout.strip(),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as error:print('[ERR] '+str(error),file=sys.stderr);sys.exit(1)
