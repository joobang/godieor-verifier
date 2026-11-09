// Independent smoke recipe; its observations do not satisfy the full acceptance suite.
const { createRequire } = require('node:module');
const { join } = require('node:path');
const assert = require('node:assert/strict');
const req = createRequire(join(process.cwd(), 'package.json'));
req('reflect-metadata');
const { NestFactory } = req('@nestjs/core');
const { AppModule } = req('./dist/src/app.module');
const { configureHttp } = req('./dist/src/common/configure-http');
const { CollectionService } = req('./dist/src/collection/collection.service');
(async () => {
  let app;
  try {
    app = await NestFactory.create(AppModule, { logger: false });
    configureHttp(app);
    await app.listen(0, '127.0.0.1');
    const service = app.get(CollectionService);
    const result = await service.collect('backfill');
    assert.ok(result.length > 0 && result.every(r => r.status === 'succeeded'));
    const base = await app.getUrl();
    const read = async path => {
      const r = await fetch(base+'/v1'+path);
      assert.equal(r.status,200);return r.json();
    };
    const before = await read('/events?schedule=dated&from=2026-11-01&to=2026-12-01');
    assert.ok(before.items.length > 0);
    await service.collect('backfill');
    const after = await read('/events?schedule=dated&from=2026-11-01&to=2026-12-01');
    assert.deepEqual(after.items.map(x=>x.id),before.items.map(x=>x.id));
    const calendar = await read('/calendar?month=2026-11&categories=movie,ott');
    assert.equal(calendar.days.length,30);
    const item = before.items[0];
    assert.equal((await read('/events/'+item.id)).event.id,item.id);
    console.log('PASS smoke: migration/Nest DI/fixture repeat IDs/calendar/detail; synthetic data only');
  } finally { if(app) await app.close(); }
})().catch(e=>{console.error(e.name+': smoke failed');process.exitCode=1;});
