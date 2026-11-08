"""Validated dates, clock times and curated abbreviations for speech only."""
import datetime
import re

MONTHS_DE='Januar Februar März April Mai Juni Juli August September Oktober November Dezember'.split()
MONTHS_EN='January February March April May June July August September October November December'.split()

def prepare(text,de,integer):
    def ordinal(n,ending='r'):
        if de:
            stems={1:'erst',2:'zweit',3:'dritt',6:'sechst',7:'siebt',8:'acht'}
            return stems.get(n,integer(n,True)+('t' if n<20 else 'st'))+'e'+ending
        special={1:'first',2:'second',3:'third',5:'fifth',8:'eighth',9:'ninth',12:'twelfth',20:'twentieth',30:'thirtieth'}
        if n in special:return special[n]
        if n>20:return integer(n//10*10,False)+' '+ordinal(n%10)
        return integer(n,False)+'th'
    def year(n):
        if de and 1100<=n<2000:return integer(n//100,True)+'hundert'+(integer(n%100,True) if n%100 else '')
        return integer(n,de)
    def date_words(y,m,d,prefix):
        if re.search(r'\b(?:version|build|id|datei|file)\s*[:=]?\s*$',prefix,re.I):return None
        try:datetime.date(y,m,d)
        except ValueError:return None
        ending='n' if de and re.search(r'\b(?:am|vom|zum|seit|ab|den)\s*$',prefix,re.I) else 'r'
        return ordinal(d,ending)+' '+(MONTHS_DE if de else MONTHS_EN)[m-1]+' '+year(y)
    def iso(m):
        value=date_words(int(m[1]),int(m[2]),int(m[3]),m.string[max(0,m.start()-24):m.start()])
        return value if value else m[0]
    # Convert only complete valid dates. IDs/paths/versions are not dates.
    text=re.sub(r'(?<![\w/\\-])(\d{4})[-‑](\d{2})[-‑](\d{2})(?![\w/\\-]|\.[A-Za-z])',iso,text)
    def local(m):
        return date_words(int(m[3]),int(m[2]),int(m[1]),m.string[max(0,m.start()-24):m.start()]) or m[0]
    if de:
        text=re.sub(r'(?<![\w./\\-])(\d{1,2})\.(\d{1,2})\.(\d{4})(?![\w/\\-]|\.[A-Za-z])',local,text)
        months={name.lower():i for i,name in enumerate(MONTHS_DE,1)}
        months.update({'jan':1,'feb':2,'mär':3,'mrz':3,'apr':4,'jun':6,'jul':7,'aug':8,'sep':9,'sept':9,'okt':10,'nov':11,'dez':12})
        def named(m):
            return date_words(int(m[3]),months[m[2].lower()],int(m[1]),m.string[max(0,m.start()-24):m.start()]) or m[0]
        text=re.sub(r'(?<!\w)(\d{1,2})\.\s*('+ '|'.join(sorted(months,key=len,reverse=True))+r')\.?\s+(\d{4})(?!\w)',named,text,flags=re.I)
    def clock(m):
        h,minute=int(m[1]),int(m[2]);second=int(m[3]) if m.lastindex>=3 and m[3] else None
        if h>23 or minute>59 or second is not None and second>59:return m[0]
        # Do not reinterpret scores, ratios, durations, or timezone offsets as clock time.
        prefix=m.string[max(0,m.start()-48):m.start()]
        if re.search(r'(?:Verhältnis|Spielstand|Ergebnis|Dauer|Laufzeit|ratio|score|duration)\s*(?:von|of|:)?\s*$',prefix,re.I):return m[0]
        if de:
            result=('ein' if h==1 else integer(h,True))+' Uhr'
            if minute:result+=' '+integer(minute,True)
            if second is not None:result+=' und '+('eine Sekunde' if second==1 else integer(second,True)+' Sekunden')
        else:
            result=integer(h,False)
            result+=(' oh '+integer(minute,False) if minute<10 else ' '+integer(minute,False)) if minute else " o'clock"
            if second is not None:result+=' and '+integer(second,False)+(' second' if second==1 else ' seconds')
        return result
    text=re.sub(r'(?<![\w:+/−-])(\d{1,2}):(\d{2})(?::(\d{2}))?(?:[ \t]*(?:Uhr|o.clock)\b)?(?![\w:])',clock,text,flags=re.I)
    if de:
        text=re.sub(r'(?<![\w.])(\d{1,2})\.(\d{2})[ \t]+Uhr\b',clock,text,flags=re.I)
        text=re.sub(r'(?<![\w:])(\d{1,2})[ \t]+Uhr\b',lambda m:(('ein' if int(m[1])==1 else integer(int(m[1]),True))+' Uhr') if int(m[1])<24 else m[0],text)
        abbreviations=[(r'z\.\s*B\.', 'zum Beispiel'),(r'd\.\s*h\.', 'das heißt'),(r'u\.\s*a\.', 'unter anderem'),
                       (r'(?:usw\.|u\.\s*s\.\s*w\.)', 'und so weiter'),(r'bzw\.', 'beziehungsweise'),(r'ggf\.', 'gegebenenfalls'),
                       (r'evtl\.', 'eventuell'),(r'vorauss\.', 'voraussichtlich'),(r'inkl\.', 'inklusive'),
                       (r'zzgl\.', 'zuzüglich'),(r'ca\.', 'etwa'),(r'Prof\.', 'Professor'),(r'Dr\.', 'Doktor')]
        for pattern,value in abbreviations:text=re.sub(r'(?<!\w)'+pattern+r'(?!\w)',value,text,flags=re.I)
        replacements={'Temperaturmin':'Mindesttemperatur','Temperaturmax':'Höchsttemperatur','Tempmin':'Mindesttemperatur','Tempmax':'Höchsttemperatur','Temperaturminimum':'Mindesttemperatur','Temperaturmaximum':'Höchsttemperatur'}
        for word,value in replacements.items():text=re.sub(r'\b'+word+r'\b',value,text,flags=re.I)
        text=re.sub(r'\b(?:Temperatur|Temp\.?)\s*[-_]?\s*(min|max)\b\.?',lambda m:'Mindesttemperatur' if m[1].lower()=='min' else 'Höchsttemperatur',text,flags=re.I)
        def duration(m):
            n=int(m[1]);unit=m[2].lower().rstrip('.')
            singular,plural={'min':('Minute','Minuten'),'sek':('Sekunde','Sekunden'),'std':('Stunde','Stunden')}[unit]
            return ('eine '+singular) if n==1 else integer(n,True)+' '+plural
        text=re.sub(r'(?<![\w.,])([0-9]+)\s*(min\.?|Sek\.|Std\.)(?!\w)',duration,text,flags=re.I)
        text=re.sub(r'\bTemp\.(?=\s|:|$)','Temperatur',text,flags=re.I)
    return text
