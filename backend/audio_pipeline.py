"""Short independent TTS utterances, saved fragments and bounded RMS normalization."""
import datetime
import json
import re
import uuid
from pathlib import Path
from app_version import VERSION
from speech_verbalizer import verbalize
from code_artifacts import without_code

RATE=24000

def chunks(text,limit=140):
    # Protect decimals/abbreviations; never split a word merely to meet a limit.
    text=re.sub(r'\s+',' ',str(text)).strip()
    protected=re.sub(r'\b(?:z\.\s?B\.|u\.\s?a\.|d\.\s?h\.|Dr\.|Prof\.|bzw\.|ca\.|Mr\.|Mrs\.)',lambda m:m.group().replace('.','\ue000'),text,flags=re.I)
    sentences=re.split(r'(?<=[.!?。！？])\s+',protected)
    result=[]
    for sentence in sentences:
        sentence=sentence.replace('\ue000','.')
        words=sentence.split();part=[];size=0
        for word in words:
            if part and size+len(word)+1>limit:result.append(' '.join(part));part=[];size=0
            part.append(word);size+=len(word)+1
        if part:result.append(' '.join(part))
    return result

def combine(fragments,rate=RATE):
    import numpy as np
    prepared=[];pause=np.zeros(round(rate*.12),dtype=np.float32)
    for fragment in fragments:
        wave=np.asarray(fragment,dtype=np.float32).reshape(-1)
        if not len(wave) or not np.isfinite(wave).all():raise ValueError('Invalid speech fragment (empty or non-finite).')
        wave=wave-wave.mean()  # Remove DC offset before level measurement.
        peak=float(np.max(np.abs(wave)));rms=float(np.sqrt(np.mean(wave*wave)))
        if peak>1e-6 and rms>1e-5:
            active=np.flatnonzero(np.abs(wave)>max(1e-5,peak*.002))
            if len(active):wave=wave[max(0,active[0]-round(rate*.025)):min(len(wave),active[-1]+round(rate*.025)+1)]
            gain=min(2.0,max(.5,.10/rms),.94/max(float(np.max(np.abs(wave))),1e-8));wave=wave*gain
        fade=min(round(rate*.006),len(wave)//2)
        if fade:wave[:fade]*=np.linspace(0,1,fade);wave[-fade:]*=np.linspace(1,0,fade)
        if prepared:prepared.append(pause)
        prepared.append(wave)
    if not prepared:raise ValueError('No speech fragments')
    joined=np.concatenate(prepared)
    peak=float(np.max(np.abs(joined)));rms=float(np.sqrt(np.mean(joined*joined)))
    if rms>1e-5 and peak>1e-6:joined*=min(2.0,.126/rms,.95/peak)
    return np.clip(joined,-.95,.95).astype(np.float32)

def render(engine,text,language,voice,request,emit,root):
    import numpy as np
    import soundfile as sf
    prepared_text=verbalize(without_code(text),language)
    if not prepared_text:prepared_text='Der Code ist als Text verfügbar.' if language in ('German','DE','de') else 'The code is available as text.'
    segments=chunks(prepared_text)
    if not segments:raise ValueError('No text remains for speech output.')
    temporary=not request.get('save_audio',True)
    folder=Path(root)/'output'/('temp' if temporary else 'audio');folder.mkdir(parents=True,exist_ok=True)
    stem=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_')+uuid.uuid4().hex[:8]
    parts=folder/(stem+'.parts');waves=[];metadata=[]
    if not temporary:parts.mkdir()
    for index,segment in enumerate(segments,1):
        emit('speech_progress',stage='synthesizing',part=index,total=len(segments))
        budget=max(128,min(512,32+20*len(segment.split())))
        conversation=[{'role':'system','content':f'Perform TTS in {language} using a {voice} voice.'},{'role':'user','content':segment}]
        _,out=engine.generate(conversation,'audio',{**request,'max_tokens':budget})
        if out.audio_codes is None or int(out.audio_lengths[0])==0:raise RuntimeError(f'No audio returned for speech fragment {index}.')
        with engine.torch.inference_mode():wave=engine.codec.decode(out.audio_codes[:1,:,:out.audio_lengths[0]]).audio_values[0]
        wave=np.asarray(wave.squeeze(0).float().cpu().numpy(),dtype=np.float32).reshape(-1)
        if not np.isfinite(wave).all() or not len(wave):raise RuntimeError(f'Invalid audio in fragment {index}.')
        waves.append(wave)
        entry={'part':index,'text':segment,'seconds':len(wave)/RATE,'token_limit':budget,'audio_frames':int(out.audio_lengths[0])}
        if not temporary:
            file=parts/f'{index:03}.wav';sf.write(str(file),wave,RATE,subtype='PCM_16');entry['file']=str(file)
        metadata.append(entry)
        del out  # Do not retain the previous fragment GPU outputs during the next call.
    emit('speech_progress',stage='normalizing',part=len(segments),total=len(segments))
    final=folder/(stem+'.wav');joined=combine(waves);sf.write(str(final),joined,RATE,subtype='PCM_16')
    if not temporary:(parts/'manifest.json').write_text(json.dumps({'app_version':VERSION,'created':datetime.datetime.now().astimezone().isoformat(),'source_text':text,'prepared_text':prepared_text,'speech_preparation':'dates-time-abbreviations-v2','language':language,'voice':voice,'sample_rate':RATE,'normalization':'bounded RMS with -0.45 dBFS peak ceiling','final':str(final),'fragments':metadata},ensure_ascii=False,indent=2),encoding='utf-8')
    emit('speech_progress',stage='complete',part=len(segments),total=len(segments))
    return str(final),temporary
