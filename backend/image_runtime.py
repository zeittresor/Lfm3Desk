"""Isolated optional DirectML image process; CPU worker never imports GPU ORT."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def python_path(root=ROOT):
    return Path(root)/'.venv-image'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')

def generate_gpu(arguments,device_id,emit,root=ROOT):
    python=python_path(root)
    if not python.is_file():raise FileNotFoundError('Optional image GPU runtime is missing. Install it in Settings.')
    command=[str(python),'-u',str(Path(root)/'backend'/'image_worker.py')]
    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONNOUSERSITE='1')
    env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None)
    result=None;failure=None
    with subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=None,text=True,encoding='utf-8',env=env,cwd=root) as process:
        try:
            process.stdin.write(json.dumps({'arguments':arguments,'device_id':device_id},ensure_ascii=False)+'\n');process.stdin.close()
            for line in process.stdout:
                try:event=json.loads(line)
                except ValueError:continue
                kind=event.pop('type','')
                if kind=='result':result=event['result']
                elif kind=='error':failure=event.get('message','Image GPU process failed')
                elif kind in ('status','image_phase','image_progress'):emit(kind,**event)
            code=process.wait()
        finally:
            if process.poll() is None:process.kill();process.wait()
    if code or failure or result is None:raise RuntimeError(failure or f'Image GPU worker exited with {code}; no result.')
    return result

def generate(engine,arguments,request,emit):
    backend=request.get('image_backend','cpu')
    if backend not in ('cpu','directml'):raise ValueError('Image backend: cpu | directml')
    fallback=None
    if backend=='directml':
        try:return generate_gpu(arguments,int(request.get('image_gpu',0)),emit)
        except Exception as error:
            fallback=str(error)
            print('Tiny-SD DirectML unavailable; CPU fallback: '+fallback,file=sys.stderr,flush=True)
            emit('status',message='Tiny-SD GPU unavailable; using CPU. '+fallback)
    from tiny_sd import TinySD
    if engine.image_engine is None:engine.image_engine=TinySD(emit)
    result=engine.image_engine.generate(**arguments)
    if fallback:
        result['requested_backend']='directml';result['fallback_reason']=fallback
        Path(result['image']).with_suffix('.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
