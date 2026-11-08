"""Same pinned 434.4 MiB TinySDDesk ONNX/INT8 base model; CPU or optional DirectML image synthesis.
Euler schedule and tokenizer follow TinySDDesk.Core's MIT implementation.
"""
import hashlib
import html
import json
import math
import os
from pathlib import Path
import secrets
import shutil
import time
import unicodedata
import urllib.request
import uuid
from secure_http import open_url

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'models'/'Tiny-SD'
MANIFEST=json.loads((Path(__file__).parent/'tiny-sd-manifest.json').read_text(encoding='utf-8'))

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def prepare(emit=lambda *a,**k:None):
    MODEL.mkdir(parents=True,exist_ok=True)
    verified_file=MODEL/'verified.json'
    try:verified=json.loads(verified_file.read_text(encoding='utf-8'))
    except (OSError,ValueError):verified={}
    candidates=[Path(os.environ['TINYSD_MODELS'])] if os.environ.get('TINYSD_MODELS') else []
    candidates += [ROOT.parent/'TinySDDesk'/'models',ROOT.parent/'TinySDDesk_AllInOne_Data'/'models']
    for item in MANIFEST['files']:
        path=MODEL/item['path'];path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            for folder in candidates:
                source=folder/item['path']
                if source.is_file() and source.stat().st_size==item['size']:
                    emit('status',message='Reusing Tiny-SD: '+item['path'])
                    try:os.link(source,path)
                    except OSError:shutil.copyfile(source,path)
                    break
        if path.is_file():
            st=path.stat();stamp=[st.st_size,st.st_mtime_ns,item['sha256']]
            if st.st_size==item['size'] and (verified.get(item['path'])==stamp or sha256(path)==item['sha256']):
                verified[item['path']]=stamp;continue
        if os.environ.get('HF_HUB_OFFLINE')=='1':raise FileNotFoundError('Tiny-SD incomplete offline: '+str(path))
        emit('status',message='Downloading Tiny-SD: '+item['path'])
        part=path.with_name(path.name+'.part')
        start=part.stat().st_size if part.exists() else 0
        if start>=item['size']:
            if start==item['size'] and sha256(part)==item['sha256']:
                os.replace(part,path);st=path.stat();verified[item['path']]=[st.st_size,st.st_mtime_ns,item['sha256']];continue
            part.unlink();start=0
        request=urllib.request.Request(item['url'],headers={'User-Agent':'Lfm3Desk/1.0','Range':f'bytes={start}-'} if start else {'User-Agent':'Lfm3Desk/1.0'})
        with open_url(request,timeout=120) as response:
            resume=start>0 and response.status==206
            total=start if resume else 0;last=0
            with part.open('ab' if resume else 'wb') as f:
                for chunk in iter(lambda:response.read(1024*1024),b''):
                    f.write(chunk);total+=len(chunk)
                    if time.monotonic()-last>0.4:
                        emit('download_progress',file=item['path'],bytes=total,total=item['size']);last=time.monotonic()
        if part.stat().st_size!=item['size'] or sha256(part)!=item['sha256']:raise IOError('Tiny-SD download integrity check failed: '+item['path'])
        os.replace(part,path);st=path.stat();verified[item['path']]=[st.st_size,st.st_mtime_ns,item['sha256']]
    verified_file.write_text(json.dumps(verified,indent=2),encoding='utf-8')
    emit('status',message='Tiny-SD ready (same pinned TinySDDesk INT8 base).')

class Tokenizer:
    def __init__(self,folder):
        import regex
        self.regex=regex
        self.pattern=regex.compile(r"<\|startoftext\|>|<\|endoftext\|>|'s|'t|'re|'ve|'m|'ll|'d|[\p{L}]+|[\p{N}]|[^\s\p{L}\p{N}]+",regex.I)
        self.vocab=json.loads((folder/'vocab.json').read_text(encoding='utf-8'))
        self.ranks={tuple(line.split()):i for i,line in enumerate((folder/'merges.txt').read_text(encoding='utf-8').splitlines()[1:]) if len(line.split())==2}
        visible=set(range(33,127))|set(range(161,173))|set(range(174,256));extra=0;self.bytes={};self.cache={}
        for i in range(256):
            self.bytes[i]=chr(i if i in visible else 256+extra)
            if i not in visible:extra+=1
    def encode(self,text):
        text=self.regex.sub(r'\s+',' ',unicodedata.normalize('NFC',html.unescape(html.unescape(text))).strip()).lower()
        ids=[49406]
        for token in self.pattern.findall(text):
            if token in ('<|startoftext|>','<|endoftext|>'):ids.append(self.vocab[token]);continue
            word=''.join(self.bytes[b] for b in token.encode('utf-8'))
            if word not in self.cache:
                parts=list(word);parts[-1]+='</w>'
                while len(parts)>1:
                    options=[(self.ranks[(a,b)],i) for i,(a,b) in enumerate(zip(parts,parts[1:])) if (a,b) in self.ranks]
                    if not options:break
                    _,best=min(options);a,b=parts[best:best+2];i=0
                    while i<len(parts)-1:
                        if parts[i]==a and parts[i+1]==b:parts[i:i+2]=[a+b]
                        i+=1
                self.cache[word]=parts
            ids.extend(self.vocab.get(part,49407) for part in self.cache[word])
        cut=len(ids)>76;ids=ids[:76]+[49407];ids += [49407]*(77-len(ids))
        return ids,cut

