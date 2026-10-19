const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),script=n=>fs.readFileSync(path.join(root,'src/common',n+'.js'),'utf8').replace(/^import[^\n]*\n/gm,'').replace(/export /g,'');
const api=new Function(['auto-reader','catalog','text-font','portrait-layout','progress','engine','saves','gallery','assets'].map(script).join('\n')+';return {autoSpeeds,autoWait,frames,tiles,catalog,textFont,PROGRESS_KEY,emptyProgress,decodeProgress,progressFromState,withProgress,newState,checkpoint,restore,readFrame,readChapterSkip,next,nextChapter,choose,previous,previewMap,SLOT_COUNT,LEGACY_KEY,slotKey,decodeSave,createSave,slotRow,imagePath,frameLayer,baseLayer,groupGallery,galleryInfo,galleryLayer,stepVariant,portraitBox};')();
function harness(hold){let now=100000,id=0;const timers=new Map(),reads=[],held=[],toasts=[];const source=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8').split('<script>')[1].split('</script>')[0].replace(/^import[^\n]*\n/gm,'').replace('export default','globalThis.page=');
 class ClockDate extends Date{static now(){return now;}}
 const context=vm.createContext({...api,Date:ClockDate,console:{log(){},error(){}},file:{readText:o=>{reads.push(o.uri);const deliver=()=>o.success({text:fs.readFileSync(path.join(root,'src',o.uri),'utf8')});if(hold)held.push(deliver);else deliver();}},storage:{get:o=>o.success(''),set:o=>o.success()},prompt:{showToast:o=>toasts.push(o.message)},setTimeout:(fn,ms)=>{const n=++id;timers.set(n,{fn,due:now+(ms||0)});return n;},clearTimeout:n=>timers.delete(n)});
 vm.runInContext(source,context);const p=context.page;Object.assign(p,p.private);p.$element=()=>({scrollTo(){}});p.$app={exit(){}};p.onInit();
 function tick(ms){const until=now+ms;for(let i=0;;i++){assert.ok(i<1000);const x=[...timers].filter(([,t])=>t.due<=until).sort((a,b)=>a[1].due-b[1].due)[0];if(!x)break;now=x[1].due;timers.delete(x[0]);x[1].fn();}now=until;}
 function decoded(){p.cgImageLoaded(1);if(p.cgPatchTile.src)p.cgImageLoaded(2);}
 return {p,tick,reads,held,toasts,timers,decoded};}

test('all gallery entries survive paging while each read is under 16KB and the grid uses one first-variant contact sheet',()=>{
 const original=JSON.parse(fs.readFileSync(path.join(root,'reports/gallery-source.json'),'utf8')),groups=api.groupGallery(original);let count=0;
 for(let i=0;i<api.galleryInfo.pages;i++){const bytes=fs.readFileSync(path.join(root,'src/common/gallery',i+'.txt'));assert.ok(bytes.length<16384);const rows=JSON.parse(bytes);assert.ok(rows.length<=4);for(let j=0;j<rows.length;j++){const g=groups[i*4+j];assert.equal(rows[j].label,g.label);assert.deepEqual(rows[j].images,g.variants.map(v=>v.image));count+=rows[j].images.length;}}
 assert.equal(count,2341);assert.equal(groups.length,295);assert.ok(!fs.existsSync(path.join(root,'src/common/gallery.txt')));
 const ux=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8');const gallery=ux.split("mode === 'gallery'")[1].split("mode === 'cg'")[0];assert.equal((gallery.match(/<image /g)||[]).length,1);assert.ok(gallery.includes('gallery-sheet'));assert.ok(!gallery.includes('image-source'));
 const previews=JSON.parse(fs.readFileSync(path.join(root,'reports/gallery-thumbnails.json'),'utf8'));assert.equal(previews.pageCount,api.galleryInfo.pages);assert.equal(previews.thumbnailImageWidgetsPerPage,1);for(let i=0;i<previews.pages.length;i++){assert.deepEqual(previews.pages[i].size,[198,184]);assert.deepEqual(previews.pages[i].firstImagesOnly,groups.slice(i*4,i*4+4).map(g=>g.variants[0].image));}
 for(const x of original)for(const patch of [false,true]){const layer=api.galleryLayer(x.image,patch);if(!layer.src)continue;assert.ok(layer.imageWidth<=280&&layer.imageHeight<=512);assert.ok(layer.left>=0&&layer.top>=0&&layer.left+layer.width<=432&&layer.top+layer.height<=432);}
});

test('gallery reads just the current page, releases prior widgets, and serializes image decoding',()=>{
 const h=harness(),p=h.p;p.openGallery();h.tick(69);assert.equal(h.reads.length,0);h.tick(1);assert.deepEqual(h.reads,['/common/gallery/0.txt']);assert.equal(p.galleryRows.length,4);assert.equal(p.loading,false);assert.ok(!('base'in p.galleryRows[0]));assert.equal(p.galleryTop.length,2);assert.equal(p.galleryBottom.length,2);assert.equal(p.galleryPreviewSrc,'/common/gallery-preview/0.jpg');
 p.viewCg(0);assert.equal(p.cgReady,false);h.tick(70);assert.equal(p.cgReady,true);assert.equal(p.loading,true);p.cycleCg();assert.equal(p.cgVariant,0);h.decoded();assert.equal(p.loading,false);p.cycleCg();assert.equal(p.cgVariant,0);h.tick(150);p.cycleCg();assert.equal(p.cgReady,false);h.tick(70);h.decoded();assert.equal(p.cgVariant,1);
 p.backToGallery();assert.equal(p.cgReady,false);assert.equal(p.cgTile.src,'');assert.equal(p.mode,'gallery');p.nextGalleryPage();h.tick(70);assert.equal(h.reads.at(-1),'/common/gallery/1.txt');assert.equal(p.galleryRows[0].index,4);
});

test('stale file callbacks and image timers cannot resurrect a closed gallery',()=>{
 const h=harness(true),p=h.p;p.openGallery();h.tick(70);assert.equal(h.held.length,1);p.toTitle();h.held.shift()();assert.equal(p.mode,'title');assert.equal(p.galleryRows.length,0);assert.equal(p.galleryPreviewSrc,'');assert.equal(p.galleryTop.length,0);assert.equal(p.cgReady,false);
 p.openGallery();h.tick(70);h.held.shift()();p.viewCg(0);p.toTitle();h.tick(20000);assert.equal(p.mode,'title');assert.equal(p.cgReady,false);assert.equal(h.timers.size,0);
});

test('background pauses pending gallery work, and failed decode returns control without a crash',()=>{
 const h=harness(),p=h.p;p.openGallery();p.onHide();h.tick(1000);assert.equal(h.reads.length,0);p.onShow();h.tick(70);assert.equal(p.mode,'gallery');p.viewCg(0);h.tick(70);assert.equal(p.loading,true);h.tick(10000);assert.equal(p.loading,false);assert.equal(p.cgReady,false);assert.equal(h.toasts.length,1);p.backToGallery();assert.equal(p.mode,'gallery');assert.ok(p.galleryRows.length>0);
});
