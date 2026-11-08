"""Archive generated fenced code as data; never execute generated files."""
import datetime
import json
from pathlib import Path
import re
import uuid
from app_version import VERSION

EXT={'python':'py','py':'py','csharp':'cs','c#':'cs','cs':'cs','javascript':'js','js':'js','typescript':'ts','ts':'ts','html':'html','css':'css','json':'json','xml':'xml','bash':'sh','sh':'sh','shell':'sh','powershell':'ps1','ps1':'ps1','bat':'bat','batch':'bat','cmd':'cmd','sql':'sql','cpp':'cpp','c++':'cpp','c':'c','java':'java','rust':'rs','go':'go','yaml':'yaml','yml':'yml','toml':'toml','markdown':'md','text':'txt','txt':'txt'}

def blocks(text):
    position=0
    opening=re.compile(r'(`{3,}|~{3,})')
    while match:=opening.search(text,position):
        marker=match[1];line_end=text.find('\n',match.end());same_end=text.find(marker,match.end())
        if same_end>=0 and (line_end<0 or same_end<line_end):
            raw=text[match.end():same_end].strip();tokens=raw.split(None,1)
            language=tokens[0].lower() if tokens else ''
            info=language if language in EXT else ''
            content=tokens[1] if info and len(tokens)>1 else '' if info else raw
            end=same_end+len(marker);yield match.start(),end,info,content,True;position=end;continue
        if line_end<0:
            yield match.start(),len(text),'',text[match.end():],False;break
        info=text[match.end():line_end].strip()
        closing=re.compile(r'(?m)^[ \t]{0,3}'+re.escape(marker[0])+'{'+str(len(marker))+r',}[ \t]*(?:\n|$)').search(text,line_end+1)
        end=closing.start() if closing else len(text)
        yield match.start(),closing.end() if closing else len(text),info,text[line_end+1:end],closing is not None
        position=closing.end() if closing else len(text)

def without_code(text):
    output=[];start=0
    for begin,end,_,_,_ in blocks(str(text)):
        output.append(text[start:begin]);output.append('\n');start=end
    output.append(text[start:]);return ''.join(output)

def archive(text,root):
    found=list(blocks(text));saved=[]
    if not found:return saved
    folder=Path(root)/'output'/'code';folder.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');group=uuid.uuid4().hex[:8]
    for index,(_,_,info,content,complete) in enumerate(found,1):
        if not content.strip():continue
        language=info.split()[0].lower() if info else 'text';extension=EXT.get(language,'txt')
        title=re.search(r'(?:filename|file)\s*=\s*["\']?([^\s"\']+)',info,re.I)
        stem=Path((title[1] if title else 'code_'+language).replace('\\','/')).stem
        stem=re.sub(r'[^\w-]','_',stem,flags=re.ASCII).strip('_')[:45] or 'code'
        path=folder/f'{stamp}_{group}_{index:02}_{stem}.{extension}'
        with path.open('x',encoding='utf-8',newline='') as file:file.write(content)
        saved.append({'path':str(path),'language':language,'complete':complete})
    if saved:
        (folder/f'{stamp}_{group}_manifest.json').write_text(json.dumps({'app_version':VERSION,'created':datetime.datetime.now().astimezone().isoformat(),'files':saved,'executed':False},ensure_ascii=False,indent=2),encoding='utf-8')
    return saved
