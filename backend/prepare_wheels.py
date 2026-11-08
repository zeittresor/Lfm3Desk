"""Resolve from local wheels first; fetch individual missing requirements only."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
from pip._vendor.packaging.requirements import Requirement,InvalidRequirement

MISSING=re.compile(r'(?:Could not find a version that satisfies the requirement|No matching distribution found for)\s+(.+)',re.I)

def missing_requirement(output):
    for line in output.splitlines():
        match=MISSING.search(line)
        if match:
            value=match.group(1).strip()
            value=re.split(r'\s+\(from(?:\s|\s*versions:)',value,maxsplit=1)[0].strip()
            # Pip already selected this dependency for the current interpreter.
            # Parse the full PEP 508 expression, then fetch its package/specifier.
            # Do not forward a parent-extra marker outside its original context.
            try:requirement=Requirement(value)
            except InvalidRequirement:continue
            if requirement.url:continue
            extras='['+','.join(sorted(requirement.extras))+']' if requirement.extras else ''
            return requirement.name+extras+str(requirement.specifier)
    return None

def native_run(arguments):
    environment=dict(os.environ,PIP_DISABLE_PIP_VERSION_CHECK='1',PIP_NO_CACHE_DIR='1',PYTHONIOENCODING='utf-8')
    lines=[]
    with subprocess.Popen([sys.executable,'-m','pip','--disable-pip-version-check','--no-cache-dir',*arguments],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',env=environment) as process:
        for line in process.stdout:
            print(line,end='',flush=True);lines.append(line)
        code=process.wait()
    return code,''.join(lines)

def collect(root,torch_spec,vision_spec,torch_index,offline=False,run=native_run):
    root=Path(root);wheelhouse=root/'wheelhouse';wheelhouse.mkdir(exist_ok=True)
    requirements=root/'backend'/'requirements.txt'
    base=['download','--no-index','--find-links',str(wheelhouse),'--dest',str(wheelhouse),'-r',str(requirements),torch_spec,vision_spec]
    had_wheels=any(wheelhouse.glob('*.whl'))
    if not had_wheels and not offline:
        print('[STEP] Initial package collection (no previous wheels found).',flush=True)
        for arguments in [
            ['download','--dest',str(wheelhouse),'--index-url',torch_index,torch_spec,vision_spec],
            ['download','--find-links',str(wheelhouse),'--dest',str(wheelhouse),'-r',str(requirements),torch_spec,vision_spec],
        ]:
            code,output=run(arguments)
            if code:raise RuntimeError('Initial wheel collection failed. '+output[-2500:])
        return
    code,output=run(base)
    if code==0:
        print('[OK] All required packages resolved from local wheels; no network needed.',flush=True);return
    if offline:raise RuntimeError('Offline wheel set incomplete. '+output[-2500:])
    fetched=set()
    for _ in range(100):
        requirement=missing_requirement(output)
        if not requirement or requirement in fetched:
            raise RuntimeError('Local packages conflict or resolution failed. No broad package update was performed. '+output[-3500:])
        fetched.add(requirement)
        name=re.split(r'[\[<>=!~]',requirement,1)[0].lower().replace('_','-')
        index=torch_index if name in ('torch','torchvision') else 'https://pypi.org/simple'
        print('[MISSING] Downloading only: '+requirement,flush=True)
        code,download_output=run(['download','--no-deps','--index-url',index,'--dest',str(wheelhouse),requirement])
        if code:raise RuntimeError('Missing package download failed. '+download_output[-2500:])
        code,output=run(base)
        if code==0:
            print('[OK] Reused existing wheels; fetched '+str(len(fetched))+' missing requirement(s).',flush=True);return
    raise RuntimeError('Package resolution limit reached')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--torch',required=True);parser.add_argument('--vision',required=True);parser.add_argument('--index',required=True);parser.add_argument('--offline',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if sys.prefix==sys.base_prefix or Path(sys.prefix).resolve()!=(root/'.venv').resolve():raise RuntimeError('Use this app\'s own .venv interpreter.')
    collect(root,args.torch,args.vision,args.index,args.offline)

if __name__=='__main__':
    try:main()
    except Exception as error:print('[ERR] '+str(error),file=sys.stderr);sys.exit(1)
