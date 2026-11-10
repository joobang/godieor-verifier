// Independent verifier-owned synthetic input and expectations, not product fixtures.
const {createRequire}=require('node:module');
const {join}=require('node:path');
const assert=require('node:assert/strict');
const req=createRequire(join(process.cwd(),'package.json'));
req('reflect-metadata');
const {NestFactory}=req('@nestjs/core');
const {AppModule}=req('./dist/src/app.module');
const {configureHttp}=req('./dist/src/common/configure-http');
const {CollectionService}=req('./dist/src/collection/collection.service');
const {CollectionRepository}=req('./dist/src/collection/collection.repository');
const suite=process.argv[2];
if(!['event-identity','time-semantics','api-filter-observations'].includes(suite)) process.exit(2);
const date=value=>({type:'date_only',value});
const instant=value=>({type:'instant',value,sourceTimeZone:null});
function record(id,kind='theatrical_release',market='KR',time=date('2026-11-06')) {
  return {externalId:id,variantKey:'release',kind,title:'Synthetic '+id,
    content:kind==='epl_match'?null:{externalId:'same-'+kind,kind:kind==='theatrical_release'?'movie':kind==='ott_season_premiere'?'drama':'game',title:'Same synthetic work'},
    seasonNumber:kind==='ott_season_premiere'?1:null,status:'scheduled',time,market,
    venueCountry:kind==='epl_match'?'GB':null,
    services:kind==='ott_season_premiere'?['netflix']:[],devices:kind==='game_release'?['pc']:[],
    home:kind==='epl_match'?{externalId:'home',name:'Synthetic Home'}:null,
    away:kind==='epl_match'?{externalId:'away',name:'Synthetic Away'}:null,
    sourceUrl:'https://example.invalid/verifier/'+id,sourceUpdatedAt:null};
}
const inputs=[
  {...record('same-title-a','theatrical_release','KR',date('2026-12-10')),title:'Synthetic same-title',content:{externalId:'work-a',kind:'movie',title:'Same title'}},
  {...record('same-title-b','theatrical_release','KR',date('2026-12-11')),title:'Synthetic same-title',content:{externalId:'work-b',kind:'movie',title:'Same title'}},
  {...record('ott-season3','ott_season_premiere','KR',date('2026-12-12')),externalId:'ott-netflix',variantKey:'season-3',seasonNumber:3},
  record('movie-kr'),record('movie-us','theatrical_release','US'),
  record('movie-day2','theatrical_release','KR',date('2026-11-07')),
  record('ott-netflix','ott_season_premiere'),
  {...record('ott-disney','ott_season_premiere'),services:['disney_plus']},
  {...record('ott-multi','ott_season_premiere'),services:['netflix','tving'],seasonNumber:2},
  record('game-pc','game_release'),{...record('game-console','game_release'),devices:['playstation','xbox']},
  record('kst-rollover','epl_match',null,instant('2026-11-06T20:00:00Z')),
  record('month-rollover','epl_match',null,instant('2026-10-31T16:30:00Z')),
  record('spring-before','epl_match',null,instant('2026-03-29T00:30:00Z')),
  record('spring-after','epl_match',null,instant('2026-03-29T01:30:00Z')),
  record('fold-first','epl_match',null,instant('2026-10-25T00:30:00Z')),
  record('fold-second','epl_match',null,instant('2026-10-25T01:30:00Z')),
  record('unknown','theatrical_release','KR',{type:'unknown',announcedYear:2027,announcedPeriod:'Q3'}),
  record('old-unknown','theatrical_release','KR',{type:'unknown',announcedYear:2025,announcedPeriod:null})];
const category={theatrical_release:'movie',ott_season_premiere:'ott',game_release:'game',epl_match:'epl'};
let current=structuredClone(inputs),failMovie=false,app,assertions=0;
function equal(a,b,message){assertions++;assert.deepEqual(a,b,message);}
function ok(value,message){assertions++;assert.ok(value,message);}
const adapter={key:'verifier_api',name:'Verifier synthetic adapter',origin:'fixture',
  scopes:[{category:'movie',market:'KR'},{category:'movie',market:'US'},{category:'ott',market:'KR'},
    {category:'game',market:'KR'},{category:'epl',market:'WORLD'}],
  async fetch(scope){if(failMovie&&scope.category==='movie')throw Error('synthetic failure');
    return structuredClone(current.filter(r=>category[r.kind]===scope.category&&(r.market===scope.market||(r.kind==='epl_match'&&scope.market==='WORLD'))));}};
