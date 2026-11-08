"""One-shot GPU image process in this application's optional private venv."""
import json
from pathlib import Path
import sys
import traceback
from app_version import VERSION
ROOT=Path(__file__).resolve().parents[1]

def emit(kind,**data):print(json.dumps({'type':kind,**data},ensure_ascii=False),flush=True)

def main():
    if sys.prefix==sys.base_prefix or Path(sys.prefix).resolve()!=(ROOT/'.venv-image').resolve():
        raise RuntimeError('Use this app\'s .venv-image interpreter.')
    print(f'LFM3 Desk {VERSION} | image GPU worker',file=sys.stderr,flush=True)
    request=json.loads(sys.stdin.readline())
    from tiny_sd import TinySD
    engine=TinySD(emit,backend='directml',device_id=int(request.get('device_id',0)))
    emit('result',result=engine.generate(**request['arguments']))

if __name__=='__main__':
    try:main()
    except Exception as error:
        traceback.print_exc(file=sys.stderr);emit('error',message=str(error));sys.exit(1)
