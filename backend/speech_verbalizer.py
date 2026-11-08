"""Deterministic speech-only typography/measurement preparation (no dependencies).

Do not apply to chat history, tool data or visible answers. Numbers are expanded
only next to supported units; identifiers, dates and weather codes stay intact.
"""
import re
import unicodedata

_DE = ('null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf '
       'dreizehn vierzehn fünfzehn sechzehn siebzehn achtzehn neunzehn').split()
_EN = ('zero one two three four five six seven eight nine ten eleven twelve '
       'thirteen fourteen fifteen sixteen seventeen eighteen nineteen').split()

def integer(n, de):
    small = _DE if de else _EN
    if n < 20:
        return small[n]
    if n < 100:
        tens = (['', '', 'zwanzig', 'dreißig', 'vierzig', 'fünfzig', 'sechzig', 'siebzig', 'achtzig', 'neunzig']
                if de else ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'])
        a, b = divmod(n, 10)
        return ((('ein' if b == 1 else small[b]) + 'und') if b else '') + tens[a] if de else tens[a] + (' ' + small[b] if b else '')
    if n < 1000:
        a, b = divmod(n, 100)
        return (('ein' if a == 1 else small[a]) + 'hundert' + (integer(b, de) if b else '')
                if de else small[a] + ' hundred' + (' ' + integer(b, de) if b else ''))
    if n < 1000000:
        a, b = divmod(n, 1000)
        return (('ein' if a == 1 else integer(a, de)) + 'tausend' + (integer(b, de) if b else '')
                if de else integer(a, de) + ' thousand' + (' ' + integer(b, de) if b else ''))
    # Large measurements: digit-by-digit avoids linguistic/scale ambiguity.
    return ' '.join(small[int(c)] for c in str(n))

def number(raw, de, one=False):
    sign = ''
    if raw[:1] in ('-', '+', '−'):
        sign = ('minus ' if raw[0] != '+' else 'plus ')
        raw = raw[1:]
    raw = raw.replace(' ', '')
    # Locale-aware thousands and decimal separators; mixed forms use last separator.
    decimal = ',' if de else '.'
    if ',' in raw and '.' in raw:
        decimal = ',' if raw.rfind(',') > raw.rfind('.') else '.'
        raw = raw.replace('.' if decimal == ',' else ',', '')
    else:
        grouping = '.' if de else ','
        if re.fullmatch(r'\d{1,3}(?:' + re.escape(grouping) + r'\d{3})+', raw):
            raw = raw.replace(grouping, '')
        elif grouping in raw:
            decimal = grouping  # Accept e.g. API-style 4.5 in a German answer.
    parts = raw.split(decimal)
    if len(parts) > 2:
        raise ValueError('Unsupported numeric notation')
    head = integer(int(parts[0]), de)
    if len(parts) == 2:
        head += (' Komma ' if de else ' point ') + ' '.join((_DE if de else _EN)[int(c)] for c in parts[1])
    elif one and int(parts[0]) == 1 and de:
        head = 'ein'
    return sign + head

_NUM = r'[+−-]?\d+(?:[.,]\d+)*'
_UNIT = r'(?:°\s*[CF]|%|km/h|m/s|hPa|mm|cm|km|kg|°)'

def verbalize(text, language):
    """Return speakable text; unknown languages get typography cleanup only."""
    lang = str(language).strip().lower()
    de = lang in ('de', 'de-de', 'german', 'deutsch')
    en = lang in ('en', 'en-us', 'en-gb', 'english', 'englisch')
    text = unicodedata.normalize('NFC', str(text)).replace('\u202f', ' ').replace('\xa0', ' ')
    # Remove presentation markup before list/heading boundaries become whitespace.
    text = re.sub(r'(?m)^\s*(?:#{1,6}\s+|>\s*|[-*+•]\s+|\d+[.)]\s+)', '', text)
    text = re.sub(r'\*\*|__|~~|`+', '', text)
    text = re.sub(r'(?<!\w)[*_](?=\S)|(?<=\S)[*_](?!\w)', '', text)
    if not (de or en):
        return re.sub(r'\s+', ' ', re.sub(r' +([,:;!?])', r'\1', text)).strip()
    if de:
        text = re.sub(r'\bNebelchance\b', 'Nebelwahrscheinlichkeit', text, flags=re.I)
        text = re.sub(r'\bRegenchance\b', 'Regenwahrscheinlichkeit', text, flags=re.I)
    # Expand max/min only beside measurements or as labels, not names like Max.
    labels = {'max': 'maximal' if de else 'maximum', 'min': 'minimal' if de else 'minimum'}
    text = re.sub(r'\b(max|min)\b\.?\s*(?=[:≈~]|' + _NUM + r'\s*' + _UNIT + r')',
                  lambda m: labels[m[1].lower()] + ' ', text, flags=re.I)
    text = re.sub(r'(' + _UNIT + r')\s+(max|min)\b\.?',
                  lambda m: m[1] + ' ' + labels[m[2].lower()], text, flags=re.I)
    for symbol, word in [('≈', 'etwa' if de else 'approximately'), ('≤', 'höchstens' if de else 'at most'),
                         ('≥', 'mindestens' if de else 'at least')]:
        text = text.replace(symbol, ' ' + word + ' ')
    text = re.sub(r'~\s*(?=[+−-]?\d)', 'etwa ' if de else 'approximately ', text)
    text = re.sub(r'\bca\.', 'etwa' if de else 'approximately', text, flags=re.I)
    # Shared-unit ranges: avoid reading the separator as a negative sign.
    def measure(m):
        first, second, unit = m['first'], m['second'], re.sub(r'\s+', '', m['unit'])
        names = ({'°C':'Grad Celsius','°F':'Grad Fahrenheit','°':'Grad','%':'Prozent','km/h':'Kilometer pro Stunde',
                  'm/s':'Meter pro Sekunde','hPa':'Hektopascal','mm':'Millimeter','cm':'Zentimeter','km':'Kilometer','kg':'Kilogramm'}
                 if de else {'°C':'degrees Celsius','°F':'degrees Fahrenheit','°':'degrees','%':'percent','km/h':'kilometers per hour',
                  'm/s':'meters per second','hPa':'hectopascals','mm':'millimeters','cm':'centimeters','km':'kilometers','kg':'kilograms'})
        try:
            value = number(first, de, one=unit in ('%', '°C', '°F', '°'))
            if second:
                number(second, de)
        except (ValueError, IndexError):
            return m.group()  # Unsupported numeric notation must never abort TTS.
        if second:
            value += (' bis ' if de else ' to ') + number(second, de, one=unit in ('%', '°C', '°F', '°'))
        return value + ' ' + names[unit]
    # Guard against matching a numeric suffix inside an identifier or unsupported number.
    pattern = r'(?<![\w.,/])(?P<first>' + _NUM + r')(?:\s*(?:[–—‑-]|bis|to)\s*(?P<second>' + _NUM + r'))?\s*(?P<unit>' + _UNIT + r')(?![\w/])'
    text = re.sub(pattern, measure, text)
    text = re.sub(r'(%|Prozent|percent)[‑–-](?=\w)', r'\1 ', text)
    # A line boundary is a clause boundary, preventing adjacent bullet labels merging.
    text = re.sub(r'(?<=[\w)])\s*\n+\s*(?=\w)', '. ', text)
    return re.sub(r'\s+', ' ', re.sub(r' +([,:;!?])', r'\1', text)).strip()
