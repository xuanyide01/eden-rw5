const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),out=path.join(root,'native-test-results'),url='http://127.0.0.1:43140';
const log=path.resolve(root,'../eden-environment/emulator.log');fs.mkdirSync(out,{recursive:true});
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(endpoint,timeout=30000){const r=await fetch(url+'/'+endpoint,{signal:AbortSignal.timeout(timeout)});if(!r.ok)throw Error(await r.text());return r;}
async function click(x,y){await request('click?x='+x+'&y='+y);await sleep(170);}
async function wait(at,re){for(let i=0;i<120;i++){const text=logs().slice(at);if(re.test(text))return text;await sleep(200);}throw Error('Native timeout '+re);}
async function expected(x,y,re){const at=logs().length;await click(x,y);return wait(at,re);}
async function shot(name){await sleep(400);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('screen')).arrayBuffer()));}
async function saveSlot(x,y,number){const at=logs().length;await click(x,y);await wait(at,new RegExp('EDEN_RW5 (slot saved '+number+' |overwrite '+number+'\\b)'));if(new RegExp('EDEN_RW5 overwrite '+number+'\\b').test(logs().slice(at)))await expected(216,215,new RegExp('EDEN_RW5 slot saved '+number+' 1 86'));}
async function menu(){await expected(216,488,/EDEN_RW5 menu/);}
async function title(){await menu();await expected(216,462,/EDEN_RW5 background loaded title/);}
async function chapter(id){await click(110,236);await click(216,126);for(let i=0;i<Math.floor((id-1)/4);i++)await click(354,474);await expected(216,126+(id-1)%4*92,new RegExp('EDEN_RW5 frame '+id+' '));}
async function firstPlay(){await expected(110,190,/EDEN_RW5 frame 1 2/);}
function currentCursor(id){const matches=[...logs().matchAll(new RegExp('EDEN_RW5 frame '+id+' (\\d+)','g'))];return Number(matches.at(-1)[1]);}
async function walkUntil(id,target){for(let i=0;currentCursor(id)<target;i++){assert.ok(i<1000);await expected(354,488,new RegExp('EDEN_RW5 frame '+id+' '));}assert.equal(currentCursor(id),target);}
(async()=>{
 const begin=logs().length,checks=[];
 await shot('title');
 // Instant text and large type allow the native long-paragraph scroll to be tested.
 if(!process.argv.includes('--configured')){await click(110,328);await click(216,126);await click(216,185);await shot('settings');await expected(216,243,/EDEN_RW5 background loaded title/);}
 await firstPlay();await shot('opening');await walkUntil(1,13);await shot('text-card');checks.push('native system-font text card is readable and dialogue has no white separator');
 await walkUntil(1,86);
 await shot('story-patch');checks.push('native full-frame and local-patch story images display');
 await menu();await expected(216,94,/EDEN_RW5 slots ready save/);await saveSlot(216,402,4);
 await menu();await expected(216,94,/EDEN_RW5 slots ready save/);for(let i=0;i<6;i++)await click(354,474);await saveSlot(216,310,27);
 await expected(354,488,/EDEN_RW5 frame 1 87/);await menu();await expected(216,140,/EDEN_RW5 slots ready load/);for(let i=0;i<6;i++)await click(354,474);await expected(216,310,/EDEN_RW5 slot loaded 27 1 86/);
 checks.push('new native saves 04 and 27 work; baseline 0.1.0 slots 01 and 30 remain untouched');
 await menu();await expected(216,324,/EDEN_RW5 auto enabled true/);
 const speeds=[];for(let i=0;i<3;i++){const t=await expected(216,370,/EDEN_RW5 auto speed [012]/);speeds.push(Number(t.match(/EDEN_RW5 auto speed ([012])/)[1]));}assert.deepEqual([...speeds].sort(),[0,1,2]);for(let i=0;i<2&&speeds.at(-1)!==1;i++){const t=await expected(216,370,/EDEN_RW5 auto speed [012]/);speeds.push(Number(t.match(/EDEN_RW5 auto speed ([012])/)[1]));}
 await shot('auto-menu');let autoAt=logs().length;await click(216,416);await wait(autoAt,/EDEN_RW5 auto advance/);
 await menu();autoAt=logs().length;await sleep(3000);assert.ok(!/EDEN_RW5 auto advance|EDEN_RW5 frame/.test(logs().slice(autoAt)));
 await expected(216,140,/EDEN_RW5 slots ready load/);autoAt=logs().length;await sleep(2000);assert.ok(!/EDEN_RW5 auto advance|EDEN_RW5 frame/.test(logs().slice(autoAt)));
 await click(216,474);autoAt=logs().length;await click(216,416);await wait(autoAt,/EDEN_RW5 auto advance/);
 await click(65,488);const stopped=currentCursor(1);autoAt=logs().length;await sleep(3000);assert.equal(currentCursor(1),stopped);assert.ok(!/EDEN_RW5 auto advance/.test(logs().slice(autoAt)));
 await menu();await shot('auto-stopped-menu');await expected(216,462,/EDEN_RW5 background loaded title/);
 checks.push('native auto speed cycles three settings, advances after typing, pauses in menu and slots, resumes, and previous disables it');
 await chapter(3);await shot('text-card-b002-start');await walkUntil(3,39);await shot('regression-after');await expected(216,140,/EDEN_RW5 frame 3 40/);await title();await chapter(18);await walkUntil(18,4);await shot('text-card-long');await title();checks.push('reported B002 card and long native card wrap clearly; tapping text card advances; chapter debug code is absent');
 await chapter(2);await walkUntil(2,40);await shot('corrected-camera');await title();checks.push('oversized 16:10 source uses original 1024x640 camera window');
 // Repeatedly enter and leave the first route and chapter page without paging to refresh.
 for(let i=0;i<3;i++){await click(110,236);await shot('route-first-'+i);await click(216,126);await shot('chapter-first-'+i);await click(216,474);await shot('route-back-'+i);await expected(216,474,/EDEN_RW5 background loaded title/);}
 checks.push('native route/chapter first pages refresh repeatedly');
 await chapter(9);await walkUntil(9,15);
 await shot('long-text-top');let at=logs().length;await request('drag?x0=210&y0=440&x1=210&y1=345');await sleep(500);const scrolled=logs().slice(at);assert.match(scrolled,/EDEN_RW5 dialogue scroll 9 15 [1-9]/);assert.ok(!/EDEN_RW5 frame/.test(scrolled));await shot('long-text-bottom');
 await expected(210,370,/EDEN_RW5 frame 9 16/);await shot('text-next-reset');await title();checks.push('native long Chinese paragraph wraps and scrolls; drag does not advance and a fresh tap does');
 await firstPlay();
 for(let id=1;id<=21;id++){await menu();await expected(216,186,id===21?/EDEN_RW5 ending 21/:new RegExp('EDEN_RW5 frame '+(id+1)+' '));if(id%5===0)console.log('CHAPTER_SKIP',id);}
 await shot('ending');await expected(216,280,/EDEN_RW5 background loaded title/);checks.push('all 21 native chapter skips follow the original sequence and reach the ending');
 await expected(110,374,/EDEN_RW5 gallery ready 295 2341/);await shot('gallery');await expected(108,146,/EDEN_RW5 cg 1 1/);await shot('cg');await expected(216,205,/EDEN_RW5 cg 1 2/);await shot('cg-difference');
 await click(216,487);await expected(216,474,/EDEN_RW5 background loaded title/);checks.push('native grouped gallery and difference cycling work');
 await expected(110,420,/EDEN_RW5 app destroyed/);await sleep(2500);at=logs().length;await request('start',90000);await wait(at,/EDEN_RW5 background loaded title/);await wait(at,/PageCallHook, name:onShow/);await sleep(600);await shot('title-after-reopen');
 await expected(110,282,/EDEN_RW5 slots ready load/);await expected(216,126,/EDEN_RW5 slot loaded 1 1 86/);await shot('save-after-reopen');await title();checks.push('native platform EXIT, process restart and persisted slot 01 reload work');
 assert.ok(!/EDEN_RW5 error|EDEN_RW5 background failed|ASSERTION FAILED|PANIC!!!|coredump/.test(logs().slice(begin)));
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')),rpk=path.join(root,'dist',manifest.package+'.debug.'+manifest.versionName+'.rpk');
 const report={result:'passed',runtime:'official vela-watch-5.0 generic emulator; not REDMI Watch 5 firmware',screen:[432,514],packageBytes:fs.statSync(rpk).size,packageSha256:crypto.createHash('sha256').update(fs.readFileSync(rpk)).digest('hex'),physicalDeviceTested:false,checks};
 fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log('NATIVE_PASSED',JSON.stringify(report));
})().catch(e=>{fs.writeFileSync(path.join(out,'failure.txt'),e.stack);console.error(e.stack);process.exitCode=1;});
