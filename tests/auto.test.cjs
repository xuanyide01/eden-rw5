const {test}=require('node:test'),assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const script=name=>fs.readFileSync(path.join(root,'src/common',name+'.js'),'utf8').replace(/^import[^\n]*\n/gm,'').replace(/export /g,'');
const api=new Function(['auto-reader','catalog','text-font','portrait-layout','progress','engine','saves','gallery','assets'].map(script).join('\n')+';return {autoSpeeds,autoWait,frames,catalog,textFont,PROGRESS_KEY,emptyProgress,decodeProgress,progressFromState,withProgress,newState,checkpoint,restore,readFrame,readChapterSkip,next,nextChapter,choose,previous,previewMap,SLOT_COUNT,LEGACY_KEY,slotKey,decodeSave,createSave,slotRow,imagePath,frameLayer,baseLayer,groupGallery,galleryInfo,galleryLayer,stepVariant,portraitBox};')();
function harness(settings){
 let now=0,serial=0;const timers=new Map(),writes=[];let fixture=null;
 const source=fs.readFileSync(path.join(root,'src/pages/index/index.ux'),'utf8').split('<script>')[1].split('</script>')[0].replace(/^import[^\n]*\n/gm,'').replace('export default','globalThis.page=');
 const context=vm.createContext({...api,file:{readText:o=>o.success({text:fixture?JSON.stringify(fixture):fs.readFileSync(path.join(root,'src',o.uri),'utf8')})},storage:{get:o=>o.success(o.key==='eden_rw5_settings_v1'?JSON.stringify(settings||{textSpeed:0}):''),set:o=>{writes.push(o);o.success();}},prompt:{showToast(){}},console:{log(){},error(){}},Date,setTimeout:(fn,ms)=>{const id=++serial;timers.set(id,{fn,due:now+(ms||0)});return id;},clearTimeout:id=>timers.delete(id)});
 vm.runInContext(source,context);const p=context.page;Object.assign(p,p.private);p.$element=()=>({scrollTo(){}});p.$app={exit(){}};p.onInit();
 function tick(ms){const end=now+ms;for(let count=0;;count++){assert.ok(count<20000);const next=[...timers].filter(([,x])=>x.due<=end).sort((a,b)=>a[1].due-b[1].due||a[0]-b[0])[0];if(!next)break;now=next[1].due;timers.delete(next[0]);next[1].fn();}now=end;}
 function enable(){p.showMenu();p.toggleAuto();p.resume();}
 return {p,tick,enable,timers,writes,setFixture:v=>{fixture=v;},get now(){return now;}};
}
test('auto defaults off; delays are three distinct settings with extra long-text time',()=>{
 const h=harness(),p=h.p;p.startNew();const c=p.session.cursor;h.tick(10000);assert.equal(p.session.cursor,c);assert.equal(p.autoEnabled,false);
 assert.equal(api.autoWait(0,50),2600);assert.equal(api.autoWait(1,50),1500);assert.equal(api.autoWait(2,50),800);assert.ok(api.autoWait(1,78)>1500);
});
test('auto waits after completing 30ms typewriter even when manual text is instant',()=>{
 const h=harness(),p=h.p;p.startNew();h.enable();const cursor=p.session.cursor;h.tick(1499);assert.equal(p.session.cursor,cursor);h.tick(1);assert.ok(p.session.cursor>cursor);
 assert.ok(p.displayText.length<p.fullText.length);assert.equal(p._autoTimer,null);const c=p.session.cursor;h.tick((p.fullText.length-1)*30);assert.equal(p.displayText,p.fullText);assert.ok(p._autoTimer!=null);h.tick(1499);assert.equal(p.session.cursor,c);h.tick(1);assert.ok(p.session.cursor>c);
});
test('menus, slots, touch scrolling and background pause and resume with a fresh interval',()=>{
 const h=harness(),p=h.p;p.startNew();h.enable();const c=p.session.cursor;
 p.showMenu();h.tick(10000);assert.equal(p.session.cursor,c);p.resume();h.tick(1000);
 p.dialogueTouchStart({touches:[{pageX:200,pageY:430}]});p.dialogueTouchMove({touches:[{pageX:200,pageY:350}]});h.tick(10000);assert.equal(p.session.cursor,c);p.dialogueTouchEnd();p.dialogueTap();assert.equal(p.session.cursor,c);
 p.onHide();h.tick(10000);assert.equal(p.session.cursor,c);p.onShow();h.tick(1499);assert.equal(p.session.cursor,c);h.tick(1);assert.ok(p.session.cursor>c);
 p.showMenu();p.openSlots('load');h.tick(10000);assert.equal(p.mode,'slots');assert.equal(p._autoTimer,null);p.closeSlots();assert.equal(p.mode,'menu');
});
test('choices wait indefinitely for a real selection and resume auto afterwards',()=>{
 const h=harness(),p=h.p;
 h.setFixture([{op:'text',speaker:'',text:'甲',background:''},{op:'choice',items:[{text:'继续',to:2}]},{op:'text',speaker:'',text:'乙',background:''},{op:'end'}]);
 p.session=api.newState(1,true);p.cachedChapter=0;p.renderFrame();h.enable();h.tick(1500);assert.equal(p.mode,'choice');assert.equal(p.autoEnabled,true);assert.equal(p._autoTimer,null);h.tick(20000);assert.equal(p.session.cursor,1);
 p.pick(0);assert.equal(p.session.cursor,2);h.tick(1499);assert.equal(p.session.cursor,2);h.tick(1);assert.equal(p.mode,'end');assert.equal(p.autoEnabled,false);
});
test('manual complete restarts waiting, stale callbacks cannot advance, previous and title disable auto',()=>{
 const h=harness(),p=h.p;p.startNew();h.enable();const old=h.timers.get(p._autoTimer).fn;
 p.advance();const c=p.session.cursor;assert.ok(p.timer!=null);p.advance();assert.equal(p.displayText,p.fullText);const validTimer=p._autoTimer;old();assert.equal(p._autoTimer,validTimer);assert.equal(p.session.cursor,c);h.tick(1499);assert.equal(p.session.cursor,c);
 p.goBack();assert.equal(p.autoEnabled,false);h.tick(10000);assert.equal(p.session.cursor,c-1);p.showMenu();p.toggleAuto();p.resume();p.toTitle();assert.equal(p.autoEnabled,false);assert.equal(p._autoTimer,null);
});
test('speed persists, enabled status does not; failure and exit cancel pending work',()=>{
 const h=harness(),p=h.p;p.startNew();p.showMenu();p.toggleAuto();p.cycleAutoSpeed();p.resume();const value=JSON.parse(h.writes.findLast(o=>o.key==='eden_rw5_settings_v1').value);
 assert.equal(value.autoSpeed,2);assert.ok(!('autoEnabled'in value));const next=harness(value);assert.equal(next.p.autoSpeed,2);assert.equal(next.p.autoEnabled,false);
 p.fail('test');assert.equal(p.autoEnabled,false);assert.equal(p._autoTimer,null);assert.equal(p.mode,'error');p.exitApplication();assert.equal(p._autoTimer,null);
});
