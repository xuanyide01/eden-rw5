const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..');
function script(name){return fs.readFileSync(path.join(root,'src/common',name+'.js'),'utf8').replace(/^import[^\n]*\n/gm,'').replace(/export /g,'');}
const api=new Function(['auto-reader','catalog','text-font','portrait-layout','progress','engine','saves','gallery','assets'].map(script).join('\n')+';return {autoSpeeds,autoWait,catalog,textFont,PROGRESS_KEY,emptyProgress,decodeProgress,progressFromState,withProgress,newState,checkpoint,restore,readFrame,readChapterSkip,next,nextChapter,choose,previous,previewMap,SLOT_COUNT,LEGACY_KEY,slotKey,decodeSave,createSave,slotRow,imagePath,frameLayer,baseLayer,frames,tiles,assets,groupGallery,galleryInfo,galleryLayer,stepVariant,portraitBox};')();
const operations={};for(const id of Object.keys(api.catalog.scenes)){operations[id]=[];const dir=path.join(root,'src/common/story',id);for(const f of fs.readdirSync(dir).sort((a,b)=>parseInt(a)-parseInt(b)))operations[id].push(...JSON.parse(fs.readFileSync(path.join(dir,f),'utf8')));}
function settle(s,skip){for(let i=0;i<1000;i++){const ops=operations[s.chapter],base=Math.floor(s.cursor/512)*512,part=ops.slice(base,base+512);const f=skip?api.readChapterSkip(part,s,skip,base,ops.length):api.readFrame(part,s,base,ops.length);if(!['yield','jump'].includes(f.type))return f;}throw Error('Reader did not settle');}
test('all 8860 Chinese messages replay in source order, including after a cleared replay',()=>{
 const proof=JSON.parse(fs.readFileSync(path.join(root,'reports/source-text-proof.json'),'utf8'));
 for(const cleared of [false,true]){
  const s=api.newState(1,true),actual=[];if(cleared)s.variables={'sf.eden_D001':1,'sf.eden_B003':1,'sf.eden_B006':1};
  for(let i=0;i<10000;i++){
   const f=settle(s);if(f.type==='end')break;assert.equal(f.type,'text');actual.push({scene:api.catalog.scenes[s.chapter].name,speaker:f.speaker,textSHA256:crypto.createHash('sha256').update(f.text).digest('hex')});
   if(i%71===0)Object.assign(s,api.decodeSave(JSON.stringify(api.createSave(s,'play',i))).state);api.next(s);
  }
  assert.ok(s.ended);assert.equal(s.chapter,21);assert.equal(s.variables['sf.eden_D001'],1);
  assert.equal(actual.length,8860);assert.deepEqual(actual,proof.map(({scene,speaker,textSHA256})=>({scene,speaker,textSHA256})));
 }
});
test('every chapter begins, skips to the next chapter, and can return to its previous frame',()=>{
 for(let id=1;id<=21;id++){
  const s=api.newState(id);assert.equal(settle(s).type,'text');const first=api.checkpoint(s);const f=settle(s,api.nextChapter(s));
  if(id<21){assert.equal(f.type,'text');assert.equal(s.rootChapter,id+1);}else assert.equal(f.type,'end');
  assert.ok(api.previous(s));assert.deepEqual(api.checkpoint(s),first);
 }
});
test('a pending choice cannot be bypassed by repeated chapter skipping',()=>{
 const s=api.newState();s.cursor=1;const ops=[{op:'text',text:'a'},{op:'choice',items:[{text:'b',to:2}]},{op:'text',text:'c'}];
 for(let i=0;i<4;i++){assert.equal(api.readChapterSkip(ops,s,api.nextChapter(s),0,3).type,'choice');assert.equal(s.cursor,1);}
});
test('all frame layers are bounded to two images and every referenced resource exists',()=>{
 for(const frame of Object.values(api.frames)){
  for(const name of [frame.base,frame.patch].filter(Boolean))assert.ok(fs.existsSync(path.join(root,'src/common/images',api.tiles[name].file)),name);
  if(frame.patch){const [x,y,w,h]=frame.box;assert.ok(x>=0&&y>=0&&w>0&&h>0&&x+w<=frame.size[0]&&y+h<=frame.size[1]);}
 }
 for(const ops of Object.values(operations))for(const op of ops)if(op.op==='text')assert.ok(api.frames[op.background]);
 for(const name of Object.keys(api.frames))for(const [w,h] of [[432,286],[432,432],[180,116]]){const p=api.frameLayer(name,w,h);assert.ok(p.left>=0&&p.top>=0&&p.left+p.width<=w+1&&p.top+p.height<=h+1);}
});
test('CG gallery preserves every declared difference and cycles within groups',()=>{
 const items=JSON.parse(fs.readFileSync(path.join(root,'reports/gallery-source.json'),'utf8')),groups=api.groupGallery(items);
 const report=JSON.parse(fs.readFileSync(path.join(root,'reports/conversion.json'),'utf8'));assert.equal(items.length,report.galleryVariants);assert.equal(groups.length,report.galleryGroups);
 for(const group of groups){assert.equal(api.stepVariant(group.variants.length-1,1,group.variants.length),0);for(const item of group.variants)assert.ok(api.frames[item.image]);}
});
function page(){
 const pending=[],timers=[],writes=[],scrolls=[];const source=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8').split('<script>')[1].split('</script>')[0].replace(/^import[^\n]*\n/gm,'').replace('export default','globalThis.page=');
 const context=vm.createContext({...api,file:{readText:o=>o.success({text:fs.readFileSync(path.join(root,'src',o.uri),'utf8')})},storage:{get:o=>pending.push(o),set:o=>writes.push(o)},prompt:{showToast(){}},console:{log(){},error(){}},Date,setTimeout:fn=>{timers.push(fn);return timers.length;},clearTimeout(){}});vm.runInContext(source,context);const p=context.page;Object.assign(p,p.private);p.$element=()=>({scrollTo:o=>scrolls.push(o)});p.onInit();pending.shift().success('');pending.shift().success('');p.textSpeed=0;return {p,pending,timers,writes,scrolls};
}
test('route and chapter first pages refresh correctly on repeated navigation',()=>{
 const {p}=page();for(let i=0;i<5;i++){p.openChapterRoutes();assert.equal(p.mode,'routes');const routeKeys=p.browseRows.map(x=>x.key);p.selectBrowse(0);assert.equal(p.mode,'chapters');assert.equal(p.browseRows[0].name,'序章');assert.ok(p.browseRows.every(x=>!routeKeys.includes(x.key)));const keys=p.browseRows.map(x=>x.key);p.nextBrowse();p.previousBrowse();assert.deepEqual(p.browseRows.map(x=>x.key),keys);p.closeBrowse();assert.equal(p.mode,'routes');p.closeBrowse();assert.equal(p.mode,'title');}
});
test('30 independent save slots load sequentially and stale callbacks are cancelled',()=>{
 const {p,pending,timers}=page();assert.equal(api.SLOT_COUNT,30);assert.equal(new Set(Array.from({length:30},(_,i)=>api.slotKey(i))).size,30);
 p.openSlots('load');const saved=JSON.stringify(api.createSave(api.newState(),'play',1000));
 for(let i=0;i<30;i++){assert.equal(pending.length,1);const call=pending.shift();assert.equal(call.key,api.slotKey(i));call.success(saved);if(i<29)timers.shift()();}
 assert.equal(p.loading,false);p.closeSlots();p.openSlots('load');const call=pending.shift();p.closeSlots();call.success('');assert.equal(pending.length,0);
 assert.match(api.slotKey(0),/^eden_rw5_/);assert.match(api.PROGRESS_KEY,/^eden_rw5_/);
});
test('long dialogue scroll never advances on drag; a fresh tap advances and resets its scroll',()=>{
 const {p,scrolls}=page();const proof=JSON.parse(fs.readFileSync(path.join(root,'reports/source-text-proof.json'),'utf8'));const longest=Object.entries(operations).flatMap(([id,ops])=>ops.map((op,cursor)=>({id,op,cursor}))).filter(x=>x.op.op==='text').sort((a,b)=>b.op.text.length-a.op.text.length)[0];
 assert.ok(longest.op.text.length>60);p.session=api.newState(Number(longest.id));p.session.cursor=longest.cursor;p.renderFrame();assert.equal(p.mode,'play');const cursor=p.session.cursor;
 p.dialogueTouchStart({touches:[{pageX:200,pageY:420}]});p.dialogueTouchMove({touches:[{pageX:200,pageY:350}]});p.dialogueTap();assert.equal(p.session.cursor,cursor);
 p.dialogueTouchStart({touches:[{pageX:200,pageY:360}]});p.dialogueTap();assert.equal(p.session.cursor,cursor+1);for(const value of scrolls){assert.equal(value.top,0);assert.equal(value.behavior,'instant');}
});
test('exit uses the platform app exit',()=>{const {p}=page();let exits=0;p.$app={exit(){exits++;}};p.exitApplication();assert.equal(exits,1);});

