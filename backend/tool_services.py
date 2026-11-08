from pathlib import Path
from tools_local import TOOLS,schema,dispatch
from online_tools import OnlineTools

WIKI_TOOLS=[
 schema('wikipedia_lookup','Search local German Wikipedia and read relevant excerpts. Use for factual/historical/scientific questions, not personal notes. Query should be a short German subject/title, e.g. Eiffelturm. question can retain the full question to find relevant paragraphs.',{'query':{'type':'string'},'question':{'type':'string'}},['query']),
 schema('wikipedia_read','Read more of a local Wikipedia article using its path from wikipedia_lookup. offset allows longer articles.',{'path':{'type':'string'},'offset':{'type':'integer'},'limit':{'type':'integer'}},['path'])]
WIKI_ONLINE_TOOLS=[
 schema('wikipedia_online_lookup','Search online Wikipedia for article excerpts. Only available when independently enabled. Use when offline Wikipedia is unavailable. language: de (default) or en.',{'query':{'type':'string'},'language':{'type':'string','enum':['de','en']}},['query']),
 schema('wikipedia_online_read','Read more of an online Wikipedia article from its title. Requires separate online Wikipedia permission.',{'title':{'type':'string'},'language':{'type':'string','enum':['de','en']}},['title'])]
WEB_TOOLS=[
 schema('web_search','Search the public web for current information. Returns source URLs and excerpts.',{'query':{'type':'string'},'limit':{'type':'integer'}},['query']),
 schema('web_read','Read a public HTTPS text page returned by web_search in this session.',{'url':{'type':'string'}},['url'])]
WEATHER_TOOLS=[schema('current_weather','Get current weather, a three-day forecast and three previous days from Open-Meteo; if offline, returns clearly dated recent cached reports or explicit unavailable status. Cached estimates are uncertain, never live forecasts. Requires an explicit place. Ask for a place if unspecified.',{'place':{'type':'string'},'country_code':{'type':'string'}},['place'])]
class ToolServices:
    def __init__(self,root,request):
        self.root=Path(root);self.request=request;self.online=OnlineTools(bool(request.get('web_enabled',False)),bool(request.get('weather_enabled',True)),bool(request.get('wiki_online_enabled',False)),offline=bool(request.get('offline',False)),root=self.root);self.wikipedia=None;self.sources=[];self.wiki_available=False;self.wiki_unavailable_reason='Offline Wikipedia is disabled.'
        if request.get('wiki_enabled',True):
            try:
                from knowledge import Wikipedia
                self.wikipedia=Wikipedia(request.get('wiki_path',''));self.wiki_available=True
            except Exception as error:self.wiki_unavailable_reason=str(error)
    def schemas(self):return TOOLS+(WIKI_TOOLS if self.wiki_available else [])+(WIKI_ONLINE_TOOLS if self.online.wiki else [])+(WEB_TOOLS if self.online.web else [])+(WEATHER_TOOLS if self.online.weather else [])
    def remember(self,result):
        if isinstance(result,dict):
            if result.get('url') and result.get('title'):
                source={k:result[k] for k in ('title','url','kind','archive') if k in result}
                if not any(s['url']==source['url'] for s in self.sources):self.sources.append(source)
            for value in result.values():self.remember(value)
        elif isinstance(result,list):
            for value in result:self.remember(value)
        return result
    def run(self,name,args):
        if name=='wikipedia_online_lookup':result=self.online.wikipedia_online_lookup(**args)
        elif name=='wikipedia_online_read':result=self.online.wikipedia_online_read(**args)
        elif name.startswith('wikipedia_'):
            if not self.request.get('wiki_enabled',True):raise PermissionError('Offline Wikipedia is disabled.')
            if not self.wiki_available:raise FileNotFoundError(self.wiki_unavailable_reason)
            if name=='wikipedia_lookup':result=self.wikipedia.lookup(**args)
            elif name=='wikipedia_read':result=self.wikipedia.read(**args)
            else:raise ValueError('Unknown Wikipedia tool')
        elif name=='web_search':result=self.online.web_search(**args)
        elif name=='web_read':result=self.online.web_read(**args)
        elif name=='current_weather':result=self.online.current_weather(**args)
        else:
            result=dispatch(name,args,self.root/'workspace')
            if name in ('list_notes','read_note'):result={**result,'scope':'Private user notes only, not general knowledge. Use wikipedia_lookup for encyclopedia questions; missing notes do not imply missing knowledge.'}
        return self.remember(result)
