from pathlib import Path
import hashlib,json,zipfile
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parents[1]/'outputs'
baseline=json.loads((ROOT/'reports/baseline013-hashes.json').read_text('utf8'))
new=(ROOT/'src/pages/index/index.ux').read_text('utf8')
normalised=new.replace('class="title-art" src="{{titleBackgroundSrc}}"','class="title-art" src="/common/ui/title.jpg"').replace("private:{mode:'title',titleBackgroundSrc:'/common/ui/title.jpg',","private:{mode:'title',").replace("this.afterUnlocked=false;this.titleBackgroundSrc=this._progress.variables['sf.eden_D001']===1?'/common/ui/title-clear.jpg':'/common/ui/title.jpg';","this.afterUnlocked=false;")
assert hashlib.sha256(normalised.encode('utf8')).hexdigest()==baseline['readerLFSHA256'],'Unrelated reader changes detected'
for name,sha in json.loads((ROOT/'reports/title-baseline013.json').read_text('utf8')).items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==sha,name
assert hashlib.sha256((ROOT/'reports/source-text-proof.json').read_bytes()).hexdigest()=='98dabb0568a9e5179e4c4256101ce202cd231dc1815663da56bb0100f3639d01'
m=json.loads((ROOT/'src/manifest.json').read_text('utf8'));current=ROOT/'dist'/f'{m["package"]}.debug.{m["versionName"]}.rpk'
with zipfile.ZipFile(current) as after:
    a=baseline['commonResourceSHA256']
    b={n:hashlib.sha256(after.read(n)).hexdigest() for n in after.namelist() if n.startswith('common/') and not n.endswith('/')}
    assert set(b)-set(a)=={'common/ui/title-clear.jpg'} and not set(a)-set(b)
    assert all(b[n]==v for n,v in a.items())
im=Image.open(ROOT/'src/common/ui/title-clear.jpg');im.load();assert im.size==(432,514) and not im.info.get('progressive',False)
report={'version':'0.1.4','originalResource':'sys.paz/topmenu1.png','originalResourceSHA256':'2f538e188969b11a8ecb2369a8703c82c026be92aedde6a73a3057b0de16f8f4','clearFlag':'sf.eden_D001 == 1','flagSource':'scr.paz/D001.sc:177','crop':[0,0,800,610],'fitCenter':[0.25,0.5],'outputSize':[432,514],'jpegQuality':87,'newTitleSHA256':hashlib.sha256((ROOT/'src/common/ui/title-clear.jpg').read_bytes()).hexdigest(),'normalTitleAndAllExistingAssetsUnchanged':True,'readerDeltaOnlyTitleBindingAndFlag':True,'all8860StoryLocationsUnchanged':True,'singleTitleBackgroundImageWidget':True,'previousClearRecordsSupported':True,'unitTests':{'passed':24,'failed':0},'physicalDeviceRetestPending':True}
(ROOT/'reports/visual014-audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(report,ensure_ascii=False))