test('corrupt save locations are rejected',()=>{for(const cursor of [-1,1.5,100000])assert.throws(()=>api.restore({...api.newState(),cursor}));});


test('native text cards cover the reported B002 regression and empty-dialogue cards without raster glyphs',()=>{
 const entries=JSON.parse(fs.readFileSync(path.join(root,'reports/text-cards.json'),'utf8'));
 assert.equal(entries.length,57);for(const item of entries){assert.equal(item.rendering,'native-text');assert.deepEqual(api.frames[item.frame].card,{text:item.text,background:item.background,foreground:item.foreground});}
 const {p}=page();p.session=api.newState(3);p.session.cursor=39;p.cachedChapter=0;p.renderFrame();
 assert.equal(p.cardText,'我想在这里亲眼见证世界的终结——');assert.equal(p.cardBackground,'#ffffff');assert.equal(p.cardColor,'#000000');
 p.advance();assert.equal(p.cardText,'');p.goBack();assert.equal(p.cardText,'我想在这里亲眼见证世界的终结——');
 p.session=api.newState(3);p.session.cursor=51;p.cachedChapter=0;p.renderFrame();assert.equal(p.fullText,'');assert.equal(p.cardText,'逃离地球计划——');assert.equal(p.cardBackground,'#000000');
});

