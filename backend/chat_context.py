"""Keep old capability refusals out of the current model context, not the transcript."""
import copy
import re

FEATURES={
 'current_weather':r'wetter|weather',
 'web_search':r'web|internet|online|network',
 'wikipedia_online_lookup':r'wikipedia|lexikon|encyclop',
 'wikipedia_lookup':r'wikipedia|lexikon|encyclop'}
NEGATIVE=re.compile(r'\b(nicht|kein\w*|cannot|unable|unavailable|can.t|don.t|not|no)\b',re.I)
ACCESS=re.compile(r'zugriff|tool|werkzeug|verfüg|access|available|dienst',re.I)

def strip_refusals(text,available):
    sentences=re.split(r'(?<=[.!?])\s+',text)
    active=[re.compile(pattern,re.I) for name,pattern in FEATURES.items() if name in available]
    kept=[part for part in sentences if not (NEGATIVE.search(part) and ACCESS.search(part) and any(pattern.search(part) for pattern in active))]
    return text if len(kept)==len(sentences) else ' '.join(kept)

def model_history(history,available):
    if not isinstance(history,list) or len(history)>256:raise ValueError('Chat history must contain at most 256 messages.')
    result=[]
    for value in history:
        if not isinstance(value,dict) or value.get('role') not in ('user','assistant','tool'):raise ValueError('Invalid chat history role')
        message=copy.deepcopy(value)
        if message['role']=='assistant' and isinstance(message.get('content'),str):
            message['content']=strip_refusals(message['content'],available)
            if not message['content'] and not message.get('tool_calls'):continue
        result.append(message)
    return result
