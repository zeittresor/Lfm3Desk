"""Compact answers without deleting distinct facts or genuine tool errors."""
import re

STYLE = ('Give one compact weather report per requested place/day. State each weather fact once; '
         'do not repeat the same forecast in an introduction, detailed block and summary. '
         'Use natural labels such as Mindesttemperatur and Höchsttemperatur instead of API field names or weather codes. '
         'After image creation, confirm briefly or describe the depicted scene, not how it was generated. '
         'Do not volunteer model names, backends, CPU/GPU, seeds, sampling steps, prompts or storage paths. '
         'Explain implementation only when the user explicitly asks. Preserve actual failures and offline/cache caveats. ')

def technical_question(question):
    return bool(re.search(r'\b(?:cpu|gpu|onnx|seed|sampler|backend|directml|technik|technisch\w*|implementation|technical)\b|(?:welch\w*|which).{0,24}(?:modell|model|prompt)|(?:wie|how).{0,40}(?:generiert|erzeugt|erstellt|generated|created)',question,re.I))

def image_result(result,question):
    if 'error' in result or technical_question(question):return result
    return {'image':result.get('image'),'status':'created','note':'Illustration, not a real photograph. Confirm briefly; do not explain tools or implementation.'}

def deduplicate(text):
    # Only identical paragraphs (whitespace/emphasis differences) are removable.
    # Different days, values and paraphrases remain: no risky semantic guessing.
    seen=set();kept=[]
    for paragraph in re.split(r'\n\s*\n',text):
        key=re.sub(r'\s+',' ',re.sub(r'\*\*|__','',paragraph)).strip().casefold()
        if not key or key not in seen:kept.append(paragraph)
        if key:seen.add(key)
    return '\n\n'.join(kept)

def spoken_answer(text,question,image_created):
    if not image_created or technical_question(question):return text
    # Narrow fallback for old context leaking technical image narration into speech.
    pattern=r'(?<=[.!?])(?=\s)|(?=\n)'
    parts=re.split(pattern,text)
    def technical(part):
        subject=re.search(r'\b(?:Bild|image|picture)\b',part,re.I)
        creation=re.search(r'\b(?:erstellt|erzeugt|generiert|generated|created)\b',part,re.I)
        detail=re.search(r'\b(?:Tiny.?SD|Stable Diffusion|ONNX|CPU|GPU|DirectML|Seed|Backend|Modell|model|sampling)\b',part,re.I)
        return subject and creation and detail and not re.search(r'\b(?:Fehler|fehlgeschlagen|nicht|error|failed|cannot)\b',part,re.I)
    return ''.join(part for part in parts if not technical(part)).strip()