class TinySD:
    def __init__(self,emit,backend="cpu",device_id=0):
        import numpy as np
        import onnxruntime as ort
        self.np=np;self.emit=emit;self.backend=backend;self.device_id=device_id;ort.disable_telemetry_events()
        if backend not in ('cpu','directml'):raise ValueError('Unknown image backend')
        if device_id<0 or device_id>31:raise ValueError('Image GPU index must be 0..31')
        if backend=='directml' and 'DmlExecutionProvider' not in ort.get_available_providers():raise RuntimeError('DirectML execution provider is unavailable')
        self.tokenizer=Tokenizer(MODEL/'tokenizer')
        options=ort.SessionOptions();options.intra_op_num_threads=min(4,os.cpu_count() or 1);options.inter_op_num_threads=1
        if backend=='directml':
            options.enable_mem_pattern=False;options.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
        providers=[('DmlExecutionProvider',{'device_id':str(device_id)}),'CPUExecutionProvider'] if backend=='directml' else ['CPUExecutionProvider']
        self.sessions={}
        for key,folder in [('clip','text_encoder'),('unet','unet'),('vae','vae_decoder_tiny')]:
            emit('status',message='Loading Tiny-SD '+key+' ('+backend+')…')
            self.sessions[key]=ort.InferenceSession(str(MODEL/folder/'model.onnx'),sess_options=options,providers=providers)
            if backend=='directml' and 'DmlExecutionProvider' not in self.sessions[key].get_providers():raise RuntimeError('DirectML session fell back to CPU: '+key)
    def generate(self,prompt,negative_prompt='',width=512,height=512,steps=20,guidance=7,seed=-1):
        from PIL import Image
        started=time.monotonic()
        np=self.np
        width=int(width);height=int(height);steps=int(steps);guidance=float(guidance);seed=int(seed)
        if width not in (256,384,512) or height not in (256,384,512):raise ValueError('Tiny-SD width/height: 256, 384 or 512')
        if not 1<=steps<=50 or not math.isfinite(guidance) or not 1<=guidance<=15:raise ValueError('Tiny-SD: steps 1..50, guidance 1..15')
        if len(prompt)>4000 or len(negative_prompt)>4000:raise ValueError('Image prompt too long')
        if seed<0:seed=secrets.randbits(32)
        if seed>2**32-1:raise ValueError('Seed must fit uint32')
        dtype={'tensor(float)':np.float32,'tensor(float16)':np.float16,'tensor(int64)':np.int64,'tensor(int32)':np.int32}
        def run(session,values,preferred=None):
            feed={m.name:np.asarray(values[m.name],dtype=dtype[m.type]) for m in session.get_inputs()}
            names=[o.name for o in session.get_outputs()];name=preferred if preferred in names else names[0]
            return session.run([name],feed)[0].astype(np.float32)
        self.emit('image_phase',phase='encoding')
        clip=self.sessions['clip'];clip_name=clip.get_inputs()[0].name
        pos,cut=self.tokenizer.encode(prompt);neg,cutneg=self.tokenizer.encode(negative_prompt)
        positive=run(clip,{clip_name:[pos]},'last_hidden_state');negative=run(clip,{clip_name:[neg]},'last_hidden_state') if guidance>1 else positive
        betas=np.linspace(math.sqrt(.00085),math.sqrt(.012),1000,dtype=np.float64)**2
        alphas=np.cumprod(1-betas);training=np.sqrt((1-alphas)/alphas)
        times=np.linspace(999,0,steps) if steps>1 else np.array([999.])
        sigmas=np.append(np.interp(times,np.arange(1000),training),0)
        latent=np.random.default_rng(seed).standard_normal((1,4,height//8,width//8),dtype=np.float32)*np.float32(sigmas[0])
        unet=self.sessions['unet']
        def predict(sample,embedding,t):
            values={'sample':sample,'encoder_hidden_states':embedding}
            for m in unet.get_inputs():
                if m.name=='timestep':values[m.name]=np.array(t if len(m.shape)==0 else [t])
            return run(unet,values)
        self.emit('image_progress',step=0,steps=steps)
        for i,t in enumerate(times):
            sigma,next_sigma=np.float32(sigmas[i]),np.float32(sigmas[i+1])
            scaled=latent/np.sqrt(sigma*sigma+1)
            p=predict(scaled,positive,t)
            noise=p if guidance<=1 else (lambda n:n+guidance*(p-n))(predict(scaled,negative,t))
            latent += noise*(next_sigma-sigma)
            self.emit('image_progress',step=i+1,steps=steps)
        self.emit('image_phase',phase='decoding')
        vae=self.sessions['vae'];pixels=run(vae,{vae.get_inputs()[0].name:latent})
        if pixels.shape!=(1,3,height,width) or not np.isfinite(pixels).all():raise ValueError('Invalid Tiny-SD image output')
        rgb=np.clip(np.rint((pixels[0].transpose(1,2,0)*.5+.5)*255),0,255).astype(np.uint8)
        folder=ROOT/'output'/'images';folder.mkdir(parents=True,exist_ok=True)
        path=folder/(time.strftime('%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:8]+'.png')
        self.emit('image_phase',phase='saving')
        Image.fromarray(rgb).save(path)
        result={'image':str(path),'seed':seed,'width':width,'height':height,'steps':steps,'prompt':prompt,'negative_prompt':negative_prompt,'prompt_truncated':cut or cutneg,'model':'TinySDDesk pinned Tiny-SD INT8','backend':'ONNX DirectML (CPU operator fallback allowed)' if self.backend=='directml' else 'ONNX CPU','gpu_index':self.device_id if self.backend=='directml' else None,'session_providers':{k:v.get_providers() for k,v in self.sessions.items()},'generation_seconds':round(time.monotonic()-started,3)}
        path.with_suffix('.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        return result
