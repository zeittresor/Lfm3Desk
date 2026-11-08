"""Prepare generated replies for speech; display/export text stays unchanged."""
from code_artifacts import without_code
import re

def _labels_only(text):
    # Balanced destinations support parentheses and spaces in image/file paths.
    pattern=re.compile(r'!?\[([^\]\n]*)\]\(')
    parts=[];start=0
    while True:
        match=pattern.search(text,start)
        if not match:parts.append(text[start:]);break
        depth=1;end=match.end()
        while end<len(text) and depth:
            if text[end]=='\\' and end+1<len(text) and text[end+1] in '()\\':end+=2;continue
            if text[end]=='(':depth+=1
            elif text[end]==')':depth-=1
            end+=1
        if depth:parts.append(text[start:match.end()]);start=match.end();continue
        parts.extend((text[start:match.start()],match.group(1)));start=end
    return ''.join(parts)

def _drop_destination(match):
    value=match.group().strip('<>');punctuation=''
    while value and value[-1] in '.,;:!?':punctuation=value[-1]+punctuation;value=value[:-1]
    return ')' * max(0,value.count(')')-value.count('('))+punctuation

def for_speech(text,artifact_paths=()):
    text=_labels_only(without_code(str(text)))
    for path in sorted(set(str(p) for p in artifact_paths if p),key=len,reverse=True):
        for variant in {path,path.replace('\\','/'),path.replace('/','\\')}:text=text.replace(variant,'')
    # Reference definitions carry destinations, not spoken content.
    text=re.sub(r'(?m)^\s*\[[^\]\n]+\]:\s*\S+.*$','',text)
    text=re.sub(r'!?\[([^\]\n]+)\]\[[^\]\n]*\]',r'\1',text)
    # Quoted paths may contain spaces. Unquoted destinations stop at whitespace.
    text=re.sub(r'''(["'`])(?:[A-Za-z]:[\\/]|\\\\|/|~[/\\]|\.\.?[/\\])[^\r\n]*?\1''','',text)
    text=re.sub(r'(?i)<?\b(?:https?://|ftp://|file://|mailto:|data:|www\.)[^\s<>\[\]"`]+>?',_drop_destination,text)
    text=re.sub(r'(?<!\w)[A-Za-z]:[\\/][^\s<>"\[\]`]+','',text)
    text=re.sub(r'(?<!\w)\\\\[^\s<>"\[\]`]+','',text)
    text=re.sub(r'(?<![\w:])(?:~|\.{1,2})?/(?:[^\s/<>"`]+/)*[^\s/<>"`]+','',text)
    text=re.sub(r'(?i)\b(?:[\w.-]+[\\/])+[\w.-]+\.(?:png|jpe?g|webp|gif|bmp|wav|mp3|flac|ogg|mp4|mkv|txt|json|pdf|zip)\b','',text)
    text=re.sub(r'(?i)\b(?:[a-z0-9-]+\.)+(?:org|com|net|de|io|edu|gov)(?:/[^\s<>"`]+)?\b','',text)
    text=re.sub(r'`([^`\n]*)`',r'\1',text)
    text=re.sub(r'\(\s*\)|\[\s*\]|<\s*>','',text)
    text=re.sub(r'[ \t]+([,.;!?])',r'\1',text)
    text=re.sub(r'[ \t]{2,}',' ',text)
    text=re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',text)
    return text.strip()