test('chapter codes remain internal and never appear in reader, chapter lists, gallery captions or slot metadata',()=>{
 const template=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8').split('<script>')[0];assert.ok(!template.includes('chapterLabel'));
 for(const chapter of api.catalog.chapters)assert.ok(!/[ABCD]\d{3}/.test(chapter.name));
 for(const item of JSON.parse(fs.readFileSync(path.join(root,'reports/gallery-source.json'),'utf8')))assert.ok(!/[ABCD]\d{3}/.test(item.label));
 const s=api.newState(3);s.cursor=39;const row=api.slotRow(0,api.createSave(s,'play',0));assert.equal(row.meta,'第 2 章');
});


test('title uses the original butterfly only after the original final clear flag is persisted',()=>{
 const {p,writes}=page();assert.equal(p.titleBackgroundSrc,'/common/ui/title.jpg');
 p.session=api.newState(21,true);p.session.cursor=88;p.cachedChapter=0;p.renderFrame();p.advance();assert.equal(p.mode,'end');assert.equal(p._progress.variables['sf.eden_D001'],1);p.toTitle();assert.equal(p.titleBackgroundSrc,'/common/ui/title-clear.jpg');
 const saved=writes.filter(x=>x.key===api.PROGRESS_KEY).at(-1);assert.ok(saved);const next=page();next.p._progress=api.decodeProgress(saved.value);next.p.refreshProgress();assert.equal(next.p.titleBackgroundSrc,'/common/ui/title-clear.jpg');next.p.startNew();assert.equal(next.p._progress.variables['sf.eden_D001'],1);next.p.toTitle();assert.equal(next.p.titleBackgroundSrc,'/common/ui/title-clear.jpg');
});

test('old cleared progress upgrades and unfinished chapter browsing keeps the normal title',()=>{
 const {p}=page();p._progress=api.decodeProgress(JSON.stringify({version:1,variables:{'sf.eden_A001':1,'sf.eden_B003':1}}));p.refreshProgress();assert.equal(p.titleBackgroundSrc,'/common/ui/title.jpg');
 p.session=api.newState(21);p.session.cursor=88;p.cachedChapter=0;p.renderFrame();p.advance();assert.equal(p.mode,'end');p.toTitle();assert.equal(p.titleBackgroundSrc,'/common/ui/title.jpg');
 p._progress=api.decodeProgress(JSON.stringify({version:1,variables:{'sf.eden_D001':1,'sf.eden_D002':1}}));p.refreshProgress();assert.equal(p.titleBackgroundSrc,'/common/ui/title-clear.jpg');
});
