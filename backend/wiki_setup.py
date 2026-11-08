"""German Wikipedia download/reuse, with persisted resume metadata."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import time
import urllib.request
from knowledge import ROOT,locate_zim
from secure_http import open_url

BASE='https://download.kiwix.org/zim/wikipedia/'
def status(message):print('[STEP] '+message,flush=True)
def validate(path):
    from libzim.reader import Archive
    archive=Archive(Path(path))
    if archive.article_count<1:raise ValueError('ZIM contains no articles')
    return {'filename':Path(path).name,'bytes':Path(path).stat().st_size,'articles':archive.article_count,'uuid':str(archive.uuid),'fulltext_index':archive.has_fulltext_index}
def prepare(flavour='mini',path='',offline=False,select_flavour=False):
    folder=ROOT/'data'/'wikipedia';folder.mkdir(parents=True,exist_ok=True)
    if path:
        info=validate(locate_zim(path));print('[OK] Existing Wikipedia: '+json.dumps(info),flush=True);return
    try:
        existing=locate_zim() if not select_flavour else next(iter(sorted(folder.glob('wikipedia_de_all_'+flavour+'_*.zim'),reverse=True)),None)
        if existing is None:raise FileNotFoundError('Requested edition missing')
        info=validate(existing);print('[OK] Reusing German Wikipedia: '+json.dumps(info),flush=True);return
    except FileNotFoundError:pass
    if offline:raise FileNotFoundError('No complete local Wikipedia ZIM available for offline setup.')
    marker=folder/'download.json'
    try:metadata=json.loads(marker.read_text(encoding='utf-8'))
    except (OSError,ValueError):metadata={}
    pattern=r'wikipedia_de_all_'+re.escape(flavour)+r'_\d{4}-\d{2}\.zim'
    if not re.fullmatch(pattern,metadata.get('filename','')):
        status('Resolving German Wikipedia '+flavour+' archive (mini: introductions; nopic: full articles without pictures)…')
        with open_url(BASE,timeout=30) as response:catalog=response.read(4*1024*1024).decode('utf-8')
        names=sorted(set(re.findall(pattern,catalog)))
        if not names:raise RuntimeError('No matching German Wikipedia in official Kiwix catalog.')
        name=names[-1];url=BASE+name
        with open_url(urllib.request.Request(url,method='HEAD'),timeout=40) as response:size=int(response.headers.get('Content-Length',0))
        if size<=0:raise RuntimeError('Archive size unavailable; refusing an unbounded download.')
        metadata={'filename':name,'url':url,'bytes':size};marker.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    name=metadata['filename'];url=BASE+name;size=int(metadata['bytes']);target=folder/name;part=folder/(name+'.part')
    start=part.stat().st_size if part.exists() else 0
    if start>size:raise RuntimeError('Partial ZIM is larger than expected; inspect '+str(part))
    if shutil.disk_usage(folder).free<size-start+256*1024*1024:raise RuntimeError('Not enough free disk space for Wikipedia: '+str(size-start)+' bytes still required.')
    status(f'Wikipedia {name}: {size/1e9:.2f} GB total, resuming at {start/1e9:.2f} GB. Cancel preserves the partial download.')
    if start<size:
        request=urllib.request.Request(url,headers={'User-Agent':'Lfm3Desk/1.1','Range':f'bytes={start}-'} if start else {'User-Agent':'Lfm3Desk/1.1'})
        with open_url(request,timeout=90) as response:
            resume=start>0 and response.status==206
            if resume and not response.headers.get('Content-Range','').startswith(f'bytes {start}-'):raise RuntimeError('Invalid resume offset from download server')
            total=start if resume else 0;last=0
            with part.open('ab' if resume else 'wb') as file:
                for chunk in iter(lambda:response.read(2*1024*1024),b''):
                    file.write(chunk);total+=len(chunk)
                    if total>size:raise RuntimeError('Archive exceeded expected size')
                    if time.monotonic()-last>1:
                        print(f'[WIKI] {total*100/size:.1f}% ({total/1e9:.2f} / {size/1e9:.2f} GB)',flush=True);last=time.monotonic()
    if part.stat().st_size!=size:raise RuntimeError('Incomplete Wikipedia download; retry Setup to resume.')
    status('Validating downloaded ZIM structure and embedded checksum (one-time full check)…')
    from libzim.reader import Archive
    archive=Archive(part)
    if not archive.has_checksum or not archive.check():raise RuntimeError('Wikipedia ZIM checksum failed. Partial file retained for inspection.')
    del archive
    os.replace(part,target);info=validate(target);(folder/'ready.json').write_text(json.dumps(info,indent=2),encoding='utf-8');print('[OK] Wikipedia ready: '+json.dumps(info),flush=True)
def prepare_optional(flavour='mini',path='',offline=False,select_flavour=False):
    error=''
    for attempt in (1,2):
        try:
            prepare(flavour,path,offline,select_flavour)
            record={'ready':True,'error':'','attempts':attempt}
            break
        except Exception as failure:
            error=str(failure)
            print(f'[WARN] Wikipedia attempt {attempt}/2: {error}',flush=True)
    else:
        record={'ready':False,'error':error,'attempts':2}
        print('[WARN] Offline Wikipedia could not be prepared after two attempts. Core setup continues. Offline tools are unavailable without a valid ZIM; optional online Wikipedia stays disabled until enabled in Settings.',flush=True)
    folder=ROOT/'data'/'wikipedia';folder.mkdir(parents=True,exist_ok=True)
    (folder/'status.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    return record['ready']

if __name__=='__main__':
    import sys
    parser=argparse.ArgumentParser();parser.add_argument('--flavour',choices=['nopic','mini'],default='mini');parser.add_argument('--path',default='');parser.add_argument('--offline',action='store_true');parser.add_argument('--select-flavour',action='store_true');parser.add_argument('--optional',action='store_true');args=parser.parse_args()
    if sys.prefix==sys.base_prefix or Path(sys.prefix).resolve()!=(ROOT/'.venv').resolve():raise SystemExit('Use this application\'s own .venv interpreter.')
    try:(prepare_optional if args.optional else prepare)(args.flavour,args.path,args.offline,args.select_flavour)
    except Exception as error:print('[ERR] Wikipedia: '+str(error),file=sys.stderr);sys.exit(1)
