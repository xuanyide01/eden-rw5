const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),crypto=require('crypto'),{execFileSync}=require('child_process');
const root=path.resolve(__dirname,'..'),out=path.join(root,'native-test-results'),log=path.resolve(root,'../eden-environment/emulator.log'),url='http://127.0.0.1:43140/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(p){const r=await fetch(url+p,{signal:AbortSignal.timeout(30000)});if(!r.ok)throw Error(await r.text());return r;}
async function wait(at,re){for(let i=0;i<120;i++){if(re.test(logs().slice(at)))return;await sleep(150);}throw Error('Gallery native timeout '+re);}
async function click(x,y,re){const at=logs().length;await request('click?x='+x+'&y='+y);if(re)await wait(at,re);await sleep(180);}
async function shot(name){await sleep(350);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('screen')).arrayBuffer()));}
const adb=path.resolve(root,'../starry-rw5/node_modules/@miwt/adb/bin/win/adb.exe');
function memory(label){const raw=execFileSync(adb,['-s','emulator-5580','shell','free'],{encoding:'utf8',windowsHide:true,timeout:30000}),row=raw.split('\n').find(x=>/Umem/.test(x));if(!row)throw Error('No virtual-device memory row');const values=row.trim().split(/\s+/).slice(0,5).map(Number);return {label,total:values[0],used:values[1],free:values[2],maxUsed:values[3],raw};}
(async()=>{const begin=logs().length,samples=[memory('title-before')];let cycles=0;
 const first=JSON.parse(fs.readFileSync(path.join(root,'src/common/gallery/0.txt'),'utf8'))[0];
 for(let run=0;run<12;run++){
  await click(110,374,/EDEN_RW5 gallery page 1\b/);if(run===0)await shot('gallery-low-memory');
  if(run%2===0){await click(108,146,/EDEN_RW5 cg 1 1 /);if(run===0)await shot('cg-low-memory');for(let i=1;i<=3;i++){await sleep(180);const variant=i%first.images.length+1;await click(216,205,new RegExp('EDEN_RW5 cg 1 '+variant+' '));cycles++;}await click(216,487,/EDEN_RW5 gallery page 1\b/);}
  else{await click(354,474,/EDEN_RW5 gallery page 2\b/);await click(64,474,/EDEN_RW5 gallery page 1\b/);}
  await click(216,474,/EDEN_RW5 background loaded title/);if(run===5||run===11){await sleep(500);samples.push(memory('title-after-'+(run+1)));}if((run+1)%4===0)console.log('GALLERY_REENTRY',run+1);
 }
 const groups=[];for(let page=0;page<74;page++)groups.push(...JSON.parse(fs.readFileSync(path.join(root,'src/common/gallery',page+'.txt'),'utf8')));
 const worst=groups.map((g,i)=>({g,i})).sort((a,b)=>b.g.images.length-a.g.images.length)[0],page=Math.floor(worst.i/4);
 await click(110,374,/EDEN_RW5 gallery page 1\b/);for(let i=1;i<=page;i++)await click(354,474,new RegExp('EDEN_RW5 gallery page '+(i+1)+'\\b'));
 await click(worst.i%2?312:108,worst.i%4<2?146:330,new RegExp('EDEN_RW5 cg '+(worst.i+1)+' 1 '));await shot('gallery-largest-group');samples.push(memory('largest-group-first-image'));
 for(let i=1;i<=worst.g.images.length;i++){await sleep(180);const variant=i%worst.g.images.length+1;await click(216,205,new RegExp('EDEN_RW5 cg '+(worst.i+1)+' '+variant+' '));cycles++;if(i%25===0)console.log('LARGEST_GROUP_DIFFERENCES',i);}
 samples.push(memory('largest-group-after-wrap'));await click(216,487,new RegExp('EDEN_RW5 gallery page '+(page+1)+'\\b'));await click(216,474,/EDEN_RW5 background loaded title/);await sleep(750);samples.push(memory('title-after-stress'));
 const recent=logs().slice(begin);assert.ok(!/EDEN_RW5 error|EDEN_RW5 cg failed|background failed|ASSERTION FAILED|PANIC!!!|coredump|NuttShell \(NSH\)/.test(recent));
 const warm=samples.find(x=>x.label==='title-after-6').used,after=samples.find(x=>x.label==='title-after-12').used;assert.ok(after-warm<1024*1024,'Repeated open/close retains over 1 MiB beyond the warmed state');
 const m=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')),data=fs.readFileSync(path.join(root,'dist',m.package+'.debug.'+m.versionName+'.rpk'));
 const report={result:'passed',packageSha256:crypto.createHash('sha256').update(data).digest('hex'),runtime:'official generic Vela virtual watch; not REDMI Watch 5 firmware',physicalDeviceRetestPending:true,reentries:12,differenceCycles:cycles,largestGroup:{index:worst.i+1,label:worst.g.label,differences:worst.g.images.length,wrapped:true},warmReentryUsedByteChange:after-warm,memorySamples:samples,sourceAtlasRGBAOnlyBudget:1146880,realDevicePeakNotMeasured:true};
 fs.writeFileSync(path.join(out,'gallery-stress-report.json'),JSON.stringify(report,null,2));console.log('GALLERY_STRESS_PASSED',JSON.stringify({...report,memorySamples:samples.map(({raw,...x})=>x)}));
})().catch(e=>{fs.writeFileSync(path.join(out,'gallery-stress-failure.txt'),e.stack);console.error(e.stack);process.exitCode=1;});
