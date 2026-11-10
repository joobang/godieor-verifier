#!/usr/bin/env python3
"""Manual Simulator contract fixture. Not a real provider or backend verification."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import calendar
import json

IDS=['00000000-0000-4000-8000-000000000001','00000000-0000-4000-8000-000000000002']
def event(index):
    return dict(id=IDS[index],kind='theatrical_release' if index==0 else 'ott_season_premiere',
        title='검증용 가상 영화' if index==0 else '검증용 가상 드라마',contentId=None,status='scheduled',
        time={'type':'date_only','date':'2026-11-06' if index==0 else '2026-11-07'},
        releaseMarket='KR',venueCountry=None,services=[] if index==0 else ['netflix'],devices=[],
        match=None,dataOrigin='fixture',updatedAt='2026-11-10T00:00:00Z')

FRESH=[dict(providerKey='ui_stub',coverage='partial',lastAttemptStatus='succeeded',
    lastSuccessfulAt='2026-11-10T00:00:00Z',dataOrigin='fixture')]
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        url=urlparse(self.path);query=parse_qs(url.query,keep_blank_values=True)
        value=lambda key,default:query.get(key,[default])[0]
        print(json.dumps({'path':url.path,'query':query},ensure_ascii=False),flush=True)
        chosen=value('categories','movie,ott').split(',')
        rows=[event(i) for i in range(2) if ('movie' if i==0 else 'ott') in chosen and value('country','KR')=='KR']
        code=200
        if url.path=='/v1/catalog/options':
            result=dict(contractVersion='0.1.0-draft.2',categories=['movie','ott','game','epl'],
                countries=['KR','US'],timeZones=['Asia/Seoul','UTC'],services=['netflix'],devices=['pc'],
                queryDefaults={'country':'KR','timeZone':'Asia/Seoul'})
        elif url.path=='/v1/calendar':
            month=value('month','2026-11');year,number=map(int,month.split('-'));days=[]
            for day in range(1,calendar.monthrange(year,number)[1]+1):
                date=f'{month}-{day:02d}';items=[e for e in rows if e['time']['date']==date]
                days.append(dict(date=date,total=len(items),previews=items[:2]))
            result=dict(month=month,catalogRevision='1',days=days,freshness=FRESH)
        elif url.path=='/v1/events':
            rows=[e for e in rows if value('from','2026-11-01')<=e['time']['date']<value('to','2026-12-01')]
            result=dict(catalogRevision='1',items=rows,nextCursor=None,freshness=FRESH)
        elif url.path.startswith('/v1/events/') and url.path.rsplit('/',1)[1] in IDS:
            index=IDS.index(url.path.rsplit('/',1)[1]);result=dict(event=event(index),
                sources=[dict(providerKey='ui_stub',url='https://example.invalid/ui-fixture',observedAt='2026-11-10T00:00:00Z',sourceUpdatedAt=None)],previousTime=None)
        else:code=404;result={'message':'stub route not supported'}
        raw=json.dumps(result,ensure_ascii=False).encode();self.send_response(code)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.end_headers();self.wfile.write(raw)

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    print('STUB_BASE_URL=http://127.0.0.1:'+str(server.server_port)+'/v1',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
