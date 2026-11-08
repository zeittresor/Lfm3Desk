"""Per-location rolling weather reports. Cached past data are never a live forecast."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import unicodedata
from app_version import VERSION

UTC=dt.timezone.utc

def place_key(value):return ' '.join(unicodedata.normalize('NFKC',str(value)).casefold().split())
def timestamp(value):return dt.datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(UTC)
def now_utc():return dt.datetime.now(UTC)

def daily_rows(data):
    daily=data.get('daily') or {};dates=daily.get('time') or []
    return [{key:value[index] for key,value in daily.items() if isinstance(value,list) and index<len(value)} for index,_ in enumerate(dates)]

class WeatherCache:
    def __init__(self,root,clock=now_utc):self.folder=Path(root)/'data'/'weather';self.clock=clock
    def _read(self,path):
        try:
            if path.stat().st_size>4*1024*1024:return None
            result=json.loads(path.read_text(encoding='utf-8-sig'))
            return result if isinstance(result,dict) and isinstance(result.get('reports'),list) and isinstance(result.get('aliases'),list) else None
        except (OSError,ValueError):return None
    def _recent(self,reports):
        now=self.clock();cutoff=now-dt.timedelta(days=3);days={}
        for report in reports:
            try:
                if not isinstance(report,dict) or not isinstance(report.get('retrieved_at'),str) or not isinstance(report.get('location'),dict) or not report['location'].get('name') or not isinstance(report.get('url'),str):continue
                when=timestamp(report['retrieved_at'])
                if cutoff<=when<=now:
                    key=when.date().isoformat()
                    if key not in days or when>timestamp(days[key]['retrieved_at']):days[key]=report
            except (KeyError,ValueError,TypeError,AttributeError):continue
        return sorted(days.values(),key=lambda report:report['retrieved_at'])[-3:]
    def save(self,report,place,country_code=''):
        location=report['location'];key=hashlib.sha256(json.dumps([round(float(location['latitude']),4),round(float(location['longitude']),4),location.get('country_code')],sort_keys=True).encode()).hexdigest()[:20]
        self.folder.mkdir(parents=True,exist_ok=True);path=self.folder/(key+'.json');old=self._read(path) or {}
        aliases=old.get('aliases',[])
        for alias in ([place_key(place),country_code.upper()],[place_key(location['name']),str(location.get('country_code') or '').upper()]):
            if alias not in aliases:aliases.append(alias)
        record={'app_version':VERSION,'location':location,'aliases':aliases,'reports':self._recent(old.get('reports',[])+[report])}
        temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8');temporary.replace(path)
    def find(self,place,country_code=''):
        query=place_key(place);country=country_code.upper();matches=[]
        if not self.folder.is_dir():return None
        for path in sorted(self.folder.glob('*.json'))[:200]:
            record=self._read(path)
            if not record:continue
            aliases=record.get('aliases',[]);exact=[query,country] in aliases
            compatible=any(isinstance(alias,list) and len(alias)==2 and alias[0]==query and (not country or alias[1]==country) for alias in aliases)
            reports=self._recent(record['reports'])
            if reports and (exact or compatible):matches.append((exact,reports))
        exact=[reports for matched,reports in matches if matched]
        candidates=exact or [reports for _,reports in matches]
        if len(candidates)!=1:return None  # Never guess between ambiguous regions.
        return candidates[0]
    def offline(self,place,country_code='',reason='Online access unavailable'):
        reports=self.find(place,country_code);now=self.clock()
        base={'online_available':False,'online_error':str(reason),'requested_place':place,'request_time':now.isoformat(),'season_reference_month':now.month,'can_offer_estimate':False,'recent_history':[],'historical_reports':[]}
        if not reports:
            return {**base,'status':'offline_no_cache','message':'No current online data and no recent regional reports from the last 72 hours. No reliable local forecast is available. Only clearly labelled general seasonal remarks may be offered, not invented local values.'}
        latest=reports[-1];offset=dt.timedelta(seconds=int(latest.get('utc_offset_seconds') or 0));today=(now+offset).date();cutoff=today-dt.timedelta(days=3)
        history={}
        for report in reports:
            for row in report.get('recent_history',[]):
                try:
                    date=dt.date.fromisoformat(row['time'])
                    if cutoff<=date<today:history[row['time']]=row
                except (ValueError,KeyError,TypeError):continue
        return {**base,'status':'offline_cached','title':'Gespeicherte Wetterberichte: '+latest['location']['name'],'kind':'Weather cache','url':latest['url'],'location':latest['location'],'cache_retrieved_at':latest['retrieved_at'],'cache_age_hours':round((now-timestamp(latest['retrieved_at'])).total_seconds()/3600,2),'recent_history':[history[key] for key in sorted(history)],'history_units':latest.get('forecast_units'),'historical_reports':[{'reported_at':r['retrieved_at'],'past_current_values':r.get('current'),'units':r.get('units')} for r in reports],'can_offer_estimate':True,'message':'Live weather cannot currently be retrieved. These are past cached reports/model-based recent-past data, NOT current measurements or a fresh forecast. State the failure and cache date/age clearly. You may offer a tentative trend/season-based estimate, explicitly uncertain and not an official forecast. Do not invent precise future values or precipitation probabilities.','attribution':latest.get('attribution')}
