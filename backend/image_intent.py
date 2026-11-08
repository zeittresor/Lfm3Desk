"""Conservative current-turn image-creation intent; never overrides disabled tools."""
import re

def requested(question):
    q=question.lower()
    noun=r'(?:bild(?:er)?|foto|illustration|cover|zeichnung|image|picture|drawing)'
    if re.search(r'\b(?:kein(?:e[ns]?)?|ohne)\s+(?:neues?\s+)?'+noun+r'\b|\b(?:do not|don.t|no)\s+(?:create\s+|generate\s+|draw\s+|paint\s+)?(?:an?\s+)?'+noun+r'\b',q):return False
    if re.search(r'\bnicht\s+(?:als\s+|ein\w*\s+)?'+noun+r'\b',q):return False
    if re.search(r'\b(?:code|script|skript|funktion|function|api)\b',q):return False
    if re.search(r'\b(?:wie|how)\s+(?:kann\s+man|erstellt\s+man|generiert\s+man|to|do\s+i)\b',q):return False
    if re.search(r'\b(?:nur\s+beschreib\w*|beschreib\w*\s+nur|only\s+describe|describe\s+only)\b',q):return False
    return bool(re.search(r'\b(?:erstell\w*|generier\w*|erzeug\w*|mache?|make|zeichne|male|create|generate|draw|paint|render)\b.{0,140}\b'+noun+r'\b',q,re.S)
                or re.search(r'\b'+noun+r'\b.{0,100}\b(?:erstellen|generieren|zeichnen|malen)\b',q,re.S)
                or re.search(r'\bals\s+(?:ein\s+)?(?:erstelltes?\s+|generiertes?\s+)?bild\b|\bvisualisiere\b',q)
                or re.search(r'\b(?:zeig\w*|show)\s+(?:mir\s+|me\s+)?(?:ein\w*|an?|some)\s+'+noun+r'\b',q))
