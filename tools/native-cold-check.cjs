const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'native-test-results'),log=path.resolve(root,'../eden-environment/emulator.log'),url='http://127.0.0.1:43140/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function request(endpoint){const r=await fetch(url+endpoint,{signal:AbortSignal.timeout(40000)});if(!r.ok)throw Error(await r.text());return r;}
async function wait(at,re){for(let i=0;i<120;i++){const text=fs.readFileSync(log,'utf8').slice(at);if(re.test(text))return;await sleep(200);}throw Error('Timeout '+re);}
async function click(x,y,re){const at=fs.readFileSync(log,'utf8').length;await request('click?x='+x+'&y='+y);if(re)await wait(at,re);await sleep(220);}
(async()=>{
 const begin=fs.readFileSync(log,'utf8').length;
 // A cold display may sleep while the relatively slow flash installation finishes.
 // Reuse the initial screenshot's pixels to detect only a fully black panel.
 const {execFileSync}=require('child_process');const first=Buffer.from(await(await request('screen')).arrayBuffer());
 fs.writeFileSync(path.join(out,'cold-title-before-wake.png'),first);
 const check=execFileSync(process.env.EDEN_PYTHON||'python',['-c','from PIL import Image;import sys;im=Image.open(sys.argv[1]).convert("RGB");print(max(im.getextrema()[i][1] for i in range(3)))',path.join(out,'cold-title-before-wake.png')],{encoding:'utf8',windowsHide:true});
 if(Number(check.trim())<3){await request('wake');await sleep(1200);}
 await click(110,282,/EDEN_RW5 slots ready load/);await click(216,126,/EDEN_RW5 slot loaded 1 1 86/);
 fs.writeFileSync(path.join(out,'cold-save-01.png'),Buffer.from(await(await request('screen')).arrayBuffer()));
 await click(216,488,/EDEN_RW5 menu/);await click(216,140,/EDEN_RW5 slots ready load/);for(let i=0;i<7;i++)await click(354,474);await click(216,218,/EDEN_RW5 slot loaded 30 1 86/);
 await click(216,488,/EDEN_RW5 menu/);await click(216,462,/EDEN_RW5 background loaded title/);
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')),rpk=path.join(root,'dist',manifest.package+'.debug.'+manifest.versionName+'.rpk');
 assert.ok(!/EDEN_RW5 error|EDEN_RW5 background failed|ASSERTION FAILED|PANIC!!!|coredump/.test(fs.readFileSync(log,'utf8').slice(begin)));
 const report={result:'passed',coldBootAndOverwriteInstall:true,persistedSlots:[1,30],physicalDeviceTested:false,packageSHA256:crypto.createHash('sha256').update(fs.readFileSync(rpk)).digest('hex')};
 fs.writeFileSync(path.join(out,'cold-report.json'),JSON.stringify(report,null,2));console.log('COLD_OVERWRITE_PASSED',JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