async function main(){
 app=await NestFactory.create(AppModule,{logger:false});configureHttp(app);await app.listen(0,'127.0.0.1');
 const collector=new CollectionService(app.get(CollectionRepository),[adapter]);await collector.onModuleInit();
 async function collect(){const outcomes=await collector.collect('backfill');ok(outcomes.every(x=>x.status==='succeeded'),'synthetic input publication');}
 await collect();const base=await app.getUrl();
 async function http(path,params={},expected=200){const u=new URL(base+'/v1'+path);for(const[k,v]of Object.entries(params))if(v!==undefined)u.searchParams.set(k,String(v));const response=await fetch(u);equal(response.status,expected,'HTTP '+u.pathname);return response.json();}
 async function list(params={}){let result=[],cursor=null,seen=new Set();do{const page=await http('/events',{schedule:'dated',from:'2026-11-01',to:'2026-11-09',timeZone:'UTC',...params,...(cursor?{cursor}:{})});for(const r of page.items){ok(!seen.has(r.id),'no duplicate across pages');seen.add(r.id);result.push(r);}cursor=page.nextCursor;ok(result.length<200,'bounded cursor traversal');}while(cursor);return result;}
 async function detail(id,zone='UTC'){return http('/events/'+id,{timeZone:zone});}
 const names=rows=>rows.map(x=>x.title.replace('Synthetic ','')).sort();
 const novExpected=['game-console','game-pc','kst-rollover','movie-day2','movie-kr','ott-disney','ott-multi','ott-netflix'];
 const initial=await list({limit:2});equal(names(initial),novExpected.slice().sort(),'independently authored November membership');
 const ids=Object.fromEntries(initial.map(x=>[x.title.replace('Synthetic ',''),x.id]));
 if(suite==='event-identity'){
   equal(new Set(initial.map(x=>x.id)).size,8,'different event identities');
   const aliases=await list({from:'2026-12-10',to:'2026-12-12',categories:'movie'});
   equal(names(aliases),['same-title','same-title']);equal(new Set(aliases.map(x=>x.id)).size,2,'same titles never identify events');equal(new Set(aliases.map(x=>x.contentId)).size,2,'same titles never identify works');
   const third=await list({from:'2026-12-12',to:'2026-12-13',categories:'ott'});equal(names(third),['ott-season3']);ok(third[0].id!==ids['ott-netflix'],'variant key keeps season event distinct');equal(third[0].season.number,3);
   const us=await list({country:'US',categories:'movie'});equal(names(us),['movie-us']);ok(us[0].id!==ids['movie-kr'],'market split');
   equal(us[0].contentId,initial.find(x=>x.id===ids['movie-kr']).contentId,'same work preserves market events');
   const dramas=initial.filter(x=>x.kind==='ott_season_premiere');equal(new Set(dramas.map(x=>x.contentId)).size,1);equal(new Set(dramas.map(x=>x.id)).size,3);
   equal((await detail(ids['ott-multi'])).event.services,['netflix','tving'],'confirmed multi-service single event');
   await collect();equal((await list({limit:1})).map(x=>x.id),initial.map(x=>x.id),'repeat collection stable ordering and IDs');
   const oldCalendar=await http('/calendar',{month:'2026-11',categories:'movie'});
   const movie=current.find(x=>x.externalId==='movie-kr');movie.time=date('2026-11-08');movie.status='postponed';await collect();
   let changed=await detail(ids['movie-kr']);equal(changed.event.id,ids['movie-kr']);equal(changed.event.status,'postponed');equal(changed.event.time,{type:'date_only',date:'2026-11-08'});equal(changed.previousTime,{type:'date_only',date:'2026-11-06'});
   equal((await list({categories:'movie'})).length,2,'correction does not add a new event');
   await http('/events',{schedule:'dated',from:'2026-11-01',to:'2026-11-09',categories:'movie',catalogRevision:oldCalendar.catalogRevision},409);
   movie.status='cancelled';await collect();equal((await detail(ids['movie-kr'])).event.status,'cancelled');
   const before=await http('/calendar',{month:'2026-11',categories:'movie'});const fresh=before.freshness.find(x=>x.providerKey==='verifier_api');ok(fresh.lastSuccessfulAt,'successful collection time');
   failMovie=true;const failed=await collector.collect('backfill');ok(failed.some(x=>x.category==='movie'&&x.status==='failed'));
   const after=await http('/calendar',{month:'2026-11',categories:'movie'});const preserved=after.freshness.find(x=>x.providerKey==='verifier_api');equal(preserved.lastSuccessfulAt,fresh.lastSuccessfulAt);equal(preserved.lastAttemptStatus,'failed');equal((await detail(ids['movie-kr'])).event.time,changed.event.time);
 } else if(suite==='time-semantics'){
   equal((await detail(ids['kst-rollover'],'Asia/Seoul')).event.time,{type:'instant',instantUtc:'2026-11-06T20:00:00.000Z',sourceTimeZone:null,displayDate:'2026-11-07',displayTime:'05:00'});
   for(const zone of ['UTC','Asia/Seoul','America/Los_Angeles'])equal((await detail(ids['movie-kr'],zone)).event.time,{type:'date_only',date:'2026-11-06'});
   const undated=await list({schedule:'undated',from:undefined,to:undefined});
   equal(names(undated),['unknown']);equal(undated[0].time,{type:'unknown',announcedYear:2027,announcedPeriod:'Q3'});
   const calendar=await http('/calendar',{month:'2026-11',timeZone:'Asia/Seoul'});
   equal(calendar.days.reduce((sum,d)=>sum+d.total,0),9,'unknown excluded, rollover included');
   ok(!calendar.days.some(d=>d.previews.some(e=>e.id===undated[0].id)),'unknown has no calendar day');
   const kstDay=await list({from:'2026-11-06',to:'2026-11-07',timeZone:'Asia/Seoul'});
   ok(!kstDay.some(e=>e.id===ids['kst-rollover']),'exclusive KST day boundary');
   const utcDay=await list({from:'2026-11-06',to:'2026-11-07',timeZone:'UTC'});
   ok(utcDay.some(e=>e.id===ids['kst-rollover']),'same instant belongs to previous UTC day');
   const spring=await list({from:'2026-03-29',to:'2026-03-30',timeZone:'Europe/London',categories:'epl'});
   equal(names(spring),['spring-after','spring-before']);
   equal(spring.find(e=>e.title==='Synthetic spring-before').time.displayTime,'00:30');
   equal(spring.find(e=>e.title==='Synthetic spring-after').time.displayTime,'02:30');
   const fold=await list({from:'2026-10-25',to:'2026-10-26',timeZone:'Europe/London',categories:'epl'});
   equal(names(fold),['fold-first','fold-second']);equal(fold.map(e=>e.time.displayTime),['01:30','01:30']);
   equal(new Set(fold.map(e=>e.id)).size,2,'DST fold keeps separate instants');
   equal(fold.map(e=>e.time.instantUtc),['2026-10-25T00:30:00.000Z','2026-10-25T01:30:00.000Z']);
   const roll=await list({from:'2026-11-01',to:'2026-11-02',timeZone:'Asia/Seoul',categories:'epl'});
   equal(names(roll),['month-rollover']);equal(roll[0].time.displayTime,'01:30');
   equal(names(await list({from:'2026-11-01',to:'2026-11-02',timeZone:'UTC',categories:'epl'})),[]);
 } else {
   equal(names(await list({categories:'ott',services:'netflix'})),['ott-multi','ott-netflix']);
   equal(names(await list({categories:'ott',services:'netflix,disney_plus'})),['ott-disney','ott-multi','ott-netflix']);
   equal(names(await list({categories:'game',devices:'playstation'})),['game-console']);
   equal(names(await list({categories:'game',devices:'pc,xbox'})),['game-console','game-pc']);
   equal(names(await list({categories:'movie,ott',services:'netflix',devices:'switch'})),['movie-day2','movie-kr','ott-multi','ott-netflix']);
   equal(names(await list({categories:'epl',services:'netflix',devices:'switch',country:'JP'})),['kst-rollover']);
   equal(names(await list({categories:'game',devices:'switch'})),[]);
   equal(names(await list({categories:'movie',country:'US'})),['movie-us']);
   await http('/events',{schedule:'dated',from:'2026-11-01',to:'2026-11-09',services:'unrecognized'},400);
 }
 await app.close();app=null;console.log(JSON.stringify({schema_version:1,suite,status:'PASS',scope:'backend-api-synthetic',assertions}));
}
main().catch(async error=>{if(app)await app.close();console.error(error instanceof assert.AssertionError?error.message:'API check execution failed');process.exitCode=1;});
